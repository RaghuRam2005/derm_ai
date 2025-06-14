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

# Pydantic models
class ImageAnalysisRequest(BaseModel):
    image_data: str  # base64 encoded image
    user_id: Optional[int] = None

class AnalysisResponse(BaseModel):
    disease: str
    description: str
    treatments: list
    confidence: float
    disclaimer: str

def base64_to_image(base64_str: str) -> Image.Image:
    """Convert base64 string to PIL Image"""
    try:
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        return image
    except Exception as e:
        raise ValueError(f"Invalid image data: {str(e)}")

def extract_confidence_from_text(text: str) -> float:
    """Extract confidence percentage from text"""
    # Look for patterns like "95%", "85% confident", etc.
    confidence_patterns = [
        r'(\d+)%\s*confident',
        r'confidence[:\s]*(\d+)%',
        r'(\d+)%\s*confidence',
        r'probability[:\s]*(\d+)%',
        r'(\d+)%\s*likely',
        r'(\d+)%\s*chance'
    ]
    
    for pattern in confidence_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    # Default confidence if not found
    return 75.0

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

def parse_gemini_response(response_text: str) -> dict:
    """Parse Gemini response and extract structured information"""
    try:
        # Try to parse as JSON first
        if response_text.strip().startswith('{'):
            return json.loads(response_text)
    except:
        pass
    
    # Parse text response
    lines = response_text.split('\n')
    result = {
        'disease': 'Unknown Skin Condition',
        'description': '',
        'treatments': [],
        'confidence': extract_confidence_from_text(response_text)
    }
    
    current_section = None
    description_lines = []
    treatment_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Remove markdown formatting from line
        clean_line = clean_text(line)
        
        # Detect sections
        line_lower = clean_line.lower()
        if any(keyword in line_lower for keyword in ['disease', 'condition', 'diagnosis']):
            current_section = 'disease'
            # Extract disease name
            if ':' in clean_line:
                disease_name = clean_line.split(':', 1)[1].strip()
                result['disease'] = disease_name if disease_name else 'Unknown Skin Condition'
            continue
        elif any(keyword in line_lower for keyword in ['description', 'symptoms', 'characteristics']):
            current_section = 'description'
            continue
        elif any(keyword in line_lower for keyword in ['treatment', 'recommendation', 'therapy']):
            current_section = 'treatments'
            continue
        
        # Add content to appropriate section
        if current_section == 'description':
            if clean_line and not any(skip in clean_line.lower() for skip in ['disease', 'condition', 'diagnosis']):
                description_lines.append(clean_line)
        elif current_section == 'treatments':
            if clean_line and not any(skip in clean_line.lower() for skip in ['treatment', 'recommendation', 'therapy', 'note:', 'disclaimer:', 'important:']):
                treatment_lines.append(clean_line)
        elif current_section is None and clean_line:
            # If no section detected, try to categorize
            if any(keyword in clean_line.lower() for keyword in ['symptom', 'appear', 'characteristic', 'present']):
                description_lines.append(clean_line)
    
    # Compile results with fallbacks
    if description_lines:
        result['description'] = ' '.join(description_lines)
    else:
        # Fallback description
        result['description'] = f"A skin condition that requires medical evaluation. The image shows characteristics that suggest {result['disease'].lower()}."
    
    if treatment_lines:
        result['treatments'] = treatment_lines
    else:
        # Fallback treatments based on common recommendations
        result['treatments'] = [
            "Consult a dermatologist for proper diagnosis",
            "Keep the affected area clean and dry",
            "Avoid scratching or irritating the area",
            "Consider topical treatments as recommended by healthcare provider"
        ]
    
    # Ensure we have meaningful content
    if result['description'] == '':
        result['description'] = f"Visual analysis suggests {result['disease']}. Professional medical evaluation recommended for accurate diagnosis."
    
    return result

@app.get("/")
async def root():
    return {"message": "Skin Disease Detection API", "status": "running"}

@app.post("/analyze", response_model=dict)
async def analyze_skin_image(request: ImageAnalysisRequest):
    try:
        # Convert base64 to image
        image = base64_to_image(request.image_data)
        
        # Prepare detailed prompt for Gemini
        prompt = """
        You are a medical AI assistant specializing in dermatology. Analyze this skin image and provide a detailed assessment.

        MANDATORY: You MUST provide ALL the following sections in your response:

        Disease/Condition: [Specific name of the skin condition - be precise]

        Description: [Provide a detailed description of what you observe, including visual characteristics, symptoms, and appearance. This section is REQUIRED and must be at least 2-3 sentences.]

        Recommended Treatments:
        [List 4-6 specific treatment recommendations. This section is REQUIRED. Include both immediate care and professional treatments.]

        Confidence Level: [Your confidence as a percentage, e.g., "85% confident"]

        CRITICAL REQUIREMENTS:
        1. ALWAYS provide a specific disease/condition name (not "unknown" or "unclear")
        2. ALWAYS provide a detailed description (minimum 2-3 sentences)
        3. ALWAYS provide at least 4 treatment recommendations
        4. Use simple text format - NO markdown symbols like ** or * 
        5. Be specific about the skin condition you detect
        6. Include confidence level as a percentage
        7. Consider common conditions: eczema, psoriasis, dermatitis, acne, fungal infections, rosacea, etc.

        Format your response exactly like this (without markdown formatting):

        Disease/Condition: [condition name]

        Description: [detailed description here]

        Recommended Treatments:
        Consult a dermatologist for proper diagnosis
        [treatment 2]
        [treatment 3]
        [treatment 4]

        Confidence Level: [percentage] confident

        Remember: This is for educational purposes and should not replace professional medical consultation.
        """
        
        # Generate response using Gemini
        response = model.generate_content([prompt, image])
        
        if not response.text:
            raise HTTPException(status_code=500, detail="No response from AI model")
        
        # Parse the response
        parsed_result = parse_gemini_response(response.text)
        
        # Add disclaimer
        parsed_result['disclaimer'] = "This AI analysis is for informational purposes only and should not replace professional medical advice."
        
        # Ensure confidence is within reasonable bounds
        if parsed_result['confidence'] > 95:
            parsed_result['confidence'] = 95.0
        elif parsed_result['confidence'] < 50:
            parsed_result['confidence'] = 65.0
        
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
