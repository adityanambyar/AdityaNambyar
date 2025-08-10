import openai
import asyncio
import logging
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import MeetingRecord
from ..config import settings

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def generate_summary(self, meeting_id: str, transcript_data: Dict[str, Any], db: Session) -> None:
        """
        Generate AI summary with:
        - Decisions made
        - Action items (Owner, Due date)
        - Open questions
        - WhatsApp blurb (≤900 chars)
        """
        meeting = db.query(MeetingRecord).filter(MeetingRecord.id == meeting_id).first()
        if not meeting:
            logger.error(f"Meeting not found: {meeting_id}")
            return
        
        try:
            # Update status to processing
            meeting.summarization_status = "processing"
            db.commit()
            
            # Extract text from transcript
            transcript_text = transcript_data.get('text', '')
            
            # Generate structured summary
            summary_data = await self._generate_structured_summary(transcript_text)
            
            # Generate WhatsApp blurb
            whatsapp_blurb = await self._generate_whatsapp_blurb(transcript_text, summary_data)
            
            # Combine all summary components
            complete_summary = {
                'decisions': summary_data.get('decisions', []),
                'action_items': summary_data.get('action_items', []),
                'open_questions': summary_data.get('open_questions', []),
                'whatsapp_blurb': whatsapp_blurb,
                'key_topics': summary_data.get('key_topics', []),
                'participants': summary_data.get('participants', []),
                'meeting_duration': self._estimate_duration(transcript_data),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Save summary
            meeting.summary = complete_summary
            meeting.summarization_status = "completed"
            db.commit()
            
            logger.info(f"Summarization completed for meeting: {meeting_id}")
            
        except Exception as e:
            logger.error(f"Summarization failed for meeting {meeting_id}: {str(e)}")
            meeting.summarization_status = "failed"
            db.commit()
    
    async def _generate_structured_summary(self, transcript_text: str) -> Dict[str, Any]:
        """Generate structured summary using OpenAI GPT"""
        
        system_prompt = """You are an expert meeting summarizer for Indian business contexts. 
        Analyze the meeting transcript and extract:
        1. Key decisions made
        2. Action items with responsible person and timeline
        3. Open questions that need follow-up
        4. Key topics discussed
        5. Participants mentioned

        Pay special attention to:
        - Indian business customs and communication styles
        - Hierarchical relationships (respect for seniors)
        - Cultural context and references
        - Mixed language usage (English with Hindi/Tamil phrases)
        - Indian names and titles

        Return a JSON structure with these categories. For action items, try to identify:
        - What needs to be done
        - Who is responsible (owner)
        - When it should be completed (due date/timeframe)
        
        If specific dates aren't mentioned, suggest reasonable timeframes based on context."""
        
        user_prompt = f"""Please analyze this meeting transcript and provide a structured summary:

        TRANSCRIPT:
        {transcript_text[:4000]}  # Limit to avoid token limits
        
        Return only valid JSON with the following structure:
        {{
            "decisions": [
                {{
                    "decision": "Clear description of what was decided",
                    "context": "Brief context or reasoning",
                    "impact": "Who/what this affects"
                }}
            ],
            "action_items": [
                {{
                    "action": "What needs to be done",
                    "owner": "Person responsible",
                    "due_date": "Timeline or due date",
                    "priority": "high|medium|low",
                    "status": "pending"
                }}
            ],
            "open_questions": [
                {{
                    "question": "What needs to be resolved",
                    "context": "Why this is important",
                    "assigned_to": "Who should address this"
                }}
            ],
            "key_topics": ["Topic 1", "Topic 2", "Topic 3"],
            "participants": ["Name 1", "Name 2", "Name 3"]
        }}"""
        
        try:
            response = await self._call_openai_with_retry(system_prompt, user_prompt)
            
            # Parse JSON response
            summary_data = json.loads(response)
            return summary_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse summary JSON: {str(e)}")
            # Return fallback structure
            return {
                "decisions": [],
                "action_items": [],
                "open_questions": [],
                "key_topics": [],
                "participants": []
            }
    
    async def _generate_whatsapp_blurb(self, transcript_text: str, summary_data: Dict[str, Any]) -> str:
        """Generate concise WhatsApp-friendly summary (≤900 chars)"""
        
        system_prompt = """Create a concise, WhatsApp-friendly summary of the meeting. 
        This should be informal, engaging, and under 900 characters. 
        Use Indian communication style with appropriate emojis and casual language.
        Include key decisions and action items in a way that's easy to quickly understand.
        
        Style guidelines:
        - Use emojis appropriately 📝 ✅ 🎯 ⏰
        - Keep it conversational but informative
        - Mention key people and deadlines
        - Use bullet points or short phrases
        - Indian English style is fine"""
        
        # Prepare context from summary
        decisions_text = "; ".join([d.get('decision', '') for d in summary_data.get('decisions', [])])
        actions_text = "; ".join([f"{a.get('action', '')} - {a.get('owner', '')}" for a in summary_data.get('action_items', [])])
        
        user_prompt = f"""Create a WhatsApp summary (max 900 chars) for this meeting:

        KEY DECISIONS: {decisions_text[:200]}
        ACTION ITEMS: {actions_text[:200]}
        TOPICS: {', '.join(summary_data.get('key_topics', [])[:3])}
        
        Make it engaging and easy to share in a WhatsApp group!"""
        
        try:
            blurb = await self._call_openai_with_retry(system_prompt, user_prompt, max_tokens=300)
            
            # Ensure it's under 900 characters
            if len(blurb) > 900:
                blurb = blurb[:897] + "..."
            
            return blurb
            
        except Exception as e:
            logger.error(f"Failed to generate WhatsApp blurb: {str(e)}")
            # Return fallback
            return "📝 Meeting summary available. Key decisions made and action items assigned. Check full details in the app! 🎯"
    
    async def _call_openai_with_retry(self, system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
        """Call OpenAI API with retry logic"""
        max_retries = settings.max_retries
        base_delay = settings.base_delay
        max_delay = settings.max_delay
        
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Cost-effective for summarization
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.3  # Lower temperature for more consistent output
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"OpenAI API attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                await asyncio.sleep(delay)
        
        raise Exception(f"OpenAI API failed after {max_retries} attempts")
    
    def _estimate_duration(self, transcript_data: Dict[str, Any]) -> str:
        """Estimate meeting duration from transcript data"""
        try:
            if 'segments' in transcript_data and transcript_data['segments']:
                last_segment = transcript_data['segments'][-1]
                if 'end' in last_segment:
                    duration_seconds = last_segment['end']
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    return f"{minutes}m {seconds}s"
            
            # Fallback: estimate based on text length (rough approximation)
            text_length = len(transcript_data.get('text', ''))
            estimated_minutes = max(1, text_length // 1000)  # Very rough estimate
            return f"~{estimated_minutes}m"
            
        except Exception:
            return "Unknown"

from datetime import datetime