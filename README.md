# Skin Disease Detection System

A complete AI-powered skin disease detection system using Streamlit frontend, FastAPI backend, and SQLITE database.

## Features

- 🔬 **AI-Powered Analysis**: Uses Deepseek model through openrouter API for disease analysis
- 👤 **User Authentication**: Optional login system to save analysis history
- 📊 **Analysis History**: View previous analyses and results
- 🎯 **Confidence Scoring**: Get confidence levels for each diagnosis
- 💡 **Treatment Recommendations**: Receive potential treatment suggestions
- 🔒 **Secure**: Password hashing and user data protection

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- openrouter (deepseek API key) and openrouter URL

### 2. Installation

Clone or download the project files and open terminal in the project folder (create a virtual environment (optional))

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

In `app` folder create a file named `.env` and paste the API key and URL as shown below

```
DEEPSEEK_API = your api key         # Paste your API here
DEEPSEEK_URL = "https://openrouter.ai/api/v1/chat/completions"
```
### 4. Database setup

create a folder named `database` for storing the password and analysis history.

### 5. Model setup

Download the model file from the link below and paste it in the `model` folder

Model link: https://drive.google.com/file/d/1lXyJE5qvZcQHHweOI4sGUHu053GHAAwF/view?usp=sharing

### 6. Running the Application

**Terminal 1 - Start Backend:**
```bash
python app/app.py
```
This starts the FastAPI backend on `http://localhost:8000`

**Terminal 2 - Start Frontend:**
```bash
streamlit run ./streamlit_app/app.py
```
This starts the Streamlit frontend on `http://localhost:8501`

## File Structure

```
skin-disease-detection/
app/
   ├── app.py           # FastAPI backend
   ├── .env             # Environment File
database/
   ├── skin_app.db      # Database folder (create this after cloning the repo)
model/
   ├── model.py         # Local model for finding the disease name
   ├── dinov2_model     # Pretrained model file (download this from link given below)
streamlit_app/
   ├── app.py           # Streamlit frontend
├── requirements.txt    # Python dependencies
├── .gitignore          # Ignore files
└── README.md          # This file
```

## Usage

1. **Access the App**: Open `http://localhost:8501` in your browser
2. **Optional Login**: Create an account to save your analysis history
3. **Upload Image**: Choose a clear skin image (PNG, JPG, JPEG)
4. **Analyze**: Click "Analyze Image" to get AI-powered insights
5. **Review Results**: Get disease detection, confidence score, and treatments
6. **View History**: If logged in, check your previous analyses

## Important Notes

⚠️ **Medical Disclaimer**: This application is for educational and informational purposes only. Always consult with qualified healthcare professionals for proper medical diagnosis and treatment.

## Troubleshooting

### Common Issues
**Relative Import Error (backend)**
If there if a **Error message** like this while starting the backend FAST API server.
```
ImportError: attempted relative import with no known parent package
```
Then run the python file as given below.
```
python -m app/app.py
```
If it doesn't work and shows the same error message, then use the commands given below.
**For linux/Mac:**
```
export PYTHONPATH=$(pwd)
```
**For windows:**
If using **command prompt**, use this
```
set PYTHONPATH=%cd%
```
If using **powershell**, use this
```
$env:PYTHONPATH = (Get-Location).Path
```
Then finally, run the python file 
```
python app/app.py
```

## License

This project is for educational purposes. Please ensure compliance with medical software regulations in your jurisdiction.
