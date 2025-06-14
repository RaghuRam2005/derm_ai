import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import os
from dotenv import load_dotenv
import timm

# Load environment variables
load_dotenv()

class DinoV2Classifier(nn.Module):
    def __init__(self, model_name, num_classes, pretrained=True):
        super().__init__()
        # Load DinoV2 base model
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=0,  # Remove classifier head
            img_size=224  # Use standard size for DinoV2
        )
        
        # Get embedding dimension for DinoV2 base
        embed_dim = 768  # DinoV2 base embedding dimension
        
        # Add classification head with more regularization
        self.classifier = nn.Sequential(
            nn.LayerNorm(embed_dim),
            nn.Linear(embed_dim, embed_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(embed_dim, num_classes)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        return self.classifier(features)

class ModelHandler:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        # Update class names to match exactly with training data
        self.class_names = [
            "Acne and Rosacea",
            "Actinic Keratosis Basal Cell Carcinoma",
            "Atopic Dermatitis",
            "Bullous Disease",
            "Cellulitis Impetigo",
            "Eczema",
            "Exanthems and Drug Eruptions",
            "Hair Loss Photos Alopecia and other Hair Diseases",
            "Herpes HPV and other STDs",
            "Light Diseases and Disorders of Pigmentation",
            "Lupus and other Connective Tissue diseases",
            "Melanoma Skin Cancer Nevi and Moles",
            "Nail Fungus and other Nail Disease",
            "Poison Ivy Photos and other Contact Dermatitis",
            "Psoriasis pictures Lichen Planus and related diseases",
            "Scabies Lyme Disease and other Infestations and Bites",
            "Seborrheic Keratoses and other Benign Tumors",
            "Systemic Disease",
            "Tinea Ringworm Candidiasis and other Fungal Infections",
            "Urticaria Hives",
            "Vascular Tumors",
            "Vasculitis Photos",
            "Warts Molluscum and other Viral Infections"
        ]
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),  # Use standard size for DinoV2
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                              std=[0.229, 0.224, 0.225])
        ])
        self.load_model()

    def load_model(self):
        """
        Load the pre-trained PyTorch model
        """
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "dinov2_dermnet_model.pth")

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at: {model_path}")

            self.model = DinoV2Classifier(
                model_name='vit_base_patch14_dinov2',
                num_classes=len(self.class_names),
                pretrained=False
            )

            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model = self.model.to(self.device)
            self.model.eval()

        except Exception as e:
            self.model = None  # Prevent any undefined state
            print(f"Error loading model: {str(e)}")
            raise RuntimeError(f"Model loading failed: {str(e)}")


    def preprocess_image(self, image):
        """
        Preprocess the input image for model prediction
        """
        # Apply transformations
        image_tensor = self.transform(image)
        # Add batch dimension
        image_tensor = image_tensor.unsqueeze(0)
        return image_tensor

    def predict(self, image):
        """
        Make prediction on the input image
        """
        if self.model is None:
            raise RuntimeError("Model is not loaded. Check logs for loading errors.")

        try:
            # Preprocess the image
            processed_image = self.preprocess_image(image).to(self.device)

            # Make prediction
            with torch.no_grad():
                outputs = self.model(processed_image)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probabilities, 1)

                predicted_class = self.class_names[int(predicted.item())]
                confidence_value = confidence.item()

                print(f"Predicted class: {predicted_class}")
                print(f"Confidence: {confidence_value:.2%}")

                return {
                    "class": predicted_class,
                    "confidence": confidence_value
                }

        except Exception as e:
            print(f"Error in predict method: {str(e)}")
            raise Exception(f"Error during prediction: {str(e)}")
