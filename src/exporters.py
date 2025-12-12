"""
Exporters Module - Export text and data to various formats.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Text export
def export_to_txt(text: str, filepath: str) -> None:
    """
    Export text to a plain text file.
    
    Args:
        text: Text content to export.
        filepath: Output file path.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)


# Word export
def export_to_docx(text: str, filepath: str, title: Optional[str] = None) -> None:
    """
    Export text to a Word document.
    
    Args:
        text: Text content to export.
        filepath: Output file path.
        title: Optional document title.
    """
    from docx import Document
    from docx.shared import Pt, Inches
    
    doc = Document()
    
    # Add title if provided
    if title:
        doc.add_heading(title, 0)
    
    # Add metadata
    doc.add_paragraph(f"Vytvořeno: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    doc.add_paragraph("")
    
    # Add text content - split by paragraphs
    for paragraph in text.split('\n\n'):
        if paragraph.strip():
            p = doc.add_paragraph(paragraph.strip())
            p.style.font.size = Pt(11)
    
    doc.save(filepath)


# PDF export for text
def export_to_pdf(text: str, filepath: str, title: Optional[str] = None) -> None:
    """
    Export text to a PDF document.
    
    Args:
        text: Text content to export.
        filepath: Output file path.
        title: Optional document title.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Try to register a font that supports Czech characters
    try:
        # Try common Windows fonts
        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
        font_name = 'DejaVu'
    except:
        font_name = 'Helvetica'  # Fallback
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Create custom style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        fontName=font_name
    )
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        fontName=font_name
    )
    
    story = []
    
    # Add title
    if title:
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.5*cm))
    
    # Add date
    date_text = f"Vytvořeno: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    story.append(Paragraph(date_text, body_style))
    story.append(Spacer(1, 1*cm))
    
    # Add text content
    for paragraph in text.split('\n'):
        if paragraph.strip():
            # Escape special characters for ReportLab
            safe_text = paragraph.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(safe_text, body_style))
            story.append(Spacer(1, 0.3*cm))
    
    doc.build(story)


# Excel export for tables
def export_table_to_xlsx(data: List[Dict[str, Any]], 
                         columns: List[str], 
                         filepath: str,
                         sheet_name: str = "Extrahovaná data") -> None:
    """
    Export tabular data to Excel.
    
    Args:
        data: List of dictionaries with data.
        columns: List of column names.
        filepath: Output file path.
        sheet_name: Name of the Excel sheet.
    """
    import pandas as pd
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)
    
    # Export to Excel with formatting
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Get workbook and worksheet for formatting
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Auto-adjust column widths
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max() if len(df) > 0 else 0,
                len(str(col))
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)


def export_matches_to_xlsx(matches: Dict[str, List[str]], 
                           filepath: str,
                           sheet_name: str = "Nalezené hodnoty") -> None:
    """
    Export pattern matches to Excel.
    
    Args:
        matches: Dictionary mapping field names to lists of matches.
        filepath: Output file path.
        sheet_name: Name of the Excel sheet.
    """
    import pandas as pd
    from openpyxl.styles import Font, PatternFill
    
    # Find the maximum number of matches for any field
    max_matches = max(len(v) for v in matches.values()) if matches else 0
    
    # Create data structure
    data = {}
    for field_name, values in matches.items():
        # Pad with empty strings to match length
        padded_values = values + [''] * (max_matches - len(values))
        data[field_name] = padded_values
    
    df = pd.DataFrame(data)
    
    # Export to Excel
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Style header row
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
        
        # Auto-adjust column widths
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max() if len(df) > 0 else 0,
                len(str(col))
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)


# PDF export for tables
def export_table_to_pdf(data: List[Dict[str, Any]], 
                        columns: List[str], 
                        filepath: str,
                        title: str = "Extrahovaná data") -> None:
    """
    Export tabular data to PDF.
    
    Args:
        data: List of dictionaries with data.
        columns: List of column names.
        filepath: Output file path.
        title: Document title.
    """
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4) if len(columns) > 4 else A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(title, styles['Heading1']))
    story.append(Paragraph(
        f"Vytvořeno: {datetime.now().strftime('%d.%m.%Y %H:%M')}", 
        styles['Normal']
    ))
    story.append(Spacer(1, 1*cm))
    
    # Create table data
    table_data = [columns]  # Header row
    for row in data:
        table_data.append([str(row.get(col, '')) for col in columns])
    
    # Create table
    table = Table(table_data)
    
    # Style the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
    ])
    table.setStyle(style)
    
    story.append(table)
    doc.build(story)


def get_export_formats_text() -> List[str]:
    """Get available export formats for text."""
    return ['txt', 'docx', 'pdf']


def get_export_formats_table() -> List[str]:
    """Get available export formats for tables."""
    return ['xlsx', 'pdf']
