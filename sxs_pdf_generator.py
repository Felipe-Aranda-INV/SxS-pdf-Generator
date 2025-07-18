import streamlit as st
import io
import base64
from PIL import Image
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
import tempfile
import os
import traceback
from typing import List, Optional, BinaryIO

# Configure page
st.set_page_config(
    page_title="Chiron SxS Model Comparison PDF Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
        background-color: #1a1a2e;
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
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background-color: #d4edda;
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
    
    .info-card {
        background-color: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
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
        background-color: #f8f9fa;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        flex: 1;
        margin: 0 0.5rem;
    }
    
    .pdf-preview {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .download-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem 0;
        text-align: center;
    }
    
    .generation-status {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #ffeaa7;
    }
</style>
""", unsafe_allow_html=True)

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
    ("Gemini", "ChatGPT"),
    ("ChatGPT", "Gemini"),
]

class PDFGenerator:
    """Production-grade PDF generator with proper error handling and memory management"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 50
        self.temp_files = []
    
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
    
    def draw_text_with_wrapping(self, canvas_obj, text: str, x: float, y: float, 
                               max_width: float, font_name: str = "Helvetica", 
                               font_size: int = 10):
        """Draw text with automatic line wrapping"""
        canvas_obj.setFont(font_name, font_size)
        
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
        
        # Draw lines
        current_y = y
        for line in lines:
            canvas_obj.drawString(x, current_y, line)
            current_y -= font_size + 2
        
        return current_y
    
    def draw_centered_text(self, canvas_obj, text: str, y: float, 
                          font_name: str = "Helvetica-Bold", font_size: int = 48):
        """Draw centered text"""
        canvas_obj.setFont(font_name, font_size)
        text_width = canvas_obj.stringWidth(text, font_name, font_size)
        x = (self.page_width - text_width) / 2
        canvas_obj.drawString(x, y, text)
    
    def draw_image_centered(self, canvas_obj, image_path: str, max_width: float = None, 
                           max_height: float = None):
        """Draw image centered on page with proper scaling"""
        try:
            # Get image dimensions
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            # Set default max dimensions if not provided
            if max_width is None:
                max_width = self.page_width - 2 * self.margin
            if max_height is None:
                max_height = self.page_height - 2 * self.margin
            
            # Calculate scaling
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width / img_width, max_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
            else:
                new_width = img_width
                new_height = img_height
            
            # Center the image
            x = (self.page_width - new_width) / 2
            y = (self.page_height - new_height) / 2
            
            # Draw image
            canvas_obj.drawImage(image_path, x, y, width=new_width, height=new_height)
            
        except Exception as e:
            st.error(f"Error drawing image: {str(e)}")
    
    def generate_pdf(self, question_id: str, prompt: str, model1: str, model2: str,
                    model1_images: List[BinaryIO], model2_images: List[BinaryIO],
                    prompt_image: Optional[BinaryIO] = None) -> io.BytesIO:
        """Generate the complete PDF with all slides"""
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        try:
            # Page 1: Question ID, Prompt, and optional prompt image
            self._create_title_page(c, question_id, prompt, prompt_image)
            
            # Page 2: First model title card
            c.showPage()
            self.draw_centered_text(c, model1, self.page_height / 2)
            
            # First model screenshots (one per page)
            for i, img_file in enumerate(model1_images):
                c.showPage()
                temp_image_path = self.prepare_image(img_file)
                if temp_image_path:
                    self.draw_image_centered(c, temp_image_path)
            
            # Second model title card
            c.showPage()
            self.draw_centered_text(c, model2, self.page_height / 2)
            
            # Second model screenshots (one per page)
            for i, img_file in enumerate(model2_images):
                c.showPage()
                temp_image_path = self.prepare_image(img_file)
                if temp_image_path:
                    self.draw_image_centered(c, temp_image_path)
            
            # Finalize PDF
            c.save()
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            st.error(f"Traceback: {traceback.format_exc()}")
            raise e
    
    def _create_title_page(self, canvas_obj, question_id: str, prompt: str, 
                          prompt_image: Optional[BinaryIO] = None):
        """Create the title page with ID, prompt, and optional image"""
        
        # Title: ID
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.drawString(self.margin, self.page_height - 50, "ID:")
        
        # Question ID with text wrapping
        y_pos = self.page_height - 80
        max_width = self.page_width - 2 * self.margin
        
        # Handle long question ID
        if '+' in question_id:
            words = question_id.split('+')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + word + "+"
                if canvas_obj.stringWidth(test_line, "Helvetica", 10) < max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line.rstrip('+'))
                        current_line = word + "+"
                    else:
                        lines.append(word)
                        current_line = ""
            
            if current_line:
                lines.append(current_line.rstrip('+'))
            
            canvas_obj.setFont("Helvetica", 10)
            for line in lines:
                canvas_obj.drawString(self.margin, y_pos, line)
                y_pos -= 15
        else:
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawString(self.margin, y_pos, question_id)
            y_pos -= 15
        
        # Initial Prompt
        y_pos -= 20
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.drawString(self.margin, y_pos, f"Initial Prompt: {prompt}")
        y_pos -= 40
        
        # Add prompt image if provided
        if prompt_image is not None:
            temp_image_path = self.prepare_image(prompt_image)
            if temp_image_path:
                # Calculate available space for image
                available_height = y_pos - 100
                self.draw_image_centered(canvas_obj, temp_image_path, 
                                       max_height=available_height)

