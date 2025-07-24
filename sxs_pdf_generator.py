import streamlit as st
import io
import base64
import re
import requests
import json
import html
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from datetime import datetime
import tempfile
import os
import traceback
from typing import List, Optional, BinaryIO, Tuple
import time

# Configure page
st.set_page_config(
    page_title="SxS Model Comparison PDF Generator",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

# Google Apps Script Webhook Configuration
WEBHOOK_URL = st.secrets.get("webhook_url", "")
WEBHOOK_TIMEOUT = 30

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Model configurations
MODEL_CONFIGS = {
    "Gemini": {
        "color": "#4285f4",
        "logo_text": "Gemini",
        "brand_names": ["Gemini", "Bard", "Google AI Studio", "AIS"]
    },
    "ChatGPT": {
        "color": "#10a37f",
        "logo_text": "ChatGPT",
        "brand_names": ["ChatGPT", "OpenAI", "GPT"]
    },
    "AIS 2.5 PRO": {
        "color": "#4285f4",
        "logo_text": "AIS 2.5 PRO",
        "brand_names": ["AIS", "Google AI Studio", "Gemini"]
    },
    "Bard 2.5 Pro": {
        "color": "#4285f4",
        "logo_text": "Bard 2.5 Pro",
        "brand_names": ["Bard", "Google AI Studio", "Gemini"]
    },
    "Bard 2.5 Flash": {
        "color": "#4285f4",
        "logo_text": "Bard 2.5 Flash",
        "brand_names": ["Bard", "Google AI Studio", "Gemini"]
    },
    "cGPT o3": {
        "color": "#10a37f",
        "logo_text": "cGPT o3",
        "brand_names": ["ChatGPT", "OpenAI", "GPT"]
    },
    "cGPT 4o": {
        "color": "#10a37f",
        "logo_text": "cGPT 4o",
        "brand_names": ["ChatGPT", "OpenAI", "GPT"]
    },
    "AIS 2.5 Flash": {
        "color": "#4285f4",
        "logo_text": "AIS 2.5 Flash",
        "brand_names": ["AIS", "Google AI Studio", "Gemini"]
    }
}

# Model combination options
MODEL_COMBINATIONS = [
    ("Bard 2.5 Pro", "AIS 2.5 PRO"),
    ("AIS 2.5 PRO", "cGPT o3"),
    ("AIS 2.5 Flash", "cGPT 4o"),
    ("Bard 2.5 Pro", "cGPT o3"),
    ("Bard 2.5 Flash", "cGPT 4o"),
]

# ============================================================================
# UI STYLING (unchanged - already correct)
# ============================================================================

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 1rem;
        background-color: #16213e;
        border-radius: 10px;
        color: white;
    }
    
    .step {
        text-align: center;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
        flex: 1;
        margin: 0 0.25rem;
    }
    
    .step.active {
        background-color: #4285f4;
        color: white;
    }
    
    .step.completed {
        background-color: #34a853;
        color: white;
    }
    
    .upload-section {
        border: 2px dashed #71b280;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background-color: #DCF58F;
        color: black;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #c3e6cb;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #f5c6cb;
    }
    
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #ffeaa7;
    }
    
    .info-card {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
        color: #0d47a1;
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
    
    .stat-card {
        text-align: center;
        padding: 1rem;
        background-color: #DCF58F;
        color: black;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        flex: 1;
        margin: 0 0.5rem;
    }
    
    .navigation-tip {
        background-color: #ffecd2;
        color: #856404;
        padding: 0.8rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #ffeaa7;
        font-size: 0.9rem;
    }
    
    .custom-form-container {
        background-color: #16213e;
        color: white;
        padding: 0.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    
    .form-row {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .form-row:last-child {
        border-bottom: none;
        justify-content: center;
        padding-top: 2rem;
    }
    
    .form-label {
        font-weight: 600;
        margin-right: 1rem;
        min-width: 140px;
        color: #e3f2fd;
    }
    
    .form-value {
        flex-grow: 1;
        padding: 0.5rem 0.75rem;
        background-color: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 6px;
        color: white;
        margin-right: 1rem;
    }
    
    .form-value.readonly {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        cursor: not-allowed;
    }
    
    .validation-status {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        text-align: center;
        min-width: 60px;
    }
    
    .validation-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .validation-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .model-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .model-icon {
        font-size: 1.5rem;
    }
    
    .pdf-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .pdf-icon {
        font-size: 1.5rem;
    }
    
    .drive-url-display {
        padding: 0.5rem 0.75rem;
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 6px;
        color: #ccc;
        font-family: monospace;
        font-size: 0.9rem;
        word-break: break-all;
    }
    
    .drive-url-ready {
        background-color: rgba(76, 175, 80, 0.1);
        border: 1px solid #4caf50;
        color: #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# GOOGLE APPS SCRIPT INTEGRATION
# ============================================================================

class AppsScriptClient:
    """Client for Google Apps Script webhook integration"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.is_connected = False
        self.last_test = None
    
    def test_connection(self) -> dict:
        """Test connection to Google Apps Script webhook"""
        try:
            if not self.webhook_url:
                return {"success": False, "message": "Webhook URL not configured"}
                
            response = requests.post(
                self.webhook_url,
                json={"action": "test_connection"},
                timeout=WEBHOOK_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                self.is_connected = result.get("success", False)
                self.last_test = datetime.now()
                return result
            else:
                self.is_connected = False
                return {"success": False, "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.is_connected = False
            return {"success": False, "message": f"Connection error: {str(e)}"}
    
    def validate_email(self, email: str, attempt_count: int = 1) -> dict:
        """Validate email against Alias Emails spreadsheet"""
        try:
            if not self.webhook_url:
                return {"success": False, "message": "Webhook URL not configured"}
                
            response = requests.post(
                self.webhook_url,
                json={
                    "action": "validate_email",
                    "email": email,
                    "attempt_count": attempt_count
                },
                timeout=WEBHOOK_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"Validation request failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Email validation error: {str(e)}"}
        
    def validate_question_id(self, question_id: str) -> dict:
        """Validate Question ID against spreadsheet SOT"""
        try:
            if not self.webhook_url:
                return {"success": True, "message": "Question ID accepted", "data": {"is_valid": True}}
                
            response = requests.post(
                self.webhook_url,
                json={
                    "action": "validate_question_id",
                    "question_id": question_id
                },
                timeout=WEBHOOK_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": True, "message": "Question ID accepted", "data": {"is_valid": True}}
                
        except Exception:
            return {"success": True, "message": "Question ID accepted", "data": {"is_valid": True}}
    
    def upload_pdf(self, pdf_buffer: io.BytesIO, filename: str, metadata: dict) -> dict:
        """Upload PDF to Google Drive"""
        try:
            if not self.webhook_url:
                return {"success": False, "message": "Upload service unavailable"}
            
            pdf_buffer.seek(0)
            pdf_data = pdf_buffer.read()
            
            # Check file size
            if len(pdf_data) > MAX_FILE_SIZE_BYTES:
                return {"success": False, "message": f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"}
            
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            response = requests.post(
                self.webhook_url,
                json={
                    "action": "upload_pdf",
                    "pdf_base64": pdf_base64,
                    "filename": filename,
                    "metadata": metadata
                },
                timeout=WEBHOOK_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": "Upload failed"}
                
        except Exception as e:
            return {"success": False, "message": f"Upload service error: {str(e)}"}
    
    def log_submission(self, form_data: dict) -> dict:
        """Log form submission to spreadsheet"""
        try:
            if not self.webhook_url:
                return {"success": True}
                
            response = requests.post(
                self.webhook_url,
                json={
                    "action": "log_submission",
                    **form_data
                },
                timeout=WEBHOOK_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": True}
                
        except Exception:
            return {"success": True}

@st.cache_resource
def get_apps_script_client():
    """Get cached AppsScript client instance"""
    return AppsScriptClient(WEBHOOK_URL)

apps_script = get_apps_script_client()

# ============================================================================
# INTEGRATION FUNCTIONS - FIXED
# ============================================================================

def parse_question_id(question_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse Question ID to extract language and project type using regex patterns"""
    language = None
    project_type = None
    
    try:
        # Extract language pattern
        language_pattern = r'human_eval_([a-z]{2}-[A-Z]{2}|[a-z]{2}-\d{3}|[a-z]{2}-[a-z]{2})\+INTERNAL'
        language_match = re.search(language_pattern, question_id)
        
        if language_match:
            language = language_match.group(1)
        
        # Extract project type
        project_type_mapping = {
            'monolingual': 'Monolingual',
            'audio_out': 'Audio Out',
            'mixed': 'Mixed',
            'code_mixed': 'Mixed',
            'language_learning': 'Language Learning',
            'learning_and_academic_help': 'Learning & Academic Help'
        }
        
        project_pattern = r'experience_([a-z_]+)_human_eval'
        project_match = re.search(project_pattern, question_id)
        
        if project_match:
            extracted_project = project_match.group(1)
            for key, value in project_type_mapping.items():
                if key in extracted_project:
                    project_type = value
                    break
        
    except Exception as e:
        print(f"Error parsing Question ID: {e}")
    
    return language, project_type

def extract_task_id_from_question_id(question_id: str) -> Optional[str]:
    """Extract Task ID from Question ID using pattern matching"""
    try:
        # Pattern: {hash}+bard_data+{TASK_ID}+INTERNAL+en:{number}
        pattern = r'bard_data\+([^+]+)\+INTERNAL'
        match = re.search(pattern, question_id)
        
        if match and match[1]:
            return match[1].strip()
        
        # Fallback patterns
        alt_patterns = [
            r'bard_data\+([^+]+)\+',       # Lenient pattern
            r'coach_P\d+[^+]+',           # coach_P pattern matching
        ]
        
        for alt_pattern in alt_patterns:
            alt_match = re.search(alt_pattern, question_id)
            if alt_match:
                return alt_match[0].replace('bard_data+', '').replace('+', '').strip()
        
        return None
    except Exception as e:
        print(f"Error extracting Task ID: {e}")
        return None

def parse_model_combination(model_comparison: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse model combination string into individual models"""
    try:
        if not model_comparison:
            return None, None
        
        # Common patterns: "Model1 vs Model2", "Model1 vs. Model2"
        if " vs " in model_comparison:
            parts = model_comparison.split(" vs ")
        elif " vs. " in model_comparison:
            parts = model_comparison.split(" vs. ")
        else:
            return None, None
        
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        
        return None, None
    except Exception:
        return None, None

def validate_email_format(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_file_size(file) -> bool:
    if hasattr(file, 'size'):
        return file.size <= MAX_FILE_SIZE_BYTES
    return True

def sanitize_html_output(text: str) -> str:
    """Sanitize text for safe HTML output"""
    return html.escape(str(text))

def validate_email_with_attempts(email: str) -> Tuple[bool, str, dict]:
    """Validate email against Alias Emails spreadsheet with attempt tracking"""
    if not email or not email.strip():
        return False, "Email is required", {}
    
    if not validate_email_format(email):
        return False, "Invalid email format", {}
    
    # Initialize or get current attempt count for this email
    email_key = f"email_attempts_{email.lower().strip()}"
    current_attempts = st.session_state.get(email_key, 0) + 1
    st.session_state[email_key] = current_attempts
    
    try:
        # Call the Google Apps Script validation
        validation_result = apps_script.validate_email(email.strip(), current_attempts)
        
        if validation_result.get("success"):
            # Email is valid
            validation_data = validation_result.get("data", {})
            validation_type = validation_data.get("validation_type", "unknown")
            
            if validation_type == "alias_list":
                message = "✅ Email found in authorized alias list"
            elif validation_type == "company_fallback":
                message = f"✅ Company email accepted after {current_attempts} attempts"
            else:
                message = "✅ Email validated successfully"
                
            return True, message, validation_data
        else:
            # Email is not valid
            error_message = validation_result.get("message", "Email validation failed")
            validation_data = validation_result.get("data", {})
            
            return False, f"❌ {error_message}", validation_data
            
    except Exception as e:
        return False, f"⚠️ Email validation error: {str(e)}", {}

def reset_email_attempts(email: str):
    """Reset attempt count for a specific email"""
    email_key = f"email_attempts_{email.lower().strip()}"
    if email_key in st.session_state:
        del st.session_state[email_key]

def get_email_attempt_count(email: str) -> int:
    """Get current attempt count for an email"""
    email_key = f"email_attempts_{email.lower().strip()}"
    return st.session_state.get(email_key, 0)

def validate_question_id_against_sot(question_id: str) -> Tuple[bool, str, dict]:
    """Validate Question ID against SOT spreadsheet"""
    try:
        validation_result = apps_script.validate_question_id(question_id)
        
        if validation_result.get("success"):
            data = validation_result.get("data", {})
            is_valid = data.get("is_valid", True)
            message = "Question ID validated successfully" if is_valid else "Question ID not found in SOT"
            return is_valid, message, data
        else:
            return True, "Question ID accepted", {}
            
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return True, "Question ID accepted", {}

def generate_drive_url(pdf_buffer: io.BytesIO, filename: str, metadata: dict) -> str:
    """Upload PDF to Google Drive and return shareable URL"""
    try:
        upload_result = apps_script.upload_pdf(pdf_buffer, filename, metadata)
        
        if upload_result.get("success"):
            return upload_result.get("data", {}).get("drive_url", "")
        else:
            st.error(f"Drive upload failed: {upload_result.get('message')}")
            return ""
            
    except Exception as e:
        st.error(f"Drive upload error: {str(e)}")
        return ""

def submit_to_spreadsheet(form_data: dict) -> bool:
    """Submit form data to Google Sheets tracking tab"""
    try:
        log_result = apps_script.log_submission(form_data)
        return log_result.get("success", False)
        
    except Exception as e:
        st.error(f"Submission logging error: {str(e)}")
        return False

def generate_filename(model1: str, model2: str) -> str:
    """Generate a standardized filename for the PDF"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model1_clean = re.sub(r'[^\w\-_.]', '_', model1)
    model2_clean = re.sub(r'[^\w\-_.]', '_', model2)
    return f"SxS_Comparison_{model1_clean}_vs_{model2_clean}_{timestamp}.pdf"

# ============================================================================
# PDF GENERATION CLASS
# ============================================================================

class PDFGenerator:
    """Production-grade PDF generator with Google Slides format and company branding"""
    
    def __init__(self):
        # Google Slides 16:9 format dimensions (720 × 405 points)
        self.page_width = 10 * inch  # 720 points
        self.page_height = 5.625 * inch  # 405 points
        self.slide_format = (self.page_width, self.page_height)
        
        # Safe margins
        self.safe_margin = 0.25 * inch  # Reduced from 0.5" to 0.25"
        self.content_width = self.page_width - (2 * self.safe_margin)
        self.content_height = self.page_height - (2 * self.safe_margin)
        
        # Company logo dimensions and position (icon)
        self.logo_size = 0.5 * inch    # Bigger square logo (36 points)
        self.logo_margin = 0.2 * inch  # Margin from edge
        
        # Color scheme (Google Slides Material Design)
        self.primary_color = HexColor('#4a86e8')  # Cornflower Blue
        self.text_color = HexColor('#1f2937')     # Dark Gray
        self.light_gray = HexColor('#f3f4f6')     # Light Gray
        
        self.temp_files = []
        self.company_logo_path = None
        
        # Download and cache company logo
        self._setup_company_logo()
    
    def _setup_company_logo(self):
        """Setup the Invisible company icon (circular logo only)"""
        try:
            # Create the Invisible icon without text
            logo_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            
            # Create a clean circular icon version
            icon_size = 72
            logo_img = Image.new('RGBA', (icon_size, icon_size), (255, 255, 255, 0))  # Transparent background
            draw = ImageDraw.Draw(logo_img)
            
            # Draw the circular logo (based on the SVG design)
            circle_margin = 4
            circle_size = icon_size - (2 * circle_margin)
            
            # Draw outer circle (dark)
            draw.ellipse([circle_margin, circle_margin, 
                         circle_margin + circle_size, circle_margin + circle_size], 
                        fill=(15, 15, 15, 255), outline=None)
            
            # Draw inner square (white) - represents the square cutout in the SVG
            inner_margin = 12
            inner_size = circle_size - (2 * inner_margin)
            inner_x = circle_margin + inner_margin
            inner_y = circle_margin + inner_margin
            
            draw.rectangle([inner_x, inner_y, inner_x + inner_size, inner_y + inner_size], 
                         fill=(255, 255, 255, 255))
            
            # Save logo
            logo_img.save(logo_temp.name, format='PNG')
            logo_temp.close()
            
            self.company_logo_path = logo_temp.name
            self.temp_files.append(logo_temp.name)
            
        except Exception as e:
            print(f"Warning: Could not create company logo: {e}")
            self.company_logo_path = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                st.warning(f"Could not clean up temp file: {e}")
        self.temp_files = []
    
    def prepare_image(self, image_file: BinaryIO) -> Optional[str]:
        """Convert uploaded image to ReportLab compatible format"""
        try:
            # Reset file pointer
            image_file.seek(0)
            
            # Open image with PIL
            img = Image.open(image_file)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            img.save(temp_file.name, format='JPEG', quality=95, optimize=True)
            temp_file.close()
            
            self.temp_files.append(temp_file.name)
            return temp_file.name
            
        except Exception as e:
            st.error(f"Error preparing image: {str(e)}")
            return None
    
    def draw_company_logo(self, canvas_obj):
        """Draw the Invisible company icon in the bottom right corner"""
        if not self.company_logo_path:
            return
            
        try:
            # Position icon in bottom right corner
            logo_x = self.page_width - self.logo_size - self.logo_margin
            logo_y = self.logo_margin
            
            # Draw logo as square icon
            canvas_obj.drawImage(
                self.company_logo_path,
                logo_x,
                logo_y,
                width=self.logo_size,
                height=self.logo_size,
                preserveAspectRatio=True
            )
            
        except Exception as e:
            print(f"Warning: Could not draw company logo: {e}")
    
    def draw_slide_background(self, canvas_obj):
        """Draw slide background with Google Slides styling"""
        # Set background to white
        canvas_obj.setFillColor(HexColor('#ffffff'))
        canvas_obj.rect(0, 0, self.page_width, self.page_height, fill=1, stroke=0)
        
        # Optional: Add subtle border
        canvas_obj.setStrokeColor(HexColor('#e5e7eb'))
        canvas_obj.setLineWidth(1)
        canvas_obj.rect(0, 0, self.page_width, self.page_height, fill=0, stroke=1)

    def draw_text_with_wrapping(self, canvas_obj, text: str, x: float, y: float, 
                           max_width: float, font_name: str = "Helvetica", 
                           font_size: int = 18):
        return self.draw_wrapped_text(canvas_obj, text, x, y, max_width, 
                                 font_name, font_size, line_height_factor=1.2)
        
        # Split text into words
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if canvas_obj.stringWidth(test_line, font_name, font_size) < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    lines.append(word)
                    current_line = ""
        
        if current_line:
            lines.append(current_line.strip())
        
        # Draw lines with proper spacing for slides
        current_y = y
        line_height = font_size * 1.2
        
        for line in lines:
            canvas_obj.drawString(x, current_y, line)
            current_y -= line_height
        
        return current_y
    
    def draw_centered_text(self, canvas_obj, text: str, y: float, 
                          font_name: str = "Helvetica-Bold", font_size: int = 48,
                          color: HexColor = None):
        """Draw centered text with slide-appropriate styling"""
        if color is None:
            color = self.text_color
            
        canvas_obj.setFont(font_name, font_size)
        canvas_obj.setFillColor(color)
        
        text_width = canvas_obj.stringWidth(text, font_name, font_size)
        x = (self.page_width - text_width) / 2
        canvas_obj.drawString(x, y, text)
    
    def draw_slide_title(self, canvas_obj, text: str, y: float = None):
        """Draw slide title with consistent positioning"""
        if y is None:
            y = self.page_height - self.safe_margin - 60
        
        self.draw_centered_text(
            canvas_obj, 
            text, 
            y, 
            font_name="Helvetica-Bold", 
            font_size=40,
            color=self.primary_color
        )
    
    def draw_image_centered(self, canvas_obj, image_path: str, max_width: float = None, 
                           max_height: float = None):
        """Draw image centered on slide with proper scaling for 16:9 format"""
        try:
            # Get image dimensions
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            # Set default max dimensions for slide format
            if max_width is None:
                max_width = self.content_width
            if max_height is None:
                max_height = self.content_height
            
            # Calculate scaling to fit within slide bounds
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width / img_width, max_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
            else:
                new_width = img_width
                new_height = img_height
            
            # Center the image on the slide
            x = (self.page_width - new_width) / 2
            y = (self.page_height - new_height) / 2
            
            # Draw image
            canvas_obj.drawImage(image_path, x, y, width=new_width, height=new_height)
            
        except Exception as e:
            st.error(f"Error drawing image: {str(e)}")
    
    def create_title_slide(self, canvas_obj, question_id: str, prompt: str, 
                      prompt_image: Optional[BinaryIO] = None):
        
        # Draw background
        self.draw_slide_background(canvas_obj)
        
        # Start from top with better spacing
        y_pos = self.page_height - self.safe_margin - 15
        
        # === QUESTION ID SECTION ===
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.setFillColor(self.primary_color)
        canvas_obj.drawString(self.safe_margin, y_pos, "ID:")
        y_pos -= 18
        
        # Write question ID with multi-line wrapping
        y_pos = self.draw_wrapped_text(canvas_obj, question_id, 
                                    self.safe_margin, y_pos, 
                                    self.content_width, 
                                    font_name="Helvetica", font_size=9,
                                    line_height_factor=1.1)
        y_pos -= 25  # spacing after ID
        
        # === DETERMINE LAYOUT STRUCTURE ===
        # Calculate column dimensions based on whether image is present
        if prompt_image is not None:
            # Two-column layout: 60% text, 38% image, 2% gap
            text_column_width = self.content_width * 0.60
            gap_width = self.content_width * 0.02
            image_column_width = self.content_width * 0.38
            image_column_x = self.safe_margin + text_column_width + gap_width
        else:
            # Single column for text when no image
            text_column_width = self.content_width
            image_column_width = 0
            image_column_x = 0
        
        # Store starting Y position for columns
        content_start_y = y_pos
        
        # === LEFT COLUMN: PROMPT TEXT ===
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.setFillColor(self.primary_color)
        canvas_obj.drawString(self.safe_margin, y_pos, "Initial Prompt:")
        y_pos -= 20
        
        # Write wrapped prompt text in left column
        prompt_end_y = self.draw_wrapped_text(canvas_obj, prompt,
                                            self.safe_margin, y_pos,
                                            text_column_width,
                                            font_name="Helvetica", font_size=12,
                                            line_height_factor=1.3)
        
        # === RIGHT COLUMN: PROMPT IMAGE ===
        if prompt_image is not None:
            available_height = content_start_y - self.safe_margin - 60  # space for Inv logo
            self.draw_prompt_image_in_column(canvas_obj, prompt_image,
                                        image_column_x, content_start_y - 20,  # Start below "Initial Prompt:"
                                        image_column_width,
                                        available_height)
        
        # Use company logo
        self.draw_company_logo(canvas_obj)

    def draw_wrapped_text(self, canvas_obj, text: str, x: float, y: float, 
                        max_width: float, font_name: str = "Helvetica", 
                        font_size: int = 12, line_height_factor: float = 1.2):
        """Draw text with automatic line wrapping and return the final Y position"""
        canvas_obj.setFont(font_name, font_size)
        canvas_obj.setFillColor(self.text_color)
        
        # Handle very long words by breaking them if necessary
        def break_long_word(word, max_word_width):
            """Break a word that's too long to fit on one line"""
            if canvas_obj.stringWidth(word, font_name, font_size) <= max_word_width:
                return [word]
            
            broken_parts = []
            current_part = ""
            
            for char in word:
                test_part = current_part + char
                if canvas_obj.stringWidth(test_part, font_name, font_size) <= max_word_width:
                    current_part = test_part
                else:
                    if current_part:
                        broken_parts.append(current_part)
                    current_part = char
            
            if current_part:
                broken_parts.append(current_part)
            
            return broken_parts
        
        # Split text into words and handle wrapping
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # Check if word itself is too long
            if canvas_obj.stringWidth(word, font_name, font_size) > max_width:
                # Add current line if it has content
                if current_line.strip():
                    lines.append(current_line.strip())
                    current_line = ""
                
                # Break the long word
                broken_words = break_long_word(word, max_width)
                for i, broken_word in enumerate(broken_words):
                    if i == len(broken_words) - 1:  # Last part
                        current_line = broken_word + " "
                    else:
                        lines.append(broken_word)
            else:
                # Normal word processing
                test_line = current_line + word + " "
                if canvas_obj.stringWidth(test_line, font_name, font_size) <= max_width:
                    current_line = test_line
                else:
                    if current_line.strip():
                        lines.append(current_line.strip())
                    current_line = word + " "
        
        # Add the last line
        if current_line.strip():
            lines.append(current_line.strip())
        
        # Draw all lines
        current_y = y
        line_height = font_size * line_height_factor
        
        for line in lines:
            canvas_obj.drawString(x, current_y, line)
            current_y -= line_height
        
        return current_y

    def draw_prompt_image_in_column(self, canvas_obj, image_file: BinaryIO, 
                                x: float, y: float, column_width: float, 
                                available_height: float):
        """Draw prompt image within the specified column bounds with proper scaling"""
        try:
            # Reset file pointer and prepare image
            image_file.seek(0)
            image_data = image_file.read()
            
            if not image_data:
                print("No image data found")
                return
                
            # Create temporary file for the image
            temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_image.write(image_data)
            temp_image.close()
            
            # Add to cleanup list
            self.temp_files.append(temp_image.name)
            
            # Verify file and get image dimensions
            if not os.path.exists(temp_image.name) or os.path.getsize(temp_image.name) == 0:
                print(f"Invalid temp image file: {temp_image.name}")
                return
                
            # Open and process the image
            img = Image.open(temp_image.name)
            img_width, img_height = img.size
            
            # Calculate scaling to fit within column bounds
            width_ratio = column_width / img_width
            height_ratio = available_height / img_height
            scale_ratio = min(width_ratio, height_ratio, 1.0)  # Don't upscale beyond original size
            
            new_width = img_width * scale_ratio
            new_height = img_height * scale_ratio
            
            # Center image horizontally within column, align to top vertically
            image_x = x + (column_width - new_width) / 2
            image_y = y - new_height  # Align to top of available space
            
            # Ensure image doesn't go below bottom margin
            min_y = self.safe_margin + 60  # Leave space for Inv logo
            if image_y < min_y:
                # Recalculate to fit within available space
                adjusted_height = y - min_y
                height_ratio = adjusted_height / img_height
                scale_ratio = min(width_ratio, height_ratio, 1.0)
                
                new_width = img_width * scale_ratio
                new_height = img_height * scale_ratio
                image_x = x + (column_width - new_width) / 2
                image_y = y - new_height
            
            # Draw the image
            canvas_obj.drawImage(temp_image.name, image_x, image_y, 
                            width=new_width, height=new_height,
                            preserveAspectRatio=True)
            
            print(f"Successfully drew prompt image at ({image_x}, {image_y}) with size {new_width}x{new_height}")
            
        except Exception as e:
            print(f"Error drawing prompt image: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
    
    def create_model_title_slide(self, canvas_obj, model_name: str):
        """Create a model title slide with Google Slides styling"""
        
        # Draw background
        self.draw_slide_background(canvas_obj)
        
        # Draw model name in center
        self.draw_centered_text(
            canvas_obj, 
            model_name, 
            self.page_height / 2, 
            font_name="Helvetica-Bold", 
            font_size=56,
            color=self.primary_color
        )
        
        # Draw company logo
        self.draw_company_logo(canvas_obj)
    
    def create_image_slide(self, canvas_obj, image_path: str):
        """Create an image slide with Google Slides styling and maximized image space"""
        
        # Draw background
        self.draw_slide_background(canvas_obj)
        
        # Draw image centered, maximizing space
        max_height = self.content_height - 20  # Minimal space for logo
        max_width = self.content_width - 20    # Small buffer for them aesthetics
        
        self.draw_image_centered(canvas_obj, image_path, 
                               max_width=max_width, 
                               max_height=max_height)
        
        # Draw company logo
        self.draw_company_logo(canvas_obj)
    
    def generate_pdf(self, question_id: str, prompt: str, model1: str, model2: str,
                    model1_images: List[BinaryIO], model2_images: List[BinaryIO],
                    prompt_image: Optional[BinaryIO] = None) -> io.BytesIO:
        """Generate the complete PDF with Google Slides 16:9 format"""
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=self.slide_format)
        
        try:
            # Slide 1: Title slide with ID, prompt, and optional image
            self.create_title_slide(c, question_id, prompt, prompt_image)
            
            # Slide 2: First model title slide
            c.showPage()
            self.create_model_title_slide(c, model1)
            
            # First model image slides (one image per slide)
            for i, img_file in enumerate(model1_images):
                c.showPage()
                temp_image_path = self.prepare_image(img_file)
                if temp_image_path:
                    self.create_image_slide(c, temp_image_path)
            
            # Second model title slide
            c.showPage()
            self.create_model_title_slide(c, model2)
            
            # Second model image slides (one image per slide)
            for i, img_file in enumerate(model2_images):
                c.showPage()
                temp_image_path = self.prepare_image(img_file)
                if temp_image_path:
                    self.create_image_slide(c, temp_image_path)
            
            # Finalize PDF
            c.save()
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            st.error(f"Traceback: {traceback.format_exc()}")
            raise e

# ============================================================================
# EMAIL VALIDATION UI COMPONENTS
# ============================================================================

def display_email_validation_ui():
    """Display email input and validation UI with attempt tracking"""
    st.subheader("📧 Email Validation")
    
    # Email input
    user_email = st.text_input(
        "Email Address *",
        placeholder="your.ops-chiron@invisible.co or your.name@invisible.email",
        help="Enter your authorized alias email or company email (@invisible.email after 3 attempts)",
        value=st.session_state.get('user_email', ''),
        key="email_input"
    )
    
    # Validation button and status
    col1, col2 = st.columns([1, 3])
    
    with col1:
        validate_button = st.button("🔍 Validate Email", disabled=not user_email)
    
    with col2:
        if validate_button and user_email:
            with st.spinner("Validating email..."):
                is_valid, message, validation_data = validate_email_with_attempts(user_email)
                
                if is_valid:
                    st.success(message)
                    st.session_state.email_validated = True
                    st.session_state.user_email = user_email
                    st.session_state.validation_data = validation_data
                else:
                    st.error(message)
                    st.session_state.email_validated = False
                    
                    # Show attempt information for company emails
                    if validation_data.get("is_company_email"):
                        attempts_remaining = validation_data.get("attempts_remaining", 0)
                        current_attempt = validation_data.get("attempt_count", 0)
                        
                        if attempts_remaining > 0:
                            st.info(f"💡 Company email detected. Try {attempts_remaining} more time{'s' if attempts_remaining > 1 else ''} to use @invisible.email fallback")
                        
                        st.write(f"**Attempt {current_attempt}/3** for company email fallback")
    
    # Show current validation status
    if user_email:
        current_attempts = get_email_attempt_count(user_email)
        if current_attempts > 0:
            st.write(f"*Validation attempts for this email: {current_attempts}*")
    
    # Reset attempts button (for testing/admin)
    if user_email and get_email_attempt_count(user_email) > 0:
        if st.button("🔄 Reset Attempts", help="Reset attempt count for this email"):
            reset_email_attempts(user_email)
            st.success("Attempt count reset")
            st.rerun()
    
    return st.session_state.get('email_validated', False)

def display_connection_status():
    """Connection status including email validation tab check"""
    
    st.sidebar.markdown("### 🔗 System Status")
    
    if st.sidebar.button("🔄 Test Connection", key="test_connection"):
        with st.sidebar:
            with st.spinner("Testing connection..."):
                connection_result = apps_script.test_connection()
        
        if connection_result.get("success"):
            st.sidebar.success("🟢 System Ready")
            
            # Show which tabs were found
            data = connection_result.get("data", {})
            tabs_found = data.get("tabs_found", [])
            
            if "Alias Emails" in tabs_found:
                st.sidebar.text("✅ Email validation: Ready")
            else:
                st.sidebar.error("❌ 'Alias Emails' tab missing")
                st.sidebar.info("Create 'Alias Emails' tab in spreadsheet")
            
            st.sidebar.text(f"📊 Tabs: {', '.join(tabs_found)}")
        else:
            st.sidebar.error("🔴 System Offline")
            st.sidebar.warning(f"❌ {connection_result.get('message', 'Connection failed')}")
    
    # Show webhook configuration status
    if WEBHOOK_URL:
        st.sidebar.text("🔗 Webhook: Configured")
    else:
        st.sidebar.error("🔗 Webhook: Not configured")
        st.sidebar.info("Set WEBHOOK_URL in Streamlit secrets")

def show_admin_functions():
    """✅ FIXED: Optional admin functions for testing email validation"""
    
    with st.sidebar.expander("🔧 Admin Functions", expanded=False):
        st.write("**Email Validation Testing**")
        
        # Test specific email
        test_email = st.text_input("Test Email:", key="admin_test_email")
        if st.button("Test Validation") and test_email:
            with st.spinner("Testing..."):
                is_valid, message, data = validate_email_with_attempts(test_email)
                if is_valid:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
                st.json(data)
        
        # Reset all email attempts
        if st.button("Reset All Email Attempts"):
            # Clear all email attempt keys from session state
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith('email_attempts_')]
            for key in keys_to_remove:
                del st.session_state[key]
            st.success("All email attempts reset")

# ============================================================================
# UI UTILITY FUNCTIONS
# ============================================================================

def get_step_status(current_page):
    """Get the status of each step based on session state"""
    steps = ["1️⃣ Metadata Input", "2️⃣ Image Upload", "3️⃣ PDF Generation", "4️⃣ Upload to Drive"]
    statuses = []
    
    for i, step in enumerate(steps):
        if step.endswith(current_page):
            statuses.append("active")
        elif step in ["1️⃣ Metadata Input", "2️⃣ Image Upload", "3️⃣ PDF Generation", "4️⃣ Upload to Drive"]:
            if step.endswith("Metadata Input") and all(key in st.session_state for key in ['question_id', 'prompt_text', 'model1', 'model2']):
                statuses.append("completed")
            elif step.endswith("Image Upload") and all(key in st.session_state for key in ['model1_images', 'model2_images']):
                statuses.append("completed")
            elif step.endswith("PDF Generation") and 'pdf_buffer' in st.session_state:
                statuses.append("completed")
            elif step.endswith("Upload to Drive") and st.session_state.get('uploaded_to_drive', False):
                statuses.append("completed")
            else:
                statuses.append("")
        else:
            statuses.append("")
    
    return statuses

def display_step_indicator(current_page):
    """Display the step indicator"""
    steps = ["1️⃣ Metadata Input", "2️⃣ Image Upload", "3️⃣ PDF Generation", "4️⃣ Upload to Drive"]
    
    if current_page == "Help":
        return
    
    statuses = get_step_status(current_page)
    
    step_html = '<div class="step-indicator">'
    for step, status in zip(steps, statuses):
        step_html += f'<div class="step {status}">{step}</div>'
    step_html += '</div>'
    
    st.markdown(step_html, unsafe_allow_html=True)

def is_step_completed(step_name):
    """Check if a step is completed based on session state"""
    if step_name == "Metadata Input":
        return all(key in st.session_state for key in ['question_id', 'prompt_text', 'model1', 'model2'])
    elif step_name == "Image Upload":
        return all(key in st.session_state for key in ['model1_images', 'model2_images'])
    elif step_name == "PDF Generation":
        return 'pdf_buffer' in st.session_state
    elif step_name == "Upload to Drive":
        return st.session_state.get('uploaded_to_drive', False)
    return False

def get_next_step(current_page):
    """Get the next step in the workflow"""
    steps = ["Metadata Input", "Image Upload", "PDF Generation", "Upload to Drive"]
    try:
        current_index = steps.index(current_page)
        if current_index < len(steps) - 1:
            return steps[current_index + 1]
    except ValueError:
        pass
    return None

def show_next_step_button(current_page):
    """Show the next step button if current step is completed"""
    if not is_step_completed(current_page):
        return
        
    next_step = get_next_step(current_page)
    if not next_step:
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        next_step_emoji = {"Image Upload": "2️⃣", "PDF Generation": "3️⃣", "Upload to Drive": "4️⃣"}
        button_text = f"Continue to {next_step_emoji.get(next_step, '▶️')} {next_step}"
        
        if st.button(button_text, type="primary", use_container_width=True, key=f"next_to_{next_step}"):
            st.session_state.current_page = next_step
            st.rerun()

def create_pdf_preview(pdf_buffer: io.BytesIO) -> str:
    """Create a base64 encoded PDF preview for display"""
    try:
        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.read()
        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        return b64_pdf
    except Exception as e:
        st.error(f"Error creating PDF preview: {str(e)}")
        return ""

def display_pdf_preview(pdf_buffer: io.BytesIO):
    """Display PDF preview in an iframe"""
    try:
        b64_pdf = create_pdf_preview(pdf_buffer)
        if b64_pdf:
            pdf_display = f"""
            <div class="pdf-preview">
                <iframe src="data:application/pdf;base64,{b64_pdf}" 
                        width="100%" height="600px" 
                        style="border: none; border-radius: 5px;">
                </iframe>
            </div>
            """
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.error("Could not generate PDF preview")
    except Exception as e:
        st.error(f"Error displaying PDF preview: {str(e)}")

def create_reorderable_image_preview(images, model_name, session_key):
    """Image preview with reordering capabilities"""
    if not images:
        return images
    
    st.markdown(f"### 🔍 Preview & Reorder {model_name} Images")
    st.info("💡 **Tip**: Use ⬆️⬇️ buttons to reorder. Final order will be saved when you click '💾 Save Images' below.")
    
    # Store reordered images in session state with unique key
    reorder_key = f"{session_key}_reordered"
    if reorder_key not in st.session_state:
        st.session_state[reorder_key] = list(images)
    
    current_images = st.session_state[reorder_key]
    
    # Check if order has changed from original
    order_changed = current_images != list(images)
    if order_changed:
        st.success("✅ **Order modified** - Remember to click 'Save Images' to confirm changes")
    
    # Display images with ONLY up/down controls
    for i, img in enumerate(current_images):
        with st.container():
            # Layout: image on left, minimal controls on right
            col_img, col_controls = st.columns([5, 1])
            
            with col_img:
                # Display image with position number
                st.image(
                    img, 
                    caption=f"Position {i+1}: {model_name}", 
                    use_container_width=True
                )
            
            with col_controls:
                st.markdown(f"**#{i+1}**")
                
                # Move up button
                if i > 0:
                    if st.button("⬆️", 
                                help="Move up", 
                                key=f"{model_name}_{session_key}_up_{i}"):
                        current_images[i], current_images[i-1] = current_images[i-1], current_images[i]
                        st.session_state[reorder_key] = current_images
                        st.rerun()
                
                # Move down button
                if i < len(current_images) - 1:
                    if st.button("⬇️", 
                                help="Move down", 
                                key=f"{model_name}_{session_key}_down_{i}"):
                        current_images[i], current_images[i+1] = current_images[i+1], current_images[i]
                        st.session_state[reorder_key] = current_images
                        st.rerun()
            
            # Subtle separator
            if i < len(current_images) - 1:
                st.markdown('<hr style="margin: 0.25rem 0; border: 0.5px solid #f0f0f0;">', unsafe_allow_html=True)
    
    # Reset to original order button
    if order_changed:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(f"🔄 Reset {model_name} Order", 
                        key=f"{model_name}_{session_key}_reset",
                        help="Reset to original upload order"):
                st.session_state[reorder_key] = list(images)
                st.success("Order reset!")
                st.rerun()
    
    return st.session_state[reorder_key]

def image_upload_page():
    """Image Upload page with fixed reordering functionality"""
    
    st.header("2️⃣ Image Upload")
    
    if not all(key in st.session_state for key in ['question_id', 'prompt_text', 'model1', 'model2']):
        st.markdown("""
        <div class="error-message">
            <strong>⚠️ Prerequisites Missing:</strong> Please complete Step 1 (Metadata Input) first.
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <div class="info-card">
        <h4>📋 Current Setup</h4>
        <p><strong>Comparison:</strong> {sanitize_html_output(st.session_state.model1)} vs {sanitize_html_output(st.session_state.model2)}</p>
        <p><strong>Question ID:</strong> {sanitize_html_output(st.session_state.question_id[:50])}...</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # =======================
    # MODEL 1 UPLOAD SECTION
    # =======================
    
    with col1:
        st.markdown(f"""
        <div class="upload-section">
            <h3>🔵 {sanitize_html_output(st.session_state.model1)} Screenshots</h3>
            <p>Upload interface screenshots and responses</p>
        </div>
        """, unsafe_allow_html=True)
        
        model1_images = st.file_uploader(
            f"Upload {st.session_state.model1} screenshots",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="model1_images_upload",
            help="Upload screenshots of the first model's interface and responses"
        )
        
        if model1_images:
            # Validate file sizes
            valid_files = []
            for img in model1_images:
                if validate_file_size(img):
                    valid_files.append(img)
                else:
                    st.error(f"File {img.name} is too large (max {MAX_FILE_SIZE_MB}MB)")
            
            if valid_files:
                st.success(f"📁 {len(valid_files)} valid image(s) uploaded for {st.session_state.model1}")
                
                # FIXED: Preview with reordering
                with st.expander("🔍 Preview & Reorder Images", expanded=True):
                    model1_images = create_reorderable_image_preview(
                        valid_files, 
                        st.session_state.model1, 
                        "model1"  # Simplified session key
                    )
    
    # =======================
    # MODEL 2 UPLOAD SECTION
    # =======================
    
    with col2:
        st.markdown(f"""
        <div class="upload-section">
            <h3>🔴 {sanitize_html_output(st.session_state.model2)} Screenshots</h3>
            <p>Upload interface screenshots and responses</p>
        </div>
        """, unsafe_allow_html=True)
        
        model2_images = st.file_uploader(
            f"Upload {st.session_state.model2} screenshots",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="model2_images_upload",
            help="Upload screenshots of the second model's interface and responses"
        )
        
        if model2_images:
            # Validate file sizes
            valid_files = []
            for img in model2_images:
                if validate_file_size(img):
                    valid_files.append(img)
                else:
                    st.error(f"File {img.name} is too large (max {MAX_FILE_SIZE_MB}MB)")
            
            if valid_files:
                st.success(f"📁 {len(valid_files)} valid image(s) uploaded for {st.session_state.model2}")
                
                # FIXED: Preview with reordering - Different session key
                with st.expander("🔍 Preview & Reorder Images", expanded=True):
                    model2_images = create_reorderable_image_preview(
                        valid_files, 
                        st.session_state.model2, 
                        "model2"  # Different session key to avoid conflicts
                    )
    
    # ===================
    # SINGLE SAVE BUTTON
    # ===================
    
    # Save images button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💾 Save Images", type="primary", use_container_width=True):
            if model1_images and model2_images:
                # Use the reordered images from session state
                final_model1_images = st.session_state.get("model1_reordered", model1_images)
                final_model2_images = st.session_state.get("model2_reordered", model2_images)
                
                # Save to main session state
                st.session_state.model1_images = final_model1_images
                st.session_state.model2_images = final_model2_images
                
                st.markdown("""
                <div class="success-message">
                    <strong>✅ Success!</strong> Images saved with your chosen order! You can now proceed to Step 3.
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                
                # Show final order confirmation
                st.info(f"📋 **Final Order Saved:**")
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"**{st.session_state.model1}:** {len(final_model1_images)} images")
                with col_info2:
                    st.write(f"**{st.session_state.model2}:** {len(final_model2_images)} images")
                    
            else:
                st.markdown("""
                <div class="error-message">
                    <strong>❌ Error:</strong> Please upload images for both models.
                </div>
                """, unsafe_allow_html=True)
    
    # Show next step button if completed
    show_next_step_button("Image Upload")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Metadata Input"
    
    # Initialize form state variables
    if 'email_validated' not in st.session_state:
        st.session_state.email_validated = False
    if 'drive_url_generated' not in st.session_state:
        st.session_state.drive_url_generated = False
    if 'drive_url' not in st.session_state:
        st.session_state.drive_url = ""
    if 'question_id_validated' not in st.session_state:
        st.session_state.question_id_validated = False
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🖨️ SxS Model Comparison PDF Generator</h1>
        <p>Generate standardized PDF documents for side-by-side LLM comparisons</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    
    nav_options = [
        "1️⃣ Metadata Input",
        "2️⃣ Image Upload", 
        "3️⃣ PDF Generation",
        "4️⃣ Upload to Drive",
        "❓ Help"
    ]
    
    page_mapping = {
        "1️⃣ Metadata Input": "Metadata Input",
        "2️⃣ Image Upload": "Image Upload", 
        "3️⃣ PDF Generation": "PDF Generation",
        "4️⃣ Upload to Drive": "Upload to Drive",
        "❓ Help": "Help"
    }
    
    # Find current selection for radio
    current_nav_selection = None
    for nav_option, page_name in page_mapping.items():
        if page_name == st.session_state.current_page:
            current_nav_selection = nav_option
            break
    
    if current_nav_selection is None:
        current_nav_selection = "1️⃣ Metadata Input"
    
    # Display navigation with status
    selected_nav = st.sidebar.radio(
        "Choose Step:",
        nav_options,
        index=nav_options.index(current_nav_selection) if current_nav_selection in nav_options else 0,
        format_func=lambda x: f"{x} {'✅' if is_step_completed(page_mapping[x]) else ''}"
    )
    
    # Update session state based on selection
    page = page_mapping[selected_nav]
    st.session_state.current_page = page
    
    # Navigation tips
    st.sidebar.markdown("""
    <div class="navigation-tip">
        💡 <strong>Navigation Tip:</strong><br>
        Complete each step to unlock the next one. Upload high-quality screenshots for best results!
    </div>
    """, unsafe_allow_html=True)
    
    # Display connection status
    display_connection_status()
    
    # Session info in sidebar
    if 'question_id' in st.session_state:
        st.sidebar.markdown("### 📋 Current Session")
        st.sidebar.info(f"**Question ID:** {st.session_state.question_id[:20]}...")
        if st.session_state.get('task_id'):
            st.sidebar.info(f"**Task ID:** {st.session_state.task_id[:30]}...")
        if 'model1' in st.session_state and 'model2' in st.session_state:
            st.sidebar.info(f"**Models:** {st.session_state.model1} vs {st.session_state.model2}")
        if st.session_state.get('sot_language'):
            st.sidebar.info(f"**Language:** {st.session_state.sot_language}")
        if st.session_state.get('sot_project_type'):
            st.sidebar.info(f"**Project:** {st.session_state.sot_project_type}")
    
    # Session stats
    if any(key in st.session_state for key in ['model1_images', 'model2_images']):
        st.sidebar.markdown("### 📊 Session Stats")
        if 'model1_images' in st.session_state:
            st.sidebar.metric("Model 1 Images", len(st.session_state.model1_images))
        if 'model2_images' in st.session_state:
            st.sidebar.metric("Model 2 Images", len(st.session_state.model2_images))
    
    # Show admin functions
    show_admin_functions()
    
    # Display step indicator
    display_step_indicator(page)
    
    # Page content
    if page == "Metadata Input":
        st.header("1️⃣ Metadata Input")
        
        st.markdown("""
        <div class="info-card">
            <h4>📋 Required Information</h4>
            <p>Please provide the basic information for your model comparison task.<br>
            You can find the <strong>Question ID</strong> at the top right of the CrC task — look for the 🛈 icon and check the "Question ID(s)" section.</p>
        </div>
        """, unsafe_allow_html=True)

        
        with st.form("metadata_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                question_id = st.text_input(
                    "Question ID *",
                    placeholder="e.g., bfdf67160ca3eca9b65f040e350b2f1f+bard_data+coach_P128628...",
                    help="Enter the unique identifier for this comparison",
                    value=st.session_state.get('question_id', '')
                )
                
                model_combo = st.selectbox(
                    "Select Model Combination *",
                    options=MODEL_COMBINATIONS,
                    format_func=lambda x: f"{x[0]} vs {x[1]}",
                    help="Choose the models being compared",
                    index=0 if 'model1' not in st.session_state else next(
                        (i for i, combo in enumerate(MODEL_COMBINATIONS) 
                         if combo[0] == st.session_state.get('model1') and combo[1] == st.session_state.get('model2')), 0)
                )
            
            with col2:
                prompt_text = st.text_area(
                    "Initial Prompt *",
                    placeholder="Enter the prompt used for both models...",
                    height=150,
                    help="What was the LLM tasked with doing, according to CrC?",
                    value=st.session_state.get('prompt_text', '')
                )
                
                prompt_image = st.file_uploader(
                    "Prompt Image (Optional)",
                    type=['png', 'jpg', 'jpeg'],
                    help="Upload an image if the prompt included visual content"
                )
                
                # Validate prompt image size - now works with 50MB limit
                if prompt_image and not validate_file_size(prompt_image):
                    st.error(f"Prompt image is too large (max {MAX_FILE_SIZE_MB}MB)")
                    prompt_image = None 
            
            submitted = st.form_submit_button("💾 Save Metadata", type="primary")
            
            if submitted:
                if question_id and prompt_text and model_combo:
                    # Validate Question ID against SOT and get SOT data
                    is_valid, message, sot_data = validate_question_id_against_sot(question_id)
                    
                    if is_valid:
                        # Extract Task ID for display
                        task_id = extract_task_id_from_question_id(question_id)
                        
                        # Get data from SOT or use selected values as fallback
                        language = sot_data.get("language", "")
                        project_type = sot_data.get("project_type", "")
                        model_comparison = sot_data.get("model_comparison", "")
                        
                        # Parse model combination from SOT
                        if model_comparison:
                            sot_model1, sot_model2 = parse_model_combination(model_comparison)
                            if sot_model1 and sot_model2:
                                # Use SOT model combination
                                final_model1, final_model2 = sot_model1, sot_model2
                            else:
                                # Fallback to user selection
                                final_model1, final_model2 = model_combo[0], model_combo[1]
                        else:
                            # Use user selection
                            final_model1, final_model2 = model_combo[0], model_combo[1]
                        
                        # Store all data in session state
                        st.session_state.question_id = question_id
                        st.session_state.task_id = task_id
                        st.session_state.prompt_text = prompt_text
                        st.session_state.model1 = final_model1
                        st.session_state.model2 = final_model2
                        st.session_state.sot_language = language
                        st.session_state.sot_project_type = project_type
                        st.session_state.sot_model_comparison = model_comparison
                        st.session_state.question_id_validated = is_valid
                        if prompt_image:
                            st.session_state.prompt_image = prompt_image
                        
                        st.markdown("""
                        <div class="success-message">
                            <strong>✅ Success!</strong> Metadata saved and auto-populated from SOT!
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show SOT information
                        if task_id:
                            st.info(f"🔍 **Task ID:** {task_id}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if language:
                                st.success(f"📍 **Language:** {language}")
                            if project_type:
                                st.success(f"📂 **Project Type:** {project_type}")
                        with col2:
                            if model_comparison:
                                st.success(f"⚔️ **Model Pairing:** {model_comparison}")
                            else:
                                st.info(f"🤖 **Selected Models:** {final_model1} vs {final_model2}")
                        
                        st.balloons()
                    else:
                        # Show the extracted Task ID for debugging
                        task_id = extract_task_id_from_question_id(question_id)
                        error_details = f"{message}"
                        if task_id:
                            error_details += f" (Extracted Task ID: {task_id})"
                        
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>❌ Validation Failed:</strong> {sanitize_html_output(error_details)}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="error-message">
                        <strong>❌ Error:</strong> Please fill in all required fields marked with *.
                    </div>
                    """, unsafe_allow_html=True)
        
        # Show next step button if completed
        show_next_step_button("Metadata Input")
    elif page == "Image Upload":
        image_upload_page() # Utility function

    
    elif page == "PDF Generation":
        st.header("3️⃣ PDF Generation")
        
        required_keys = ['question_id', 'prompt_text', 'model1', 'model2', 'model1_images', 'model2_images']
        missing_keys = [key for key in required_keys if key not in st.session_state]
        
        if missing_keys:
            st.markdown("""
            <div class="error-message">
                <strong>⚠️ Prerequisites Missing:</strong> Please complete all previous steps before generating PDF.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Display summary
        st.subheader("📋 Final Review")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="info-card">
                <h4>📝 Document Information</h4>
                <p><strong>Question ID:</strong> {sanitize_html_output(st.session_state.question_id[:50])}...</p>
                <p><strong>Model Comparison:</strong> {sanitize_html_output(st.session_state.model1)} vs {sanitize_html_output(st.session_state.model2)}</p>
                <p><strong>Prompt:</strong> {sanitize_html_output(st.session_state.prompt_text[:100])}...</p>
                <p><strong>Prompt Image:</strong> {"Yes" if st.session_state.get('prompt_image') else "No"}</p>
                <p><strong>Format:</strong> Google Slides 16:9 Widescreen</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stats-container">
                <div class="stat-card">
                    <h3>{len(st.session_state.model1_images)}</h3>
                    <p>{sanitize_html_output(st.session_state.model1)} Images</p>
                </div>
                <div class="stat-card">
                    <h3>{len(st.session_state.model2_images)}</h3>
                    <p>{sanitize_html_output(st.session_state.model2)} Images</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================================================
        # 🛡️ SINGLE GENERATION LOGIC - PREVENTS MULTIPLE PDF CREATION
        # ============================================================================
        
        # Check if PDF has already been generated this session
        pdf_already_generated = st.session_state.get('pdf_generated', False)
        
        if not pdf_already_generated:
            # Show generation button only if PDF hasn't been generated yet
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Generate PDF", type="primary", use_container_width=True):
                    with st.spinner("Generating PDF..."):
                        try:
                            # Use context manager for proper cleanup
                            with PDFGenerator() as pdf_gen:
                                pdf_buffer = pdf_gen.generate_pdf(
                                    st.session_state.question_id,
                                    st.session_state.prompt_text,
                                    st.session_state.model1,
                                    st.session_state.model2,
                                    st.session_state.model1_images,
                                    st.session_state.model2_images,
                                    st.session_state.get('prompt_image')
                                )
                                
                                # Store in session state with generation timestamp
                                st.session_state.pdf_buffer = pdf_buffer
                                st.session_state.pdf_generated = True
                                st.session_state.pdf_generation_time = datetime.now().isoformat()
                                
                                st.markdown("""
                                <div class="success-message">
                                    <strong>✅ Success!</strong> PDF generated successfully! Review the preview below and download when ready.
                                </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                                
                        except Exception as e:
                            st.markdown(f"""
                            <div class="error-message">
                                <strong>❌ Error:</strong> Failed to generate PDF. Please try again.
                            </div>
                            """, unsafe_allow_html=True)
                            # Don't set pdf_generated to True on failure
        else:
            # PDF already generated - show status and regeneration option
            generation_time = st.session_state.get('pdf_generation_time', 'Unknown')
            st.markdown(f"""
            <div class="success-message">
                <strong>✅ PDF Already Generated</strong><br>
                <small>Generated at: {generation_time}</small><br>
                <small>To generate a new PDF, start a new session or reset current session.</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Optional: Add regeneration button with warning
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.expander("🔄 Advanced: Regenerate PDF", expanded=False):
                    st.warning("⚠️ **Warning**: Regenerating will replace the current PDF and you'll need to re-upload to Drive.")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("🔄 Regenerate PDF", type="secondary", use_container_width=True):
                            # Reset PDF generation state
                            st.session_state.pdf_generated = False
                            st.session_state.drive_url_generated = False
                            st.session_state.drive_url = ""
                            st.session_state.uploaded_to_drive = False
                            if 'pdf_buffer' in st.session_state:
                                del st.session_state.pdf_buffer
                            st.success("🔄 Ready to regenerate PDF")
                            st.rerun()
                    
                    with col_b:
                        if st.button("🆕 Start New Session", type="primary", use_container_width=True):
                            # Clear entire session state except current page
                            keys_to_clear = [key for key in st.session_state.keys() if key not in ['current_page']]
                            for key in keys_to_clear:
                                del st.session_state[key]
                            st.session_state.current_page = "Metadata Input"
                            st.success("🆕 New session started!")
                            st.rerun()
        
        # ============================================================================
        # PDF PREVIEW AND DOWNLOAD SECTION
        # ============================================================================
        
        # PDF Preview and Download Section
        if st.session_state.get('pdf_generated') and 'pdf_buffer' in st.session_state:
            st.markdown("---")
            
            # PDF Preview
            st.subheader("📄 PDF Preview")
            display_pdf_preview(st.session_state.pdf_buffer)
            
            # Download button
            filename = generate_filename(st.session_state.model1, st.session_state.model2)
            
            # Reset buffer position for download
            st.session_state.pdf_buffer.seek(0)
            pdf_data = st.session_state.pdf_buffer.read()
            
            # File info
            st.info(f"🪪 **Filename:** {filename}")
            st.info(f"🏋️‍♀️ **File Size:** {len(pdf_data) / 1024:.1f} KB")    
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    type="secondary",
                    use_container_width=True
                )
        
        # Show next step button if completed
        show_next_step_button("PDF Generation")
    
    elif page == "Upload to Drive":
        st.header("4️⃣ Upload to Drive & Submit")
        
        if not st.session_state.get('pdf_generated'):
            st.markdown("""
            <div class="error-message">
                <strong>⚠️ Prerequisites Missing:</strong> Please complete Step 3 (PDF Generation) first.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Custom Form Container
        st.markdown("""
        <div class="custom-form-container">
            <h3 style="text-align: center; margin-bottom: 0.1rem; color: #e3f2fd;">
                📋 Submission Form
            </h3>
        """, unsafe_allow_html=True)
        
        # Get PDF info
        filename = generate_filename(st.session_state.model1, st.session_state.model2)
        st.session_state.pdf_buffer.seek(0)
        pdf_data = st.session_state.pdf_buffer.read()
        file_size_kb = len(pdf_data) / 1024
        
        # Email Input Row
        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.markdown('<p class="form-label">Email Address:</p>', unsafe_allow_html=True)
        with col2:
            user_email = st.text_input(
                "",
                placeholder="Please input your email address",
                key="email_input_form",
                label_visibility="collapsed"
            )
        with col3:
            if user_email:
                if validate_email_format(user_email):
                    # Use simplified validation for form display
                    is_email_valid, _, _ = validate_email_with_attempts(user_email)
                    if is_email_valid:
                        st.markdown('<div class="validation-status validation-success">✓ Valid</div>', unsafe_allow_html=True)
                        st.session_state.email_validated = True
                        st.session_state.user_email = user_email
                    else:
                        st.markdown('<div class="validation-status validation-error">✗ Invalid</div>', unsafe_allow_html=True)
                        st.session_state.email_validated = False
                else:
                    st.markdown('<div class="validation-status validation-error">✗ Format</div>', unsafe_allow_html=True)
                    st.session_state.email_validated = False
            else:
                st.markdown('<div class="validation-status">⚪ Pending</div>', unsafe_allow_html=True)
                st.session_state.email_validated = False
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Question ID Row
        col1, col2, col3 = st.columns([2, 8, 2])
        with col1:
            st.markdown('<p class="form-label">Question ID:</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="form-value readonly">{sanitize_html_output(st.session_state.question_id)}</div>', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Prompt Text Row
        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.markdown('<p class="form-label">Prompt Text:</p>', unsafe_allow_html=True)
        with col2:
            prompt_display = st.session_state.prompt_text[:100] + "..." if len(st.session_state.prompt_text) > 100 else st.session_state.prompt_text
            st.markdown(f'<div class="form-value readonly">{sanitize_html_output(prompt_display)}</div>', unsafe_allow_html=True)
        with col3:
            has_prompt_image = bool(st.session_state.get('prompt_image'))
            if has_prompt_image:
                st.markdown('<div class="validation-status validation-success">📷 Has Image</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="validation-status">📷 No Image</div>', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Model 1 Row
        col1, col2, col3 = st.columns([2, 8, 2])
        with col1:
            st.markdown('<p class="form-label">Model 1:</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="model-info">
                <span class="model-icon">🤖</span>
                <div>
                    <strong>{sanitize_html_output(st.session_state.model1)}</strong><br>
                    <small>{len(st.session_state.model1_images)} screenshot(s)</small>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Model 2 Row
        col1, col2, col3 = st.columns([2, 8, 2])
        with col1:
            st.markdown('<p class="form-label">Model 2:</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="model-info">
                <span class="model-icon">🤖</span>
                <div>
                    <strong>{sanitize_html_output(st.session_state.model2)}</strong><br>
                    <small>{len(st.session_state.model2_images)} screenshot(s)</small>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # PDF and Drive URL Row
        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.markdown('<p class="form-label">PDF File:</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="pdf-info">
                <span class="pdf-icon">📄</span>
                <div class="pdf-details">
                    <strong>{sanitize_html_output(filename)}</strong><br>
                    <small>{file_size_kb:.1f} KB</small>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        with col3:
            # Load Button for Drive URL - SINGLE UPLOAD PER SESSION
            load_button_disabled = not st.session_state.email_validated
            drive_already_uploaded = st.session_state.get('drive_url_generated', False)

            if not drive_already_uploaded:
                if st.button("Load", key="load_drive_url", disabled=load_button_disabled):
                    with st.spinner("Uploading to Google Drive..."):
                        metadata = {
                            'user_email': user_email,
                            'question_id': st.session_state.question_id,
                            'model1': st.session_state.model1,
                            'model2': st.session_state.model2,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        drive_url = generate_drive_url(st.session_state.pdf_buffer, filename, metadata)
                        
                        if drive_url:
                            st.session_state.drive_url = drive_url
                            st.session_state.drive_url_generated = True
                            st.session_state.drive_upload_time = datetime.now().isoformat()
                            st.success("Drive URL generated successfully!")
                            st.rerun()
                        else:
                            st.error("Unable to generate Drive URL. Please try again.")
            else:
                # Show already uploaded status
                upload_time = st.session_state.get('drive_upload_time', 'Unknown')
                st.markdown(f"""
                <div style="padding: 0.5rem; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; text-align: center;">
                    <strong>✅ Already Uploaded</strong><br>
                    <small>Uploaded at: {upload_time}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Drive URL Display Row
        col1, col2, col3 = st.columns([2, 8, 2])
        with col1:
            st.markdown('<p class="form-label">Drive URL:</p>', unsafe_allow_html=True)
        with col2:
            if st.session_state.drive_url_generated and st.session_state.drive_url:
                st.markdown(f'<div class="drive-url-display drive-url-ready">{sanitize_html_output(st.session_state.drive_url)}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="drive-url-display">URL will be generated after clicking Load...</div>', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 2rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Submit Button Row
        col1, col2, col3 = st.columns([4, 4, 4])
        with col2:
            submit_disabled = not (st.session_state.email_validated and st.session_state.drive_url_generated)
            
            if st.button("📤 Submit", key="submit_form", disabled=submit_disabled, use_container_width=True):
                with st.spinner("Submitting..."):
                    # Prepare submission data - using SOT data
                    form_data = {
                        'user_email': user_email,
                        'drive_url': st.session_state.get('drive_url', ''),
                        'question_id': st.session_state.question_id,
                        'language': st.session_state.get('sot_language', ''),
                        'project_type': st.session_state.get('sot_project_type', ''),
                        'prompt_text': st.session_state.prompt_text,
                        'has_prompt_image': bool(st.session_state.get('prompt_image')),
                        'model1': st.session_state.model1,
                        'model1_image_count': len(st.session_state.model1_images),
                        'model2': st.session_state.model2,
                        'model2_image_count': len(st.session_state.model2_images),
                        'pdf_filename': filename,
                        'file_size_kb': file_size_kb
                    }
                    
                    success = submit_to_spreadsheet(form_data)
                    
                    if success:
                        st.session_state.uploaded_to_drive = True
                        st.success("🎉 Form submitted successfully!")
                        st.balloons()
                        
                        # Display success message
                        drive_link = f'<a href="{st.session_state.drive_url}" target="_blank">View File</a>' if st.session_state.drive_url else "Not available"
                        st.markdown(f"""
                        <div class="success-message">
                            <h4>✅ Submission Completed!</h4>
                            <p><strong>Email:</strong> {sanitize_html_output(user_email)}</p>
                            <p><strong>PDF:</strong> {sanitize_html_output(filename)}</p>
                            <p><strong>Drive URL:</strong> {drive_link}</p>
                            <p><strong>Timestamp:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Reset email attempts after successful submission
                        reset_email_attempts(user_email)
                    else:
                        st.error("❌ Submission failed. Please try again.")
            
            # Show submission requirements
            if submit_disabled:
                requirements = []
                if not st.session_state.email_validated:
                    requirements.append("✗ Valid email required")
                if not st.session_state.drive_url_generated:
                    requirements.append("✗ Drive URL required (click Load)")
                
                st.markdown(f'<div style="text-align: center; color: #ffa726; font-size: 0.9rem; margin-top: 1rem;">{"<br>".join(requirements)}</div>', unsafe_allow_html=True)
        
        # Close the custom form container
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add spacing after the form
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Completion section
        if st.session_state.get('uploaded_to_drive'):
            st.markdown("---")
            st.subheader("🎉 Completion")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.success("✅ Successfully submitted!")
                if st.session_state.drive_url:
                    st.info(f"🔗 **Drive URL:** [View PDF]({st.session_state.drive_url})")
            
            with col2:
                if st.button("🔄 Start New Comparison", type="primary"):
                    # Clear session state
                    keys_to_clear = [key for key in st.session_state.keys() if key not in ['current_page']]
                    for key in keys_to_clear:
                        del st.session_state[key]
                    st.session_state.current_page = "Metadata Input"
                    st.success("🆕 Ready for a new comparison!")
                    st.rerun()
    
    elif page == "Help":
        st.header("❓ Help & Documentation")
        
        tab1, tab2, tab3 = st.tabs(["📋 Instructions", "🔧 Troubleshooting", "📊 Examples"])
        
        with tab1:
            st.markdown("""
            ### 📋 How to Use This App
            
            #### 1️⃣ Metadata Input
            - Enter the **Question ID** (🛈 top right in CrC task)
            - Select the **Model Combination** being compared
            - Enter the **Initial Prompt** used for both models
            - Optionally upload a **Prompt Image**
            
            #### 2️⃣ Image Upload
            - Upload screenshots for both models
            - Preview images to ensure they're correct
            - Supports PNG, JPG, and JPEG formats
            
            #### 3️⃣ PDF Generation
            - Review your inputs in the summary
            - Click **Generate PDF** to create the document
            - **Preview** the PDF before downloading
            - **Download** the generated PDF file
            
            #### 4️⃣ Upload to Drive & Submit
            - Enter your **email address** for validation
            - Review all populated data from previous steps
            - Click **Load** to generate Drive URL
            - Click **Submit** to complete the process
            
            ### 📄 PDF Structure
            1. **Title Page**: Question ID, Prompt, and optional image
            2. **First Model Brand Page**: Model name
            3. **First Model Screenshots**: One image per slide
            4. **Second Model Brand Page**: Model name
            5. **Second Model Screenshots**: One image per slide
            """)
        
        with tab2:
            st.markdown("""
            ### 🔧 Troubleshooting
            
            #### Common Issues:
            - **Email validation fails**: Ensure email is in authorized alias list or use company email (@invisible.email) after 3 attempts
            - **File too large**: All files must be under 50MB
            - **PDF generation fails**: Check image formats and try again
            - **Upload fails**: Ensure stable internet connection
            - **Form submission disabled**: Complete all required steps first
            
            #### Best Practices:
            - Use high-resolution screenshots (1920x1080 recommended)
            - Compress large images before upload using online tools
            - Ensure images are in supported formats (PNG, JPG, JPEG)
            - Complete all steps in order for best results
            - Test connection before starting long sessions
            """)
        
        with tab3:
            st.markdown("""
            ### 📊 Examples
            
            #### Supported Model Combinations:
            - **Bard 2.5 Pro** vs **AIS 2.5 PRO**
            - **AIS 2.5 PRO** vs **cGPT o3**
            - **AIS 2.5 Flash** vs **cGPT 4o**
            - **Bard 2.5 Pro** vs **cGPT o3**
            - **Bard 2.5 Flash** vs **cGPT 4o**
            
            #### Question ID → Task ID Mapping:
            **Sample Question ID:**
            ```
            a5009505a2b411ff7b171226bb33306a+bard_data+coach_P128631_quality_sxs_e2e_experience_learning_and_academic_help_frozen_pool_human_eval_en-US-50+INTERNAL+en:18019373568084263285
            ```
            **Extracted Task ID:**
            ```
            coach_P128631_quality_sxs_e2e_experience_learning_and_academic_help_frozen_pool_human_eval_en-US-50
            ```
            **Auto-populated:**
            - Language: `en-US`
            - Model Comparison: `Bard 2.5 Pro vs. AIS 2.5 Pro`
            - Project Type: `Text`
            
            #### Email Validation Process:
            1. **Check Alias List**: Email must be registered in CrC
            2. **Company Fallback**: @invisible.email emails accepted after 3 failed attempts
            3. **Format Validation**: Must be valid email format
            
            #### Sample Email Formats:
            ```
            ops-chiron-nonstem-en-us-007@invisible.co
            ops-chiron-coding-en-us-007@invisible.co
            ops-chiron-math-en-us-007@invisible.co
            ```
            
            #### File Size Limits:
            - **Individual Images**: 2MB maximum each
            - **PDF Output**: Automatically optimized for web sharing
            """)

if __name__ == "__main__":
    main()