import streamlit as st
import io
import base64
from PIL import Image
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
import requests
from typing import List, Optional, BinaryIO

# Configure page
st.set_page_config(
    page_title="SxS Model Comparison PDF Generator",
    page_icon="🖨️",
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
    
    .pdf-preview {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .generation-status {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #ffeaa7;
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
]

class PDFGenerator:
    """Production-grade PDF generator with Google Slides format and company branding"""
    
    def __init__(self):
        # Google Slides 16:9 format dimensions (720 × 405 points)
        self.page_width = 10 * inch  # 720 points
        self.page_height = 5.625 * inch  # 405 points
        self.slide_format = (self.page_width, self.page_height)
        
        # Safe margins (reduced for larger images)
        self.safe_margin = 0.25 * inch  # Reduced from 0.5" to 0.25"
        self.content_width = self.page_width - (2 * self.safe_margin)
        self.content_height = self.page_height - (2 * self.safe_margin)
        
        # Company logo dimensions and position (icon only, bigger)
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
            from PIL import Image, ImageDraw
            
            # Create larger icon (72x72 pixels for crisp rendering)
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
        line_height = font_size * 1.2  # Increased line height for better readability
        
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
            y = self.page_height - self.safe_margin - 60  # Standard title position
        
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
        
        # === QUESTION ID SECTION (Full Width at Top) ===
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.setFillColor(self.primary_color)
        canvas_obj.drawString(self.safe_margin, y_pos, "ID:")
        y_pos -= 18
        
        # Draw question ID with proper multi-line wrapping
        y_pos = self.draw_wrapped_text(canvas_obj, question_id, 
                                    self.safe_margin, y_pos, 
                                    self.content_width, 
                                    font_name="Helvetica", font_size=9,
                                    line_height_factor=1.1)
        y_pos -= 25  # Extra spacing after ID
        
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
        
        # Draw wrapped prompt text in left column
        prompt_end_y = self.draw_wrapped_text(canvas_obj, prompt,
                                            self.safe_margin, y_pos,
                                            text_column_width,
                                            font_name="Helvetica", font_size=12,
                                            line_height_factor=1.3)
        
        # === RIGHT COLUMN: PROMPT IMAGE ===
        if prompt_image is not None:
            available_height = content_start_y - self.safe_margin - 60  # Leave space for logo
            self.draw_prompt_image_in_column(canvas_obj, prompt_image,
                                        image_column_x, content_start_y - 20,  # Start below "Initial Prompt:"
                                        image_column_width,
                                        available_height)
        
        # Draw company logo
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
            min_y = self.safe_margin + 60  # Leave space for company logo
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
        
        # Draw image centered, maximizing space (leaving minimal space for logo)
        max_height = self.content_height - 20  # Leave minimal space for logo
        max_width = self.content_width - 20    # Small buffer for aesthetics
        
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
    
    def _create_title_page(self, canvas_obj, question_id: str, prompt: str, 
                          prompt_image: Optional[BinaryIO] = None):
        """Legacy method - replaced by create_title_slide"""
        self.create_title_slide(canvas_obj, question_id, prompt, prompt_image)

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

def generate_filename(model1: str, model2: str) -> str:
    """Generate a standardized filename for the PDF"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model1_clean = model1.replace(" ", "_").replace(".", "")
    model2_clean = model2.replace(" ", "_").replace(".", "")
    return f"SxS_Comparison_{model1_clean}_vs_{model2_clean}_{timestamp}.pdf"

def display_google_form():
    """Placeholder for Google Drive integration"""
    pass  # Remove form functionality

def main():
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Metadata Input"
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🖨️ SxS Model Comparison PDF Generator</h1>
        <p>Generate standardized PDF documents for side-by-side LLM comparisons</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation with enhanced UI
    st.sidebar.title("🧭 Navigation")
    
    # Enhanced navigation with emoji numbers and status indicators
    nav_options = [
        "1️⃣ Metadata Input",
        "2️⃣ Image Upload", 
        "3️⃣ PDF Generation",
        "4️⃣ Upload to Drive",
        "❓ Help"
    ]
    
    # Create a mapping for display vs actual page names
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
        Complete each step to unlock the next one. Look for the "Continue" button at the bottom of each completed step!
    </div>
    """, unsafe_allow_html=True)
    
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
        st.header("1️⃣ Metadata Input")
        
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
        
        # Show next step button if completed
        show_next_step_button("Metadata Input")
    
    elif page == "Image Upload":
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
        
        # Show next step button if completed
        show_next_step_button("Image Upload")
    
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
                <p><strong>Question ID:</strong> {st.session_state.question_id[:50]}...</p>
                <p><strong>Model Comparison:</strong> {st.session_state.model1} vs {st.session_state.model2}</p>
                <p><strong>Prompt:</strong> {st.session_state.prompt_text[:100]}...</p>
                <p><strong>Prompt Image:</strong> {"Yes" if st.session_state.get('prompt_image') else "No"}</p>
                <p><strong>Format:</strong> Google Slides 16:9 Widescreen</p>
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
            
            
            
            # Download button
            filename = generate_filename(st.session_state.model1, st.session_state.model2)
            
            # Reset buffer position for download
            st.session_state.pdf_buffer.seek(0)
            pdf_data = st.session_state.pdf_buffer.read()
        # File info
            st.info(f"📄 **Filename:** {filename}")
            st.info(f"📊 **File Size:** {len(pdf_data) / 1024:.1f} KB")    
        

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
        st.header("4️⃣ Upload to Drive")
        
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
                    type="secondary",
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
                st.session_state.uploaded_to_drive = True
                st.success("🎉 Great! Your submission has been recorded.")
                st.balloons()
        
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
            - Enter the **Question ID** (unique identifier)
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
            
            #### 4️⃣ Upload to Drive
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
            
            #### Navigation Tips:
            - Complete each step to unlock the next one
            - Use the "Continue" buttons to move forward
            - Check the step indicator to see your progress
            - All data is preserved when navigating between steps
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