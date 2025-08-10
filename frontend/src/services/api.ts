import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout for file uploads
})

// Upload audio file
export const uploadAudio = async (file: File, title?: string) => {
  const formData = new FormData()
  formData.append('file', file)
  if (title) {
    formData.append('title', title)
  }

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

// Start transcription
export const transcribeMeeting = async (meetingId: string) => {
  const response = await api.post('/transcribe', null, {
    params: { meeting_id: meetingId }
  })
  return response.data
}

// Start summarization
export const summarizeMeeting = async (meetingId: string) => {
  const response = await api.post('/summarize', null, {
    params: { meeting_id: meetingId }
  })
  return response.data
}

// Get meeting details
export const getMeeting = async (meetingId: string) => {
  const response = await api.get(`/meeting/${meetingId}`)
  return response.data
}

// Delete meeting
export const deleteMeeting = async (meetingId: string) => {
  const response = await api.delete(`/meeting/${meetingId}`)
  return response.data
}

// Get health status
export const getHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

// Download PDF (returns blob)
export const downloadPDF = async (meetingId: string) => {
  const response = await api.get(`/minutes/${meetingId}/pdf`, {
    responseType: 'blob',
  })
  return response.data
}

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'An error occurred'
      throw new Error(message)
    } else if (error.request) {
      // Request made but no response received
      throw new Error('Unable to connect to server. Please check your internet connection.')
    } else {
      // Something else happened
      throw new Error('An unexpected error occurred')
    }
  }
)

export default api