#!/usr/bin/env python3
"""
Simple HTML to PDF Converter for MedBot
A lightweight, reliable tool for converting markdown to beautiful PDFs via HTML
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil
import webbrowser
import tempfile
from typing import Optional, List
import markdown
import argparse
import requests

# Try to import lightweight PDF libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
    print("ReportLab available for PDF generation")
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ReportLab not available, will use HTML output")

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
    print("pdfkit available for PDF generation")
except ImportError:
    PDFKIT_AVAILABLE = False
    print("pdfkit not available")

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
    print("BeautifulSoup available for HTML parsing")
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("BeautifulSoup not available, HTML parsing limited")

class SimpleHTMLToPDFConverter:
    """Simple HTML to PDF converter using lightweight methods"""
    
    def __init__(self, output_dir: str = "pdf_outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Check available PDF engines
        self.available_engines = self._detect_available_engines()
        print(f"🔍 Available PDF engines: {', '.join(self.available_engines) if self.available_engines else 'None'}")
        
    def _detect_available_engines(self) -> List[str]:
        """Detect which PDF engines are available on the system"""
        engines = []
        
        # Check pdfkit (wkhtmltopdf wrapper)
        if PDFKIT_AVAILABLE:
            try:
                # Test if wkhtmltopdf is available
                if shutil.which('wkhtmltopdf'):
                    engines.append('pdfkit')
                    print("pdfkit + wkhtmltopdf detected!")
                else:
                    print("pdfkit available but wkhtmltopdf not found")
            except Exception:
                pass
        
        # Check reportlab (pure Python)
        if REPORTLAB_AVAILABLE:
            engines.append('reportlab')
            print("ReportLab detected!")
        
        # Check if browser printing is available (fallback)
        engines.append('browser-print')
        
        return engines
    
    def _clean_text_for_reportlab(self, text: str) -> str:
        """Clean text for ReportLab by removing HTML tags and problematic characters"""
        if not text:
            return ""
        
        import re
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Replace problematic characters
        clean_text = clean_text.replace('&', '&amp;')
        clean_text = clean_text.replace('<', '&lt;')
        clean_text = clean_text.replace('>', '&gt;')
        clean_text = clean_text.replace('"', '&quot;')
        clean_text = clean_text.replace("'", '&#39;')
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Remove any remaining HTML entities that might cause issues
        clean_text = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_text)
        
        # Ensure text is not too long for ReportLab
        if len(clean_text) > 1000:
            clean_text = clean_text[:1000] + "..."
        
        return clean_text
    
    def _get_logo_base64(self) -> str:
        """Convert MedBot logo to base64 for embedding in HTML"""
        try:
            logo_path = Path("images/MedBotLogo.png")
            if logo_path.exists():
                import base64
                with open(logo_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                    return f"data:image/png;base64,{img_data}"
            else:
                print(f"Warning: Logo file not found at {logo_path}")
                return ""
        except Exception as e:
            print(f"Warning: Could not load logo: {e}")
            return ""
    
    def create_beautiful_html_template(self, title: str = "Research Article") -> str:
        """Create a beautiful HTML template with modern styling"""
        
        # Get logo as base64
        logo_base64 = self._get_logo_base64()
        if logo_base64:
            print(f"✅ Logo loaded successfully (size: {len(logo_base64)} characters)")
        else:
            print("⚠️ Logo not loaded, will use fallback emoji")
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #2d3748;
            background: #ffffff;
            max-width: 100%;
            margin: 0;
            padding: 0 60px 40px 60px;
            font-size: 16px;
            counter-reset: h1-counter h2-counter h3-counter h4-counter;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 50px;
            padding: 45px 0;
            background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 25%, #7c3aed 50%, #9333ea 75%, #be185d 100%);
            color: white;
            border-radius: 0 0 20px 20px;
            margin: 0 -60px 50px -60px;
            position: relative;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
            animation: shimmer 3s ease-in-out infinite;
        }}
        
        .header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 25%, #ec4899 50%, #f59e0b 75%, #10b981 100%);
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        }}
        
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        /* Professional accent elements */
        .header .accent-line {{
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
            transform: translateY(-50%);
        }}
        
        .header .accent-dots {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 8px;
        }}
        
        .header .accent-dots::before,
        .header .accent-dots::after {{
            content: '';
            width: 6px;
            height: 6px;
            background: rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            animation: pulse 2s ease-in-out infinite;
        }}
        
        .header .accent-dots::after {{
            animation-delay: 1s;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.6; transform: scale(1); }}
            50% {{ opacity: 1; transform: scale(1.2); }}
        }}
        
        .download-btn {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 18px 35px;
            border-radius: 35px;
            font-size: 16px;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            backdrop-filter: blur(15px);
            border: 3px solid rgba(255, 255, 255, 0.3);
            z-index: 1000;
        }}
        
        .download-btn:hover {{
            transform: translateY(-4px) scale(1.08);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.7);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            border-color: rgba(255, 255, 255, 0.6);
        }}
        
        .download-btn:active {{
            transform: translateY(-2px) scale(1.04);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        
        .download-btn::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            border-radius: 30px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .download-btn:hover::before {{
            opacity: 1;
        }}
        
        .logo {{
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 15px;
            text-shadow: 0 4px 8px rgba(0,0,0,0.4), 0 8px 16px rgba(0,0,0,0.2);
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
        }}
        
        .logo-icon {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.8);
            position: relative;
            overflow: hidden;
            border: 2px solid rgba(255, 255, 255, 0.2);
            min-height: 60px;
        }}
        
        .logo-icon img {{
            width: 40px;
            height: 40px;
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            animation: icon-bounce 3s ease-in-out infinite;
            max-width: 100%;
            height: auto;
        }}
        
        .logo-icon img:not([src]) {{
            display: none;
        }}
        
        .logo-icon img[src=""] {{
            display: none;
        }}
        
        .logo-icon:empty::before {{
            content: '🏥';
            font-size: 32px;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            animation: icon-bounce 3s ease-in-out infinite;
        }}
        
        @keyframes icon-bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-3px); }}
        }}
        
        .logo-icon::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 40%, rgba(255, 255, 255, 0.3) 50%, transparent 60%);
            animation: icon-shine 2s ease-in-out infinite;
        }}
        
        @keyframes icon-shine {{
            0% {{ transform: translateX(-100%) rotate(45deg); }}
            100% {{ transform: translateX(100%) rotate(45deg); }}
        }}
        
        .subtitle {{
            font-size: 1.3rem;
            font-weight: 500;
            opacity: 0.95;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            position: relative;
            z-index: 2;
        }}
        
        .date {{
            margin-top: 25px;
            opacity: 0.85;
            font-size: 1rem;
            font-weight: 400;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
            position: relative;
            z-index: 2;
            padding: 8px 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        h1 {{
            font-size: 2.2rem;
            color: #2b6cb0;
            margin: 40px 0 20px 0;
            font-weight: 600;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
            position: relative;
            counter-increment: h1-counter;
            text-align: left;
            padding-left: 0;
        }}
        
        h1::before {{
            content: counter(h1-counter) ". ";
            color: #4299e1;
            font-weight: 700;
            margin-right: 10px;
        }}
        
        h1::after {{
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #4299e1, #667eea);
            border-radius: 2px;
        }}
        
        h2 {{
            font-size: 1.6rem;
            color: #3182ce;
            margin: 30px 0 15px 0;
            font-weight: 600;
            position: relative;
            padding-left: 0;
            counter-increment: h2-counter;
            text-align: left;
        }}
        
        h2::before {{
            content: counter(h1-counter) "." counter(h2-counter) ". ";
            color: #4299e1;
            font-weight: 700;
            margin-right: 10px;
        }}
        
        h3 {{
            font-size: 1.3rem;
            color: #3182ce;
            margin: 25px 0 12px 0;
            font-weight: 500;
            counter-increment: h3-counter;
            text-align: left;
            padding-left: 0;
        }}
        
        h3::before {{
            content: counter(h1-counter) "." counter(h2-counter) "." counter(h3-counter) ". ";
            color: #4299e1;
            font-weight: 700;
            margin-right: 8px;
        }}
        
        h4 {{
            font-size: 1.2rem;
            color: #3182ce;
            margin: 20px 0 10px 0;
            font-weight: 500;
            counter-increment: h4-counter;
            text-align: left;
            padding-left: 0;
        }}
        
        h4::before {{
            content: counter(h1-counter) "." counter(h2-counter) "." counter(h3-counter) "." counter(h4-counter) ". ";
            color: #4299e1;
            font-weight: 700;
            margin-right: 8px;
        }}
        
        p {{
            margin: 16px 0;
            text-align: justify !important;
            color: #4a5568;
            padding-left: 0;
            margin-left: 0;
            line-height: 1.8;
            word-spacing: 0.5px;
        }}
        
        .abstract {{
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border-left: 4px solid #4299e1;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: justify !important;
        }}
        
        .abstract h2 {{
            color: #2b6cb0;
            margin-top: 0;
            border: none;
        }}
        
        .abstract h2::after {{
            display: none;
        }}
        
        table {{
            width: 100% !important;
            max-width: 100% !important;
            border-collapse: collapse;
            margin: 25px 0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }}
        
        th, td {{
            padding: 15px 18px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        th {{
            background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
            color: white;
            font-weight: 600;
            font-size: 0.95rem;
        }}
        
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        tr:hover {{
            background: #ebf8ff;
            transition: background-color 0.2s ease;
        }}
        
        .figure {{
            text-align: center;
            margin: 35px 0;
            padding: 25px;
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }}
        
        .figure img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }}
        
        .figure-caption {{
            margin-top: 20px;
            font-style: italic;
            color: #718096;
            font-size: 0.95rem;
        }}
        
        .footer {{
            margin-top: 80px;
            padding: 40px 0;
            border-top: 2px solid #e2e8f0;
            text-align: center;
            color: #718096;
            font-size: 0.9rem;
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            margin: 60px -20px -40px -20px;
            border-radius: 12px 12px 0 0;
        }}
        
        .footer .logo {{
            font-size: 1.5rem;
            color: #1e40af;
            margin-bottom: 10px;
            font-weight: 700;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        
        .footer .subtitle {{
            color: #374151;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .footer div {{
            color: #4b5563;
            font-weight: 500;
        }}
        
        /* Print styles */
        @media print {{
            body {{
                max-width: none;
                padding: 20px;
                font-size: 12pt;
            }}
            
            .header {{
                margin-bottom: 30px;
                page-break-after: avoid;
            }}
            
            .download-btn {{
                display: none; /* Hide download button when printing */
            }}
            
            h1, h2, h3, h4 {{
                page-break-after: avoid;
            }}
            
            .figure {{
                page-break-inside: avoid;
            }}
            
            .footer {{
                margin-top: 40px;
            }}
            
            /* Ensure tables don't break across pages */
            table {{
                page-break-inside: avoid;
            }}
            
            /* Better page breaks for content */
            p {{
                orphans: 3;
                widows: 3;
            }}
        }}
        
        /* Content alignment and spacing */
        .content-wrapper {{
            max-width: 100%;
            margin: 0;
            padding: 20px 0 0 0;
            width: 100%;
        }}
        
        /* Ensure headings and content are perfectly aligned */
        h1, h2, h3, h4 {{
            margin-left: 0 !important;
            padding-left: 0 !important;
            text-align: left !important;
        }}
        
        /* Justify all paragraph text for professional look */
        p, ul, ol, table, blockquote {{
            margin-left: 0 !important;
            padding-left: 0 !important;
            text-align: justify !important;
        }}
        
        /* Remove any default margins that might cause misalignment */
        * {{
            box-sizing: border-box;
        }}
        
        /* Ensure content uses full width */
        #content {{
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        
        /* Ensure all text content is properly justified */
        #content p, #content ul, #content ol, #content blockquote {{
            text-align: justify !important;
            margin: 16px 0 !important;
            padding: 0 !important;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            body {{
                padding: 20px 15px;
                max-width: 100%;
                margin: 0;
            }}
            
            .header {{
                margin: 0 -15px 30px -15px;
                padding: 40px 15px;
                border-radius: 0 0 15px 15px;
            }}
            
            .logo {{
                font-size: 2.8rem;
                gap: 15px;
            }}
            
            .logo-icon {{
                width: 50px;
                height: 50px;
            }}
            
            .logo-icon img {{
                width: 35px;
                height: 35px;
            }}
            
            .subtitle {{
                font-size: 1.1rem;
            }}
            
            .date {{
                font-size: 0.9rem;
                padding: 6px 15px;
            }}
            
            .content-wrapper {{
                max-width: 100%;
                margin: 0;
                padding: 0;
            }}
            
            h1 {{
                font-size: 1.8rem;
            }}
            
            h2 {{
                font-size: 1.4rem;
            }}
            
            table {{
                font-size: 0.9rem;
            }}
            
            th, td {{
                padding: 10px 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <button class="download-btn" onclick="downloadAsPDF()">
            📄 DOWNLOAD PDF
        </button>
        <div class="accent-line"></div>
        <div class="logo">
            <div class="logo-icon">
                <img src="{logo_base64}" alt="MedBot Logo">
            </div>
            <span>MedBot</span>
        </div>
        <div class="subtitle">Healthcare AI Assistant</div>
        <div class="date" id="current-date"></div>
        <div class="accent-dots"></div>
    </div>
     
    <div id="content" class="content-wrapper">
        <!-- Content will be inserted here -->
    </div>
    
    <div class="footer">
        <div class="logo">MedBot</div>
        <div class="subtitle">Advanced Healthcare AI Assistant</div>
        <div>Professional medical research analysis and insights</div>
        <div style="margin-top: 10px; font-size: 0.8rem; opacity: 0.7;">
            Generated on <span id="current-date-footer"></span>
        </div>
    </div>
    
    <script>
        const now = new Date();
        const dateString = now.toLocaleDateString('en-US', {{
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }});
        
        document.getElementById('current-date').textContent = dateString;
        document.getElementById('current-date-footer').textContent = dateString;
        
        function downloadAsPDF() {{
            // Use browser's print functionality to save as PDF
            window.print();
        }}
        
        // Handle logo image loading
        document.addEventListener('DOMContentLoaded', function() {{
            const logoImg = document.querySelector('.logo-icon img');
            if (logoImg) {{
                logoImg.onerror = function() {{
                    console.log('Logo image failed to load, showing fallback');
                    this.style.display = 'none';
                    const icon = this.parentElement;
                    icon.innerHTML = '🏥';
                    icon.style.fontSize = '32px';
                    icon.style.filter = 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))';
                }};
                logoImg.onload = function() {{
                    console.log('Logo image loaded successfully');
                }};
            }}
        }});
        
        // Add keyboard shortcut (Ctrl+P or Cmd+P)
        document.addEventListener('keydown', function(e) {{
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {{
                e.preventDefault();
                downloadAsPDF();
            }}
        }});
    </script>
</body>
</html>"""
    
    def convert_markdown_to_html(self, markdown_file: Path) -> str:
        """Convert markdown file to HTML using the beautiful template"""
        
        if not markdown_file.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_file}")
        
        # Read markdown content
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
                'markdown.extensions.attr_list'
            ]
        )
        
        # Get title from first heading or filename
        title = markdown_file.stem.replace('_', ' ').title()
        
        # Create HTML with template
        full_html = self.create_beautiful_html_template(title)
        
        # Insert content
        full_html = full_html.replace('<!-- Content will be inserted here -->', html_content)
        
        return full_html
    
    def convert_markdown_to_pdf(self, markdown_file: Path, output_name: Optional[str] = None) -> Optional[Path]:
        """Convert markdown file to HTML and open in browser for PDF download"""
        
        if not markdown_file.exists():
            print(f"Markdown file not found: {markdown_file}")
            return None
        
        # Determine output name with timestamp to avoid conflicts
        if output_name is None:
            output_name = markdown_file.stem
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{output_name}_{timestamp}.html"
        
        print(f"Converting {markdown_file.name} to HTML...")
        print(f"Output: {output_file}")
        
        # Convert markdown to HTML first
        try:
            html_content = self.convert_markdown_to_html(markdown_file)
            if not html_content:
                print("Failed to convert markdown to HTML")
                return None
        except Exception as e:
            print(f"HTML conversion failed: {e}")
            return None
        
        # Save HTML file and open in browser
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"HTML file created successfully: {output_file}")
            print("Opening in browser for PDF download...")
            print("Instructions:")
            print("1. Click the 'DOWNLOAD PDF' button in the top-right corner")
            print("2. Or press Ctrl+P (Cmd+P on Mac) to open print dialog")
            print("3. Select 'Save as PDF' as destination")
            print("4. Choose your desired location and save")
            
            # Open in default browser only once
            try:
                webbrowser.open(f'file://{output_file.absolute()}')
                print(f"✅ Browser opened successfully with file: {output_file.absolute()}")
            except Exception as browser_error:
                print(f"⚠️ Browser opening failed: {browser_error}")
                print(f"📁 You can manually open this file: {output_file.absolute()}")
                
                # Fallback: try to open with system default application
                try:
                    import subprocess
                    import platform
                    
                    if platform.system() == "Windows":
                        os.startfile(str(output_file.absolute()))
                        print(f"✅ File opened with default application on Windows")
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", str(output_file.absolute())])
                        print(f"✅ File opened with default application on macOS")
                    else:  # Linux
                        subprocess.run(["xdg-open", str(output_file.absolute())])
                        print(f"✅ File opened with default application on Linux")
                except Exception as app_error:
                    print(f"⚠️ Application opening failed: {app_error}")
                    print(f"📁 Please manually open: {output_file.absolute()}")
            
            return output_file
            
        except Exception as e:
            print(f"Failed to save HTML file: {e}")
            return None
    
    def _convert_with_reportlab(self, html_content: str, output_file: Path) -> bool:
        """Convert HTML to PDF using ReportLab with proper structure preservation"""
        try:
            print("Converting with ReportLab...")
            
            # Create a PDF document with proper margins
            doc = SimpleDocTemplate(
                str(output_file), 
                pagesize=A4,
                leftMargin=1*inch,
                rightMargin=1*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            # Define professional styles
            styles = getSampleStyleSheet()
            
            # Custom styles for better structure
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                spaceBefore=20,
                textColor=colors.darkblue,
                alignment=1,  # Center alignment
                fontName='Helvetica-Bold'
            )
            
            h1_style = ParagraphStyle(
                'CustomH1',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=15,
                spaceBefore=25,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold',
                leftIndent=0,
                alignment=0  # Left alignment
            )
            
            h2_style = ParagraphStyle(
                'CustomH2',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold',
                leftIndent=0,
                alignment=0  # Left alignment
            )
            
            h3_style = ParagraphStyle(
                'CustomH3',
                parent=styles['Heading3'],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold',
                leftIndent=0,
                alignment=0  # Left alignment
            )
            
            h4_style = ParagraphStyle(
                'CustomH4',
                parent=styles['Heading4'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=12,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold',
                leftIndent=0,
                alignment=0  # Left alignment
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                spaceBefore=6,
                leading=14,
                fontName='Helvetica',
                alignment=4,  # Justified alignment
                backColor=None,
                leftIndent=0  # Align with headings
            )
            
            abstract_style = ParagraphStyle(
                'CustomAbstract',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                spaceBefore=6,
                leading=14,
                fontName='Helvetica',
                leftIndent=0,  # Align with headings
                rightIndent=0,
                backColor=None,  # Remove background color
                alignment=4  # Justified alignment
            )
            
            table_style = ParagraphStyle(
                'CustomTable',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                spaceBefore=6,
                fontName='Helvetica',
                backColor=None  # Remove background color
            )
            
            # Parse HTML content properly
            if BEAUTIFULSOUP_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title from HTML
                title = "Research Article"
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                
                # Start building PDF elements
                elements = []
                
                # Add title page
                elements.append(Paragraph(title, title_style))
                elements.append(Spacer(1, 40))
                
                # Add metadata
                from datetime import datetime
                current_date = datetime.now().strftime("%B %d, %Y")
                elements.append(Paragraph(f"Generated by MedBot Healthcare AI Assistant", normal_style))
                elements.append(Paragraph(f"Date: {current_date}", normal_style))
                elements.append(Spacer(1, 30))
                
                # Add page break
                elements.append(PageBreak())
                
                # Process the main content systematically - COMPREHENSIVE APPROACH
                main_content = soup.find('body') or soup

                # Track heading numbers for proper structure
                h1_count = 0
                h2_count = 0
                h3_count = 0
                h4_count = 0

                # Process all elements recursively to capture all content
                def process_element(element):
                    nonlocal h1_count, h2_count, h3_count, h4_count
                    
                    if not hasattr(element, 'name'):
                        return
                        
                    # Skip script tags and other unwanted elements
                    if element.name in ['script', 'style', 'meta', 'link']:
                        return

                    # Skip unwanted content sections
                    if element.name == 'div' and element.get('class'):
                        div_classes = element.get('class', [])
                        if any(cls in div_classes for cls in ['header', 'footer', 'footer-content', 'footer-title', 'footer-info']):
                            return

                    if element.name == 'h1':
                        h1_count += 1
                        h2_count = 0
                        h3_count = 0
                        h4_count = 0
                        text = element.get_text().strip()
                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                elements.append(Paragraph(f"{h1_count}. {clean_text}", h1_style))
                    elif element.name == 'h2':
                        h2_count += 1
                        h3_count = 0
                        h4_count = 0
                        text = element.get_text().strip()
                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                elements.append(Paragraph(f"{h1_count}.{h2_count}. {clean_text}", h2_style))
                    elif element.name == 'h3':
                        h3_count += 1
                        h4_count = 0
                        text = element.get_text().strip()
                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                elements.append(Paragraph(f"{h1_count}.{h2_count}.{h3_count}. {clean_text}", h3_style))
                    elif element.name == 'h4':
                        h4_count += 1
                        text = element.get_text().strip()
                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                elements.append(Paragraph(f"{h1_count}.{h2_count}.{h3_count}.{h4_count}. {clean_text}", h4_style))
                    elif element.name == 'p':
                        text = element.get_text().strip()
                        if text:
                            # Filter out JavaScript code and unwanted content
                            if any(keyword in text.lower() for keyword in ['const ', 'function', 'document.', 'getelementbyid', 'script', 'javascript', 'document generated successfully', 'this document was created by medbot', 'professional medical research analysis']):
                                return  # Skip unwanted content

                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                # Check if this is an abstract
                                if 'abstract' in clean_text.lower() or len(clean_text) > 200:
                                    elements.append(Paragraph(clean_text, abstract_style))
                                else:
                                    elements.append(Paragraph(clean_text, normal_style))
                    elif element.name == 'table':
                        # Handle tables with proper structure
                        try:
                            print(f"Processing table...")

                            # Process table data with better structure handling
                            data = []

                            # Find all rows
                            rows = element.find_all('tr')
                            if rows:
                                # Process each row
                                for row in rows:
                                    row_data = []
                                    cells = row.find_all(['th', 'td'])

                                    for cell in cells:
                                        cell_text = cell.get_text().strip()
                                        clean_cell_text = self._clean_text_for_reportlab(cell_text)
                                        if clean_cell_text:
                                            # Check if this is a header cell (th) or data cell (td)
                                            if cell.name == 'th':
                                                # Header cell - use bold style
                                                header_style = ParagraphStyle(
                                                    'TableHeader',
                                                    parent=table_style,
                                                    fontName='Helvetica-Bold',
                                                    fontSize=10,
                                                    backColor=None
                                                )
                                                row_data.append(Paragraph(clean_cell_text, header_style))
                                            else:
                                                # Data cell - use normal style
                                                row_data.append(Paragraph(clean_cell_text, table_style))

                                    if row_data:  # Only add rows with content
                                        data.append(row_data)

                                if data:
                                    # Calculate optimal column widths based on content
                                    max_cols = max(len(row) for row in data) if data else 1

                                    # Adjust column widths based on content
                                    col_widths = []
                                    for col_idx in range(max_cols):
                                        # Find the longest text in this column
                                        max_width = 0
                                        for row in data:
                                            if col_idx < len(row):
                                                text_length = len(row[col_idx].text)
                                                max_width = max(max_width, text_length)

                                        # Set column width based on content (minimum 1.5 inch, maximum 3 inch)
                                        col_width = max(1.5*inch, min(3*inch, max_width * 0.1*inch))
                                        col_widths.append(col_width)

                                    # Create table with proper styling
                                    table = Table(data, colWidths=col_widths)

                                    # Enhanced table styling with better visual appeal
                                    table_style_list = [
                                        # Basic alignment
                                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                                        ('VALIGN', (0,0), (-1,-1), 'TOP'),

                                        # Enhanced grid lines
                                        ('INNERGRID', (0,0), (-1,-1), 0.8, colors.darkblue),
                                        ('BOX', (0,0), (-1,-1), 1.2, colors.darkblue),

                                        # Header row styling (first row) - Professional look
                                        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                                        ('FONTSIZE', (0,0), (-1,0), 11),
                                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                        ('BOTTOMPADDING', (0,0), (-1,0), 10),
                                        ('TOPPADDING', (0,0), (-1,0), 10),

                                        # Data rows styling - Clean and readable
                                        ('BACKGROUND', (0,1), (-1,-1), colors.white),
                                        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                                        ('FONTSIZE', (0,1), (-1,-1), 10),
                                        ('TEXTCOLOR', (0,1), (-1,-1), colors.black),

                                        # Alternating row colors for better readability
                                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey]),

                                        # Enhanced padding for better spacing
                                        ('BOTTOMPADDING', (0,1), (-1,-1), 10),
                                        ('TOPPADDING', (0,1), (-1,-1), 10),
                                        ('LEFTPADDING', (0,0), (-1,-1), 8),
                                        ('RIGHTPADDING', (0,0), (-1,-1), 8),

                                        # Row height for better proportions
                                        ('MINIMUMHEIGHT', (0,0), (-1,-1), 25),
                                    ]

                                    # Apply table styling
                                    table.setStyle(TableStyle(table_style_list))

                                    elements.append(table)
                                    elements.append(Spacer(1, 15))
                                    print(f"Success: Table processed successfully with {len(data)} rows and {max_cols} columns")
                                else:
                                    # Fallback: add table as text
                                    table_text = element.get_text().strip()
                                    clean_table_text = self._clean_text_for_reportlab(table_text)
                                    if clean_table_text:
                                        elements.append(Paragraph(f"Table Content: {clean_table_text}", normal_style))

                        except Exception as e:
                            print(f"Warning: Table processing failed: {e}")
                            # Fallback: add table as text
                            table_text = element.get_text().strip()
                            clean_table_text = self._clean_text_for_reportlab(table_text)
                            if clean_table_text:
                                elements.append(Paragraph(f"Table Content: {clean_table_text}", normal_style))
                    elif element.name in ['ul', 'ol']:
                        # Handle lists with proper indentation
                        list_items = element.find_all('li')
                        for i, li in enumerate(list_items):
                            text = li.get_text().strip()
                            if text:
                                clean_text = self._clean_text_for_reportlab(text)
                                if clean_text:
                                    if element.name == 'ol':
                                        elements.append(Paragraph(f"{i+1}. {clean_text}", normal_style))
                                    else:
                                        elements.append(Paragraph(f"• {clean_text}", normal_style))
                        elements.append(Spacer(1, 8))
                    elif element.name == 'div':
                        # Handle special divs like abstract, figures
                        div_class = element.get('class', [])
                        text = element.get_text().strip()

                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                if 'abstract' in div_class:
                                    elements.append(Paragraph("Abstract", h2_style))
                                    elements.append(Paragraph(clean_text, abstract_style))
                                elif 'figure' in div_class:
                                    elements.append(Paragraph("Figure", h3_style))
                                    elements.append(Paragraph(clean_text, normal_style))
                                else:
                                    elements.append(Paragraph(clean_text, normal_style))
                    elif element.name == 'blockquote':
                        # Handle blockquotes
                        text = element.get_text().strip()
                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                elements.append(Paragraph(f'"{clean_text}"', normal_style))
                    elif element.name == 'code':
                        # Handle code blocks
                        text = element.get_text().strip()
                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                elements.append(Paragraph(f"Code: {clean_text}", normal_style))
                    elif element.name == 'pre':
                        # Handle preformatted text
                        text = element.get_text().strip()
                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                elements.append(Paragraph(f"Code Block: {clean_text}", normal_style))
                    
                    # Process all children recursively
                    for child in element.children:
                        process_element(child)

                # Start processing from the main content
                process_element(main_content)

                # Add a simple, clean end marker
                elements.append(Spacer(1, 30))
                elements.append(Paragraph("─" * 60, normal_style))
                elements.append(Spacer(1, 15))
                elements.append(Paragraph("End of Document", normal_style))
                
                # Add amazing and professional end of document
                elements.append(Spacer(1, 40))
                
                # Add a decorative line
                elements.append(Paragraph("─" * 80, normal_style))
                elements.append(Spacer(1, 20))
                
                # End of document title
                end_title_style = ParagraphStyle(
                    'EndTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    spaceAfter=15,
                    spaceBefore=10,
                    textColor=colors.darkblue,
                    alignment=1,  # Center alignment
                    fontName='Helvetica-Bold'
                )
                elements.append(Paragraph("End of Document", end_title_style))
                
                # Add metadata in a professional format
                metadata_style = ParagraphStyle(
                    'Metadata',
                    parent=styles['Normal'],
                    fontSize=10,
                    spaceAfter=5,
                    spaceBefore=5,
                    leading=12,
                    fontName='Helvetica',
                    alignment=1,  # Center alignment
                    textColor=colors.grey
                )
                
                elements.append(Paragraph(f"Generated on {current_date}", metadata_style))
                elements.append(Paragraph("by MedBot Healthcare AI Assistant", metadata_style))
                elements.append(Paragraph("Professional Medical Research Analysis & Insights", metadata_style))
                
                # Add version and timestamp
                elements.append(Spacer(1, 15))
                elements.append(Paragraph("Document Version: 1.0", metadata_style))
                elements.append(Paragraph(f"Generated at: {datetime.now().strftime('%H:%M:%S')}", metadata_style))
                
                # Add final decorative element
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("•" * 40, metadata_style))
                
            else:
                # Fallback without BeautifulSoup
                elements = []
                elements.append(Paragraph("Research Article", title_style))
                elements.append(Spacer(1, 20))
                
                # Simple text extraction
                import re
                text_content = re.sub(r'<[^>]+>', '', html_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                
                # Split into paragraphs
                paragraphs = text_content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        elements.append(Paragraph(para.strip(), normal_style))
                        elements.append(Spacer(1, 8))
            
            # Build the PDF
            if elements:
                try:
                    doc.build(elements)
                    print(f"PDF created successfully with ReportLab: {output_file}")
                    print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")
                    return True
                except PermissionError:
                    print(f"Permission denied: {output_file}")
                    print("The file might be open in another application. Please close it and try again.")
                    return False
                except Exception as e:
                    print(f"PDF build failed: {e}")
                    return False
            else:
                print("No content to convert")
                return False
                
        except Exception as e:
            print(f"ReportLab conversion failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _convert_with_pdfkit(self, html_content: str, output_file: Path) -> bool:
        """Convert HTML to PDF using pdfkit (wkhtmltopdf wrapper)"""
        try:
            print("Converting with pdfkit...")
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html = f.name
            
            # Convert HTML to PDF using pdfkit
            # pdfkit.from_string(html_content, str(output_file), options={'page-size': 'A4', 'margin-top': '20mm', 'margin-right': '20mm', 'margin-bottom': '20mm', 'margin-left': '20mm', 'encoding': 'UTF-8', 'print-media-type': True, 'no-outline': True, 'enable-local-file-access': True, 'quiet': True, 'dpi': 300, 'image-quality': 100, 'disable-smart-shrinking': True})
            
            # Use wkhtmltopdf directly for better control and options
            cmd = [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--margin-top', '20mm',
                '--margin-right', '20mm',
                '--margin-bottom', '20mm',
                '--margin-left', '20mm',
                '--encoding', 'UTF-8',
                '--print-media-type',
                '--no-outline',
                '--enable-local-file-access',
                '--quiet',
                '--dpi', '300',
                '--image-quality', '100',
                '--disable-smart-shrinking',
                temp_html,
                str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Cleanup
            os.unlink(temp_html)
            
            if result.returncode == 0 and output_file.exists() and output_file.stat().st_size > 0:
                print(f"PDF created successfully with pdfkit: {output_file}")
                print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")
                return True
            else:
                print(f"pdfkit failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"pdfkit conversion failed: {e}")
            return False
    
    def _convert_with_browser_print(self, html_content: str, output_file: Path) -> bool:
        """Convert using browser print (preview only, PDF saved automatically)"""
        try:
            print("Using browser preview method...")
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html = f.name
            
            # Open in browser for preview only
            print(f"🌐 Opening HTML in browser for preview...")
            print(f"📋 Instructions:")
            print(f"   1. Review the formatted document in the browser")
            print(f"   2. Close the browser tab when done previewing")
            print(f"   3. PDF will be saved automatically to: {output_file}")
            
            # Open in default browser
            webbrowser.open(f'file://{temp_html}')
            
            # Wait for user to complete preview
            input("Press Enter when you've finished previewing (close browser tab)...")
            
            # Cleanup
            os.unlink(temp_html)
            
            # Create a simple PDF using basic HTML-to-PDF conversion
            print("Creating PDF from HTML content...")
            success = self._create_simple_pdf(html_content, output_file)
            
            if success:
                print(f"PDF created successfully: {output_file}")
                print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")
                return True
            else:
                print(f"Failed to create PDF automatically")
                return False
                
        except Exception as e:
            print(f"Browser preview method failed: {e}")
            return False
    
    def _create_simple_pdf(self, html_content: str, output_file: Path) -> bool:
        """Create a simple PDF using basic HTML-to-PDF conversion"""
        try:
            # Try to use a simple HTML-to-PDF approach
            if 'weasyprint' in self.available_engines:
                return self._convert_with_weasyprint(html_content, output_file)
            
            # If no engines available, create a basic HTML file that can be printed
            print("No PDF engines available. Creating HTML file for manual printing...")
            html_output = self.output_dir / f"{output_file.stem}.html"
            
            with open(html_output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"HTML file created: {html_output}")
            print(f"To convert to PDF:")
            print(f"   1. Open {html_output} in your browser")
            print(f"   2. Press Ctrl+P and select 'Save as PDF'")
            print(f"   3. Save to: {output_file}")
            
            return False
            
        except Exception as e:
            print(f"Simple PDF creation failed: {e}")
            return False
    
    def batch_convert(self, markdown_dir: str = "articles") -> List[Path]:
        """Convert all markdown files in a directory to PDFs"""
        markdown_dir = Path(markdown_dir)
        
        if not markdown_dir.exists():
            print(f"Directory not found: {markdown_dir}")
            return []
        
        markdown_files = list(markdown_dir.glob("**/*.md"))
        
        if not markdown_files:
            print(f"No markdown files found in {markdown_dir}")
            return []
        
        print(f"Found {len(markdown_files)} markdown files to convert")
        
        successful_conversions = []
        
        for md_file in markdown_files:
            print(f"\n{'='*60}")
            print(f"Processing: {md_file.name}")
            print(f"{'='*60}")
            
            # Convert to PDF
            pdf_file = self.convert_markdown_to_pdf(md_file, md_file.stem)
            
            if pdf_file and pdf_file.exists():
                successful_conversions.append(pdf_file)
                print(f"Successfully converted: {pdf_file.name}")
            else:
                print(f"Failed to convert: {md_file.name}")
        
        print(f"\nBatch conversion complete!")
        print(f"Successful: {len(successful_conversions)}/{len(markdown_files)}")
        
        return successful_conversions

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description="Convert markdown files to beautiful PDFs via HTML")
    parser.add_argument("input", help="Markdown file or directory to convert")
    parser.add_argument("-o", "--output", help="Output directory for PDFs")
    parser.add_argument("--batch", action="store_true", help="Batch convert all markdown files in directory")
    
    args = parser.parse_args()
    
    converter = SimpleHTMLToPDFConverter(output_dir=args.output or "pdf_outputs")
    
    input_path = Path(args.input)
    
    if args.batch or input_path.is_dir():
        # Batch conversion
        converter.batch_convert(str(input_path))
    else:
        # Single file conversion
        pdf_file = converter.convert_markdown_to_pdf(input_path)
        if pdf_file:
            print(f"Successfully created: {pdf_file}")
        else:
            print("Conversion failed")
            sys.exit(1)

if __name__ == "__main__":
    main()
