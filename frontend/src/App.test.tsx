import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'

// Mock the API service
vi.mock('./services/api', () => ({
  apiService: {
    uploadAudio: vi.fn(),
    transcribeAudio: vi.fn(),
    getTranscript: vi.fn(),
    generateSummary: vi.fn(),
    getSummary: vi.fn(),
    downloadPDF: vi.fn(),
    deleteAudio: vi.fn(),
  }
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('App', () => {
  it('renders without crashing', () => {
    renderWithRouter(<App />)
    expect(screen.getByText(/MeetNotes/i)).toBeInTheDocument()
  })

  it('shows India branding', () => {
    renderWithRouter(<App />)
    expect(screen.getByText(/India/i)).toBeInTheDocument()
  })
})