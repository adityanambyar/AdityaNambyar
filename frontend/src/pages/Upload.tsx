import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { 
  Upload as UploadIcon, 
  FileAudio, 
  CheckCircle, 
  AlertCircle,
  X,
  Play,
  Clock,
  Trash2
} from 'lucide-react'
import { toast } from 'react-hot-toast'
import { apiService, UploadResponse } from '../services/api'
import { formatFileSize } from '../lib/utils'

const Upload: React.FC = () => {
  const navigate = useNavigate()
  const [uploadedFiles, setUploadedFiles] = useState<Array<{
    file: File
    status: 'uploading' | 'success' | 'error'
    progress?: number
    response?: UploadResponse
    error?: string
  }>>([])
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      status: 'uploading' as const,
      progress: 0,
    }))
    
    setUploadedFiles(prev => [...prev, ...newFiles])
    handleUpload(acceptedFiles)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/mp4': ['.m4a'],
      'audio/mpeg': ['.mp3'],
      'audio/wav': ['.wav'],
    },
    maxSize: 200 * 1024 * 1024, // 200MB
    multiple: true,
  })

  const handleUpload = async (files: File[]) => {
    setIsUploading(true)
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const fileIndex = uploadedFiles.length + i
      
      try {
        // Simulate progress
        for (let progress = 0; progress <= 100; progress += 10) {
          setUploadedFiles(prev => 
            prev.map((item, index) => 
              index === fileIndex 
                ? { ...item, progress }
                : item
            )
          )
          await new Promise(resolve => setTimeout(resolve, 100))
        }

        const response = await apiService.uploadAudio(file)
        
        setUploadedFiles(prev => 
          prev.map((item, index) => 
            index === fileIndex 
              ? { ...item, status: 'success', response }
              : item
          )
        )
        
        toast.success(`${file.name} uploaded successfully!`)
        
        // Navigate to meeting details after successful upload
        setTimeout(() => {
          navigate(`/meeting/${response.meeting_id}`)
        }, 1500)
        
      } catch (error: any) {
        console.error('Upload error:', error)
        
        setUploadedFiles(prev => 
          prev.map((item, index) => 
            index === fileIndex 
              ? { 
                  ...item, 
                  status: 'error', 
                  error: error.response?.data?.detail || error.message || 'Upload failed'
                }
              : item
          )
        )
        
        toast.error(`Failed to upload ${file.name}: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    setIsUploading(false)
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const retryUpload = (index: number) => {
    const fileItem = uploadedFiles[index]
    if (fileItem && fileItem.status === 'error') {
      setUploadedFiles(prev => 
        prev.map((item, i) => 
          i === index 
            ? { ...item, status: 'uploading', progress: 0, error: undefined }
            : item
        )
      )
      handleUpload([fileItem.file])
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-blue-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-blue-600'
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Audio</h1>
        <p className="text-gray-600">
          Upload your meeting audio files for transcription and summarization. 
          Supports M4A, MP3, and WAV formats up to 200MB.
        </p>
      </div>

      {/* Upload Zone */}
      <div className="mb-8">
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive 
              ? 'border-india-saffron bg-india-saffron bg-opacity-5' 
              : 'border-gray-300 hover:border-india-saffron hover:bg-gray-50'
            }
          `}
        >
          <input {...getInputProps()} />
          
          <div className="flex flex-col items-center space-y-4">
            <div className="p-4 rounded-full bg-india-saffron bg-opacity-10">
              <UploadIcon className="h-8 w-8 text-india-saffron" />
            </div>
            
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop your audio files here' : 'Drag & drop audio files here'}
              </p>
              <p className="text-gray-500 mt-1">
                or click to browse files
              </p>
            </div>
            
            <div className="text-sm text-gray-400 space-y-1">
              <p>Supported formats: M4A, MP3, WAV</p>
              <p>Maximum file size: 200MB</p>
              <p>Files are automatically deleted after 24 hours</p>
            </div>
          </div>
        </div>
      </div>

      {/* India Features Info */}
      <div className="bg-gradient-to-r from-india-saffron to-india-green bg-opacity-10 p-6 rounded-lg mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-3">🇮🇳 India-First Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-india-saffron rounded-full"></div>
            <span className="text-sm text-gray-700">Tamil language support with English glosses</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-india-green rounded-full"></div>
            <span className="text-sm text-gray-700">Hindi language support with English glosses</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-india-blue rounded-full"></div>
            <span className="text-sm text-gray-700">Multi-language WhatsApp summaries</span>
          </div>
        </div>
      </div>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Uploaded Files</h2>
          </div>
          
          <div className="divide-y divide-gray-200">
            {uploadedFiles.map((fileItem, index) => (
              <div key={index} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    <FileAudio className="h-8 w-8 text-gray-400" />
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {fileItem.file.name}
                        </p>
                        {getStatusIcon(fileItem.status)}
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                        <span>{formatFileSize(fileItem.file.size)}</span>
                        <span>•</span>
                        <span className={`font-medium ${getStatusColor(fileItem.status)}`}>
                          {fileItem.status === 'uploading' && fileItem.progress !== undefined
                            ? `Uploading... ${fileItem.progress}%`
                            : fileItem.status === 'success'
                            ? 'Uploaded successfully'
                            : 'Upload failed'
                          }
                        </span>
                        
                        {fileItem.response && (
                          <>
                            <span>•</span>
                            <span>Meeting ID: {fileItem.response.meeting_id}</span>
                          </>
                        )}
                      </div>
                      
                      {/* Progress Bar */}
                      {fileItem.status === 'uploading' && fileItem.progress !== undefined && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-india-saffron h-2 rounded-full transition-all duration-300"
                              style={{ width: `${fileItem.progress}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                      
                      {/* Error Message */}
                      {fileItem.status === 'error' && fileItem.error && (
                        <p className="text-sm text-red-600 mt-2">{fileItem.error}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {fileItem.status === 'success' && fileItem.response && (
                      <button
                        onClick={() => navigate(`/meeting/${fileItem.response!.meeting_id}`)}
                        className="p-2 text-gray-400 hover:text-india-saffron transition-colors"
                        title="View Meeting Details"
                      >
                        <Play className="h-4 w-4" />
                      </button>
                    )}
                    
                    {fileItem.status === 'error' && (
                      <button
                        onClick={() => retryUpload(index)}
                        className="p-2 text-gray-400 hover:text-india-saffron transition-colors"
                        title="Retry Upload"
                      >
                        <UploadIcon className="h-4 w-4" />
                      </button>
                    )}
                    
                    <button
                      onClick={() => removeFile(index)}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                      title="Remove File"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Tips */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-3">💡 Upload Tips</h3>
        <ul className="text-sm text-blue-800 space-y-2">
          <li>• Ensure good audio quality for better transcription accuracy</li>
          <li>• Files are automatically processed for transcription after upload</li>
          <li>• You can generate summaries and PDF minutes once transcription is complete</li>
          <li>• Audio files are automatically deleted after 24 hours for privacy</li>
          <li>• Use the "Delete now" button if you need immediate removal</li>
        </ul>
      </div>
    </div>
  )
}

export default Upload