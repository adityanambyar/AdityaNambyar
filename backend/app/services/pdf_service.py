from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for better formatting"""
        # Custom title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        # Custom heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Custom body style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leading=14
        )
    
    async def generate_meeting_minutes(
        self, meeting_data: Dict[str, Any], transcript_data: Dict[str, Any], 
        summary_data: Dict[str, Any]
    ) -> str:
        """Generate timestamped PDF meeting minutes"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                pdf_path = tmp_file.name
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build PDF content
            story = []
            
            # Add header
            story.extend(self._create_header(meeting_data))
            
            # Add meeting details
            story.extend(self._create_meeting_details(meeting_data))
            
            # Add summary section
            story.extend(self._create_summary_section(summary_data))
            
            # Add transcript section
            story.extend(self._create_transcript_section(transcript_data))
            
            # Build PDF
            doc.build(story)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    def _create_header(self, meeting_data: Dict[str, Any]) -> List:
        """Create PDF header"""
        elements = []
        
        # Title
        title = Paragraph("MeetNotes India - Meeting Minutes", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Meeting info
        meeting_info = [
            ["Meeting ID:", str(meeting_data.get("id", "N/A"))],
            ["Original Filename:", meeting_data.get("original_filename", "N/A")],
            ["Upload Date:", meeting_data.get("uploaded_at", "N/A")],
            ["File Size:", f"{meeting_data.get('file_size', 0) / (1024*1024):.2f} MB"]
        ]
        
        meeting_table = Table(meeting_info, colWidths=[2*inch, 4*inch])
        meeting_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(meeting_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_meeting_details(self, meeting_data: Dict[str, Any]) -> List:
        """Create meeting details section"""
        elements = []
        
        # Meeting Details heading
        details_heading = Paragraph("Meeting Details", self.heading_style)
        elements.append(details_heading)
        
        # Meeting details table
        details_data = [
            ["Audio Type:", meeting_data.get("mime_type", "N/A")],
            ["Expires At:", meeting_data.get("expires_at", "N/A")],
            ["Status:", "Active" if not meeting_data.get("is_deleted") else "Deleted"]
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(details_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_summary_section(self, summary_data: Dict[str, Any]) -> List:
        """Create summary section"""
        elements = []
        
        # Summary heading
        summary_heading = Paragraph("Meeting Summary", self.heading_style)
        elements.append(summary_heading)
        
        # Decisions
        if summary_data.get("decisions"):
            decisions_heading = Paragraph("✅ Key Decisions", self.styles['Heading3'])
            elements.append(decisions_heading)
            
            for decision in summary_data["decisions"][:5]:  # Top 5 decisions
                decision_text = Paragraph(f"• {decision}", self.body_style)
                elements.append(decision_text)
            
            elements.append(Spacer(1, 12))
        
        # Action Items
        if summary_data.get("action_items"):
            actions_heading = Paragraph("📝 Action Items", self.styles['Heading3'])
            elements.append(actions_heading)
            
            for item in summary_data["action_items"][:5]:  # Top 5 action items
                owner = item.get("owner", "Unassigned")
                action = item.get("action", "")
                action_text = Paragraph(f"• {owner}: {action}", self.body_style)
                elements.append(action_text)
            
            elements.append(Spacer(1, 12))
        
        # Open Questions
        if summary_data.get("open_questions"):
            questions_heading = Paragraph("❓ Open Questions", self.styles['Heading3'])
            elements.append(questions_heading)
            
            for question in summary_data["open_questions"][:5]:  # Top 5 questions
                question_text = Paragraph(f"• {question}", self.body_style)
                elements.append(question_text)
            
            elements.append(Spacer(1, 12))
        
        # WhatsApp Blurb
        if summary_data.get("whatsapp_blurb"):
            blurb_heading = Paragraph("📱 WhatsApp Summary", self.styles['Heading3'])
            elements.append(blurb_heading)
            
            blurb_text = Paragraph(summary_data["whatsapp_blurb"], self.body_style)
            elements.append(blurb_text)
            elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_transcript_section(self, transcript_data: Dict[str, Any]) -> List:
        """Create transcript section with timestamps"""
        elements = []
        
        # Transcript heading
        transcript_heading = Paragraph("Meeting Transcript", self.heading_style)
        elements.append(transcript_heading)
        
        # Language info
        language = transcript_data.get("language", "Unknown")
        confidence = transcript_data.get("confidence", 0)
        
        lang_info = Paragraph(
            f"Language: {language} | Confidence: {confidence:.2f}%",
            self.styles['Normal']
        )
        elements.append(lang_info)
        elements.append(Spacer(1, 12))
        
        # Transcript segments with timestamps
        segments = transcript_data.get("segments", [])
        if segments:
            for segment in segments:
                start_time = segment.get("start", 0)
                end_time = segment.get("end", 0)
                text = segment.get("text", "")
                
                # Format timestamp
                start_str = self._format_timestamp(start_time)
                end_str = self._format_timestamp(end_time)
                
                # Create timestamped text
                timestamp_text = f"[{start_str} - {end_str}] {text}"
                segment_para = Paragraph(timestamp_text, self.body_style)
                elements.append(segment_para)
                elements.append(Spacer(1, 6))
        
        return elements
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    async def cleanup_pdf(self, pdf_path: str):
        """Clean up temporary PDF file"""
        try:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
                logger.info(f"Cleaned up temporary PDF: {pdf_path}")
        except Exception as e:
            logger.error(f"Error cleaning up PDF: {str(e)}")

pdf_service = PDFService()