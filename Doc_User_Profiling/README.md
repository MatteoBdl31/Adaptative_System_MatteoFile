# Documentation Directory

This directory contains documentation for the Adaptive Trails system.

## User Profiling System Documentation

The main documentation file is: `User_Profiling_System_Documentation.md`

## Converting to PDF

### Option 1: Using Pandoc (Recommended)

1. Install Pandoc:
   ```bash
   # macOS
   brew install pandoc
   
   # Linux
   sudo apt-get install pandoc
   
   # Windows
   # Download from https://pandoc.org/installing.html
   ```

2. Install LaTeX (for better PDF formatting):
   ```bash
   # macOS
   brew install --cask mactex
   
   # Linux
   sudo apt-get install texlive-full
   ```

3. Convert to PDF:
   ```bash
   cd Doc_User_Profiling
   pandoc User_Profiling_System_Documentation.md -o User_Profiling_System_Documentation.pdf --pdf-engine=xelatex -V geometry:margin=1in
   ```

### Option 2: Using Online Converters

1. Open the Markdown file in a text editor
2. Copy the content
3. Use an online Markdown to PDF converter:
   - [Markdown to PDF](https://www.markdowntopdf.com/)
   - [Dillinger](https://dillinger.io/) (export as PDF)
   - [StackEdit](https://stackedit.io/) (export as PDF)

### Option 3: Using VS Code

1. Install the "Markdown PDF" extension in VS Code
2. Open the Markdown file
3. Right-click and select "Markdown PDF: Export (pdf)"

### Option 4: Using Python (with markdown and weasyprint)

```bash
cd Doc_User_Profiling
pip install markdown weasyprint
python convert_to_pdf.py
```

## File Structure

```
Doc_User_Profiling/
├── README.md (this file)
├── User_Profiling_System_Documentation.md
└── convert_to_pdf.py
```

## Document Contents

The documentation covers:

1. **Overview** - System introduction and key features
2. **System Architecture** - Component structure and data flow
3. **User Profiles** - Detailed description of all 7 profiles
4. **Profile Detection Algorithm** - How profiles are detected
5. **Scoring Methodology** - Detailed scoring formulas for each profile
6. **Database Schema** - Database structure and relationships
7. **Implementation Details** - Code structure and integration points
8. **Usage Examples** - Code examples for common operations
9. **Limitations and Future Improvements** - Current limitations and roadmap

## Notes

- The documentation is written in Markdown format for easy editing
- All code examples are in Python
- Mathematical formulas use standard notation
- The document is designed to be self-contained and comprehensive
