Here's your **updated README.md** with the improved **Troubleshooting** section:

---

````markdown
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
- openrouter (Deepseek API key) and openrouter URL

### 2. Installation

Clone or download the project files and open a terminal in the project folder (create a virtual environment if desired):

```bash
# Install dependencies
pip install -r requirements.txt
````

### 3. Environment Setup

In the `app` folder, create a file named `.env` and paste the following content:

```
DEEPSEEK_API = your_api_key         # Paste your API key here
DEEPSEEK_URL = "https://openrouter.ai/api/v1/chat/completions"
```

### 4. Database Setup

Create a folder named `database` to store the password and analysis history.

### 5. Model Setup

Download the model file from the link below and place it in the `model` folder:

[Model Link](https://drive.google.com/file/d/1lXyJE5qvZcQHHweOI4sGUHu053GHAAwF/view?usp=sharing)

### 6. Running the Application

**Terminal 1 – Start Backend:**

```bash
python app/app.py
```

Starts the FastAPI backend at `http://localhost:8000`

**Terminal 2 – Start Frontend:**

```bash
streamlit run ./streamlit_app/app.py
```

Starts the Streamlit frontend at `http://localhost:8501`

## File Structure

```
skin-disease-detection/
├── app/
│   ├── app.py           # FastAPI backend
│   ├── .env             # Environment file
├── database/
│   ├── skin_app.db      # Database (create this after cloning the repo)
├── model/
│   ├── model.py         # Local model logic
│   ├── dinov2_model     # Pretrained model file (download separately)
├── streamlit_app/
│   ├── app.py           # Streamlit frontend
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Usage

1. **Access the App**: Open `http://localhost:8501` in your browser
2. **Optional Login**: Create an account to save analysis history
3. **Upload Image**: Choose a clear skin image (PNG, JPG, JPEG)
4. **Analyze**: Click "Analyze Image" to get AI-powered insights
5. **Review Results**: View disease detection, confidence scores, and treatment suggestions
6. **View History**: If logged in, check your past analyses

## Important Notes

⚠️ **Medical Disclaimer**: This application is for educational and informational purposes only. Always consult a qualified healthcare professional for medical diagnosis and treatment.

## Troubleshooting

### Common Issues

**Relative Import Error (Backend)**
If you see the following error when starting the FastAPI backend:

```
ImportError: attempted relative import with no known parent package
```

Try running the backend using the `-m` flag:

```bash
python -m app.app
```

If the issue persists, set the `PYTHONPATH` environment variable as follows:

#### On Linux/Mac:

```bash
export PYTHONPATH=$(pwd)
```

#### On Windows:

**Using Command Prompt:**

```cmd
set PYTHONPATH=%cd%
```

**Using PowerShell:**

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

Then run the backend again:

```bash
python app/app.py
```

## License

This project is for educational purposes. Ensure compliance with medical software regulations in your jurisdiction.

```