def get_step_status(current_page):
    """Get the status of each step based on session state"""
    steps = ["Metadata Input", "Image Upload", "PDF Generation", "Form Submission"]
    statuses = []
    
    for i, step in enumerate(steps):
        if step == current_page:
            statuses.append("active")
        elif step in ["Metadata Input", "Image Upload", "PDF Generation", "Form Submission"]:
            if step == "Metadata Input" and all(key in st.session_state for key in ['question_id', 'prompt_text', 'model1', 'model2']):
                statuses.append("completed")
            elif step == "Image Upload" and all(key in st.session_state for key in ['model1_images', 'model2_images']):
                statuses.append("completed")
            elif step == "PDF Generation" and 'pdf_buffer' in st.session_state:
                statuses.append("completed")
            elif step == "Form Submission" and st.session_state.get('form_submitted', False):
                statuses.append("completed")
            else:
                statuses.append("")
        else:
            statuses.append("")
    
    return statuses

def display_step_indicator(current_page):
    """Display the step indicator"""
    steps = ["Metadata Input", "Image Upload", "PDF Generation", "Form Submission"]
    
    if current_page == "Help":
        return
    
    statuses = get_step_status(current_page)
    
    step_html = '<div class="step-indicator">'
    for step, status in zip(steps, statuses):
        step_html += f'<div class="step {status}">{step}</div>'
    step_html += '</div>'
    
    st.markdown(step_html, unsafe_allow_html=True)

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
                <h4>📄 PDF Preview</h4>
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

