from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import base64
import io
from PIL import Image
import os
from typing import Optional
import json
import re
from dotenv import load_dotenv
from model.model import ModelHandler

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

# Configure Gemini API
# Set your API key as environment variable: GEMINI_API_KEY
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API")
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')
image_model = ModelHandler()

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

def parse_gemini_response(response_text: str, disease_name: str) -> dict:
    """Parse Gemini response and extract 'description' and 'treatment' from raw text."""
    try:
        # If response is JSON formatted, parse it directly
        if response_text.strip().startswith('{'):
            return json.loads(response_text)
    except Exception:
        pass

    response_text = clean_text(response_text)
    
    result = {
        'description': '',
        'treatment': []
    }

    # Extract under headings
    desc_match = re.search(r'Description of .*?:\s*(.*?)(?:Treatments for|$)', response_text, re.IGNORECASE | re.DOTALL)
    treatment_match = re.search(r'Treatments for .*?:\s*(.*)', response_text, re.IGNORECASE | re.DOTALL)

    if desc_match:
        result['description'] = desc_match.group(1).strip()

    if treatment_match:
        # Split by newlines or periods if necessary, avoiding blank entries
        raw_treatments = treatment_match.group(1).strip()
        treatments = re.split(r'\n|(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', raw_treatments)
        result['treatment'] = [t.strip() for t in treatments if t.strip()]
    
    # Fallbacks
    if not result['description']:
        result['description'] = f"Visual investigation suggests the condition is likely {disease_name}. Further description couldn't be determined."

    if not result['treatment']:
        result['treatment'] = [
            "Consult a dermatologist for proper diagnosis.",
            "Keep the affected area clean and dry.",
            "Avoid scratching or irritating the affected area."
        ]

    return result

@app.get("/")
async def root():
    return {"message": "Skin Disease Detection API", "status": "running"}

@app.post("/analyze", response_model=dict)
async def analyze_skin_image(request: ImageAnalysisRequest):
    try:
        # Convert base64 to image
        image = base64_to_image(request.image_data)
        disease = image_model.predict(image)
        
        # Prepare detailed prompt for Gemini
        prompt = f"""
        Description of {disease['class']} (generate it in a small paragraph):
        Treatments for {disease['class']} (generate a points with no numbering, only a space between each point):
        generate answer under these two headings, do not change or modify them
        """
        
        # Generate response using Gemini
        response = model.generate_content([prompt])
        
        if not response.text:
            raise HTTPException(status_code=500, detail="No response from AI model")
        
        # Parse the response
        parsed_result = parse_gemini_response(response.text, disease['class'])
        parsed_result['disease'] = disease['class']
        parsed_result['confidence'] = disease['confidence']

        return parsed_result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "gemini-1.5-flash"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
