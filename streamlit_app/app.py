import streamlit as st
import requests
import json
import base64
from PIL import Image
import io
from datetime import datetime
import sqlite3
import hashlib
import os

# Configure page
st.set_page_config(
    page_title="Skin Disease Detection",
    page_icon="🔬",
    layout="wide"
)

# Database Path
BASE_PATH = os.path.dirname(__file__)
DB_PATH = os.path.abspath(os.path.join(BASE_PATH, "..", "database", "skin_app.db"))

# Backend URL
BACKEND_URL = "http://localhost:8000"

# Database setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Analysis history table
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  image_name TEXT,
                  analysis_result TEXT,
                  confidence REAL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[1] == hash_password(password):
        return result[0]  # Return user ID
    return None

def create_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                 (username, hash_password(password)))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None

def save_analysis(user_id, image_name, analysis_result, confidence):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Use disease name as the display name
    disease_name = analysis_result.get('disease', 'Unknown Condition')
    
    c.execute("""INSERT INTO analysis_history 
                 (user_id, image_name, analysis_result, confidence) 
                 VALUES (?, ?, ?, ?)""",
             (user_id, disease_name, json.dumps(analysis_result), confidence))
    conn.commit()
    conn.close()

def get_user_history(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT image_name, analysis_result, confidence, timestamp 
                 FROM analysis_history 
                 WHERE user_id = ? 
                 ORDER BY timestamp DESC""", (user_id,))
    results = c.fetchall()
    conn.close()
    return results

def image_to_base64(image):
    """Convert PIL image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def analyze_skin_image(image, user_id=None):
    """Send image to backend for analysis"""
    try:
        # Convert image to base64
        img_base64 = image_to_base64(image)
        
        # Prepare payload
        payload = {
            "image_data": img_base64,
            "user_id": user_id
        }
        
        # Send to backend
        st.info("Sending image to AI model for analysis...")
        response = requests.post(f"{BACKEND_URL}/analyze", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            st.success("Analysis completed successfully!")
            return result
        else:
            st.error(f"Backend error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend. Make sure the backend server is running on port 8000.")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The analysis is taking longer than expected.")
        return None
    except Exception as e:
        st.error(f"Error analyzing image: {str(e)}")
        return None

def display_analysis_results(result):
    """Display analysis results in a formatted way"""
    if not result:
        st.error("No analysis results to display")
        return
    
    # Display in a clean format
    st.markdown("### 🎯 Detected Condition")
    disease = result.get('disease', 'Unknown Condition')
    st.write(f"**{disease}**")

    st.markdown("### 📊 Confidence Level")
    confidence = result.get('confidence', 0.0)
    st.progress(confidence)
    st.write(f"{confidence*100:.1f}%")
    
    st.markdown("### 📝 Description")
    description = result.get('description', 'No description available')
    if description and description.strip():
        st.write(description)
    else:
        st.info("No description was provided for this condition.")
    
    st.markdown("### 🤒 Symptoms")
    symptoms = result.get('Symptoms', [])
    if symptoms and len(symptoms) > 0:
        for i, symptom in enumerate(symptoms, 1):
            if symptom and symptom.strip():
                st.write(f"{i}. {symptom}")
    else:
        st.info("No specific symptoms were listed for this condition.")
    
    st.markdown("### 💊 Recommended Treatments")
    treatments = result.get('treatments', [])
    if treatments and len(treatments) > 0:
        for i, treatment in enumerate(treatments, 1):
            if treatment and treatment.strip():
                st.write(f"{i}. {treatment}")
    else:
        st.info("No specific treatments were recommended.")

    st.markdown("### 🩺 When to Consult a Doctor")
    medical_care = result.get('medical_care', [])
    if medical_care and len(medical_care) > 0:
        for i, care_advice in enumerate(medical_care, 1):
            if care_advice and care_advice.strip():
                st.write(f"{i}. {care_advice}")
    else:
        st.info("No specific recommendations for when to consult a doctor were provided for this condition. " \
                "If you have concerns or symptoms worsen, please consult a healthcare professional.")

# Initialize database
init_db()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Sidebar for login/logout
with st.sidebar:
    st.header("👤 User Account")
    
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login")
            login_username = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Login"):
                user_id = authenticate_user(login_username, login_password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = login_username
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        with tab2:
            st.subheader("Sign Up")
            signup_username = st.text_input("Choose Username", key="signup_user")
            signup_password = st.text_input("Choose Password", type="password", key="signup_pass")
            signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            
            if st.button("Sign Up"):
                if signup_password != signup_confirm:
                    st.error("Passwords don't match")
                elif len(signup_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif len(signup_username) < 3:
                    st.error("Username must be at least 3 characters")
                else:
                    user_id = create_user(signup_username, signup_password)
                    if user_id:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists")
    
    else:
        st.success(f"Welcome, {st.session_state.username}!")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
        
        st.markdown("---")
        
        # History section
        if st.button("View Analysis History"):
            st.session_state.show_history = True
            st.rerun()

# Main content
st.title("🔬 Skin Disease Detection System")
st.markdown("Upload an image of skin condition for AI-powered analysis")

# Main tabs
if st.session_state.logged_in and st.session_state.get('show_history', False):
    if st.button("← Back to Analysis"):
        st.session_state.show_history = False
        st.rerun()
    
    st.header("📊 Analysis History")
    history = get_user_history(st.session_state.user_id)
    
    if history:
        for i, (disease_name, analysis_json, confidence, timestamp) in enumerate(history):
            with st.expander(f"{disease_name} - {timestamp} (Confidence: {confidence*100:.1f}%)"):
                try:
                    analysis = json.loads(analysis_json)
                    display_analysis_results(analysis)
                except json.JSONDecodeError:
                    st.error("Error loading analysis data")
    else:
        st.info("No analysis history found.")

else:
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a skin image...", 
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear image of the skin condition you want to analyze"
    )
    
    if uploaded_file is not None:
        # Display image
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📸 Uploaded Image")
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
        
        with col2:
            st.subheader("🔍 Analysis")
            
            if st.button("Analyze Image", type="primary"):
                with st.spinner("Analyzing image... This may take a few moments."):
                    result = analyze_skin_image(image, st.session_state.user_id)
                    
                    if result:
                        # Display results
                        display_analysis_results(result)
                        
                        # Disclaimer
                        st.warning("⚠️ **Medical Disclaimer:** This is an AI-powered analysis for informational purposes only. " \
                                 "Always consult with a qualified healthcare professional for proper medical diagnosis and treatment.")
                        
                        # Save to history if logged in
                        if st.session_state.logged_in:
                            try:
                                save_analysis(
                                    st.session_state.user_id,
                                    uploaded_file.name,
                                    result,
                                    result.get('confidence', 0.0)
                                )
                                st.info("✅ Analysis saved to your history!")
                            except Exception as e:
                                st.warning(f"Could not save to history: {str(e)}")

# Instructions
with st.expander("📋 How to use this app"):
    st.markdown("""
    1. **Optional:** Create an account to save your analysis history
    2. **Upload Image:** Choose a clear photo of the skin condition
    3. **Analyze:** Click the analyze button to get AI-powered insights
    4. **Review Results:** Get information about potential conditions and treatments
    5. **Consult Professional:** Always verify results with a healthcare provider
    
    **Tips for better results:**
    - Use good lighting and focus
    - Include the affected area clearly
    - Avoid blurry or distant images
    - Multiple angles can be helpful
    """)

st.markdown("---")
st.markdown("*Powered by AI - For educational purposes only*")
