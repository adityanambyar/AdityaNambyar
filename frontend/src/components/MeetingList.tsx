import React, { useState, useEffect } from 'react'
import { 
  FileText, 
  Clock, 
  Download, 
  Trash2, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Search,
  Filter
} from 'lucide-react'
import { deleteMeeting } from '../services/api'

interface Meeting {
  meeting_id: string
  title: string
  upload_time: string
  auto_delete_time: string
  has_transcript: boolean
  has_summary: boolean
}

interface MeetingListProps {
  meetings: Meeting[]
  onMeetingSelect: (meetingId: string) => void
  onMeetingsUpdate: (meetings: Meeting[]) => void
}

const MeetingList: React.FC<MeetingListProps> = ({ 
  meetings, 
  onMeetingSelect, 
  onMeetingsUpdate 
}) => {
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'processed' | 'pending'>('all')
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    // In a real app, this would fetch meetings from the API
    // For now, we'll simulate loading
    const timer = setTimeout(() => {
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const handleDelete = async (meetingId: string, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent row click
    
    if (!confirm('Are you sure you want to delete this meeting? This action cannot be undone.')) {
      return
    }

    setDeletingIds(prev => new Set(prev).add(meetingId))
    
    try {
      await deleteMeeting(meetingId)
      const updatedMeetings = meetings.filter(m => m.meeting_id !== meetingId)
      onMeetingsUpdate(updatedMeetings)
    } catch (error) {
      console.error('Failed to delete meeting:', error)
      alert('Failed to delete meeting. Please try again.')
    } finally {
      setDeletingIds(prev => {
        const newSet = new Set(prev)
        newSet.delete(meetingId)
        return newSet
      })
    }
  }

  const formatDateTime = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Kolkata'
    })
  }

  const getTimeUntilDeletion = (deleteTime: string) => {
    const now = new Date()
    const deleteDate = new Date(deleteTime)
    const hoursLeft = Math.max(0, Math.floor((deleteDate.getTime() - now.getTime()) / (1000 * 60 * 60)))
    return hoursLeft
  }

  const getStatusColor = (meeting: Meeting) => {
    if (meeting.has_transcript && meeting.has_summary) {
      return 'text-success-600 bg-success-100'
    } else if (meeting.has_transcript || meeting.has_summary) {
      return 'text-warning-600 bg-warning-100'
    } else {
      return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusText = (meeting: Meeting) => {
    if (meeting.has_transcript && meeting.has_summary) {
      return 'Complete'
    } else if (meeting.has_transcript) {
      return 'Transcribed'
    } else if (meeting.has_summary) {
      return 'Summarized'
    } else {
      return 'Pending'
    }
  }

  const filteredMeetings = meetings.filter(meeting => {
    // Search filter
    const matchesSearch = meeting.title.toLowerCase().includes(searchTerm.toLowerCase())
    
    // Status filter
    let matchesStatus = true
    if (filterStatus === 'processed') {
      matchesStatus = meeting.has_transcript && meeting.has_summary
    } else if (filterStatus === 'pending') {
      matchesStatus = !meeting.has_transcript || !meeting.has_summary
    }
    
    return matchesSearch && matchesStatus
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
        <span className="ml-2 text-gray-600">Loading meetings...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search meetings..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 input-field"
          />
        </div>
        
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="pl-10 input-field"
          >
            <option value="all">All Status</option>
            <option value="processed">Fully Processed</option>
            <option value="pending">Pending Processing</option>
          </select>
        </div>
      </div>

      {filteredMeetings.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {meetings.length === 0 ? 'No meetings yet' : 'No meetings found'}
          </h3>
          <p className="text-gray-600">
            {meetings.length === 0 
              ? 'Upload your first meeting recording to get started.'
              : 'Try adjusting your search or filter criteria.'
            }
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Meeting</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Auto-Delete</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredMeetings.map((meeting) => {
                  const hoursLeft = getTimeUntilDeletion(meeting.auto_delete_time)
                  const isDeleting = deletingIds.has(meeting.meeting_id)
                  
                  return (
                    <tr
                      key={meeting.meeting_id}
                      onClick={() => onMeetingSelect(meeting.meeting_id)}
                      className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                        isDeleting ? 'opacity-50' : ''
                      }`}
                    >
                      <td className="py-4 px-4">
                        <div>
                          <h4 className="font-medium text-gray-900">{meeting.title}</h4>
                          <p className="text-sm text-gray-500">ID: {meeting.meeting_id}</p>
                        </div>
                      </td>
                      
                      <td className="py-4 px-4 text-sm text-gray-600">
                        {formatDateTime(meeting.upload_time)}
                      </td>
                      
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(meeting)}`}>
                            {getStatusText(meeting)}
                          </span>
                          <div className="flex space-x-1">
                            {meeting.has_transcript && (
                              <CheckCircle className="h-4 w-4 text-success-500" title="Transcribed" />
                            )}
                            {meeting.has_summary && (
                              <FileText className="h-4 w-4 text-primary-500" title="Summarized" />
                            )}
                          </div>
                        </div>
                      </td>
                      
                      <td className="py-4 px-4">
                        <div className={`flex items-center text-sm ${
                          hoursLeft <= 1 ? 'text-error-600' : hoursLeft <= 6 ? 'text-warning-600' : 'text-gray-600'
                        }`}>
                          <Clock className="h-4 w-4 mr-1" />
                          {hoursLeft}h left
                        </div>
                      </td>
                      
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-2">
                          {meeting.has_transcript && meeting.has_summary && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                window.open(
                                  `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/minutes/${meeting.meeting_id}/pdf`, 
                                  '_blank'
                                )
                              }}
                              className="p-1 text-gray-400 hover:text-primary-600 transition-colors"
                              title="Download PDF"
                            >
                              <Download className="h-4 w-4" />
                            </button>
                          )}
                          
                          <button
                            onClick={(e) => handleDelete(meeting.meeting_id, e)}
                            disabled={isDeleting}
                            className="p-1 text-gray-400 hover:text-error-600 transition-colors disabled:opacity-50"
                            title="Delete meeting"
                          >
                            {isDeleting ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Summary Stats */}
      {meetings.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{meetings.length}</div>
            <div className="text-sm text-gray-600">Total Meetings</div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-success-600">
              {meetings.filter(m => m.has_transcript && m.has_summary).length}
            </div>
            <div className="text-sm text-gray-600">Fully Processed</div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-warning-600">
              {meetings.filter(m => getTimeUntilDeletion(m.auto_delete_time) <= 6).length}
            </div>
            <div className="text-sm text-gray-600">Expiring Soon</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MeetingList