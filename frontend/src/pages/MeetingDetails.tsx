import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Play, 
  FileText, 
  Download, 
  Trash2, 
  Clock, 
  FileAudio,
  CheckCircle,
  AlertCircle,
  Users,
  Calendar,
  MessageSquare,
  Copy,
  Share2
} from 'lucide-react'
import { toast } from 'react-hot-toast'
import { apiService, Meeting, Transcript, Summary } from '../services/api'
import { formatFileSize, formatDate, getLanguageName } from '../lib/utils'

const MeetingDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [transcript, setTranscript] = useState<Transcript | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'transcript' | 'summary' | 'whatsapp'>('overview')

  useEffect(() => {
    if (id) {
      loadMeetingData(parseInt(id))
    }
  }, [id])

  const loadMeetingData = async (meetingId: number) => {
    try {
      setLoading(true)
      
      // Load meeting details (mock data for now)
      const mockMeeting: Meeting = {
        id: meetingId,
        filename: `meeting_${meetingId.toString().padStart(3, '0')}.m4a`,
        original_filename: `Team Meeting - ${new Date().toLocaleDateString()}.m4a`,
        file_size: 31457280, // 30MB
        mime_type: 'audio/mp4',
        uploaded_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        is_deleted: false,
      }
      setMeeting(mockMeeting)

      // Try to load existing transcript and summary
      try {
        const existingTranscript = await apiService.getTranscript(meetingId)
        setTranscript(existingTranscript)
      } catch (error) {
        console.log('No existing transcript found')
      }

      try {
        const existingSummary = await apiService.getSummary(meetingId)
        setSummary(existingSummary)
      } catch (error) {
        console.log('No existing summary found')
      }

    } catch (error) {
      console.error('Error loading meeting data:', error)
      toast.error('Failed to load meeting data')
    } finally {
      setLoading(false)
    }
  }

  const handleTranscribe = async () => {
    if (!meeting) return
    
    try {
      setProcessing(true)
      const response = await apiService.transcribeAudio(meeting.id)
      
      const newTranscript: Transcript = {
        id: response.transcript_id,
        meeting_id: meeting.id,
        content: response.transcript.text,
        language: response.transcript.language,
        confidence: response.transcript.confidence,
        created_at: new Date().toISOString(),
      }
      
      setTranscript(newTranscript)
      toast.success('Audio transcribed successfully!')
      setActiveTab('transcript')
      
    } catch (error: any) {
      console.error('Transcription error:', error)
      toast.error(`Transcription failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setProcessing(false)
    }
  }

  const handleGenerateSummary = async () => {
    if (!meeting || !transcript) return
    
    try {
      setProcessing(true)
      const newSummary = await apiService.generateSummary(meeting.id)
      setSummary(newSummary)
      toast.success('Summary generated successfully!')
      setActiveTab('summary')
      
    } catch (error: any) {
      console.error('Summary generation error:', error)
      toast.error(`Summary generation failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setProcessing(false)
    }
  }

  const handleDownloadPDF = async () => {
    if (!meeting) return
    
    try {
      setProcessing(true)
      const blob = await apiService.downloadPDF(meeting.id)
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `meeting_minutes_${meeting.id}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success('PDF downloaded successfully!')
      
    } catch (error: any) {
      console.error('PDF download error:', error)
      toast.error(`PDF download failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setProcessing(false)
    }
  }

  const handleDeleteAudio = async () => {
    if (!meeting) return
    
    if (!confirm('Are you sure you want to delete this audio file? This action cannot be undone.')) {
      return
    }
    
    try {
      setProcessing(true)
      await apiService.deleteAudio(meeting.id)
      toast.success('Audio file deleted successfully!')
      navigate('/')
      
    } catch (error: any) {
      console.error('Delete error:', error)
      toast.error(`Delete failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setProcessing(false)
    }
  }

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    toast.success(`${label} copied to clipboard!`)
  }

  const shareWhatsApp = (text: string) => {
    const encodedText = encodeURIComponent(text)
    const whatsappUrl = `https://wa.me/?text=${encodedText}`
    window.open(whatsappUrl, '_blank')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-india-saffron"></div>
      </div>
    )
  }

  if (!meeting) {
    return (
      <div className="p-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Meeting Not Found</h1>
        <p className="text-gray-600 mb-6">The meeting you're looking for doesn't exist or has been deleted.</p>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-india-saffron text-white rounded-lg hover:bg-india-saffron-dark transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  const getStatusColor = () => {
    const now = new Date()
    const expiresAt = new Date(meeting.expires_at)
    
    if (meeting.is_deleted) return 'text-red-500'
    if (expiresAt < now) return 'text-orange-500'
    if (expiresAt.getTime() - now.getTime() < 3600000) return 'text-yellow-500' // 1 hour
    return 'text-green-500'
  }

  const getStatusText = () => {
    const now = new Date()
    const expiresAt = new Date(meeting.expires_at)
    
    if (meeting.is_deleted) return 'Deleted'
    if (expiresAt < now) return 'Expired'
    if (expiresAt.getTime() - now.getTime() < 3600000) return 'Expires Soon'
    return 'Active'
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Meeting Details</h1>
            <p className="text-gray-600">ID: {meeting.id}</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>

        {/* Meeting Info Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="flex items-center space-x-3">
              <FileAudio className="h-6 w-6 text-india-saffron" />
              <div>
                <p className="text-sm font-medium text-gray-600">File Name</p>
                <p className="text-sm text-gray-900 truncate">{meeting.original_filename}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <Clock className="h-6 w-6 text-india-green" />
              <div>
                <p className="text-sm font-medium text-gray-600">Uploaded</p>
                <p className="text-sm text-gray-900">{formatDate(meeting.uploaded_at)}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <Calendar className="h-6 w-6 text-india-blue" />
              <div>
                <p className="text-sm font-medium text-gray-600">Expires</p>
                <p className="text-sm text-gray-900">{formatDate(meeting.expires_at)}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <CheckCircle className="h-6 w-6 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-600">Status</p>
                <p className={`text-sm font-medium ${getStatusColor()}`}>
                  {getStatusText()}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'overview', label: 'Overview', icon: FileText },
              { id: 'transcript', label: 'Transcript', icon: FileText },
              { id: 'summary', label: 'Summary', icon: Users },
              { id: 'whatsapp', label: 'WhatsApp', icon: MessageSquare },
            ].map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${activeTab === tab.id
                      ? 'border-india-saffron text-india-saffron'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 border border-gray-200 rounded-lg">
                  <div className="p-3 rounded-full bg-india-saffron bg-opacity-10 mx-auto mb-4">
                    <FileText className="h-8 w-8 text-india-saffron mx-auto" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Transcription</h3>
                  <p className="text-3xl font-bold text-india-saffron mb-2">
                    {transcript ? '✓' : '—'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {transcript ? 'Completed' : 'Not started'}
                  </p>
                  {!transcript && (
                    <button
                      onClick={handleTranscribe}
                      disabled={processing}
                      className="mt-3 px-4 py-2 bg-india-saffron text-white rounded-lg hover:bg-india-saffron-dark disabled:opacity-50 transition-colors"
                    >
                      {processing ? 'Processing...' : 'Start Transcription'}
                    </button>
                  )}
                </div>

                <div className="text-center p-6 border border-gray-200 rounded-lg">
                  <div className="p-3 rounded-full bg-india-green bg-opacity-10 mx-auto mb-4">
                    <Users className="h-8 w-8 text-india-green mx-auto" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Summary</h3>
                  <p className="text-3xl font-bold text-india-green mb-2">
                    {summary ? '✓' : '—'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {summary ? 'Generated' : 'Not available'}
                  </p>
                  {transcript && !summary && (
                    <button
                      onClick={handleGenerateSummary}
                      disabled={processing}
                      className="mt-3 px-4 py-2 bg-india-green text-white rounded-lg hover:bg-india-green-dark disabled:opacity-50 transition-colors"
                    >
                      {processing ? 'Processing...' : 'Generate Summary'}
                    </button>
                  )}
                </div>

                <div className="text-center p-6 border border-gray-200 rounded-lg">
                  <div className="p-3 rounded-full bg-india-blue bg-opacity-10 mx-auto mb-4">
                    <Download className="h-8 w-8 text-india-blue mx-auto" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">PDF Minutes</h3>
                  <p className="text-3xl font-bold text-india-blue mb-2">
                    {summary ? '✓' : '—'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {summary ? 'Available' : 'Not available'}
                  </p>
                  {summary && (
                    <button
                      onClick={handleDownloadPDF}
                      disabled={processing}
                      className="mt-3 px-4 py-2 bg-india-blue text-white rounded-lg hover:bg-india-blue-dark disabled:opacity-50 transition-colors"
                    >
                      {processing ? 'Processing...' : 'Download PDF'}
                    </button>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Actions</h3>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={handleDeleteAudio}
                    disabled={processing}
                    className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors flex items-center space-x-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    <span>Delete Audio</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Transcript Tab */}
          {activeTab === 'transcript' && (
            <div>
              {transcript ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <h3 className="text-lg font-medium text-gray-900">Transcript</h3>
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                        {getLanguageName(transcript.language)}
                      </span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                        {Math.round(transcript.confidence * 100)}% confidence
                      </span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(transcript.content, 'Transcript')}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
                    >
                      <Copy className="h-4 w-4" />
                      <span>Copy</span>
                    </button>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-gray-900 whitespace-pre-wrap">{transcript.content}</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Transcript Available</h3>
                  <p className="text-gray-600 mb-4">Start transcription to see the transcript here.</p>
                  <button
                    onClick={handleTranscribe}
                    disabled={processing}
                    className="px-4 py-2 bg-india-saffron text-white rounded-lg hover:bg-india-saffron-dark disabled:opacity-50 transition-colors"
                  >
                    {processing ? 'Processing...' : 'Start Transcription'}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Summary Tab */}
          {activeTab === 'summary' && (
            <div>
              {summary ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">Meeting Summary</h3>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(summary, null, 2), 'Summary')}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
                    >
                      <Copy className="h-4 w-4" />
                      <span>Copy All</span>
                    </button>
                  </div>

                  {/* Decisions */}
                  {summary.decisions.length > 0 && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Decisions Made</h4>
                      <div className="space-y-2">
                        {summary.decisions.map((decision, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <div className="w-2 h-2 bg-india-saffron rounded-full mt-2 flex-shrink-0"></div>
                            <p className="text-gray-700">{decision}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Items */}
                  {summary.action_items.length > 0 && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Action Items</h4>
                      <div className="space-y-3">
                        {summary.action_items.map((item, index) => (
                          <div key={index} className="border border-gray-200 rounded-lg p-3">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="text-gray-900 font-medium">{item.action}</p>
                                <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                                  <span>Owner: {item.owner}</span>
                                  <span>Due: {formatDate(item.due_date)}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Open Questions */}
                  {summary.open_questions.length > 0 && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Open Questions</h4>
                      <div className="space-y-2">
                        {summary.open_questions.map((question, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <div className="w-2 h-2 bg-india-blue rounded-full mt-2 flex-shrink-0"></div>
                            <p className="text-gray-700">{question}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Summary Available</h3>
                  <p className="text-gray-600 mb-4">Generate a summary to see the key points here.</p>
                  {transcript ? (
                    <button
                      onClick={handleGenerateSummary}
                      disabled={processing}
                      className="px-4 py-2 bg-india-green text-white rounded-lg hover:bg-india-green-dark disabled:opacity-50 transition-colors"
                    >
                      {processing ? 'Processing...' : 'Generate Summary'}
                    </button>
                  ) : (
                    <p className="text-sm text-gray-500">Complete transcription first to generate summary</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* WhatsApp Tab */}
          {activeTab === 'whatsapp' && (
            <div>
              {summary ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">WhatsApp Summary</h3>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => copyToClipboard(summary.whatsapp_blurb, 'WhatsApp summary')}
                        className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
                      >
                        <Copy className="h-4 w-4" />
                        <span>Copy</span>
                      </button>
                      <button
                        onClick={() => shareWhatsApp(summary.whatsapp_blurb)}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                      >
                        <Share2 className="h-4 w-4" />
                        <span>Share on WhatsApp</span>
                      </button>
                    </div>
                  </div>

                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-sm font-bold">W</span>
                      </div>
                      <div className="flex-1">
                        <p className="text-green-900 whitespace-pre-wrap">{summary.whatsapp_blurb}</p>
                        <p className="text-xs text-green-700 mt-2">
                          Character count: {summary.whatsapp_blurb.length}/900
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="text-sm text-gray-600">
                    <p>This WhatsApp summary is optimized for sharing on messaging platforms and includes:</p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Key decisions and action items</li>
                      <li>Important dates and deadlines</li>
                      <li>Open questions that need follow-up</li>
                      <li>Language-appropriate headers (Tamil/Hindi/English)</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No WhatsApp Summary Available</h3>
                  <p className="text-gray-600 mb-4">Generate a summary first to see the WhatsApp blurb here.</p>
                  {transcript ? (
                    <button
                      onClick={handleGenerateSummary}
                      disabled={processing}
                      className="px-4 py-2 bg-india-green text-white rounded-lg hover:bg-india-green-dark disabled:opacity-50 transition-colors"
                    >
                      {processing ? 'Processing...' : 'Generate Summary'}
                    </button>
                  ) : (
                    <p className="text-sm text-gray-500">Complete transcription first to generate summary</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MeetingDetails