# SxS-pdf-Generator

Streamlit app for generating standardized PDF documents for side-by-side AI model comparisons with integration to Google Sheets.

## 🚀 Features

- **Multi-step workflow** with progress tracking
- **Drag-and-drop image uploads** with preview
- **Standardized PDF generation** matching required format
- **Integrated Google Form** for seamless submission
- **Professional UI/UX** with responsive design
- **Error handling** and validation
- **Session management** with progress persistence

## 📦 Production Deployment 🔧 Environment Configuration

### Required Files Structure

sxs-pdf-generator/
├── sxs_pdf_generator.py        # Main application
├── requirements.txt            # Dependencies
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── README.md                  # This file

### Configuration Files

#### `.streamlit/config.toml`
- Theme settings (colors, fonts)
- Server configuration
- Upload limits (200MB max)
- Security settings

#### `requirements.txt`
- Streamlit (latest stable)
- Pillow (image processing)
- ReportLab (PDF generation)
- Python-dateutil (date handling)


### Development Commands
```bash
# Run with auto-reload
streamlit run sxs_pdf_generator.py --server.runOnSave true

# Run with debug mode
streamlit run sxs_pdf_generator.py --server.headless false

# Run on specific port
streamlit run sxs_pdf_generator.py --server.port 8502
```

## 📊 Application Architecture

### Component Structure
```
Main Application
├── Navigation (Sidebar)
├── Step Indicator (Progress)
├── Metadata Input (Step 1)
├── Image Upload (Step 2)
├── PDF Generation (Step 3)
├── Form/Doc Submission (Step 4)
└── Help & Documentation
```

### Data Flow
1. **User Input** → Session State
2. **Image Upload** → Temporary Storage
3. **PDF Generation** → Buffer
4. **Form/Drive-Sheets Submission** → Google Forms / Drive + Sheets
5. **Session Reset** → Clean State

## 🎯 Model Combinations Supported as of v2 Process 7/18/25

- Bard 2.5 Pro vs AIS 2.5 PRO
- AIS 2.5 PRO vs cGPT o3
- AIS 2.5 Flash vs cGPT 4o
- Bard 2.5 Pro vs cGPT o3
- Bard 2.5 Flash vs cGPT 4o

## 📄 PDF Structure

1. **Cover Page**: Question ID + Initial Prompt + optional Image
2. **Model 1 Brand Page**: Logo/name
3. **Model 1 Screenshots**: Interface captures
4. **Model 2 Brand Page**: Logo/name
5. **Model 2 Screenshots**: Interface captures

## 🔒 Security Features

- **XSRF Protection**: Enabled
- **CORS Handling**: Configured
- **Input Validation**: Comprehensive?
- **File Type Restrictions**: Images only :)
- **Upload Size Limits**: 200MB max
- **Session Isolation**: User-specific

## 📊 Performance Optimizations

- **Lazy Loading**: Images loaded on demand
- **Session Caching**: Persistent state
- **Efficient PDF Generation**: Optimized ReportLab
- **Memory Management**: Mexican mom cleanup
- **Error Boundaries**: Graceful failure handling

## 🧪 Testing

### Manual Testing Checklist   ---------  REMINDER to check
- [ ] Metadata input validation
- [ ] Image upload functionality
- [ ] PDF generation process
- [ ] Form submission integration
- [ ] Error handling scenarios
- [ ] Cross-browser compatibility
- [ ] Mobile responsiveness

## 📈 Monitoring & Analytics

### Built-in Metrics
- Session state tracking
- Error logging
- Performance monitoring
- User interaction tracking

### Monitoring
- Streamlit Cloud analytics (?)
- Google Form responses (Google sheets probably)
- Server performance metrics
- User feedback collection (Chiron team & agents)

## 🔧 Troubleshooting

### Debug Mode
```bash
# Enable debug logging
streamlit run sxs_pdf_generator.py --server.headless false --logger.level debug
```

## 📞 Support

For technical issues or questions:
1. Check the Help section in the app
2. Review this README
3. Check application logs
4. Contact Felipe A on Slack

## 🔄 ToDo & Maintenance

### Upcoming features
- OCR integration
- 

## 📄 License

This project is licensed under

## 📋 Changelog

### v1.0.0 (Current)
- Initial production release
- Multi-step workflow
- Google Form integration
- Sleek UI/UX
- Comprehensive error handling