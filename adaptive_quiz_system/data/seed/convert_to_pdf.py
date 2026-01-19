#!/usr/bin/env python3
"""
Convert Markdown documentation to PDF.

This script converts the DATA_GENERATION_GUIDE.md to PDF format
for easy sharing and offline reference.

Usage:
    python data/seed/convert_to_pdf.py
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
        page-break-after: avoid;
    }
    h2 {
        color: #34495e;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 5px;
        margin-top: 30px;
        page-break-after: avoid;
    }
    h3 {
        color: #7f8c8d;
        margin-top: 20px;
        page-break-after: avoid;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    pre {
        background-color: #f4f4f4;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
        page-break-inside: avoid;
    }
    pre code {
        background-color: transparent;
        padding: 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
        page-break-inside: avoid;
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
    ul, ol {
        margin: 10px 0;
        padding-left: 30px;
    }
    li {
        margin: 5px 0;
    }
    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 15px;
        margin: 15px 0;
        color: #555;
        font-style: italic;
    }
    """
    
    # Wrap HTML with proper structure
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Data Generation Guide</title>
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
    md_file = script_dir / "DATA_GENERATION_GUIDE.md"
    pdf_file = script_dir / "DATA_GENERATION_GUIDE.pdf"
    
    if not md_file.exists():
        print(f"Error: {md_file} not found")
        sys.exit(1)
    
    convert_markdown_to_pdf(md_file, pdf_file)
    print(f"\nPDF available at: {pdf_file}")
