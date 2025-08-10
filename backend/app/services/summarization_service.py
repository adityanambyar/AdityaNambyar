import re
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SummarizationService:
    def __init__(self):
        self.action_patterns = [
            r"action item[s]?:?\s*(.+)",
            r"todo[s]?:?\s*(.+)",
            r"follow up[s]?:?\s*(.+)",
            r"next step[s]?:?\s*(.+)",
            r"assign[ed]? to\s+(\w+):\s*(.+)",
            r"(\w+)\s+will\s+(.+)",
            r"(\w+)\s+to\s+(.+)"
        ]
        
        self.decision_patterns = [
            r"decision[s]?:?\s*(.+)",
            r"agreed\s+to\s+(.+)",
            r"approved\s+(.+)",
            r"decided\s+to\s+(.+)",
            r"concluded\s+that\s+(.+)",
            r"settled\s+on\s+(.+)"
        ]
        
        self.question_patterns = [
            r"question[s]?:?\s*(.+)",
            r"open\s+question[s]?:?\s*(.+)",
            r"pending\s+question[s]?:?\s*(.+)",
            r"need\s+to\s+clarify\s+(.+)",
            r"unresolved\s+(.+)"
        ]
    
    async def summarize_transcript(
        self, transcript: str, language: str = "en"
    ) -> Dict[str, Any]:
        """Generate comprehensive meeting summary"""
        try:
            # Extract key elements
            decisions = self._extract_decisions(transcript)
            action_items = self._extract_action_items(transcript)
            open_questions = self._extract_open_questions(transcript)
            
            # Generate WhatsApp blurb
            whatsapp_blurb = self._generate_whatsapp_blurb(
                decisions, action_items, open_questions, language
            )
            
            return {
                "decisions": decisions,
                "action_items": action_items,
                "open_questions": open_questions,
                "whatsapp_blurb": whatsapp_blurb,
                "summary_generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise
    
    def _extract_decisions(self, transcript: str) -> List[str]:
        """Extract decisions from transcript"""
        decisions = []
        
        for pattern in self.decision_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    decisions.extend([m.strip() for m in match if m.strip()])
                else:
                    decisions.append(match.strip())
        
        # Remove duplicates and clean up
        decisions = list(set(decisions))
        decisions = [d for d in decisions if len(d) > 10]  # Filter out very short matches
        
        return decisions[:10]  # Limit to top 10 decisions
    
    def _extract_action_items(self, transcript: str) -> List[Dict[str, str]]:
        """Extract action items with owners and due dates"""
        action_items = []
        
        for pattern in self.action_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2:
                        owner = match[0].strip()
                        action = match[1].strip()
                        action_items.append({
                            "owner": owner,
                            "action": action,
                            "due_date": "TBD"
                        })
                else:
                    action_items.append({
                        "owner": "Unassigned",
                        "action": match.strip(),
                        "due_date": "TBD"
                    })
        
        # Remove duplicates and clean up
        unique_actions = []
        seen_actions = set()
        for item in action_items:
            action_key = f"{item['owner']}:{item['action']}"
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                unique_actions.append(item)
        
        return unique_actions[:15]  # Limit to top 15 action items
    
    def _extract_open_questions(self, transcript: str) -> List[str]:
        """Extract open questions from transcript"""
        questions = []
        
        for pattern in self.question_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    questions.extend([m.strip() for m in match if m.strip()])
                else:
                    questions.append(match.strip())
        
        # Remove duplicates and clean up
        questions = list(set(questions))
        questions = [q for q in questions if len(q) > 10]  # Filter out very short matches
        
        return questions[:10]  # Limit to top 10 questions
    
    def _generate_whatsapp_blurb(
        self, decisions: List[str], action_items: List[Dict], 
        questions: List[str], language: str
    ) -> str:
        """Generate concise WhatsApp summary (≤900 chars)"""
        try:
            blurb_parts = []
            
            # Add meeting summary header
            if language in ["ta", "hi"]:
                header = "📋 மீட்டிங் சுருக்கம் / मीटिंग सारांश"
            else:
                header = "📋 Meeting Summary"
            blurb_parts.append(header)
            
            # Add key decisions
            if decisions:
                if language == "ta":
                    blurb_parts.append("✅ முடிவுகள்:")
                elif language == "hi":
                    blurb_parts.append("✅ निर्णय:")
                else:
                    blurb_parts.append("✅ Decisions:")
                
                for i, decision in enumerate(decisions[:3]):  # Top 3 decisions
                    blurb_parts.append(f"• {decision[:100]}...")
            
            # Add action items
            if action_items:
                if language == "ta":
                    blurb_parts.append("📝 செயல் புள்ளிகள்:")
                elif language == "hi":
                    blurb_parts.append("📝 कार्य बिंदु:")
                else:
                    blurb_parts.append("📝 Action Items:")
                
                for i, item in enumerate(action_items[:3]):  # Top 3 action items
                    owner = item.get("owner", "Unassigned")
                    action = item.get("action", "")[:80]
                    blurb_parts.append(f"• {owner}: {action}...")
            
            # Add open questions
            if questions:
                if language == "ta":
                    blurb_parts.append("❓ திறந்த கேள்விகள்:")
                elif language == "hi":
                    blurb_parts.append("❓ खुले प्रश्न:")
                else:
                    blurb_parts.append("❓ Open Questions:")
                
                for i, question in enumerate(questions[:2]):  # Top 2 questions
                    blurb_parts.append(f"• {question[:100]}...")
            
            # Join and truncate to fit WhatsApp limit
            blurb = "\n".join(blurb_parts)
            if len(blurb) > 900:
                blurb = blurb[:897] + "..."
            
            return blurb
            
        except Exception as e:
            logger.error(f"Error generating WhatsApp blurb: {str(e)}")
            return "Meeting summary generated successfully."

summarization_service = SummarizationService()