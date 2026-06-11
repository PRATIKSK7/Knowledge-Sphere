import os
from io import BytesIO
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ReportGenerator:
    @staticmethod
    def generate_pdf(data: Dict[str, Any]) -> bytes:
        """
        Generates a beautiful academic PDF report using ReportLab.
        data must contain: title, query, answer, citations, entities, relationships
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Define clean, modern styles
        title_style = ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#1E293B'), # Slate 800
            spaceAfter=15
        )
        
        h2_style = ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#2563EB'), # Blue 600
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            name='ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'), # Slate 700
            spaceAfter=8
        )

        bullet_style = ParagraphStyle(
            name='ReportBullet',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            leftIndent=15,
            firstLineIndent=-10,
            textColor=colors.HexColor('#475569'),
            spaceAfter=4
        )

        story = []

        # Document Header
        story.append(Paragraph(data.get("title", "Research Intelligence Platform Report"), title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Query:</b> {data.get('query', 'N/A')}", body_style))
        story.append(Paragraph(f"<b>Generated On:</b> {os.environ.get('CURRENT_TIME', '2026-06-06')}", body_style))
        story.append(Paragraph(f"<b>Confidence Score:</b> {data.get('confidence_score', '0.85')}", body_style))
        story.append(Spacer(1, 15))

        # Main Answer
        story.append(Paragraph("Executive Summary & Analysis", h2_style))
        answer_text = data.get("answer", "No analysis content generated.")
        # Replace newlines with paragraph breaks
        for paragraph in answer_text.split("\n\n"):
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), body_style))
        story.append(Spacer(1, 15))

        # Entities Table
        entities = data.get("entities", [])
        if entities:
            story.append(Paragraph("Key Concepts & Entities Identified", h2_style))
            table_data = [["Entity Name", "Type", "Details"]]
            for ent in entities[:10]: # Cap to top 10 for layout
                props = ent.get("properties", {})
                props_str = ", ".join([f"{k}: {v}" for k, v in props.items()]) if props else "None"
                table_data.append([
                    ent.get("name", ""),
                    ent.get("label", ""),
                    props_str[:50]
                ])

            t = Table(table_data, colWidths=[150, 100, 250])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(t)
            story.append(Spacer(1, 15))

        # References Section
        citations = data.get("citations", [])
        if citations:
            story.append(Paragraph("References & Sources", h2_style))
            for cit in citations:
                ref_line = f"<b>{cit.get('citation_key', '')}</b>: {cit.get('document_title', '')}"
                story.append(Paragraph(ref_line, bullet_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_docx(data: Dict[str, Any]) -> bytes:
        """
        Mock docx generator returning raw string bites.
        """
        content = f"Title: {data.get('title')}\nQuery: {data.get('query')}\n\nContent:\n{data.get('answer')}"
        return content.encode("utf-8")
