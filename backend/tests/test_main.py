import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import io
import json
from datetime import datetime, timedelta

from app.main import app
from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.models.summary import Summary

client = TestClient(app)

@pytest.fixture
def mock_meeting():
    return Meeting(
        id="test-meeting-123",
        original_filename="test_audio.m4a",
        file_size=1024000,
        mime_type="audio/mp4",
        uploaded_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        is_deleted=False
    )

@pytest.fixture
def mock_transcript():
    return Transcript(
        meeting_id="test-meeting-123",
        content="This is a test transcript in English.",
        language="en",
        confidence=0.95,
        segments=[],
        created_at=datetime.utcnow()
    )

@pytest.fixture
def mock_summary():
    return Summary(
        meeting_id="test-meeting-123",
        decisions=["Decision 1", "Decision 2"],
        action_items=[
            {"action": "Action 1", "owner": "John", "due_date": "2024-01-15"},
            {"action": "Action 2", "owner": "Jane", "due_date": "2024-01-20"}
        ],
        open_questions=["Question 1", "Question 2"],
        whatsapp_blurb="Meeting summary: Decisions made, actions assigned.",
        created_at=datetime.utcnow()
    )

class TestHealthEndpoint:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "timestamp": response.json()["timestamp"]}

class TestUploadEndpoint:
    @patch('app.services.storage_service.StorageService.upload_file')
    @patch('app.services.meeting_service.MeetingService.create_meeting')
    def test_upload_audio_success(self, mock_create_meeting, mock_upload):
        """Test successful audio upload"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_create_meeting.return_value = mock_meeting
        mock_upload.return_value = "test-123"

        # Create a mock audio file
        audio_content = b"fake audio content"
        files = {"file": ("test_audio.m4a", io.BytesIO(audio_content), "audio/mp4")}
        
        response = client.post("/api/v1/upload/", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == "test-123"
        assert data["message"] == "Audio uploaded successfully"

    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        files = {"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")}
        response = client.post("/api/v1/upload/", files=files)
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_file_too_large(self):
        """Test upload with file too large"""
        # Create a file larger than 200MB
        large_content = b"x" * (201 * 1024 * 1024)  # 201MB
        files = {"file": ("large_audio.m4a", io.BytesIO(large_content), "audio/mp4")}
        
        response = client.post("/api/v1/upload/", files=files)
        
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]

    def test_upload_no_file(self):
        """Test upload without file"""
        response = client.post("/api/v1/upload/")
        
        assert response.status_code == 422

class TestTranscribeEndpoint:
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    @patch('app.services.whisper_service.WhisperService.transcribe')
    @patch('app.services.transcript_service.TranscriptService.create_transcript')
    def test_transcribe_success(self, mock_create_transcript, mock_transcribe, mock_get_meeting):
        """Test successful transcription"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_meeting.is_deleted = False
        mock_get_meeting.return_value = mock_meeting
        
        mock_transcript_result = {
            "text": "This is a test transcript",
            "language": "en",
            "segments": []
        }
        mock_transcribe.return_value = mock_transcript_result
        
        mock_transcript = Mock()
        mock_transcript.id = "transcript-123"
        mock_create_transcript.return_value = mock_transcript

        response = client.post("/api/v1/transcribe/test-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Transcription completed successfully"
        assert data["transcript_id"] == "transcript-123"

    def test_transcribe_meeting_not_found(self):
        """Test transcription for non-existent meeting"""
        response = client.post("/api/v1/transcribe/nonexistent")
        
        assert response.status_code == 404
        assert "Meeting not found" in response.json()["detail"]

    @patch('app.services.meeting_service.MeetingService.get_meeting')
    def test_transcribe_deleted_meeting(self, mock_get_meeting):
        """Test transcription for deleted meeting"""
        mock_meeting = Mock()
        mock_meeting.is_deleted = True
        mock_get_meeting.return_value = mock_meeting
        
        response = client.post("/api/v1/transcribe/test-123")
        
        assert response.status_code == 400
        assert "Meeting has been deleted" in response.json()["detail"]

class TestSummaryEndpoint:
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    @patch('app.services.transcript_service.TranscriptService.get_transcript')
    @patch('app.services.summary_service.SummaryService.generate_summary')
    @patch('app.services.summary_service.SummaryService.create_summary')
    def test_generate_summary_success(self, mock_create_summary, mock_generate, mock_get_transcript, mock_get_meeting):
        """Test successful summary generation"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_meeting.is_deleted = False
        mock_get_meeting.return_value = mock_meeting
        
        mock_transcript = Mock()
        mock_transcript.content = "Test transcript content"
        mock_get_transcript.return_value = mock_transcript
        
        mock_summary_data = {
            "decisions": ["Decision 1"],
            "action_items": [{"action": "Action 1", "owner": "John", "due_date": "2024-01-15"}],
            "open_questions": ["Question 1"],
            "whatsapp_blurb": "Meeting summary"
        }
        mock_generate.return_value = mock_summary_data
        
        mock_summary = Mock()
        mock_summary.id = "summary-123"
        mock_create_summary.return_value = mock_summary

        response = client.post("/api/v1/summarize/test-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Summary generated successfully"
        assert data["summary_id"] == "summary-123"

    def test_generate_summary_no_transcript(self):
        """Test summary generation without transcript"""
        response = client.post("/api/v1/summarize/test-123")
        
        assert response.status_code == 400
        assert "No transcript available" in response.json()["detail"]

class TestGetTranscriptEndpoint:
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    @patch('app.services.transcript_service.TranscriptService.get_transcript')
    def test_get_transcript_success(self, mock_get_transcript, mock_get_meeting):
        """Test successful transcript retrieval"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_get_meeting.return_value = mock_meeting
        
        mock_transcript = Mock()
        mock_transcript.content = "Test transcript content"
        mock_transcript.language = "en"
        mock_transcript.confidence = 0.95
        mock_get_transcript.return_value = mock_transcript

        response = client.get("/api/v1/transcript/test-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test transcript content"
        assert data["language"] == "en"
        assert data["confidence"] == 0.95

    def test_get_transcript_meeting_not_found(self):
        """Test transcript retrieval for non-existent meeting"""
        response = client.get("/api/v1/transcript/nonexistent")
        
        assert response.status_code == 404
        assert "Meeting not found" in response.json()["detail"]

class TestGetSummaryEndpoint:
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    @patch('app.services.summary_service.SummaryService.get_summary')
    def test_get_summary_success(self, mock_get_summary, mock_get_meeting):
        """Test successful summary retrieval"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_get_meeting.return_value = mock_meeting
        
        mock_summary = Mock()
        mock_summary.decisions = ["Decision 1"]
        mock_summary.action_items = [{"action": "Action 1", "owner": "John", "due_date": "2024-01-15"}]
        mock_summary.open_questions = ["Question 1"]
        mock_summary.whatsapp_blurb = "Meeting summary"
        mock_get_summary.return_value = mock_summary

        response = client.get("/api/v1/summary/test-123")
        
        assert response.status_code == 200
        data = response.json()
        assert "decisions" in data
        assert "action_items" in data
        assert "open_questions" in data
        assert "whatsapp_blurb" in data

    def test_get_summary_meeting_not_found(self):
        """Test summary retrieval for non-existent meeting"""
        response = client.get("/api/v1/summary/nonexistent")
        
        assert response.status_code == 404
        assert "Meeting not found" in response.json()["detail"]

class TestDownloadPDFEndpoint:
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    @patch('app.services.transcript_service.TranscriptService.get_transcript')
    @patch('app.services.summary_service.SummaryService.get_summary')
    @patch('app.services.pdf_service.PDFService.generate_pdf')
    def test_download_pdf_success(self, mock_generate_pdf, mock_get_summary, mock_get_transcript, mock_get_meeting):
        """Test successful PDF download"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_meeting.original_filename = "test_audio.m4a"
        mock_meeting.uploaded_at = datetime.utcnow()
        mock_get_meeting.return_value = mock_meeting
        
        mock_transcript = Mock()
        mock_transcript.content = "Test transcript content"
        mock_get_transcript.return_value = mock_transcript
        
        mock_summary = Mock()
        mock_summary.decisions = ["Decision 1"]
        mock_summary.action_items = [{"action": "Action 1", "owner": "John", "due_date": "2024-01-15"}]
        mock_summary.open_questions = ["Question 1"]
        mock_get_summary.return_value = mock_summary
        
        mock_pdf_content = b"PDF content"
        mock_generate_pdf.return_value = mock_pdf_content

        response = client.get("/api/v1/minutes/test-123/pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"] == "attachment; filename=meeting_minutes_test-123.pdf"
        assert len(response.content) > 0

    def test_download_pdf_meeting_not_found(self):
        """Test PDF download for non-existent meeting"""
        response = client.get("/api/v1/minutes/nonexistent/pdf")
        
        assert response.status_code == 404
        assert "Meeting not found" in response.json()["detail"]

class TestDeleteAudioEndpoint:
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    @patch('app.services.meeting_service.MeetingService.delete_meeting')
    @patch('app.services.storage_service.StorageService.delete_file')
    def test_delete_audio_success(self, mock_delete_storage, mock_delete_meeting, mock_get_meeting):
        """Test successful audio deletion"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_meeting.is_deleted = False
        mock_get_meeting.return_value = mock_meeting
        
        mock_delete_meeting.return_value = True
        mock_delete_storage.return_value = True

        response = client.delete("/api/v1/delete/test-123")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Audio file deleted successfully"

    def test_delete_audio_meeting_not_found(self):
        """Test audio deletion for non-existent meeting"""
        response = client.delete("/api/v1/delete/nonexistent")
        
        assert response.status_code == 404
        assert "Meeting not found" in response.json()["detail"]

    @patch('app.services.meeting_service.MeetingService.get_meeting')
    def test_delete_audio_already_deleted(self, mock_get_meeting):
        """Test audio deletion for already deleted meeting"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_meeting.is_deleted = True
        mock_get_meeting.return_value = mock_meeting
        
        response = client.delete("/api/v1/delete/test-123")
        
        assert response.status_code == 400
        assert "Meeting has already been deleted" in response.json()["detail"]

class TestGetMeetingsEndpoint:
    @patch('app.services.meeting_service.MeetingService.get_meetings')
    def test_get_meetings_success(self, mock_get_meetings):
        """Test successful meetings retrieval"""
        mock_meetings = [
            Mock(id="meeting-1", original_filename="audio1.m4a", uploaded_at=datetime.utcnow()),
            Mock(id="meeting-2", original_filename="audio2.m4a", uploaded_at=datetime.utcnow())
        ]
        mock_get_meetings.return_value = mock_meetings

        response = client.get("/api/v1/meetings/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch('app.services.meeting_service.MeetingService.get_meetings')
    def test_get_meetings_empty(self, mock_get_meetings):
        """Test meetings retrieval when no meetings exist"""
        mock_get_meetings.return_value = []

        response = client.get("/api/v1/meetings/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

class TestGetMeetingEndpoint:
    @patch('app.services.meeting_service.MeetingService.get_meeting')
    def test_get_meeting_success(self, mock_get_meeting):
        """Test successful meeting retrieval"""
        mock_meeting = Mock()
        mock_meeting.id = "test-123"
        mock_meeting.original_filename = "test_audio.m4a"
        mock_meeting.uploaded_at = datetime.utcnow()
        mock_meeting.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_get_meeting.return_value = mock_meeting

        response = client.get("/api/v1/meetings/test-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-123"
        assert data["original_filename"] == "test_audio.m4a"

    def test_get_meeting_not_found(self):
        """Test meeting retrieval for non-existent meeting"""
        response = client.get("/api/v1/meetings/nonexistent")
        
        assert response.status_code == 404
        assert "Meeting not found" in response.json()["detail"]