import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Upload, 
  FileText, 
  Clock, 
  Download,
  Play,
  Trash2,
  Calendar,
  Users
} from 'lucide-react'
import { apiService, Meeting, Transcript, Summary } from '../services/api'
import { formatFileSize, formatDate } from '../lib/utils'

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalMeetings: 0,
    totalTranscripts: 0,
    totalSummaries: 0,
    totalPDFs: 0,
  })
  const [recentMeetings, setRecentMeetings] = useState<Meeting[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      // In a real app, you'd have a dedicated dashboard endpoint
      // For now, we'll simulate the data
      setStats({
        totalMeetings: 12,
        totalTranscripts: 10,
        totalSummaries: 8,
        totalPDFs: 6,
      })
      
      // Mock recent meetings data
      setRecentMeetings([
        {
          id: 1,
          filename: 'meeting_001.m4a',
          original_filename: 'Team Standup - 2024-01-15.m4a',
          file_size: 15728640, // 15MB
          mime_type: 'audio/mp4',
          uploaded_at: '2024-01-15T10:00:00Z',
          expires_at: '2024-01-16T10:00:00Z',
          is_deleted: false,
        },
        {
          id: 2,
          filename: 'meeting_002.m4a',
          original_filename: 'Product Review - 2024-01-14.m4a',
          file_size: 31457280, // 30MB
          mime_type: 'audio/mp4',
          uploaded_at: '2024-01-14T14:30:00Z',
          expires_at: '2024-01-15T14:30:00Z',
          is_deleted: false,
        },
      ])
    } catch (error) {
      console.error('Error loading dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (meeting: Meeting) => {
    const now = new Date()
    const expiresAt = new Date(meeting.expires_at)
    
    if (meeting.is_deleted) return 'text-red-500'
    if (expiresAt < now) return 'text-orange-500'
    if (expiresAt.getTime() - now.getTime() < 3600000) return 'text-yellow-500' // 1 hour
    return 'text-green-500'
  }

  const getStatusText = (meeting: Meeting) => {
    const now = new Date()
    const expiresAt = new Date(meeting.expires_at)
    
    if (meeting.is_deleted) return 'Deleted'
    if (expiresAt < now) return 'Expired'
    if (expiresAt.getTime() - now.getTime() < 3600000) return 'Expires Soon'
    return 'Active'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-india-saffron"></div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">Welcome to MeetNotes India - Your meeting transcription assistant</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-india-saffron bg-opacity-10">
              <Upload className="h-6 w-6 text-india-saffron" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Meetings</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalMeetings}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-india-green bg-opacity-10">
              <FileText className="h-6 w-6 text-india-green" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Transcripts</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalTranscripts}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-india-blue bg-opacity-10">
              <Users className="h-6 w-6 text-india-blue" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Summaries</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalSummaries}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-india-white bg-opacity-10">
              <Download className="h-6 w-6 text-india-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">PDFs Generated</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalPDFs}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/upload"
            className="flex items-center justify-center p-4 border-2 border-dashed border-india-saffron rounded-lg hover:bg-india-saffron hover:bg-opacity-5 transition-colors group"
          >
            <Upload className="h-6 w-6 text-india-saffron group-hover:scale-110 transition-transform" />
            <span className="ml-2 text-india-saffron font-medium">Upload Audio</span>
          </Link>
          
          <Link
            to="/minutes"
            className="flex items-center justify-center p-4 border-2 border-dashed border-india-green rounded-lg hover:bg-india-green hover:bg-opacity-5 transition-colors group"
          >
            <FileText className="h-6 w-6 text-india-green group-hover:scale-110 transition-transform" />
            <span className="ml-2 text-india-green font-medium">View Minutes</span>
          </Link>
          
          <Link
            to="/recent"
            className="flex items-center justify-center p-4 border-2 border-dashed border-india-blue rounded-lg hover:bg-india-blue hover:bg-opacity-5 transition-colors group"
          >
            <Clock className="h-6 w-6 text-india-blue group-hover:scale-110 transition-transform" />
            <span className="ml-2 text-india-blue font-medium">Recent Meetings</span>
          </Link>
        </div>
      </div>

      {/* Recent Meetings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Recent Meetings</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {recentMeetings.map((meeting) => (
            <div key={meeting.id} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3">
                    <Play className="h-5 w-5 text-gray-400" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {meeting.original_filename}
                      </p>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{formatFileSize(meeting.file_size)}</span>
                        <span>•</span>
                        <span>{formatDate(meeting.uploaded_at)}</span>
                        <span>•</span>
                        <span className={`font-medium ${getStatusColor(meeting)}`}>
                          {getStatusText(meeting)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Link
                    to={`/meeting/${meeting.id}`}
                    className="p-2 text-gray-400 hover:text-india-saffron transition-colors"
                    title="View Details"
                  >
                    <FileText className="h-4 w-4" />
                  </Link>
                  
                  <button
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                    title="Delete Now"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="px-6 py-4 border-t border-gray-200">
          <Link
            to="/recent"
            className="text-india-saffron hover:text-india-saffron-dark font-medium text-sm"
          >
            View all meetings →
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard