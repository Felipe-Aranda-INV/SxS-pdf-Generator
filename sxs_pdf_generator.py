import streamlit as st
import io
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, blue, red
import base64
from datetime import datetime
import os
import streamlit.components.v1 as components

# Configure page
st.set_page_config(
    page_title="SxS Model Comparison PDF Generator",
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
        background: linear-gradient(90deg, #4285f4 0%, #34a853 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 10px;
    }
    
    .step {
        text-align: center;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
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
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .info-card {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
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
    }
    
    .iframe-container {
        width: 100%;
        height: 800px;
        border: 1px solid #ddd;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
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

# Model combination options (matching the requirements)
MODEL_COMBINATIONS = [
    ("Bard 2.5 Pro", "AIS 2.5 PRO"),
    ("AIS 2.5 PRO", "cGPT o3"),
    ("AIS 2.5 Flash", "cGPT 4o"),
    ("Bard 2.5 Pro", "cGPT o3"),
    ("Bard 2.5 Flash", "cGPT 4o"),
    ("Gemini", "ChatGPT"),
    ("ChatGPT", "Gemini"),
]

def get_step_status(current_page):
    """Get the status of each step based on session state"""
    steps = ["Metadata Input", "Image Upload", "PDF Generation", "Form Submission"]
    statuses = []
    
    for i, step in enumerate(steps):
        if step == current_page:
            statuses.append("active")
        elif i < steps.index(current_page):
            # Check if previous steps are completed
            if step == "Metadata Input" and all(key in st.session_state for key in ['question_id', 'prompt_text', 'model1', 'model2']):
                statuses.append("completed")
            elif step == "Image Upload" and all(key in st.session_state for key in ['model1_images', 'model2_images']):
                statuses.append("completed")
            elif step == "PDF Generation" and 'pdf_buffer' in st.session_state:
                statuses.append("completed")
            else:
                statuses.append("")
        else:
            statuses.append("")
    
    return statuses

def display_step_indicator(current_page):
    """Display the step indicator"""
    steps = ["Metadata Input", "Image Upload", "PDF Generation", "Form Submission"]
    statuses = get_step_status(current_page)
    
    step_html = '<div class="step-indicator">'
    for step, status in zip(steps, statuses):
        step_html += f'<div class="step {status}">{step}</div>'
    step_html += '</div>'
    
    st.markdown(step_html, unsafe_allow_html=True)

def create_brand_page_image(model_name, width=1200, height=800):
    """Create a brand page image for the model"""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to load a default font, fallback to default if not available
    try:
        font_large = ImageFont.truetype("arial.ttf", 80)
        font_medium = ImageFont.truetype("arial.ttf", 40)
    except:
        try:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        except:
            font_large = None
            font_medium = None
    
    # Get model configuration
    config = MODEL_CONFIGS.get(model_name, {"color": "#000000", "logo_text": model_name})
    
    # Draw the model name in the center
    if font_large:
        text = config["logo_text"]
        try:
            bbox = draw.textbbox((0, 0), text, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = len(text) * 40
            text_height = 80
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), text, fill=config["color"], font=font_large)
    
    return img

def create_pdf_with_images(question_id, prompt, model1, model2, model1_images, model2_images):
    """Create PDF with the standardized SxS format"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Page 1: ID and Initial Prompt
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 50, f"ID:")
    
    # Handle long question ID by wrapping text
    y_pos = height - 80
    max_width = width - 100
    
    # Split long question ID into multiple lines if needed
    words = question_id.split('+')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + word + "+"
        if c.stringWidth(test_line, "Helvetica", 10) < max_width:
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
    
    c.setFont("Helvetica", 10)
    for line in lines:
        c.drawString(50, y_pos, line)
        y_pos -= 15
    
    # Add initial prompt
    y_pos -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, f"Initial Prompt: {prompt}")
    y_pos -= 30
    
    # Add any prompt image if it exists
    if hasattr(st.session_state, 'prompt_image') and st.session_state.prompt_image:
        try:
            img = Image.open(st.session_state.prompt_image)
            img_width, img_height = img.size
            
            # Scale image to fit on page
            max_width = width - 100
            max_height = 400
            
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width / img_width, max_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save image temporarily and add to PDF
            temp_img = io.BytesIO()
            img.save(temp_img, format='PNG')
            temp_img.seek(0)
            
            c.drawImage(temp_img, 50, y_pos - img.height, width=img.width, height=img.height)
            y_pos -= img.height + 20
        except Exception as e:
            st.error(f"Error adding prompt image: {str(e)}")
    
    c.showPage()
    
    # Page 2: First Model Brand Page
    c.setFont("Helvetica-Bold", 48)
    text_width = c.stringWidth(model1, "Helvetica-Bold", 48)
    x = (width - text_width) / 2
    y = height / 2
    c.drawString(x, y, model1)
    c.showPage()
    
    # Add Model 1 images
    for i, img_file in enumerate(model1_images):
        try:
            img = Image.open(img_file)
            img_width, img_height = img.size
            
            # Scale image to fit on page
            max_width = width - 100
            max_height = height - 100
            
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width / img_width, max_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center the image on the page
            x = (width - img.width) / 2
            y = (height - img.height) / 2
            
            # Save image temporarily and add to PDF
            temp_img = io.BytesIO()
            img.save(temp_img, format='PNG')
            temp_img.seek(0)
            
            c.drawImage(temp_img, x, y, width=img.width, height=img.height)
            c.showPage()
            
        except Exception as e:
            st.error(f"Error adding {model1} image {i+1}: {str(e)}")
    
    # Model 2 Brand Page
    c.setFont("Helvetica-Bold", 48)
    text_width = c.stringWidth(model2, "Helvetica-Bold", 48)
    x = (width - text_width) / 2
    y = height / 2
    c.drawString(x, y, model2)
    c.showPage()
    
    # Add Model 2 images
    for i, img_file in enumerate(model2_images):
        try:
            img = Image.open(img_file)
            img_width, img_height = img.size
            
            # Scale image to fit on page
            max_width = width - 100
            max_height = height - 100
            
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width / img_width, max_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center the image on the page
            x = (width - img.width) / 2
            y = (height - img.height) / 2
            
            # Save image temporarily and add to PDF
            temp_img = io.BytesIO()
            img.save(temp_img, format='PNG')
            temp_img.seek(0)
            
            c.drawImage(temp_img, x, y, width=img.width, height=img.height)
            c.showPage()
            
        except Exception as e:
            st.error(f"Error adding {model2} image {i+1}: {str(e)}")
    
    c.save()
    buffer.seek(0)
    return buffer

def display_google_form():
    """Display the Google Form as an iframe"""
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeAFiZgcylypm6JP_uBGbj2Cmz3Syl-ZMqj6ZHut4xsg7_g_Q/viewform"
    
    # Create iframe HTML
    iframe_html = f"""
    <div class="iframe-container">
        <iframe src="{form_url}" 
                width="100%" 
                height="100%" 
                frameborder="0" 
                marginheight="0" 
                marginwidth="0">
            Loading Google Form...
        </iframe>
    </div>
    """
    
    # Display the iframe
    components.html(iframe_html, height=800)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 SxS Model Comparison PDF Generator</h1>
        <p>Generate standardized PDF documents for side-by-side model comparisons</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Go to", ["Metadata Input", "Image Upload", "PDF Generation", "Form Submission", "Help"])
    
    # Display step indicator
    display_step_indicator(page)
    
    # Display current session info in sidebar
    if 'question_id' in st.session_state:
        st.sidebar.markdown("### 📋 Current Session")
        st.sidebar.info(f"**ID:** {st.session_state.question_id[:20]}...")
        if 'model1' in st.session_state and 'model2' in st.session_state:
            st.sidebar.info(f"**Models:** {st.session_state.model1} vs {st.session_state.model2}")
    
    # Add session stats
    if any(key in st.session_state for key in ['model1_images', 'model2_images']):
        st.sidebar.markdown("### 📊 Session Stats")
        if 'model1_images' in st.session_state:
            st.sidebar.metric("Model 1 Images", len(st.session_state.model1_images))
        if 'model2_images' in st.session_state:
            st.sidebar.metric("Model 2 Images", len(st.session_state.model2_images))
    
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
                st.success(f"📁 {len(model1_images)} image(s) uploaded")
                with st.expander("🔍 Preview Images"):
                    for i, img in enumerate(model1_images):
                        st.image(img, caption=f"{st.session_state.model1} - Image {i+1}", use_column_width=True)
        
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
                st.success(f"📁 {len(model2_images)} image(s) uploaded")
                with st.expander("🔍 Preview Images"):
                    for i, img in enumerate(model2_images):
                        st.image(img, caption=f"{st.session_state.model2} - Image {i+1}", use_column_width=True)
        
        # Save images button
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Generate PDF", type="primary"):
                with st.spinner("Generating PDF..."):
                    try:
                        pdf_buffer = create_pdf_with_images(
                            st.session_state.question_id,
                            st.session_state.prompt_text,
                            st.session_state.model1,
                            st.session_state.model2,
                            st.session_state.model1_images,
                            st.session_state.model2_images
                        )
                        
                        st.session_state.pdf_buffer = pdf_buffer
                        
                        st.markdown("""
                        <div class="success-message">
                            <strong>✅ Success!</strong> PDF generated successfully! You can now download it or proceed to Step 4.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.balloons()
                        
                    except Exception as e:
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>❌ Error:</strong> Failed to generate PDF: {str(e)}
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            if 'pdf_buffer' in st.session_state:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"SxS_Comparison_{st.session_state.model1.replace(' ', '_')}_vs_{st.session_state.model2.replace(' ', '_')}_{timestamp}.pdf"
                
                st.download_button(
                    label="📥 Download PDF",
                    data=st.session_state.pdf_buffer,
                    file_name=filename,
                    mime="application/pdf",
                    type="secondary"
                )
    
    elif page == "Form Submission":
        st.header("📝 Step 4: Form Submission")
        
        if 'pdf_buffer' not in st.session_state:
            st.markdown("""
            <div class="error-message">
                <strong>⚠️ Prerequisites Missing:</strong> Please complete Step 3 (PDF Generation) first.
            </div>
            """, unsafe_allow_html=True)
            return
        
        st.markdown("""
        <div class="info-card">
            <h4>📋 Submit Your Generated PDF</h4>
            <p>Your PDF has been generated successfully! Please use the form below to submit your comparison document.</p>
            <p><strong>Instructions:</strong></p>
            <ul>
                <li>Download your PDF from Step 3 if you haven't already</li>
                <li>Fill out the form below with the required information</li>
                <li>Upload your generated PDF file using the drag-and-drop area in the form</li>
                <li>Submit the form to complete the process</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick download button for convenience
        if 'pdf_buffer' in st.session_state:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"SxS_Comparison_{st.session_state.model1.replace(' ', '_')}_vs_{st.session_state.model2.replace(' ', '_')}_{timestamp}.pdf"
                
                st.download_button(
                    label="📥 Download PDF (if needed)",
                    data=st.session_state.pdf_buffer,
                    file_name=filename,
                    mime="application/pdf",
                    type="secondary"
                )
        
        st.markdown("---")
        
        # Display the Google Form
        st.subheader("📋 Submission Form")
        display_google_form()
        
        st.markdown("---")
        
        # Reset option
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Start New Comparison", type="primary"):
                for key in list(st.session_state.keys()):
                    if key != 'form_submitted':  # Keep form submission status
                        del st.session_state[key]
                st.rerun()
    
    elif page == "Help":
        st.header("❓ Help & Documentation")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Instructions", "🔧 Troubleshooting", "📊 Examples", "🚀 Tips"])
        
        with tab1:
            st.markdown("""
            ### 📋 How to Use This App
            
            #### Step 1: Metadata Input
            - Enter the **Question ID** (unique identifier for this comparison)
            - Select the **Model Combination** you're comparing
            - Enter the **Initial Prompt** used for both models
            - Optionally upload an image if the prompt included visual content
            
            #### Step 2: Image Upload
            - Upload screenshots for the **first model** (interface, responses, etc.)
            - Upload screenshots for the **second model**
            - Preview images to ensure they're correct
            - The app supports PNG, JPG, and JPEG formats
            
            #### Step 3: PDF Generation
            - Review your inputs in the summary
            - Click **Generate PDF** to create the standardized document
            - **Download** the generated PDF file
            
            #### Step 4: Form Submission
            - Use the integrated Google Form to submit your generated PDF
            - Fill out the required form fields
            - Upload your PDF using the drag-and-drop area
            - Submit the form to complete the process
            
            ### 📄 PDF Structure
            The generated PDF follows this standardized format:
            1. **Cover Page**: Question ID and Initial Prompt
            2. **First Model Brand Page**: Model name/logo
            3. **First Model Screenshots**: Interface and responses
            4. **Second Model Brand Page**: Model name/logo  
            5. **Second Model Screenshots**: Interface and responses
            """)
        
        with tab2:
            st.markdown("""
            ### 🔧 Troubleshooting
            
            #### Common Issues:
            - **Images not displaying**: Check file format (PNG, JPG, JPEG only) and size
            - **PDF generation failed**: Ensure all required fields are filled
            - **Download not working**: Try refreshing the page and regenerating
            - **Form not loading**: Check your internet connection and try refreshing
            
            #### Best Practices:
            - Use clear, high-resolution screenshots
            - Capture complete interface views
            - Preview images before generating PDF
            - Keep filenames descriptive for organization
            - Test with sample data first
            
            #### Error Messages:
            - **"Prerequisites Missing"**: Complete previous steps first
            - **"Please fill in all required fields"**: Check for missing mandatory information
            - **"Failed to generate PDF"**: Check image formats and sizes
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
            
            #### Sample Question ID Format:
            ```
            bfdf67160ca3eca9b65f040e350b2f1f+bard_data+coach_P128628_quality_sxs_e2e_experience_learning_and_academic_help_frozen_pool_human_eval_en-US-10+INTERNAL+en:5641200679061623267
            ```
            
            #### Sample Prompt:
            ```
            Help me do this [image of math problem]
            ```
            
            #### File Output Format:
            ```
            SxS_Comparison_Bard_2.5_Pro_vs_cGPT_o3_20240118_143052.pdf
            ```
            """)
        
        with tab4:
            st.markdown("""
            ### 🚀 Pro Tips
            
            #### Workflow Optimization:
            1. **Prepare screenshots** before starting the app
            2. **Use consistent naming** for easy identification
            3. **Test with sample data** first
            4. **Save frequently** during the process
            5. **Review the summary** before generating PDF
            
            #### Screenshot Guidelines:
            - **Full interface capture**: Include entire conversation flow
            - **High resolution**: Use at least 1920x1080 for clarity
            - **Consistent framing**: Keep similar screenshot boundaries
            - **Sequential order**: Upload images in conversation order
            
            #### PDF Optimization:
            - **Review metadata** before generation
            - **Check image quality** in preview
            - **Verify model sequence** matches your comparison
            - **Test download** before form submission
            
            #### Form Submission:
            - **Double-check PDF** before uploading
            - **Fill all required fields** in the form
            - **Keep backup copies** of your work
            - **Submit promptly** after generation
            """)

if __name__ == "__main__":
    main()
