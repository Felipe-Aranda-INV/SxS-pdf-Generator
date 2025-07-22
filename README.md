# SxS PDF Generator

Streamlit application for generating standardized PDF documents for side-by-side AI model comparisons with Google Sheets integration.

## 📋 How to Use This App

### 1️⃣ Metadata Input
- Enter the **Question ID** (found in CrC under the "i" icon in top right corner)
- Select the appropriate **Model Combination** being compared
- Enter the **Initial Prompt** used for both models
- Optionally upload a **Prompt Image** if the prompt included visual content

### 2️⃣ Image Upload
- Upload screenshots for both models showing their interfaces and responses
- Preview images to confirm accuracy and clarity
- Supports PNG, JPG, and JPEG formats (max 200MB total)

### 3️⃣ PDF Generation
- Review your inputs in the comprehensive summary
- Click **Generate PDF** to create the standardized document
- **Preview** the PDF in-browser before downloading
- **Download** the generated PDF file locally

### 4️⃣ Upload to Drive & Submit
- Enter your **CrC alias email** (validated against authorized user roster)
- Review all populated data from previous steps
- Click **Load** to generate Google Drive shareable URL
- Click **Submit** to complete the process and log to tracking spreadsheet

## 📊 Application Architecture

### Component Structure
```
Main Application
├── Navigation (Sidebar)
├── Step Indicator (Progress Bar)
├── Metadata Input (Step 1)
├── Image Upload (Step 2) 
├── PDF Generation (Step 3)
├── Form Submission (Step 4)
└── Help & Documentation
```

### Data Flow
1. **User Input** → Session State Storage
2. **Image Upload** → Temporary File Processing
3. **PDF Generation** → In-Memory Buffer
4. **Drive Upload** → Google Drive API
5. **Form Submission** → Google Sheets Logging
6. **Session Reset** → Clean State for Next Use

## 🎯 Supported Model Combinations (v2 Process 7/18/25)
- **Bard 2.5 Pro** vs **AIS 2.5 PRO**
- **AIS 2.5 PRO** vs **cGPT o3**
- **AIS 2.5 Flash** vs **cGPT 4o**
- **Bard 2.5 Pro** vs **cGPT o3**
- **Bard 2.5 Flash** vs **cGPT 4o**

## 📄 PDF Document Structure
1. **Cover Page**: Question ID + Initial Prompt + Optional Image
2. **Model 1 Brand Page**: Model name/logo
3. **Model 1 Screenshots**: Interface captures (one per page)
4. **Model 2 Brand Page**: Model name/logo  
5. **Model 2 Screenshots**: Interface captures (one per page)

*Format: Google Slides 16:9 widescreen with company branding*

## 🔄 Form Validation & Requirements
- **Email**: Must be valid format and exist in authorized users spreadsheet
- **Drive URL**: Auto-generated after successful email validation
- **Submit Button**: Only enabled when all validation requirements are met
- **Real-time Feedback**: Live validation status indicators

## 🔒 Security & Performance Features

### Security
- **XSRF Protection**: Cross-site request forgery prevention
- **Input Validation**: Comprehensive data sanitization
- **File Type Restrictions**: Images only (PNG, JPG, JPEG)
- **Upload Size Limits**: 200MB maximum per session
- **Session Isolation**: User-specific state management

### Performance Optimizations
- **Lazy Loading**: Images processed on demand
- **Session Caching**: Persistent state across navigation
- **Efficient PDF Generation**: Optimized ReportLab rendering
- **Memory Management**: Automatic temporary file cleanup
- **Error Boundaries**: Graceful failure handling with user feedback

## 🔧 Troubleshooting

### Common Issues
- **Email not validated**: Verify email exists in authorized users spreadsheet
- **Load button disabled**: Email must be validated first
- **Submit button disabled**: Both email validation and Drive URL generation required
- **PDF preview issues**: Check browser popup blocker settings
- **Image upload failures**: Ensure files are under 200MB and supported formats

### Best Practices
- Use high-resolution screenshots (1920x1080 recommended)
- Complete steps in sequential order for optimal experience
- Use official CrC alias email address
- Verify image quality before proceeding to PDF generation

## 📞 Support & Contact
For technical issues or questions:
1. Check the **Help** section within the application
2. Review this README documentation
3. Check application logs for error details
4. Contact **Felipe A** on Slack for technical support

## 🔄 Roadmap & Maintenance

### Planned Features
- **OCR Integration**: Automatic text extraction from uploaded images
- **Analytics Dashboard**: Usage metrics and insights

### Version History
**v1.0.0 (Current Production)**
- Multi-step guided workflow
- Google Cloud integration (Drive + Sheets) PLACEHOLDERS
- Real-time form validation
- Comprehensive error handling
- Company branding and styling

---

*Last Updated: July 21, 2025 | Maintained by Felipe A*