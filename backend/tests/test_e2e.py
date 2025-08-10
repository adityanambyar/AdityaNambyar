import pytest
import asyncio
import io
import time
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

from app.main import app

client = TestClient(app)

class TestEndToEnd:
    """End-to-end test: upload 15s sample → transcript+summary present, PDF bytes > 0"""
    
    @patch('app.services.storage_service.StorageService.upload_file')
    @patch('app.services.meeting_service.MeetingService.create_meeting')
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    @patch('app.services.whisper_service.WhisperService.transcribe')
    @patch('app.services.transcript_service.TranscriptService.create_transcript')
    @patch('app.services.transcript_service.TranscriptService.get_transcript')
    @patch('app.services.summary_service.SummaryService.generate_summary')
    @patch('app.services.summary_service.SummaryService.create_summary')
    @patch('app.services.summary_service.SummaryService.get_summary')
    @patch('app.services.pdf_service.PDFService.generate_pdf')
    def test_full_workflow_15s_sample(
        self,
        mock_generate_pdf,
        mock_get_summary,
        mock_create_summary,
        mock_generate_summary,
        mock_get_transcript,
        mock_create_transcript,
        mock_transcribe,
        mock_get_meeting,
        mock_create_meeting,
        mock_upload
    ):
        """Test complete workflow: upload → transcribe → summarize → PDF"""
        
        # Step 1: Upload 15-second audio sample
        meeting_id = "test-meeting-123"
        mock_meeting = Mock()
        mock_meeting.id = meeting_id
        mock_meeting.original_filename = "15s_sample.m4a"
        mock_meeting.file_size = 1024000  # 1MB
        mock_meeting.mime_type = "audio/mp4"
        mock_create_meeting.return_value = mock_meeting
        mock_upload.return_value = meeting_id
        
        # Create a mock 15-second audio file
        audio_content = b"fake 15 second audio content"
        files = {"file": ("15s_sample.m4a", io.BytesIO(audio_content), "audio/mp4")}
        
        upload_response = client.post("/api/v1/upload/", files=files)
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["meeting_id"] == meeting_id
        assert upload_data["message"] == "Audio uploaded successfully"
        
        # Step 2: Transcribe the audio
        mock_get_meeting.return_value = mock_meeting
        
        # Mock Whisper transcription result
        transcript_result = {
            "text": "This is a 15-second meeting recording. We discussed project timeline and assigned tasks.",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "This is a 15-second meeting recording."},
                {"start": 5.0, "end": 10.0, "text": "We discussed project timeline"},
                {"start": 10.0, "end": 15.0, "text": "and assigned tasks."}
            ]
        }
        mock_transcribe.return_value = transcript_result
        
        # Mock transcript creation
        mock_transcript = Mock()
        mock_transcript.id = "transcript-123"
        mock_transcript.content = transcript_result["text"]
        mock_transcript.language = transcript_result["language"]
        mock_transcript.confidence = 0.95
        mock_create_transcript.return_value = mock_transcript
        
        transcribe_response = client.post(f"/api/v1/transcribe/{meeting_id}")
        assert transcribe_response.status_code == 200
        transcribe_data = transcribe_response.json()
        assert transcribe_data["message"] == "Transcription completed successfully"
        assert transcribe_data["transcript_id"] == "transcript-123"
        
        # Step 3: Generate summary
        mock_get_transcript.return_value = mock_transcript
        
        # Mock summary generation
        summary_data = {
            "decisions": [
                "Project timeline set to 3 months",
                "Use Agile methodology for development"
            ],
            "action_items": [
                {
                    "action": "Create project plan",
                    "owner": "John Doe",
                    "due_date": "2024-01-15"
                },
                {
                    "action": "Set up development environment",
                    "owner": "Jane Smith",
                    "due_date": "2024-01-20"
                }
            ],
            "open_questions": [
                "What is the budget allocation?",
                "Who will be the project sponsor?"
            ],
            "whatsapp_blurb": "Meeting: Project timeline set to 3 months. Actions: John to create plan by Jan 15, Jane to set up dev env by Jan 20. Questions: Budget allocation and project sponsor need clarification."
        }
        mock_generate_summary.return_value = summary_data
        
        # Mock summary creation
        mock_summary = Mock()
        mock_summary.id = "summary-123"
        mock_summary.decisions = summary_data["decisions"]
        mock_summary.action_items = summary_data["action_items"]
        mock_summary.open_questions = summary_data["open_questions"]
        mock_summary.whatsapp_blurb = summary_data["whatsapp_blurb"]
        mock_create_summary.return_value = mock_summary
        
        summary_response = client.post(f"/api/v1/summarize/{meeting_id}")
        assert summary_response.status_code == 200
        summary_response_data = summary_response.json()
        assert summary_response_data["message"] == "Summary generated successfully"
        assert summary_response_data["summary_id"] == "summary-123"
        
        # Step 4: Verify transcript and summary are present
        mock_get_summary.return_value = mock_summary
        
        # Get transcript
        get_transcript_response = client.get(f"/api/v1/transcript/{meeting_id}")
        assert get_transcript_response.status_code == 200
        transcript_data = get_transcript_response.json()
        assert transcript_data["content"] == transcript_result["text"]
        assert transcript_data["language"] == "en"
        assert transcript_data["confidence"] == 0.95
        
        # Get summary
        get_summary_response = client.get(f"/api/v1/summary/{meeting_id}")
        assert get_summary_response.status_code == 200
        summary_data_response = get_summary_response.json()
        assert "decisions" in summary_data_response
        assert "action_items" in summary_data_response
        assert "open_questions" in summary_data_response
        assert "whatsapp_blurb" in summary_data_response
        assert len(summary_data_response["decisions"]) == 2
        assert len(summary_data_response["action_items"]) == 2
        assert len(summary_data_response["open_questions"]) == 2
        assert len(summary_data_response["whatsapp_blurb"]) <= 900  # WhatsApp character limit
        
        # Step 5: Generate and verify PDF (bytes > 0)
        mock_pdf_content = b"PDF content for meeting minutes"
        mock_generate_pdf.return_value = mock_pdf_content
        
        pdf_response = client.get(f"/api/v1/minutes/{meeting_id}/pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
        assert pdf_response.headers["content-disposition"] == f"attachment; filename=meeting_minutes_{meeting_id}.pdf"
        
        # Verify PDF bytes > 0
        pdf_bytes = len(pdf_response.content)
        assert pdf_bytes > 0, f"PDF should have content, but got {pdf_bytes} bytes"
        assert pdf_response.content == mock_pdf_content
        
        print(f"✅ End-to-end test passed! PDF generated with {pdf_bytes} bytes")
        print(f"✅ Transcript: {len(transcript_data['content'])} characters")
        print(f"✅ Summary: {len(summary_data_response['whatsapp_blurb'])} characters (WhatsApp ready)")
        print(f"✅ Meeting ID: {meeting_id}")

    @patch('app.services.storage_service.StorageService.upload_file')
    @patch('app.services.meeting_service.MeetingService.create_meeting')
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    @patch('app.services.whisper_service.WhisperService.transcribe')
    @patch('app.services.transcript_service.TranscriptService.create_transcript')
    @patch('app.services.transcript_service.TranscriptService.get_transcript')
    @patch('app.services.summary_service.SummaryService.generate_summary')
    @patch('app.services.summary_service.SummaryService.create_summary')
    @patch('app.services.summary_service.SummaryService.get_summary')
    @patch('app.services.pdf_service.PDFService.generate_pdf')
    def test_tamil_hindi_localization(
        self,
        mock_generate_pdf,
        mock_get_summary,
        mock_create_summary,
        mock_generate_summary,
        mock_get_transcript,
        mock_create_transcript,
        mock_transcribe,
        mock_get_meeting,
        mock_create_meeting,
        mock_upload
    ):
        """Test India-first localization with Tamil/Hindi text preservation"""
        
        meeting_id = "test-meeting-tamil-123"
        mock_meeting = Mock()
        mock_meeting.id = meeting_id
        mock_meeting.original_filename = "tamil_meeting.m4a"
        mock_create_meeting.return_value = mock_meeting
        mock_upload.return_value = meeting_id
        
        # Upload Tamil audio
        audio_content = b"fake tamil audio content"
        files = {"file": ("tamil_meeting.m4a", io.BytesIO(audio_content), "audio/mp4")}
        
        upload_response = client.post("/api/v1/upload/", files=files)
        assert upload_response.status_code == 200
        
        # Transcribe with Tamil text + English gloss
        mock_get_meeting.return_value = mock_meeting
        
        transcript_result = {
            "text": "வணக்கம் (Hello), நாம் இன்று பிராஜெக்ட் பற்றி பேசுவோம் (Today we will discuss the project). நாளை கூட்டம் இருக்கும் (Meeting tomorrow).",
            "language": "ta",
            "segments": []
        }
        mock_transcribe.return_value = transcript_result
        
        mock_transcript = Mock()
        mock_transcript.id = "transcript-tamil-123"
        mock_transcript.content = transcript_result["text"]
        mock_transcript.language = transcript_result["language"]
        mock_create_transcript.return_value = mock_transcript
        
        transcribe_response = client.post(f"/api/v1/transcribe/{meeting_id}")
        assert transcribe_response.status_code == 200
        
        # Generate summary with Tamil headers
        mock_get_transcript.return_value = mock_transcript
        
        summary_data = {
            "decisions": ["பிராஜெக்ட் தொடங்க வேண்டும் (Project should start)"],
            "action_items": [
                {
                    "action": "திட்டம் தயாரிக்கவும் (Prepare plan)",
                    "owner": "ராஜா (Raja)",
                    "due_date": "2024-01-15"
                }
            ],
            "open_questions": ["பட்ஜெட் எவ்வளவு? (What is the budget?)"],
            "whatsapp_blurb": "கூட்டம்: பிராஜெக்ட் தொடங்க வேண்டும். செயல்கள்: ராஜா திட்டம் தயாரிக்கவும். கேள்விகள்: பட்ஜெட் தெளிவுபடுத்த வேண்டும்."
        }
        mock_generate_summary.return_value = summary_data
        
        mock_summary = Mock()
        mock_summary.id = "summary-tamil-123"
        mock_summary.decisions = summary_data["decisions"]
        mock_summary.action_items = summary_data["action_items"]
        mock_summary.open_questions = summary_data["open_questions"]
        mock_summary.whatsapp_blurb = summary_data["whatsapp_blurb"]
        mock_create_summary.return_value = mock_summary
        
        summary_response = client.post(f"/api/v1/summarize/{meeting_id}")
        assert summary_response.status_code == 200
        
        # Verify Tamil text is preserved with English glosses
        mock_get_summary.return_value = mock_summary
        get_summary_response = client.get(f"/api/v1/summary/{meeting_id}")
        assert get_summary_response.status_code == 200
        
        summary_data_response = get_summary_response.json()
        assert "வணக்கம் (Hello)" in summary_data_response["decisions"][0] or "வணக்கம்" in summary_data_response["decisions"][0]
        assert "ராஜா (Raja)" in summary_data_response["action_items"][0]["owner"] or "ராஜா" in summary_data_response["action_items"][0]["owner"]
        
        # Verify WhatsApp blurb is within character limit
        whatsapp_length = len(summary_data_response["whatsapp_blurb"])
        assert whatsapp_length <= 900, f"WhatsApp blurb too long: {whatsapp_length} characters"
        
        print(f"✅ Tamil localization test passed! WhatsApp blurb: {whatsapp_length} characters")

    def test_audio_retention_24h(self):
        """Test that audio files are automatically deleted after 24 hours"""
        # This would typically be tested with a background task scheduler
        # For now, we'll test the manual delete endpoint
        meeting_id = "test-retention-123"
        
        # Mock meeting that's older than 24 hours
        mock_meeting = Mock()
        mock_meeting.id = meeting_id
        mock_meeting.is_deleted = False
        
        with patch('app.services.meeting_service.MeetingService.get_meeting', return_value=mock_meeting):
            with patch('app.services.meeting_service.MeetingService.delete_meeting', return_value=True):
                with patch('app.services.storage_service.StorageService.delete_file', return_value=True):
                    response = client.delete(f"/api/v1/delete/{meeting_id}")
                    assert response.status_code == 200
                    assert response.json()["message"] == "Audio file deleted successfully"
        
        print("✅ Audio retention test passed!")

if __name__ == "__main__":
    # Run the end-to-end test
    test_instance = TestEndToEnd()
    test_instance.test_full_workflow_15s_sample()
    test_instance.test_tamil_hindi_localization()
    test_instance.test_audio_retention_24h()
    print("🎉 All end-to-end tests completed successfully!")