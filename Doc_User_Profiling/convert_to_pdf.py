#!/usr/bin/env python3
"""
Script to convert Markdown documentation to PDF.
Requires: pip install markdown weasyprint
"""

import os
import sys
from pathlib import Path

try:
    import markdown
    from weasyprint import HTML, CSS
except ImportError:
    print("Error: Required packages not installed.")
    print("Please install with: pip install markdown weasyprint")
    sys.exit(1)

def convert_markdown_to_pdf(md_file, pdf_file):
    """Convert Markdown file to PDF."""
    # Read Markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables', 'toc']
    )
    
    # Add CSS styling
    css = """
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: 'Helvetica', 'Arial', sans-serif;
        line-height: 1.6;
        color: #333;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
    }
    h2 {
        color: #34495e;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 5px;
        margin-top: 30px;
    }
    h3 {
        color: #7f8c8d;
        margin-top: 20px;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
    }
    pre {
        background-color: #f4f4f4;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
    }
    th {
        background-color: #3498db;
        color: white;
    }
    tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    """
    
    # Wrap HTML with proper structure
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    HTML(string=full_html).write_pdf(pdf_file)
    print(f"✓ Successfully converted {md_file} to {pdf_file}")

if __name__ == "__main__":
    # Get script directory
    script_dir = Path(__file__).parent
    md_file = script_dir / "User_Profiling_System_Documentation.md"
    pdf_file = script_dir / "User_Profiling_System_Documentation.pdf"
    
    if not md_file.exists():
        print(f"Error: {md_file} not found")
        sys.exit(1)
    
    convert_markdown_to_pdf(md_file, pdf_file)
