from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os
import tempfile
import logging
from datetime import datetime
from typing import Dict, Any, List
from ..models import MeetingRecord
from ..config import settings

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        # Ensure PDF temp directory exists
        os.makedirs(settings.pdf_temp_dir, exist_ok=True)
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2C3E50')
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#34495E'),
            borderWidth=1,
            borderColor=colors.HexColor('#BDC3C7'),
            borderPadding=5
        ))
        
        # Indian language style (for preserving formatting)
        self.styles.add(ParagraphStyle(
            name='IndianText',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',  # Could be enhanced with Devanagari fonts
            spaceAfter=6
        ))
        
        # Timestamp style
        self.styles.add(ParagraphStyle(
            name='Timestamp',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=TA_LEFT
        ))
        
        # Action item style
        self.styles.add(ParagraphStyle(
            name='ActionItem',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=6
        ))
    
    async def generate_pdf(self, meeting: MeetingRecord) -> str:
        """Generate timestamped PDF of meeting minutes"""
        try:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meeting_{meeting.id}_{timestamp}.pdf"
            pdf_path = os.path.join(settings.pdf_temp_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Add title and metadata
            story.extend(self._build_header(meeting))
            
            # Add summary sections
            if meeting.summary:
                story.extend(self._build_summary_section(meeting.summary))
            
            # Add transcript with timestamps
            if meeting.transcript:
                story.extend(self._build_transcript_section(meeting.transcript))
            
            # Add footer
            story.extend(self._build_footer())
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF generated successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise Exception(f"Failed to generate PDF: {str(e)}")
    
    def _build_header(self, meeting: MeetingRecord) -> List:
        """Build PDF header with meeting information"""
        story = []
        
        # Title
        title = Paragraph(meeting.title, self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Meeting metadata table
        metadata = [
            ['Meeting ID:', str(meeting.id)],
            ['Date & Time:', meeting.upload_time.strftime('%B %d, %Y at %I:%M %p IST')],
            ['Original File:', meeting.original_filename],
            ['Generated On:', datetime.now().strftime('%B %d, %Y at %I:%M %p IST')]
        ]
        
        if meeting.summary and 'meeting_duration' in meeting.summary:
            metadata.append(['Duration:', meeting.summary['meeting_duration']])
        
        metadata_table = Table(metadata, colWidths=[1.5*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1'))
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_summary_section(self, summary: Dict[str, Any]) -> List:
        """Build summary section with decisions, action items, etc."""
        story = []
        
        # Summary header
        story.append(Paragraph("📋 Executive Summary", self.styles['SectionHeader']))
        
        # WhatsApp blurb
        if summary.get('whatsapp_blurb'):
            story.append(Paragraph("<b>Quick Summary:</b>", self.styles['Normal']))
            story.append(Paragraph(summary['whatsapp_blurb'], self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Key decisions
        if summary.get('decisions'):
            story.append(Paragraph("🎯 Key Decisions", self.styles['SectionHeader']))
            for i, decision in enumerate(summary['decisions'], 1):
                decision_text = f"<b>{i}. {decision.get('decision', 'N/A')}</b>"
                if decision.get('context'):
                    decision_text += f"<br/><i>Context:</i> {decision['context']}"
                if decision.get('impact'):
                    decision_text += f"<br/><i>Impact:</i> {decision['impact']}"
                
                story.append(Paragraph(decision_text, self.styles['Normal']))
                story.append(Spacer(1, 8))
        
        # Action items
        if summary.get('action_items'):
            story.append(Paragraph("✅ Action Items", self.styles['SectionHeader']))
            
            # Create action items table
            action_data = [['#', 'Action', 'Owner', 'Due Date', 'Priority']]
            for i, action in enumerate(summary['action_items'], 1):
                action_data.append([
                    str(i),
                    action.get('action', 'N/A'),
                    action.get('owner', 'TBD'),
                    action.get('due_date', 'TBD'),
                    action.get('priority', 'Medium').title()
                ])
            
            action_table = Table(action_data, colWidths=[0.3*inch, 2.5*inch, 1.2*inch, 1*inch, 0.8*inch])
            action_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
            ]))
            
            story.append(action_table)
            story.append(Spacer(1, 12))
        
        # Open questions
        if summary.get('open_questions'):
            story.append(Paragraph("❓ Open Questions", self.styles['SectionHeader']))
            for i, question in enumerate(summary['open_questions'], 1):
                question_text = f"<b>{i}. {question.get('question', 'N/A')}</b>"
                if question.get('context'):
                    question_text += f"<br/><i>Context:</i> {question['context']}"
                if question.get('assigned_to'):
                    question_text += f"<br/><i>Assigned to:</i> {question['assigned_to']}"
                
                story.append(Paragraph(question_text, self.styles['Normal']))
                story.append(Spacer(1, 8))
        
        # Key topics
        if summary.get('key_topics'):
            story.append(Paragraph("🏷️ Key Topics Discussed", self.styles['SectionHeader']))
            topics_text = " • ".join(summary['key_topics'])
            story.append(Paragraph(topics_text, self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Participants
        if summary.get('participants'):
            story.append(Paragraph("👥 Participants", self.styles['SectionHeader']))
            participants_text = " • ".join(summary['participants'])
            story.append(Paragraph(participants_text, self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        return story
    
    def _build_transcript_section(self, transcript: Dict[str, Any]) -> List:
        """Build transcript section with timestamps"""
        story = []
        
        story.append(Paragraph("📝 Full Transcript", self.styles['SectionHeader']))
        
        # Add note about Indian language preservation
        if transcript.get('india_enhanced'):
            note = "Note: This transcript preserves Tamil and Hindi text with English glosses in parentheses."
            story.append(Paragraph(f"<i>{note}</i>", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Process segments if available (timestamped)
        if transcript.get('segments'):
            for segment in transcript['segments']:
                start_time = self._format_timestamp(segment.get('start', 0))
                end_time = self._format_timestamp(segment.get('end', 0))
                text = segment.get('text', '').strip()
                
                if text:
                    # Timestamp
                    timestamp_text = f"[{start_time} - {end_time}]"
                    story.append(Paragraph(timestamp_text, self.styles['Timestamp']))
                    
                    # Transcript text
                    story.append(Paragraph(text, self.styles['IndianText']))
                    story.append(Spacer(1, 6))
        
        else:
            # Fallback: just show the full text without timestamps
            full_text = transcript.get('text', 'No transcript available.')
            story.append(Paragraph(full_text, self.styles['IndianText']))
        
        return story
    
    def _build_footer(self) -> List:
        """Build PDF footer"""
        story = []
        
        story.append(Spacer(1, 30))
        footer_text = f"Generated by MeetNotes India • {datetime.now().strftime('%B %d, %Y')} • Confidential"
        story.append(Paragraph(footer_text, self.styles['Timestamp']))
        
        return story
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS format"""
        try:
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return f"{minutes:02d}:{seconds:02d}"
        except:
            return "00:00"