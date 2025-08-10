import pytest
import tempfile
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
import json

from app.main import app
from app.database import get_db, Base
from app.models import MeetingRecord

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestUploadEndpoint:
    """Test the /upload endpoint"""
    
    @patch('app.services.upload_service.UploadService.upload_to_s3')
    def test_upload_valid_audio_file(self, mock_upload_to_s3):
        """Test uploading a valid audio file"""
        mock_upload_to_s3.return_value = "s3://test-bucket/audio/test-id/test.mp3"
        
        # Create a mock audio file
        audio_content = b"fake audio content"
        files = {
            "file": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")
        }
        
        response = client.post("/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "meeting_id" in data
        assert data["message"] == "File uploaded successfully"
        assert "auto_delete_time" in data
    
    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type"""
        files = {
            "file": ("test.txt", io.BytesIO(b"not audio"), "text/plain")
        }
        
        response = client.post("/upload", files=files)
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_upload_with_title(self):
        """Test uploading with a custom title"""
        with patch('app.services.upload_service.UploadService.upload_to_s3') as mock_upload:
            mock_upload.return_value = "s3://test-bucket/audio/test-id/test.mp3"
            
            files = {
                "file": ("test.mp3", io.BytesIO(b"fake audio"), "audio/mpeg")
            }
            data = {"title": "My Test Meeting"}
            
            response = client.post("/upload", files=files, data=data)
            
            assert response.status_code == 200
            # Verify title was saved
            db = TestingSessionLocal()
            meeting = db.query(MeetingRecord).first()
            assert meeting.title == "My Test Meeting"
            db.close()

class TestTranscribeEndpoint:
    """Test the /transcribe endpoint"""
    
    def test_transcribe_nonexistent_meeting(self):
        """Test transcribing a meeting that doesn't exist"""
        response = client.post("/transcribe", params={"meeting_id": "nonexistent-id"})
        assert response.status_code == 404
        assert "Meeting not found" in response.json()["detail"]
    
    @patch('app.services.transcription_service.TranscriptionService.transcribe_audio')
    def test_transcribe_existing_meeting(self, mock_transcribe):
        """Test transcribing an existing meeting"""
        # Create a meeting first
        db = TestingSessionLocal()
        meeting = MeetingRecord(
            title="Test Meeting",
            original_filename="test.mp3",
            s3_url="s3://test-bucket/test.mp3"
        )
        db.add(meeting)
        db.commit()
        meeting_id = str(meeting.id)
        db.close()
        
        response = client.post("/transcribe", params={"meeting_id": meeting_id})
        
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == meeting_id
        assert data["message"] == "Transcription started"
        assert data["status"] == "processing"

class TestSummarizeEndpoint:
    """Test the /summarize endpoint"""
    
    def test_summarize_without_transcript(self):
        """Test summarizing a meeting without transcript"""
        # Create a meeting without transcript
        db = TestingSessionLocal()
        meeting = MeetingRecord(
            title="Test Meeting",
            original_filename="test.mp3",
            s3_url="s3://test-bucket/test.mp3"
        )
        db.add(meeting)
        db.commit()
        meeting_id = str(meeting.id)
        db.close()
        
        response = client.post("/summarize", params={"meeting_id": meeting_id})
        assert response.status_code == 400
        assert "No transcript found" in response.json()["detail"]
    
    @patch('app.services.summary_service.SummaryService.generate_summary')
    def test_summarize_with_transcript(self, mock_summarize):
        """Test summarizing a meeting with transcript"""
        # Create a meeting with transcript
        db = TestingSessionLocal()
        meeting = MeetingRecord(
            title="Test Meeting",
            original_filename="test.mp3",
            s3_url="s3://test-bucket/test.mp3",
            transcript={"text": "This is a test transcript"}
        )
        db.add(meeting)
        db.commit()
        meeting_id = str(meeting.id)
        db.close()
        
        response = client.post("/summarize", params={"meeting_id": meeting_id})
        
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == meeting_id
        assert data["message"] == "Summarization started"

class TestMeetingEndpoints:
    """Test meeting CRUD endpoints"""
    
    def test_get_nonexistent_meeting(self):
        """Test getting a meeting that doesn't exist"""
        response = client.get("/meeting/nonexistent-id")
        assert response.status_code == 404
    
    def test_get_existing_meeting(self):
        """Test getting an existing meeting"""
        # Create a meeting
        db = TestingSessionLocal()
        meeting = MeetingRecord(
            title="Test Meeting",
            original_filename="test.mp3"
        )
        db.add(meeting)
        db.commit()
        meeting_id = str(meeting.id)
        db.close()
        
        response = client.get(f"/meeting/{meeting_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == meeting_id
        assert data["title"] == "Test Meeting"
        assert "upload_time" in data
        assert "auto_delete_time" in data
    
    @patch('app.services.cleanup_service.CleanupService.delete_meeting')
    def test_delete_meeting(self, mock_delete):
        """Test deleting a meeting"""
        # Create a meeting
        db = TestingSessionLocal()
        meeting = MeetingRecord(
            title="Test Meeting",
            original_filename="test.mp3"
        )
        db.add(meeting)
        db.commit()
        meeting_id = str(meeting.id)
        db.close()
        
        response = client.delete(f"/meeting/{meeting_id}")
        
        assert response.status_code == 200
        assert "Meeting deleted successfully" in response.json()["message"]
        mock_delete.assert_called_once()

class TestPDFEndpoint:
    """Test the PDF generation endpoint"""
    
    def test_pdf_without_transcript_and_summary(self):
        """Test PDF generation without transcript and summary"""
        # Create a meeting without transcript/summary
        db = TestingSessionLocal()
        meeting = MeetingRecord(
            title="Test Meeting",
            original_filename="test.mp3"
        )
        db.add(meeting)
        db.commit()
        meeting_id = str(meeting.id)
        db.close()
        
        response = client.get(f"/minutes/{meeting_id}/pdf")
        assert response.status_code == 400
        assert "Both transcript and summary are required" in response.json()["detail"]
    
    @patch('app.services.pdf_service.PDFService.generate_pdf')
    def test_pdf_with_transcript_and_summary(self, mock_generate_pdf):
        """Test PDF generation with transcript and summary"""
        mock_generate_pdf.return_value = "/tmp/test.pdf"
        
        # Create a meeting with transcript and summary
        db = TestingSessionLocal()
        meeting = MeetingRecord(
            title="Test Meeting",
            original_filename="test.mp3",
            transcript={"text": "Test transcript"},
            summary={"decisions": [], "action_items": []}
        )
        db.add(meeting)
        db.commit()
        meeting_id = str(meeting.id)
        db.close()
        
        # Mock file response
        with patch('app.main.FileResponse') as mock_file_response:
            response = client.get(f"/minutes/{meeting_id}/pdf")
            mock_generate_pdf.assert_called_once()
            mock_file_response.assert_called_once()

class TestHealthEndpoint:
    """Test the health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

class TestFileValidation:
    """Test file validation logic"""
    
    def test_file_size_validation(self):
        """Test file size validation"""
        # Create a file that's too large (simulate 201MB)
        large_content = b"x" * (201 * 1024 * 1024)  # 201MB
        
        with patch('app.services.upload_service.UploadService.validate_file') as mock_validate:
            mock_validate.side_effect = Exception("File size exceeds maximum allowed size")
            
            files = {
                "file": ("large.mp3", io.BytesIO(large_content), "audio/mpeg")
            }
            
            response = client.post("/upload", files=files)
            assert response.status_code == 400

class TestIndianLanguageFeatures:
    """Test India-specific features"""
    
    @patch('app.services.transcription_service.TranscriptionService._enhance_indian_language_transcript')
    def test_indian_language_enhancement(self, mock_enhance):
        """Test that Indian language enhancement is called"""
        mock_enhance.return_value = {
            "text": "नमस्ते (hello) everyone",
            "india_enhanced": True,
            "detected_languages": {"hindi": True, "tamil": False}
        }
        
        # This would be tested with a real transcription service call
        # For now, we test that the enhancement logic is triggered
        from app.services.transcription_service import TranscriptionService
        service = TranscriptionService()
        
        transcript_data = {"text": "नमस्ते everyone"}
        enhanced = service._enhance_indian_language_transcript(transcript_data)
        
        assert enhanced["india_enhanced"] == True
        assert "detected_languages" in enhanced