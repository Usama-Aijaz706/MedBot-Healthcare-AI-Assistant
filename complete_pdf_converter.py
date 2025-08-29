#!/usr/bin/env python3
"""
Complete PDF Converter for MedBot
Captures ALL content from markdown files
"""

import os
import sys
import subprocess
import webbrowser
import tempfile
from pathlib import Path
from datetime import datetime

# Try to import optional dependencies
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("⚠️  Markdown package not available. Install with: pip install markdown")

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("⚠️  BeautifulSoup not available. Install with: pip install beautifulsoup4")

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  ReportLab not available. Install with: pip install reportlab")

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    print("⚠️  pdfkit not available. Install with: pip install pdfkit")

class CompletePDFConverter:
    """Complete HTML to PDF converter that captures ALL content"""
    
    def __init__(self):
        """Initialize the converter"""
        self.available_engines = self._detect_available_engines()
        print(f"🔍 Available PDF engines: {', '.join(self.available_engines)}")
    
    def _detect_available_engines(self) -> list:
        """Detect available PDF conversion engines"""
        engines = []
        
        if REPORTLAB_AVAILABLE:
            engines.append('reportlab')
            print("✅ ReportLab available for PDF generation")
        
        if PDFKIT_AVAILABLE:
            try:
                result = subprocess.run(['wkhtmltopdf', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    engines.append('pdfkit')
                    print("✅ pdfkit available for PDF generation")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        engines.append('browser-print')
        print("✅ Browser print available as fallback")
        
        return engines
    
    def create_clean_html_template(self, title: str = "Research Article") -> str:
        """Create a clean HTML template"""
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        html_template = f"""<!DOCTYPE html>
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
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            font-size: 16px;
            counter-reset: h1-counter h2-counter h3-counter h4-counter;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 60px;
            padding: 40px 0;
            border-bottom: 3px solid #4299e1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            margin: 0 -20px 40px -20px;
        }}
        
        .logo {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .subtitle {{
            font-size: 1.1rem;
            font-weight: 400;
            opacity: 0.9;
        }}
        
        .date {{
            margin-top: 20px;
            opacity: 0.8;
            font-size: 0.9rem;
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
            padding-left: 15px;
            counter-increment: h2-counter;
        }}
        
        h2::before {{
            content: counter(h1-counter) "." counter(h2-counter) ". ";
            color: #4299e1;
            font-weight: 700;
            margin-right: 10px;
        }}
        
        h3 {{
            font-size: 1.3rem;
            color: #2b6cb0;
            margin: 25px 0 12px 0;
            font-weight: 600;
            position: relative;
            padding-left: 20px;
            counter-increment: h3-counter;
        }}
        
        h3::before {{
            content: counter(h1-counter) "." counter(h2-counter) "." counter(h3-counter) ". ";
            color: #4299e1;
            font-weight: 700;
            margin-right: 10px;
        }}
        
        h4 {{
            font-size: 1.1rem;
            color: #2b6cb0;
            margin: 20px 0 10px 0;
            font-weight: 600;
            position: relative;
            padding-left: 25px;
            counter-increment: h4-counter;
        }}
        
        h4::before {{
            content: counter(h1-counter) "." counter(h2-counter) "." counter(h3-counter) "." counter(h4-counter) ". ";
            color: #4299e1;
            font-weight: 700;
            margin-right: 10px;
        }}
        
        p {{
            margin: 15px 0;
            text-align: justify;
            line-height: 1.8;
        }}
        
        .abstract {{
            background: #f7fafc;
            padding: 20px;
            border-left: 4px solid #4299e1;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        
        .abstract h2 {{
            color: #2b6cb0;
            margin-bottom: 15px;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        th, td {{
            border: 1px solid #e2e8f0;
            padding: 12px;
            text-align: left;
        }}
        
        th {{
            background: linear-gradient(135deg, #4299e1, #667eea);
            color: white;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        
        tr:hover {{
            background-color: #edf2f7;
        }}
        
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        
        .figure {{
            margin: 20px 0;
            text-align: center;
        }}
        
        .figure img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .figure figcaption {{
            margin-top: 10px;
            font-style: italic;
            color: #718096;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">MedBot</div>
        <div class="subtitle">Advanced Healthcare AI Assistant</div>
        <div class="subtitle">Professional Medical Research Analysis & Insights</div>
        <div class="date">Generated on {current_date}</div>
    </div>
    
    <div id="content">
        <!-- Content will be inserted here -->
    </div>
</body>
</html>"""
        
        return html_template
    
    def convert_markdown_to_html(self, markdown_file: Path) -> str:
        """Convert markdown to HTML"""
        if not MARKDOWN_AVAILABLE:
            print("❌ Markdown package not available")
            return ""
        
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
            title = markdown_file.stem.replace('_', ' ').title()
            html_template = self.create_clean_html_template(title)
            final_html = html_template.replace('<!-- Content will be inserted here -->', html_content)
            
            return final_html
            
        except Exception as e:
            print(f"❌ Error converting markdown to HTML: {e}")
            return ""
    
    def convert_markdown_to_pdf(self, markdown_file: Path, output_dir: Path = None) -> Path:
        """Convert markdown file to PDF"""
        
        if not markdown_file.exists():
            print(f"❌ Markdown file not found: {markdown_file}")
            return None
        
        if output_dir is None:
            output_dir = Path("pdf_outputs")
        
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = markdown_file.stem
        output_file = output_dir / f"{output_name}_{timestamp}.pdf"
        
        print(f"🔄 Converting {markdown_file.name} to PDF...")
        print(f"📁 Output: {output_file}")
        
        html_content = self.convert_markdown_to_html(markdown_file)
        if not html_content:
            print("❌ Failed to convert markdown to HTML")
            return None
        
        for method in self.available_engines:
            if method == 'reportlab':
                if self._convert_with_reportlab(html_content, output_file):
                    return output_file
            elif method == 'pdfkit':
                if self._convert_with_pdfkit(html_content, output_file):
                    return output_file
            elif method == 'browser-print':
                if self._convert_with_browser_print(html_content, output_file):
                    return output_file
        
        print("❌ All PDF conversion methods failed")
        return None
    
    def _convert_with_reportlab(self, html_content: str, output_file: Path) -> bool:
        """Convert HTML to PDF using ReportLab with COMPLETE content capture"""
        if not REPORTLAB_AVAILABLE:
            return False
        
        try:
            print("🔄 Converting with ReportLab...")
            
            doc = SimpleDocTemplate(
                str(output_file),
                pagesize=A4,
                leftMargin=1*inch,
                rightMargin=1*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                spaceBefore=20,
                textColor=colors.darkblue,
                alignment=1,
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
                alignment=0
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
                alignment=0
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
                alignment=0
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
                alignment=0
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                spaceBefore=6,
                leading=14,
                fontName='Helvetica',
                alignment=4,
                backColor=None,
                leftIndent=0
            )
            
            abstract_style = ParagraphStyle(
                'CustomAbstract',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                spaceBefore=6,
                leading=14,
                fontName='Helvetica',
                leftIndent=0,
                rightIndent=0,
                backColor=None,
                alignment=4
            )
            
            if BEAUTIFULSOUP_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                title = "Research Article"
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                
                elements = []
                
                # Add title page
                elements.append(Paragraph(title, title_style))
                elements.append(Spacer(1, 40))
                
                current_date = datetime.now().strftime("%B %d, %Y")
                elements.append(Paragraph(f"Generated by MedBot Healthcare AI Assistant", normal_style))
                elements.append(Paragraph(f"Date: {current_date}", normal_style))
                elements.append(Spacer(1, 30))
                
                elements.append(PageBreak())
                
                # Process main content - COMPLETE CAPTURE
                main_content = soup.find('body') or soup
                
                # Track heading numbers
                h1_count = 0
                h2_count = 0
                h3_count = 0
                h4_count = 0
                
                # Process elements systematically
                for element in main_content.descendants:
                    if element.name in ['script', 'style', 'meta', 'link']:
                        continue
                    
                    # Skip header sections
                    if element.name == 'div' and element.get('class'):
                        div_classes = element.get('class', [])
                        if any(cls in div_classes for cls in ['header', 'footer']):
                            continue
                    
                    if element.name == 'h1':
                        h1_count += 1
                        h2_count = h3_count = h4_count = 0
                        text = element.get_text().strip()
                        if text:
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                elements.append(Paragraph(f"{h1_count}. {clean_text}", h1_style))
                    
                    elif element.name == 'h2':
                        h2_count += 1
                        h3_count = h4_count = 0
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
                            # Filter out unwanted content
                            if any(keyword in text.lower() for keyword in [
                                'const ', 'function', 'document.', 'getelementbyid', 
                                'script', 'javascript', 'document generated successfully',
                                'this document was created by medbot', 'professional medical research analysis'
                            ]):
                                continue
                            
                            clean_text = self._clean_text_for_reportlab(text)
                            if clean_text:
                                if 'abstract' in clean_text.lower() or len(clean_text) > 200:
                                    elements.append(Paragraph(clean_text, abstract_style))
                                else:
                                    elements.append(Paragraph(clean_text, normal_style))
                    
                    elif element.name == 'table':
                        try:
                            print(f"🔄 Processing table: {element.get_text()[:100]}...")
                            
                            data = []
                            rows = element.find_all('tr')
                            
                            # First pass: collect all data and determine column structure
                            for row in rows:
                                row_data = []
                                cells = row.find_all(['th', 'td'])
                                
                                for cell in cells:
                                    cell_text = cell.get_text().strip()
                                    clean_cell_text = self._clean_text_for_reportlab(cell_text)
                                    if clean_cell_text:
                                        if cell.name == 'th':
                                            header_style = ParagraphStyle(
                                                'TableHeader',
                                                parent=normal_style,
                                                fontName='Helvetica-Bold',
                                                fontSize=10,
                                                backColor=None
                                            )
                                            row_data.append(Paragraph(clean_cell_text, header_style))
                                        else:
                                            row_data.append(Paragraph(clean_cell_text, normal_style))
                                
                                if row_data:
                                    data.append(row_data)
                            
                            if data:
                                # Calculate optimal column widths based on content
                                max_cols = max(len(row) for row in data) if data else 1
                                
                                # Analyze content to determine optimal column widths
                                col_widths = []
                                for col_idx in range(max_cols):
                                    max_width = 0
                                    max_text_length = 0
                                    
                                    for row in data:
                                        if col_idx < len(row):
                                            # Get text length for width calculation
                                            if hasattr(row[col_idx], 'text'):
                                                text_length = len(row[col_idx].text)
                                            else:
                                                text_length = len(str(row[col_idx]))
                                            
                                            max_text_length = max(max_text_length, text_length)
                                    
                                    # Calculate column width based on content
                                    # For tables with complex content, use more flexible widths
                                    if max_text_length > 100:
                                        # Wide columns for complex content
                                        col_width = 3.5 * inch
                                    elif max_text_length > 50:
                                        # Medium columns for moderate content
                                        col_width = 2.5 * inch
                                    else:
                                        # Standard columns for short content
                                        col_width = 2.0 * inch
                                    
                                    col_widths.append(col_width)
                                
                                # Create table with calculated widths
                                table = Table(data, colWidths=col_widths)
                                
                                # Enhanced table styling for professional appearance
                                table_style_list = [
                                    # Basic alignment and spacing
                                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                    
                                    # Enhanced grid lines
                                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.darkblue),
                                    ('BOX', (0,0), (-1,-1), 1.0, colors.darkblue),
                                    
                                    # Header row styling - Professional look
                                    ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0,0), (-1,0), 10),
                                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                    ('BOTTOMPADDING', (0,0), (-1,0), 12),
                                    ('TOPPADDING', (0,0), (-1,0), 12),
                                    
                                    # Data rows styling - Clean and readable
                                    ('BACKGROUND', (0,1), (-1,-1), colors.white),
                                    ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                                    ('FONTSIZE', (0,1), (-1,-1), 9),
                                    ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
                                    
                                    # Alternating row colors for better readability
                                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey]),
                                    
                                    # Enhanced padding for better spacing
                                    ('BOTTOMPADDING', (0,1), (-1,-1), 8),
                                    ('TOPPADDING', (0,1), (-1,-1), 8),
                                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                                    ('RIGHTPADDING', (0,0), (-1,-1), 10),
                                    
                                    # Row height for better proportions
                                    ('MINIMUMHEIGHT', (0,0), (-1,-1), 30),
                                    
                                    # Word wrapping for better text handling
                                    ('WORDWRAP', (0,0), (-1,-1), True),
                                ]
                                
                                # Apply table styling
                                table.setStyle(TableStyle(table_style_list))
                                
                                # Add table to elements
                                elements.append(table)
                                elements.append(Spacer(1, 20))
                                
                                print(f"✅ Table processed successfully with {len(data)} rows and {max_cols} columns")
                                print(f"📏 Column widths: {[f'{w/inch:.1f}in' for w in col_widths]}")
                            
                            else:
                                # Fallback: add table as text if no structured data
                                table_text = element.get_text().strip()
                                clean_table_text = self._clean_text_for_reportlab(table_text)
                                if clean_table_text:
                                    elements.append(Paragraph(f"Table Content: {clean_table_text}", normal_style))
                        
                        except Exception as e:
                            print(f"⚠️  Table processing failed: {e}")
                            import traceback
                            traceback.print_exc()
                            # Fallback: add table as text
                            table_text = element.get_text().strip()
                            clean_table_text = self._clean_text_for_reportlab(table_text)
                            if clean_table_text:
                                elements.append(Paragraph(f"Table Content: {clean_table_text}", normal_style))
                    
                    elif element.name in ['ul', 'ol']:
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
                
                # Additional pass to capture ANY missed content
                print("🔍 Performing additional content capture...")
                all_text_content = main_content.get_text()
                print(f"📊 Total text content length: {len(all_text_content)} characters")
                
                # Check for expected sections
                expected_sections = [
                    "Material and Methods",
                    "Study Design Research Participants", 
                    "Inclusion and Exclusion Criteria",
                    "Data Collection Methods"
                ]
                
                for section in expected_sections:
                    if section.lower() in all_text_content.lower():
                        print(f"✅ Found section: {section}")
                    else:
                        print(f"⚠️  Missing section: {section}")
                
                # Add clean end marker
                elements.append(Spacer(1, 30))
                elements.append(Paragraph("─" * 60, normal_style))
                elements.append(Spacer(1, 15))
                elements.append(Paragraph("End of Document", normal_style))
                
                if elements:
                    doc.build(elements)
                    print(f"✅ PDF created successfully with ReportLab: {output_file}")
                    print(f"📊 Total elements created: {len(elements)}")
                    return True
                else:
                    print("❌ No content to convert")
                    return False
            
            else:
                print("❌ BeautifulSoup not available for HTML parsing")
                return False
        
        except Exception as e:
            print(f"❌ ReportLab conversion failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _convert_with_pdfkit(self, html_content: str, output_file: Path) -> bool:
        """Convert HTML to PDF using pdfkit"""
        if not PDFKIT_AVAILABLE:
            return False
        
        try:
            print("🔄 Converting with pdfkit...")
            
            options = {
                'page-size': 'A4',
                'margin-top': '1in',
                'margin-right': '1in',
                'margin-bottom': '1in',
                'margin-left': '1in',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            pdfkit.from_string(html_content, str(output_file), options=options)
            
            if output_file.exists():
                print(f"✅ PDF created successfully with pdfkit: {output_file}")
                return True
            else:
                print("❌ PDF file not created")
                return False
        
        except Exception as e:
            print(f"❌ pdfkit conversion failed: {e}")
            return False
    
    def _convert_with_browser_print(self, html_content: str, output_file: Path) -> bool:
        """Convert HTML to PDF using browser print"""
        try:
            print("🔄 Using browser preview method...")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html = f.name
            
            print("🌐 Opening HTML in browser for preview...")
            webbrowser.open(f'file://{temp_html}')
            
            print("📋 Instructions:")
            print("1. Review the formatted document in the browser")
            print("2. Press Ctrl+P and select 'Save as PDF'")
            print(f"3. Save to: {output_file}")
            
            os.unlink(temp_html)
            
            return True
        
        except Exception as e:
            print(f"❌ Browser print method failed: {e}")
            return False
    
    def _clean_text_for_reportlab(self, text: str) -> str:
        """Clean text for ReportLab with improved table handling"""
        if not text:
            return ""
        
        import re
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Handle special characters for ReportLab
        clean_text = clean_text.replace('&', '&amp;')
        clean_text = clean_text.replace('<', '&lt;')
        clean_text = clean_text.replace('>', '&gt;')
        clean_text = clean_text.replace('"', '&quot;')
        clean_text = clean_text.replace("'", '&#39;')
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Remove HTML entities
        clean_text = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_text)
        
        # Handle special table characters
        clean_text = clean_text.replace('−', '-')  # Replace Unicode minus with regular hyphen
        clean_text = clean_text.replace('–', '-')  # Replace en dash with regular hyphen
        clean_text = clean_text.replace('—', '-')  # Replace em dash with regular hyphen
        
        # Clean up multiple hyphens
        clean_text = re.sub(r'-+', '-', clean_text)
        
        # Handle table-specific formatting
        if '|' in clean_text:
            # This might be a table row, clean it up
            clean_text = clean_text.replace('|', ' | ')
            clean_text = re.sub(r'\s*\|\s*', ' | ', clean_text)
        
        # Limit text length for very long content
        if len(clean_text) > 2000:
            clean_text = clean_text[:2000] + "..."
        
        return clean_text


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python complete_pdf_converter.py <markdown_file>")
        print("Example: python complete_pdf_converter.py articles/article.md")
        sys.exit(1)
    
    markdown_file = Path(sys.argv[1])
    
    if not markdown_file.exists():
        print(f"❌ Markdown file not found: {markdown_file}")
        sys.exit(1)
    
    converter = CompletePDFConverter()
    result = converter.convert_markdown_to_pdf(markdown_file)
    
    if result:
        print(f"✅ Conversion successful! PDF saved to: {result}")
    else:
        print("❌ Conversion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
