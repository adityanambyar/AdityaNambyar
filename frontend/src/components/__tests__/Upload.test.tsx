import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import Upload from '../Upload'

// Mock the API service
const mockApiService = {
  uploadAudio: vi.fn(),
}

vi.mock('../../services/api', () => ({
  apiService: mockApiService,
}))

// Mock react-toastify
vi.mock('react-toastify', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
  ToastContainer: vi.fn(() => <div data-testid="toast-container" />),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
      <ToastContainer />
    </BrowserRouter>
  )
}

describe('Upload Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload form correctly', () => {
    renderWithRouter(<Upload />)
    
    expect(screen.getByText(/Upload Audio File/i)).toBeInTheDocument()
    expect(screen.getByText(/Drag and drop your audio file here/i)).toBeInTheDocument()
    expect(screen.getByText(/or click to browse/i)).toBeInTheDocument()
    expect(screen.getByText(/Supported formats: M4A, MP3, WAV/i)).toBeInTheDocument()
    expect(screen.getByText(/Max file size: 200MB/i)).toBeInTheDocument()
  })

  it('handles file selection via click', async () => {
    renderWithRouter(<Upload />)
    
    const fileInput = screen.getByTestId('file-input')
    const file = new File(['audio content'], 'test.m4a', { type: 'audio/mp4' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    
    await waitFor(() => {
      expect(screen.getByText('test.m4a')).toBeInTheDocument()
      expect(screen.getByText('1 MB')).toBeInTheDocument()
    })
  })

  it('handles drag and drop', async () => {
    renderWithRouter(<Upload />)
    
    const dropZone = screen.getByTestId('drop-zone')
    const file = new File(['audio content'], 'test.m4a', { type: 'audio/mp4' })
    
    fireEvent.dragEnter(dropZone)
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [file],
      },
    })
    
    await waitFor(() => {
      expect(screen.getByText('test.m4a')).toBeInTheDocument()
    })
  })

  it('validates file type correctly', async () => {
    renderWithRouter(<Upload />)
    
    const fileInput = screen.getByTestId('file-input')
    const invalidFile = new File(['text content'], 'test.txt', { type: 'text/plain' })
    
    fireEvent.change(fileInput, { target: { files: [invalidFile] } })
    
    await waitFor(() => {
      expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument()
    })
  })

  it('validates file size correctly', async () => {
    renderWithRouter(<Upload />)
    
    const fileInput = screen.getByTestId('file-input')
    // Create a file larger than 200MB
    const largeFile = new File(['x'.repeat(201 * 1024 * 1024)], 'large.m4a', { type: 'audio/mp4' })
    
    fireEvent.change(fileInput, { target: { files: [largeFile] } })
    
    await waitFor(() => {
      expect(screen.getByText(/File too large/i)).toBeInTheDocument()
    })
  })

  it('uploads file successfully', async () => {
    mockApiService.uploadAudio.mockResolvedValue({
      meeting_id: 'test-123',
      message: 'Audio uploaded successfully',
    })
    
    renderWithRouter(<Upload />)
    
    const fileInput = screen.getByTestId('file-input')
    const file = new File(['audio content'], 'test.m4a', { type: 'audio/mp4' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    
    const uploadButton = screen.getByText(/Upload Audio/i)
    fireEvent.click(uploadButton)
    
    await waitFor(() => {
      expect(mockApiService.uploadAudio).toHaveBeenCalledWith(file)
    })
  })

  it('shows loading state during upload', async () => {
    mockApiService.uploadAudio.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    renderWithRouter(<Upload />)
    
    const fileInput = screen.getByTestId('file-input')
    const file = new File(['audio content'], 'test.m4a', { type: 'audio/mp4' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    
    const uploadButton = screen.getByText(/Upload Audio/i)
    fireEvent.click(uploadButton)
    
    expect(screen.getByText(/Uploading.../i)).toBeInTheDocument()
    expect(uploadButton).toBeDisabled()
  })

  it('handles upload error', async () => {
    const errorMessage = 'Upload failed'
    mockApiService.uploadAudio.mockRejectedValue(new Error(errorMessage))
    
    renderWithRouter(<Upload />)
    
    const fileInput = screen.getByTestId('file-input')
    const file = new File(['audio content'], 'test.m4a', { type: 'audio/mp4' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    
    const uploadButton = screen.getByText(/Upload Audio/i)
    fireEvent.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText(/Upload failed/i)).toBeInTheDocument()
    })
  })

  it('clears file selection', async () => {
    renderWithRouter(<Upload />)
    
    const fileInput = screen.getByTestId('file-input')
    const file = new File(['audio content'], 'test.m4a', { type: 'audio/mp4' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    
    await waitFor(() => {
      expect(screen.getByText('test.m4a')).toBeInTheDocument()
    })
    
    const clearButton = screen.getByText(/Clear/i)
    fireEvent.click(clearButton)
    
    expect(screen.queryByText('test.m4a')).not.toBeInTheDocument()
    expect(screen.getByText(/Drag and drop your audio file here/i)).toBeInTheDocument()
  })

  it('shows India-specific branding', () => {
    renderWithRouter(<Upload />)
    
    expect(screen.getByText(/MeetNotes India/i)).toBeInTheDocument()
    expect(screen.getByText(/Powered by Whisper AI/i)).toBeInTheDocument()
  })

  it('displays supported file formats correctly', () => {
    renderWithRouter(<Upload />)
    
    expect(screen.getByText(/M4A, MP3, WAV/i)).toBeInTheDocument()
    expect(screen.getByText(/200MB/i)).toBeInTheDocument()
  })

  it('handles multiple file selection gracefully', async () => {
    renderWithRouter(<Upload />)
    
    const fileInput = screen.getByTestId('file-input')
    const file1 = new File(['audio content'], 'test1.m4a', { type: 'audio/mp4' })
    const file2 = new File(['audio content'], 'test2.m4a', { type: 'audio/mp4' })
    
    fireEvent.change(fileInput, { target: { files: [file1, file2] } })
    
    // Should only take the first file
    await waitFor(() => {
      expect(screen.getByText('test1.m4a')).toBeInTheDocument()
      expect(screen.queryByText('test2.m4a')).not.toBeInTheDocument()
    })
  })
})