def generate_filename(model1: str, model2: str) -> str:
    """Generate a standardized filename for the PDF"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model1_clean = model1.replace(" ", "_").replace(".", "")
    model2_clean = model2.replace(" ", "_").replace(".", "")
    return f"SxS_Comparison_{model1_clean}_vs_{model2_clean}_{timestamp}.pdf"

def display_google_form():
    """Display the Google Form"""
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeAFiZgcylypm6JP_uBGbj2Cmz3Syl-ZMqj6ZHut4xsg7_g_Q/viewform"
    
    iframe_html = f"""
    <div style="width: 100%; height: 600px; border: 1px solid #ddd; border-radius: 10px; overflow: hidden;">
        <iframe src="{form_url}?embedded=true" 
                width="100%" 
                height="600" 
                frameborder="0" 
                marginheight="0" 
                marginwidth="0">
            Loading Google Form...
        </iframe>
    </div>
    """
    
    try:
        st.components.v1.html(iframe_html, height=620)
    except Exception as e:
        st.error(f"Error loading form: {str(e)}")
        st.markdown(f"""
        ### 🔗 Direct Form Access
        [Click here to open the Google Form]({form_url})
        """)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 SxS Model Comparison PDF Generator</h1>
        <p>Generate standardized PDF documents for side-by-side model comparisons</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Go to", ["Metadata Input", "Image Upload", "PDF Generation", "Form Submission", "Help"])
    
    # Display step indicator
    display_step_indicator(page)
    
    # Session info in sidebar
    if 'question_id' in st.session_state:
        st.sidebar.markdown("### 📋 Current Session")
        st.sidebar.info(f"**ID:** {st.session_state.question_id[:20]}...")
        if 'model1' in st.session_state and 'model2' in st.session_state:
            st.sidebar.info(f"**Models:** {st.session_state.model1} vs {st.session_state.model2}")
    
    # Session stats
    if any(key in st.session_state for key in ['model1_images', 'model2_images']):
        st.sidebar.markdown("### 📊 Session Stats")
        if 'model1_images' in st.session_state:
            st.sidebar.metric("Model 1 Images", len(st.session_state.model1_images))
        if 'model2_images' in st.session_state:
            st.sidebar.metric("Model 2 Images", len(st.session_state.model2_images))
    
    # Page content
    if page == "Metadata Input":
        st.header("📝 Step 1: Metadata Input")
        
        st.markdown("""
        <div class="info-card">
            <h4>📋 Required Information</h4>
            <p>Please provide the basic information for your model comparison. All fields marked with * are required.</p>
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
                    help="The prompt that was given to both models",
                    value=st.session_state.get('prompt_text', '')
                )
                
                prompt_image = st.file_uploader(
                    "Prompt Image (Optional)",
                    type=['png', 'jpg', 'jpeg'],
                    help="Upload an image if the prompt included visual content"
                )
            
            submitted = st.form_submit_button("💾 Save Metadata", type="primary")
            
            if submitted:
                if question_id and prompt_text and model_combo:
                    st.session_state.question_id = question_id
                    st.session_state.prompt_text = prompt_text
                    st.session_state.model1 = model_combo[0]
                    st.session_state.model2 = model_combo[1]
                    if prompt_image:
                        st.session_state.prompt_image = prompt_image
                    
                    st.markdown("""
                    <div class="success-message">
                        <strong>✅ Success!</strong> Metadata saved successfully! You can now proceed to Step 2.
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                else:
                    st.markdown("""
                    <div class="error-message">
                        <strong>❌ Error:</strong> Please fill in all required fields marked with *.
                    </div>
                    """, unsafe_allow_html=True)
    
    elif page == "Image Upload":
        st.header("📸 Step 2: Image Upload")
        
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
            <p><strong>Comparison:</strong> {st.session_state.model1} vs {st.session_state.model2}</p>
            <p><strong>Question ID:</strong> {st.session_state.question_id[:50]}...</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="upload-section">
                <h3>🔵 {st.session_state.model1} Screenshots</h3>
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
                st.success(f"📁 {len(model1_images)} image(s) uploaded for {st.session_state.model1}")
                with st.expander("🔍 Preview Images"):
                    for i, img in enumerate(model1_images):
                        st.image(img, caption=f"{st.session_state.model1} - Image {i+1}", use_container_width=True)
        
        with col2:
            st.markdown(f"""
            <div class="upload-section">
                <h3>🔴 {st.session_state.model2} Screenshots</h3>
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
                st.success(f"📁 {len(model2_images)} image(s) uploaded for {st.session_state.model2}")
                with st.expander("🔍 Preview Images"):
                    for i, img in enumerate(model2_images):
                        st.image(img, caption=f"{st.session_state.model2} - Image {i+1}", use_container_width=True)
        
        # Save images
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("💾 Save Images", type="primary"):
                if model1_images and model2_images:
                    st.session_state.model1_images = model1_images
                    st.session_state.model2_images = model2_images
                    
                    st.markdown("""
                    <div class="success-message">
                        <strong>✅ Success!</strong> Images saved successfully! You can now proceed to Step 3.
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                else:
                    st.markdown("""
                    <div class="error-message">
                        <strong>❌ Error:</strong> Please upload images for both models.
                    </div>
                    """, unsafe_allow_html=True)
    
    elif page == "PDF Generation":
        st.header("📄 Step 3: PDF Generation")
        
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
                <p><strong>Question ID:</strong> {st.session_state.question_id[:50]}...</p>
                <p><strong>Model Comparison:</strong> {st.session_state.model1} vs {st.session_state.model2}</p>
                <p><strong>Prompt:</strong> {st.session_state.prompt_text[:100]}...</p>
                <p><strong>Prompt Image:</strong> {"Yes" if st.session_state.get('prompt_image') else "No"}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stats-container">
                <div class="stat-card">
                    <h3>{len(st.session_state.model1_images)}</h3>
                    <p>{st.session_state.model1} Images</p>
                </div>
                <div class="stat-card">
                    <h3>{len(st.session_state.model2_images)}</h3>
                    <p>{st.session_state.model2} Images</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Generation button
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
                            
                            # Store in session state
                            st.session_state.pdf_buffer = pdf_buffer
                            st.session_state.pdf_generated = True
                            
                            st.markdown("""
                            <div class="success-message">
                                <strong>✅ Success!</strong> PDF generated successfully! Review the preview below and download when ready.
                            </div>
                            """, unsafe_allow_html=True)
                            st.balloons()
                            
                    except Exception as e:
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>❌ Error:</strong> Failed to generate PDF: {str(e)}
                        </div>
                        """, unsafe_allow_html=True)
        
        # PDF Preview and Download Section
        if st.session_state.get('pdf_generated') and 'pdf_buffer' in st.session_state:
            st.markdown("---")
            
            # PDF Preview
            st.subheader("📄 PDF Preview")
            display_pdf_preview(st.session_state.pdf_buffer)
            
            # Download Section
            st.markdown("""
            <div class="download-section">
                <h3>📥 Download Your PDF</h3>
                <p>Your PDF has been generated successfully. Click the button below to download it.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Download button
            filename = generate_filename(st.session_state.model1, st.session_state.model2)
            
            # Reset buffer position for download
            st.session_state.pdf_buffer.seek(0)
            pdf_data = st.session_state.pdf_buffer.read()
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            
            # File info
            st.info(f"📄 **Filename:** {filename}")
            st.info(f"📊 **File Size:** {len(pdf_data) / 1024:.1f} KB")
    
    elif page == "Form Submission":
        st.header("📝 Step 4: Form Submission")
        
        if not st.session_state.get('pdf_generated'):
            st.markdown("""
            <div class="error-message">
                <strong>⚠️ Prerequisites Missing:</strong> Please complete Step 3 (PDF Generation) first.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Quick download for convenience
        if 'pdf_buffer' in st.session_state:
            filename = generate_filename(st.session_state.model1, st.session_state.model2)
            st.session_state.pdf_buffer.seek(0)
            pdf_data = st.session_state.pdf_buffer.read()
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.download_button(
                    label="📥 Download PDF (Required for Form)",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary",
                    help="Download your PDF before submitting the form"
                )
        
        st.markdown("---")
        
        # Form submission
        st.subheader("📋 Submission Form")
        
        st.markdown("""
        <div class="info-card">
            <h4>📋 Submit Your Generated PDF</h4>
            <p>Your PDF has been generated successfully! Please use the form below to submit your comparison document.</p>
        </div>
        """, unsafe_allow_html=True)
        
        display_google_form()
        
        st.markdown("---")
        
        # Completion
        st.subheader("🎉 Completion")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Mark as Submitted", type="secondary"):
                st.session_state.form_submitted = True
                st.success("🎉 Great! Your submission has been recorded.")
                st.balloons()
        
        with col2:
            if st.button("🔄 Start New Comparison", type="primary"):
                # Clear session state
                keys_to_clear = [key for key in st.session_state.keys() if key != 'form_submitted']
                for key in keys_to_clear:
                    del st.session_state[key]
                st.success("🆕 Ready for a new comparison!")
                st.rerun()
    
    elif page == "Help":
        st.header("❓ Help & Documentation")
        
        tab1, tab2, tab3 = st.tabs(["📋 Instructions", "🔧 Troubleshooting", "📊 Examples"])
        
        with tab1:
            st.markdown("""
            ### 📋 How to Use This App
            
            #### Step 1: Metadata Input
            - Enter the **Question ID** (unique identifier)
            - Select the **Model Combination** being compared
            - Enter the **Initial Prompt** used for both models
            - Optionally upload a **Prompt Image**
            
            #### Step 2: Image Upload
            - Upload screenshots for both models
            - Preview images to ensure they're correct
            - Supports PNG, JPG, and JPEG formats
            
            #### Step 3: PDF Generation
            - Review your inputs in the summary
            - Click **Generate PDF** to create the document
            - **Preview** the PDF before downloading
            - **Download** the generated PDF file
            
            #### Step 4: Form Submission
            - Use the Google Form to submit your PDF
            - Fill out required fields and upload your PDF
            - Mark as submitted when complete
            
            ### 📄 PDF Structure
            1. **Title Page**: Question ID, Prompt, and optional image
            2. **First Model Brand Page**: Model name
            3. **First Model Screenshots**: One image per page
            4. **Second Model Brand Page**: Model name
            5. **Second Model Screenshots**: One image per page
            """)
        
        with tab2:
            st.markdown("""
            ### 🔧 Troubleshooting
            
            #### Common Issues:
            - **PDF not downloading**: Check browser popup blocker settings
            - **Images not processing**: Ensure files are under 200MB
            - **Form not loading**: Try refreshing the page
            - **Preview not showing**: Browser may need PDF viewer plugin
            
            #### Best Practices:
            - Use high-resolution screenshots (1920x1080 recommended)
            - Ensure images are in supported formats (PNG, JPG, JPEG)
            - Keep total file size reasonable for web upload
            - Test download before submitting form
            """)
        
        with tab3:
            st.markdown("""
            ### 📊 Examples
            
            #### Supported Model Combinations:
            - **Bard 2.5 Pro** vs **AIS 2.5 PRO**
            - **AIS 2.5 PRO** vs **cGPT o3**
            - **AIS 2.5 Flash** vs **cGPT 4o**
            - **Gemini** vs **ChatGPT**
            
            #### Sample Question ID:
            ```
            bfdf67160ca3eca9b65f040e350b2f1f+bard_data+coach_P128628_quality_sxs_e2e_experience_learning_and_academic_help_frozen_pool_human_eval_en-US-10+INTERNAL+en:5641200679061623267
            ```
            
            #### Sample Prompt:
            ```
            Help me do this [image of math problem]
            ```
            """)

if __name__ == "__main__":
    main()