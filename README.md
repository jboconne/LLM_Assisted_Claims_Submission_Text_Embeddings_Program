# LLM Assisted Claims Submission Text Extraction Program

## Overview

The LLM Assisted Claims Submission Text Extraction Program is a comprehensive automation system designed to extract, process, and organize claims data from various file formats. The system processes multiple file types including PDFs, audio files, video files, and text documents, then populates ACORD insurance forms and JSON schemas with the extracted information.

## 🚀 Features

- **Multi-format Support**: Handles PDF, audio (WAV, MP3), video (MP4, AVI, MOV), and text files
- **Intelligent Text Extraction**: Uses advanced OCR, speech recognition, and text parsing
- **ACORD Form Integration**: Automatically populates standard insurance forms
- **Structured Data Output**: Generates both JSON schemas and populated ACORD forms
- **Comprehensive Logging**: Detailed logging and progress tracking throughout the process
- **Error Handling**: Robust error handling with retry mechanisms
- **Modular Architecture**: Well-organized, maintainable codebase

## 📁 Project Structure

```
LLM_Claims_Submission_Text_Extraction_Program/
├── lib/                           # Core library modules
│   ├── file_text_extractor.py    # Main text extraction engine
│   └── audio_splitter.py         # Audio file processing utilities
├── scripts/                       # Processing scripts
│   ├── copy_source_files.py      # File copying and organization
│   ├── extract_text_batch.py     # Batch text extraction
│   └── import_data.py            # Data import and ACORD form creation
├── data/                          # Input data files
│   └── [various input files]     # Source files for processing
├── source_input_files/            # Organized input files
│   ├── acord/                     # ACORD form templates
│   └── json/                      # JSON schema templates
├── source_output_files/           # Extracted text and populated forms
│   ├── acord/                     # Populated ACORD forms
│   └── json/                      # Generated JSON files
├── logs/                          # Processing logs (auto-generated)
├── LLM_Assisted_Claims_Submission_Text_Extraction_Program.py  # Master script
├── requirements.txt               # Python dependencies
└── README.md                     # This documentation
```

## 🛠️ Installation

### Prerequisites

1. **Python 3.8+** installed on your system
2. **Tesseract OCR** (for PDF text extraction)
3. **FFmpeg** (for audio/video processing)

### System Dependencies

#### Windows
```bash
# Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Install FFmpeg
# Download from: https://ffmpeg.org/download.html
```

#### macOS
```bash
# Install Tesseract OCR
brew install tesseract

# Install FFmpeg
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
# Install Tesseract OCR
sudo apt-get install tesseract-ocr

# Install FFmpeg
sudo apt-get install ffmpeg
```

### Python Dependencies

1. **Clone or download** the project to your local machine
2. **Navigate** to the project directory
3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Quick Start

Run the master script to execute the complete workflow:

```bash
python LLM_Assisted_Claims_Submission_Text_Extraction_Program.py
```

### Individual Phases

You can also run individual phases of the workflow:

```bash
# Phase 1: Copy source files
python scripts/copy_source_files.py

# Phase 2: Extract text from files
python scripts/extract_text_batch.py

# Phase 3: Import data and create ACORD forms
python scripts/import_data.py
```

### Master Script Options

The master script provides an interactive menu:

1. **Run Complete Workflow** - Executes all phases sequentially
2. **Run Phase 1** - Copy source files only
3. **Run Phase 2** - Extract text only
4. **Run Phase 3** - Populate ACORD forms only
5. **Run Phase 4** - Import data to JSON only
6. **Exit** - Close the program

## 📋 Workflow Phases

### Phase 1: Copy Source Files
- Copies files from the `data/` directory to `source_input_files/`
- Filters files by type (optional)
- Organizes files for processing

### Phase 2: Extract Text
- Processes each file based on its type
- **PDFs**: Uses pdfplumber for text extraction
- **Audio**: Uses speech recognition with Google's API
- **Video**: Extracts audio and applies speech recognition
- **Text**: Direct text extraction
- Saves extracted text to `source_output_files/`

### Phase 3: Populate ACORD Forms
- Loads ACORD form templates
- Maps extracted data to form fields
- Creates populated ACORD forms
- Saves to `source_output_files/acord/`

### Phase 4: Import Data to JSON
- Creates structured JSON schemas
- Maps data to ACORD-specific formats
- Generates confidence scores
- Saves to `data/json/`

## 🔧 Configuration

### File Type Support

The system supports the following file types:

- **Documents**: `.pdf`, `.txt`
- **Audio**: `.wav`, `.mp3`, `.mpeg`
- **Video**: `.mp4`, `.avi`, `.mov`, `.mkv`

### ACORD Form Templates

The system includes templates for:
- **ACORD 1**: Property Loss Notice
- **ACORD 101**: Additional Remarks Schedule
- **ACORD 3**: Liability Notice of Occurrence

### Customization

You can customize the system by:
- Adding new ACORD form templates to `source_input_files/acord/`
- Modifying field mappings in `scripts/import_data.py`
- Adjusting extraction parameters in `lib/file_text_extractor.py`

## 📊 Output Files

### Text Extraction Results
- **Location**: `source_output_files/`
- **Format**: `.txt` files with extracted content
- **Naming**: `{original_filename}.txt`

### ACORD Forms
- **Location**: `source_output_files/acord/`
- **Format**: `.txt` files with populated forms
- **Naming**: `populated_{template_name}.txt`

### JSON Schemas
- **Location**: `source_output_files/json/`
- **Format**: `.json` files with structured data
- **Types**: Basic JSON, schema-based JSON, and ACORD-specific schemas
- **Templates**: Uses JSON schemas from `source_input_files/json/` as templates

### Logs
- **Location**: `logs/`
- **Format**: Timestamped log files
- **Content**: Detailed processing information

## 🐛 Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract is installed and in your system PATH
   - Windows users may need to restart after installation

2. **Audio processing errors**
   - Check that FFmpeg is properly installed
   - Ensure audio files are in supported formats

3. **PDF extraction issues**
   - Verify PDF files are not password-protected
   - Check that pdfplumber is properly installed

4. **Memory issues with large files**
   - Large video files may require significant RAM
   - Consider processing files individually

### Debug Mode

Enable detailed logging by modifying the logging level in the scripts:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## 🔒 Security Considerations

- **API Keys**: Speech recognition uses Google's free API (no key required)
- **File Access**: System only reads from specified directories
- **Data Privacy**: Extracted text is stored locally
- **Network Access**: Internet required for speech recognition

## 📈 Performance

### Processing Times (approximate)
- **PDF files**: 1-5 seconds per page
- **Audio files**: 2-10 seconds per minute of audio
- **Video files**: 5-15 seconds per minute of video
- **Text files**: <1 second

### Resource Requirements
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Varies based on input file sizes
- **CPU**: Multi-core recommended for batch processing

## 🤝 Contributing

To contribute to this project:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Code Style
- Follow PEP 8 guidelines
- Include docstrings for all functions
- Add type hints where appropriate
- Maintain comprehensive error handling

## 📄 License

This project is provided as-is for educational and commercial use. Please ensure compliance with any third-party licenses for included libraries.

## 🆘 Support

For support or questions:

1. **Check** the logs in the `logs/` directory
2. **Review** this README for common solutions
3. **Verify** all dependencies are properly installed
4. **Test** with a simple file first

## 🔄 Version History

- **v1.0** - Initial release with complete workflow
- Enhanced text extraction capabilities
- ACORD form integration
- Comprehensive logging and error handling

---

**Note**: This system is designed for processing insurance claims data and should be used in compliance with relevant data protection and privacy regulations.
