import React, { useState, useEffect } from 'react'
import { 
  FileText, 
  Download, 
  Trash2, 
  Clock, 
  Users, 
  CheckCircle, 
  Loader2,
  AlertCircle,
  Play,
  MessageSquare,
  Target,
  HelpCircle
} from 'lucide-react'
import { getMeeting, transcribeMeeting, summarizeMeeting, deleteMeeting } from '../services/api'

interface MeetingDetailsProps {
  meetingId: string
  onBack: () => void
}

interface Meeting {
  meeting_id: string
  title: string
  upload_time: string
  auto_delete_time: string
  has_transcript: boolean
  has_summary: boolean
  transcript?: any
  summary?: any
}

const MeetingDetails: React.FC<MeetingDetailsProps> = ({ meetingId, onBack }) => {
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [loading, setLoading] = useState(true)
  const [transcribing, setTranscribing] = useState(false)
  const [summarizing, setSummarizing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'summary' | 'transcript'>('summary')

  useEffect(() => {
    loadMeeting()
  }, [meetingId])

  const loadMeeting = async () => {
    try {
      setLoading(true)
      const data = await getMeeting(meetingId)
      setMeeting(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load meeting')
    } finally {
      setLoading(false)
    }
  }

  const handleTranscribe = async () => {
    if (!meeting) return
    
    try {
      setTranscribing(true)
      setError(null)
      await transcribeMeeting(meetingId)
      
      // Poll for completion
      const pollForTranscript = async () => {
        const updatedMeeting = await getMeeting(meetingId)
        if (updatedMeeting.has_transcript) {
          setMeeting(updatedMeeting)
          setTranscribing(false)
        } else {
          setTimeout(pollForTranscript, 3000) // Check every 3 seconds
        }
      }
      
      setTimeout(pollForTranscript, 3000)
    } catch (err) {
      setTranscribing(false)
      setError(err instanceof Error ? err.message : 'Transcription failed')
    }
  }

  const handleSummarize = async () => {
    if (!meeting) return
    
    try {
      setSummarizing(true)
      setError(null)
      await summarizeMeeting(meetingId)
      
      // Poll for completion
      const pollForSummary = async () => {
        const updatedMeeting = await getMeeting(meetingId)
        if (updatedMeeting.has_summary) {
          setMeeting(updatedMeeting)
          setSummarizing(false)
        } else {
          setTimeout(pollForSummary, 3000) // Check every 3 seconds
        }
      }
      
      setTimeout(pollForSummary, 3000)
    } catch (err) {
      setSummarizing(false)
      setError(err instanceof Error ? err.message : 'Summarization failed')
    }
  }

  const handleDelete = async () => {
    if (!meeting || !confirm('Are you sure you want to delete this meeting? This action cannot be undone.')) {
      return
    }
    
    try {
      await deleteMeeting(meetingId)
      onBack()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete meeting')
    }
  }

  const handleDownloadPDF = () => {
    window.open(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/minutes/${meetingId}/pdf`, '_blank')
  }

  const formatDateTime = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'long',
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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
        <span className="ml-2 text-gray-600">Loading meeting details...</span>
      </div>
    )
  }

  if (!meeting) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-error-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Meeting Not Found</h3>
        <p className="text-gray-600 mb-4">The meeting you're looking for doesn't exist or has been deleted.</p>
        <button onClick={onBack} className="btn-primary">
          Back to Meetings
        </button>
      </div>
    )
  }

  const hoursLeft = getTimeUntilDeletion(meeting.auto_delete_time)

  return (
    <div className="space-y-6">
      {/* Meeting Header */}
      <div className="card">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">{meeting.title}</h1>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>📅 {formatDateTime(meeting.upload_time)}</span>
              <span className={`flex items-center ${hoursLeft <= 1 ? 'text-error-600' : 'text-warning-600'}`}>
                <Clock className="h-4 w-4 mr-1" />
                Auto-delete in {hoursLeft}h
              </span>
            </div>
          </div>
          
          <div className="flex space-x-2">
            {meeting.has_transcript && meeting.has_summary && (
              <button onClick={handleDownloadPDF} className="btn-secondary">
                <Download className="h-4 w-4 mr-2" />
                PDF
              </button>
            )}
            <button onClick={handleDelete} className="btn-danger">
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </button>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className={`p-4 rounded-lg border-2 ${
            meeting.has_transcript 
              ? 'border-success-200 bg-success-50' 
              : 'border-gray-200 bg-gray-50'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className={`h-5 w-5 ${meeting.has_transcript ? 'text-success-600' : 'text-gray-400'}`} />
                <span className="font-medium">Transcription</span>
              </div>
              {meeting.has_transcript ? (
                <CheckCircle className="h-5 w-5 text-success-600" />
              ) : transcribing ? (
                <Loader2 className="h-5 w-5 text-primary-600 animate-spin" />
              ) : (
                <button onClick={handleTranscribe} className="btn-primary text-sm py-1 px-3">
                  <Play className="h-3 w-3 mr-1" />
                  Start
                </button>
              )}
            </div>
          </div>

          <div className={`p-4 rounded-lg border-2 ${
            meeting.has_summary 
              ? 'border-success-200 bg-success-50' 
              : 'border-gray-200 bg-gray-50'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MessageSquare className={`h-5 w-5 ${meeting.has_summary ? 'text-success-600' : 'text-gray-400'}`} />
                <span className="font-medium">Summary</span>
              </div>
              {meeting.has_summary ? (
                <CheckCircle className="h-5 w-5 text-success-600" />
              ) : summarizing ? (
                <Loader2 className="h-5 w-5 text-primary-600 animate-spin" />
              ) : meeting.has_transcript ? (
                <button onClick={handleSummarize} className="btn-primary text-sm py-1 px-3">
                  <Play className="h-3 w-3 mr-1" />
                  Start
                </button>
              ) : (
                <span className="text-sm text-gray-500">Needs transcript</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-error-50 border border-error-200 rounded-lg flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-error-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-error-800">Error</h4>
            <p className="text-sm text-error-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Content Tabs */}
      {(meeting.has_transcript || meeting.has_summary) && (
        <div>
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {meeting.has_summary && (
                <button
                  onClick={() => setActiveTab('summary')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'summary'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  📊 Summary
                </button>
              )}
              {meeting.has_transcript && (
                <button
                  onClick={() => setActiveTab('transcript')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'transcript'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  📝 Transcript
                </button>
              )}
            </nav>
          </div>

          {/* Summary Tab */}
          {activeTab === 'summary' && meeting.summary && (
            <div className="space-y-6">
              {/* WhatsApp Blurb */}
              {meeting.summary.whatsapp_blurb && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    📱 WhatsApp Summary
                  </h3>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-green-800">{meeting.summary.whatsapp_blurb}</p>
                  </div>
                </div>
              )}

              {/* Key Decisions */}
              {meeting.summary.decisions && meeting.summary.decisions.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <Target className="h-5 w-5 mr-2 text-primary-600" />
                    Key Decisions
                  </h3>
                  <div className="space-y-4">
                    {meeting.summary.decisions.map((decision: any, index: number) => (
                      <div key={index} className="border-l-4 border-primary-500 pl-4">
                        <p className="font-medium text-gray-900">{decision.decision}</p>
                        {decision.context && (
                          <p className="text-sm text-gray-600 mt-1">{decision.context}</p>
                        )}
                        {decision.impact && (
                          <p className="text-sm text-primary-700 mt-1">Impact: {decision.impact}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Items */}
              {meeting.summary.action_items && meeting.summary.action_items.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <CheckCircle className="h-5 w-5 mr-2 text-success-600" />
                    Action Items
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Action</th>
                          <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Owner</th>
                          <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Due Date</th>
                          <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Priority</th>
                        </tr>
                      </thead>
                      <tbody>
                        {meeting.summary.action_items.map((item: any, index: number) => (
                          <tr key={index} className="border-b border-gray-100">
                            <td className="py-3 px-3 text-sm text-gray-900">{item.action}</td>
                            <td className="py-3 px-3 text-sm text-gray-700">{item.owner}</td>
                            <td className="py-3 px-3 text-sm text-gray-700">{item.due_date}</td>
                            <td className="py-3 px-3">
                              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                item.priority === 'high' 
                                  ? 'bg-error-100 text-error-800'
                                  : item.priority === 'medium'
                                  ? 'bg-warning-100 text-warning-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {item.priority}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Open Questions */}
              {meeting.summary.open_questions && meeting.summary.open_questions.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <HelpCircle className="h-5 w-5 mr-2 text-warning-600" />
                    Open Questions
                  </h3>
                  <div className="space-y-4">
                    {meeting.summary.open_questions.map((question: any, index: number) => (
                      <div key={index} className="border-l-4 border-warning-500 pl-4">
                        <p className="font-medium text-gray-900">{question.question}</p>
                        {question.context && (
                          <p className="text-sm text-gray-600 mt-1">{question.context}</p>
                        )}
                        {question.assigned_to && (
                          <p className="text-sm text-warning-700 mt-1">Assigned to: {question.assigned_to}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Additional Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {meeting.summary.key_topics && meeting.summary.key_topics.length > 0 && (
                  <div className="card">
                    <h4 className="font-semibold text-gray-900 mb-3">🏷️ Key Topics</h4>
                    <div className="flex flex-wrap gap-2">
                      {meeting.summary.key_topics.map((topic: string, index: number) => (
                        <span key={index} className="bg-primary-100 text-primary-800 px-3 py-1 rounded-full text-sm">
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {meeting.summary.participants && meeting.summary.participants.length > 0 && (
                  <div className="card">
                    <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                      <Users className="h-4 w-4 mr-2" />
                      Participants
                    </h4>
                    <div className="space-y-1">
                      {meeting.summary.participants.map((participant: string, index: number) => (
                        <div key={index} className="text-sm text-gray-700">• {participant}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Transcript Tab */}
          {activeTab === 'transcript' && meeting.transcript && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                📝 Full Transcript
              </h3>
              
              {meeting.transcript.india_enhanced && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                  <p className="text-sm text-blue-800">
                    ℹ️ This transcript preserves Tamil and Hindi text with English glosses in parentheses.
                  </p>
                </div>
              )}

              <div className="space-y-4 max-h-96 overflow-y-auto">
                {meeting.transcript.segments ? (
                  meeting.transcript.segments.map((segment: any, index: number) => (
                    <div key={index} className="border-b border-gray-100 pb-3">
                      <div className="text-xs text-gray-500 mb-1">
                        [{Math.floor(segment.start / 60)}:{(segment.start % 60).toFixed(0).padStart(2, '0')} - 
                         {Math.floor(segment.end / 60)}:{(segment.end % 60).toFixed(0).padStart(2, '0')}]
                      </div>
                      <p className="text-gray-900">{segment.text}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-900 whitespace-pre-wrap">{meeting.transcript.text}</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default MeetingDetails