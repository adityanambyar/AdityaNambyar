import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds for large file uploads
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export interface Meeting {
  id: number
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  uploaded_at: string
  expires_at: string
  is_deleted: boolean
}

export interface Transcript {
  id: number
  meeting_id: number
  content: string
  language: string
  confidence: number
  created_at: string
}

export interface Summary {
  id: number
  meeting_id: number
  decisions: string[]
  action_items: Array<{
    owner: string
    action: string
    due_date: string
  }>
  open_questions: string[]
  whatsapp_blurb: string
  created_at: string
}

export interface UploadResponse {
  message: string
  meeting_id: number
  filename: string
  original_filename: string
  file_size: number
  expires_at: string
  s3_key: string
}

export interface TranscriptionResponse {
  message: string
  meeting_id: number
  transcript_id: number
  transcript: {
    text: string
    language: string
    confidence: number
    segments: Array<{
      start: number
      end: number
      text: string
      confidence: number
    }>
  }
  language: string
  confidence: number
  duration: number
  segments_count: number
}

export const apiService = {
  // Upload audio file
  async uploadAudio(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post<UploadResponse>('/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    return response.data
  },

  // Transcribe audio
  async transcribeAudio(meetingId: number): Promise<TranscriptionResponse> {
    const response = await api.post<TranscriptionResponse>(`/transcribe/${meetingId}`)
    return response.data
  },

  // Get transcript
  async getTranscript(meetingId: number): Promise<Transcript> {
    const response = await api.get<Transcript>(`/transcribe/${meetingId}`)
    return response.data
  },

  // Generate summary
  async generateSummary(meetingId: number): Promise<Summary> {
    const response = await api.post<Summary>(`/summarize/${meetingId}`)
    return response.data
  },

  // Get summary
  async getSummary(meetingId: number): Promise<Summary> {
    const response = await api.get<Summary>(`/summarize/${meetingId}`)
    return response.data
  },

  // Get WhatsApp summary
  async getWhatsAppSummary(meetingId: number): Promise<{ whatsapp_blurb: string }> {
    const response = await api.get(`/summarize/${meetingId}/whatsapp`)
    return response.data
  },

  // Download PDF
  async downloadPDF(meetingId: number): Promise<Blob> {
    const response = await api.get(`/minutes/${meetingId}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Delete audio
  async deleteAudio(meetingId: number): Promise<{ message: string }> {
    const response = await api.delete(`/upload/${meetingId}`)
    return response.data
  },

  // Get meeting preview
  async getMeetingPreview(meetingId: number): Promise<any> {
    const response = await api.get(`/minutes/${meetingId}/preview`)
    return response.data
  },
}

export default api