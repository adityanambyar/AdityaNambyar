import React, { useState } from 'react'
import { FileAudio, Upload, FileText, Download, Trash2, Clock, Users } from 'lucide-react'
import FileUpload from './components/FileUpload'
import MeetingDetails from './components/MeetingDetails'
import MeetingList from './components/MeetingList'

interface Meeting {
  meeting_id: string
  title: string
  upload_time: string
  auto_delete_time: string
  has_transcript: boolean
  has_summary: boolean
}

function App() {
  const [currentView, setCurrentView] = useState<'upload' | 'meetings' | 'meeting-detail'>('upload')
  const [selectedMeeting, setSelectedMeeting] = useState<string | null>(null)
  const [meetings, setMeetings] = useState<Meeting[]>([])

  const handleUploadSuccess = (meetingId: string) => {
    setSelectedMeeting(meetingId)
    setCurrentView('meeting-detail')
  }

  const handleMeetingSelect = (meetingId: string) => {
    setSelectedMeeting(meetingId)
    setCurrentView('meeting-detail')
  }

  const handleBackToList = () => {
    setCurrentView('meetings')
    setSelectedMeeting(null)
  }

  const handleBackToUpload = () => {
    setCurrentView('upload')
    setSelectedMeeting(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <FileAudio className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">MeetNotes India</h1>
                <p className="text-sm text-gray-600">AI-powered meeting transcription and summarization</p>
              </div>
            </div>
            
            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentView('upload')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'upload'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Upload className="h-4 w-4 inline mr-2" />
                Upload
              </button>
              <button
                onClick={() => setCurrentView('meetings')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'meetings'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <FileText className="h-4 w-4 inline mr-2" />
                Meetings
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'upload' && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Upload Meeting Recording
              </h2>
              <p className="text-lg text-gray-600">
                Upload your audio file (MP3, M4A, WAV) and get AI-powered transcription 
                and summary with Indian language support
              </p>
            </div>
            
            <FileUpload onUploadSuccess={handleUploadSuccess} />
            
            {/* Features */}
            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-6 bg-white rounded-xl shadow-sm">
                <div className="bg-primary-100 p-3 rounded-full w-12 h-12 mx-auto mb-4">
                  <FileAudio className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Smart Transcription</h3>
                <p className="text-sm text-gray-600">
                  Whisper-powered transcription with Tamil and Hindi language preservation
                </p>
              </div>
              
              <div className="text-center p-6 bg-white rounded-xl shadow-sm">
                <div className="bg-success-100 p-3 rounded-full w-12 h-12 mx-auto mb-4">
                  <Users className="h-6 w-6 text-success-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">AI Summarization</h3>
                <p className="text-sm text-gray-600">
                  Automatic extraction of decisions, action items, and key points
                </p>
              </div>
              
              <div className="text-center p-6 bg-white rounded-xl shadow-sm">
                <div className="bg-warning-100 p-3 rounded-full w-12 h-12 mx-auto mb-4">
                  <Clock className="h-6 w-6 text-warning-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Privacy First</h3>
                <p className="text-sm text-gray-600">
                  Automatic deletion after 24 hours with manual delete option
                </p>
              </div>
            </div>
          </div>
        )}

        {currentView === 'meetings' && (
          <div>
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900">Your Meetings</h2>
              <button
                onClick={handleBackToUpload}
                className="btn-primary"
              >
                <Upload className="h-4 w-4 inline mr-2" />
                Upload New Meeting
              </button>
            </div>
            <MeetingList 
              meetings={meetings}
              onMeetingSelect={handleMeetingSelect}
              onMeetingsUpdate={setMeetings}
            />
          </div>
        )}

        {currentView === 'meeting-detail' && selectedMeeting && (
          <div>
            <div className="mb-6">
              <button
                onClick={handleBackToList}
                className="btn-secondary"
              >
                ← Back to Meetings
              </button>
            </div>
            <MeetingDetails 
              meetingId={selectedMeeting}
              onBack={handleBackToList}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>&copy; 2024 MeetNotes India. Built for Indian businesses with ❤️</p>
            <p className="text-sm mt-2">
              Supports English, Hindi (हिन्दी), and Tamil (தமிழ்) languages
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
