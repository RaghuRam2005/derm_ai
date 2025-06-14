# Skin Disease Detection System

A complete AI-powered skin disease detection system using Streamlit frontend, FastAPI backend, and Google Gemini AI.

## Features

- 🔬 **AI-Powered Analysis**: Uses Google Gemini AI to analyze skin images
- 👤 **User Authentication**: Optional login system to save analysis history
- 📊 **Analysis History**: View previous analyses and results
- 🎯 **Confidence Scoring**: Get confidence levels for each diagnosis
- 💡 **Treatment Recommendations**: Receive potential treatment suggestions
- 🔒 **Secure**: Password hashing and user data protection

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Google Gemini API key (free tier available)

### 2. Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key for later use

### 3. Installation

```bash
# Clone or download the project files
# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Setup

Set your Gemini API key as an environment variable:

**Windows:**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY=your_api_key_here
```

### 5. Running the Application

**Terminal 1 - Start Backend:**
```bash
python main.py
```
This starts the FastAPI backend on `http://localhost:8000`

**Terminal 2 - Start Frontend:**
```bash
streamlit run app.py
```
This starts the Streamlit frontend on `http://localhost:8501`

## File Structure

```
skin-disease-detection/
├── app.py              # Streamlit frontend
├── main.py             # FastAPI backend
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── skin_app.db        # SQLite database (created automatically)
```

## Usage

1. **Access the App**: Open `http://localhost:8501` in your browser
2. **Optional Login**: Create an account to save your analysis history
3. **Upload Image**: Choose a clear skin image (PNG, JPG, JPEG)
4. **Analyze**: Click "Analyze Image" to get AI-powered insights
5. **Review Results**: Get disease detection, confidence score, and treatments
6. **View History**: If logged in, check your previous analyses

## API Endpoints

- `GET /` - API status
- `POST /analyze` - Analyze skin image
- `GET /health` - Health check

## Features in Detail

### Frontend (Streamlit)
- Clean, intuitive interface
- Image upload and preview
- User authentication system
- Analysis history management
- Responsive design

### Backend (FastAPI)
- RESTful API design
- Google Gemini AI integration
- Image processing and analysis
- Structured response parsing
- Error handling and validation

### Database
- SQLite for user data and history
- Password hashing for security
- Analysis history storage

## Important Notes

⚠️ **Medical Disclaimer**: This application is for educational and informational purposes only. Always consult with qualified healthcare professionals for proper medical diagnosis and treatment.

### Privacy and Security
- Passwords are hashed using SHA-256
- Images are not permanently stored
- Analysis history is linked to user accounts

### Limitations
- Requires internet connection for AI analysis
- Analysis quality depends on image quality
- Not a substitute for professional medical advice

## Troubleshooting

### Common Issues

1. **Backend Connection Error**
   - Ensure backend is running on port 8000
   - Check if GEMINI_API_KEY is set correctly

2. **API Key Issues**
   - Verify your Gemini API key is valid
   - Check if you have API quota remaining

3. **Image Upload Issues**
   - Ensure image is in supported format (PNG, JPG, JPEG)
   - Check image file size (should be reasonable)

4. **Database Issues**
   - Delete `skin_app.db` to reset the database
   - Ensure write permissions in the app directory

## Customization

### Adding New Features
- Modify `app.py` for frontend changes
- Update `main.py` for backend functionality
- Add new dependencies to `requirements.txt`

### Styling
- Streamlit supports custom CSS
- Modify the `st.set_page_config()` for page settings

## Development

### Running in Development Mode

Backend with auto-reload:
```bash
uvicorn main:app --reload --port 8000
```

Frontend with auto-reload:
```bash
streamlit run app.py --server.runOnSave true
```

## Production Deployment

For production deployment, consider:
- Using environment variables for sensitive data
- Setting up proper database (PostgreSQL, MySQL)
- Using HTTPS for security
- Implementing rate limiting
- Adding logging and monitoring

## License

This project is for educational purposes. Please ensure compliance with medical software regulations in your jurisdiction.