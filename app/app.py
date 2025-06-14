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
            
        # Detect sections
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['disease', 'condition', 'diagnosis']):
            current_section = 'disease'
            # Extract disease name
            if ':' in line:
                result['disease'] = line.split(':', 1)[1].strip()
            continue
        elif any(keyword in line_lower for keyword in ['description', 'symptoms', 'characteristics']):
            current_section = 'description'
            continue
        elif any(keyword in line_lower for keyword in ['treatment', 'recommendation', 'therapy']):
            current_section = 'treatments'
            continue
        
        # Add content to appropriate section
        if current_section == 'description':
            description_lines.append(line)
        elif current_section == 'treatments':
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                treatment_lines.append(line[1:].strip())
            elif line and not line.startswith(('Note:', 'Disclaimer:', 'Important:')):
                treatment_lines.append(line)
        elif current_section is None:
            # If no section detected, add to description
            description_lines.append(line)
    
    # Compile results
    if description_lines:
        result['description'] = ' '.join(description_lines)
    if treatment_lines:
        result['treatments'] = treatment_lines
    
    # Fallback if no structured data found
    if not result['description'] and not result['treatments']:
        result['description'] = response_text[:500] + "..." if len(response_text) > 500 else response_text
    
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

        Please provide your response in the following format:

        **Disease/Condition:** [Name of the skin condition]

        **Description:** [Detailed description of what you observe, including symptoms, appearance, and characteristics]

        **Recommended Treatments:**
        - [Treatment option 1]
        - [Treatment option 2]
        - [Treatment option 3]
        - [Additional recommendations]

        **Confidence Level:** [Your confidence percentage, e.g., "85% confident"]

        Important guidelines:
        1. Be specific about the skin condition you detect
        2. Provide confidence level as a percentage
        3. Include both topical and systemic treatment options where appropriate
        4. Mention when to see a healthcare provider
        5. If you're uncertain, suggest differential diagnoses
        6. Consider common skin conditions like eczema, psoriasis, dermatitis, acne, fungal infections, etc.

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