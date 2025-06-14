from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
from PIL import Image
import os
from typing import Optional
import json
import re
from dotenv import load_dotenv
from model.model import ModelHandler
from functools import lru_cache
import requests

# Initialize FastAPI app
app = FastAPI(title="Skin Disease Detection API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
# Configure deepseek API keys
# Set your API key as environment variable: DEEPSEEK_KEY
OPENROUTER_API, OPENROUTER_URL = os.getenv("DEEPSEEK_API"), os.getenv("DEEPSEEK_URL")
IMAGE_MODEL = ModelHandler()

# Pydantic models
class ImageAnalysisRequest(BaseModel):
    image_data: str  # base64 encoded image
    user_id: Optional[int] = None

class AnalysisResponse(BaseModel):
    disease: str
    description: str
    treatments: list
    confidence: float

def base64_to_image(base64_str: str) -> Image.Image:
    """Convert base64 string to PIL Image"""
    try:
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        return image
    except Exception as e:
        raise ValueError(f"Invalid image data: {str(e)}")

def clean_text(text: str) -> str:
    """Clean text by removing markdown formatting and extra characters"""
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Remove *italic*
    text = re.sub(r'#+\s*', '', text)               # Remove headers
    text = re.sub(r'[-•*]\s*', '', text)            # Remove bullet points
    text = re.sub(r'\n+', ' ', text)                # Replace multiple newlines with space
    text = re.sub(r'\s+', ' ', text)                # Replace multiple spaces with single space
    return text.strip()

def parse_sections(content):
    """Parse the content into structured sections"""
    sections = {
        "description": "",
        "Symptoms": [],
        "treatments": [],
        "medical_care": []
    }
    
    current_section = None
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers (case insensitive)
        line_lower = line.lower()
        if "description:" in line_lower:
            current_section = "description"
            # If there's content after the colon, add it
            content_after_colon = line.split(':', 1)[1].strip() if ':' in line else ""
            if content_after_colon:
                sections["description"] = content_after_colon
            continue
        elif "symptoms:" in line_lower:
            current_section = "Symptoms"
            continue
        elif "treatment:" in line_lower:
            current_section = "treatments"
            continue
        elif "when to seek medical care:" in line_lower or "medical care:" in line_lower:
            current_section = "medical_care"
            continue
        
        # Skip lines that are just special characters or formatting
        if re.match(r'^[\s`~{}[\]\\*-•]+$', line):
            continue
            
        # Clean the line
        cleaned_line = clean_text(line)
        if not cleaned_line:
            continue
            
        # Add content to appropriate section
        if current_section:
            if current_section == "description":
                if sections["description"]:
                    sections["description"] += " "
                sections["description"] += cleaned_line
            else:
                # Only add non-empty lines
                if cleaned_line and len(cleaned_line) > 2:  # Avoid single characters
                    sections[current_section].append(cleaned_line)
    
    # Clean up the sections
    sections["description"] = sections["description"].strip()
    
    # Remove duplicates and clean up lists
    for key in ["Symptoms", "treatments", "medical_care"]:
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in sections[key]:
            item_clean = item.strip()
            if item_clean and item_clean.lower() not in seen and len(item_clean) > 5:
                seen.add(item_clean.lower())
                unique_items.append(item_clean)
        sections[key] = unique_items
    
    return sections

@lru_cache(maxsize=100)
def get_disease_info(disease_name):
    """Get detailed information about a skin disease using DeepSeek"""
    try:
        prompt = f"""Provide comprehensive medical information about the skin condition "{disease_name}". Format your response exactly as follows:

Description:
Provide a clear, detailed overview of the condition in 2-3 sentences. Include what causes it, what it looks like, and who it typically affects.

Symptoms:
List the main symptoms and signs of this condition. Each symptom should be on a separate line.

Treatment:
List the available treatment options, including both medical treatments and home care recommendations. Each treatment should be on a separate line.

When to Seek Medical Care:
List specific situations when someone should see a doctor for this condition. Each situation should be on a separate line.

Please provide accurate, helpful medical information while being clear that this is for educational purposes only."""

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Skin Disease Detection System"
        }

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a knowledgeable dermatology assistant. Provide clear, accurate medical information about skin conditions. Use the exact format requested with clear section headers. Keep information concise but comprehensive."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }

        print(f"Making API request to DeepSeek for disease: {disease_name}")
        
        if not OPENROUTER_URL:
            raise Exception("openrouter URL was not set.")
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=data,
            timeout=30
        )

        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"Raw API Response: {content[:200]}...")
            
            # Parse the content into structured sections
            sections = parse_sections(content)
            
            print(f"Parsed sections: {sections}")
            
            # Ensure all sections have content - provide defaults if empty
            if not sections["description"]:
                sections["description"] = f"A skin condition that requires medical evaluation for proper diagnosis and treatment."
            
            if not sections["Symptoms"]:
                sections["Symptoms"] = [
                    "Visible changes in skin appearance",
                    "May cause discomfort or irritation",
                    "Consult a healthcare provider for accurate symptom assessment"
                ]
            
            if not sections["treatments"]:
                sections["treatments"] = [
                    "Consult a dermatologist for proper diagnosis and treatment plan",
                    "Keep the affected area clean and dry",
                    "Avoid scratching or further irritating the area",
                    "Follow healthcare provider's recommendations"
                ]
            
            if not sections["medical_care"]:
                sections["medical_care"] = [
                    "If symptoms persist or worsen",
                    "If you experience pain or severe discomfort",
                    "If the condition spreads to other areas",
                    "For proper diagnosis and treatment recommendations"
                ]
            
            return sections
            
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Error in get_disease_info: {str(e)}")
        # Return default information if API fails
        return {
            "description": f"A skin condition identified as {disease_name}. Please consult a healthcare professional for proper diagnosis and treatment.",
            "Symptoms": [
                "Visible changes in skin appearance",
                "May cause discomfort or irritation",
                "Symptoms may vary between individuals"
            ],
            "treatments": [
                "Consult a dermatologist for proper diagnosis and treatment plan",
                "Keep the affected area clean and dry",
                "Avoid scratching or further irritating the area"
            ],
            "medical_care": [
                "If symptoms persist or worsen",
                "If you experience pain or severe discomfort",
                "For proper diagnosis and treatment recommendations"
            ]
        }

@app.get("/")
async def root():
    return {"message": "Skin Disease Detection API", "status": "running"}

@app.post("/analyze", response_model=dict)
async def analyze_skin_image(request: ImageAnalysisRequest):
    try:
        print("Starting image analysis...")
        
        # Convert base64 to image
        image = base64_to_image(request.image_data)
        print("Image converted successfully")
        
        # Get disease prediction from model
        disease = IMAGE_MODEL.predict(image)
        print(f"Disease prediction: {disease}")
        
        # Get detailed information using DeepSeek
        print(f"Getting disease info for: {disease['class']}")
        disease_info = get_disease_info(disease['class'])
        
        # Prepare final response
        response = {
            "disease": disease['class'],
            "confidence": disease['confidence'],
            "description": disease_info["description"],
            "Symptoms": disease_info["Symptoms"],
            "treatments": disease_info["treatments"],
            "medical_care": disease_info["medical_care"]
        }
        
        print(f"Final response: {response}")
        return response
    
    except ValueError as e:
        print(f"ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "deepseek"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
