import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileAudio, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { uploadAudio } from '../services/api'

interface FileUploadProps {
  onUploadSuccess: (meetingId: string) => void
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [title, setTitle] = useState('')

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    setError(null)
    setSuccess(null)
    setUploading(true)
    setUploadProgress(0)

    try {
      // Validate file size (200MB limit)
      const maxSize = 200 * 1024 * 1024
      if (file.size > maxSize) {
        throw new Error('File size exceeds 200MB limit')
      }

      // Validate file type
      const allowedTypes = ['audio/mpeg', 'audio/mp4', 'audio/x-m4a', 'audio/wav', 'audio/wave']
      if (!allowedTypes.includes(file.type)) {
        throw new Error('Only MP3, M4A, and WAV files are supported')
      }

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const result = await uploadAudio(file, title || undefined)
      
      clearInterval(progressInterval)
      setUploadProgress(100)
      
      setSuccess(`File uploaded successfully! Meeting ID: ${result.meeting_id}`)
      setUploading(false)
      
      // Redirect to meeting details after a short delay
      setTimeout(() => {
        onUploadSuccess(result.meeting_id)
      }, 1500)

    } catch (err) {
      setUploading(false)
      setUploadProgress(0)
      setError(err instanceof Error ? err.message : 'Upload failed')
    }
  }, [title, onUploadSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/mpeg': ['.mp3'],
      'audio/mp4': ['.m4a'],
      'audio/x-m4a': ['.m4a'],
      'audio/wav': ['.wav'],
      'audio/wave': ['.wav']
    },
    multiple: false,
    disabled: uploading
  })

  return (
    <div className="w-full">
      {/* Title Input */}
      <div className="mb-6">
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
          Meeting Title (Optional)
        </label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter a title for this meeting..."
          className="input-field"
          disabled={uploading}
        />
      </div>

      {/* File Drop Zone */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
          isDragActive
            ? 'border-primary-400 bg-primary-50'
            : uploading
            ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
            : 'border-gray-300 hover:border-primary-400 hover:bg-primary-50 cursor-pointer'
        }`}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="space-y-4">
            <Loader2 className="h-12 w-12 text-primary-600 mx-auto animate-spin" />
            <div>
              <p className="text-lg font-medium text-gray-900">Uploading...</p>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 mt-1">{uploadProgress}% complete</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-primary-100 p-3 rounded-full w-16 h-16 mx-auto">
              {isDragActive ? (
                <Upload className="h-10 w-10 text-primary-600" />
              ) : (
                <FileAudio className="h-10 w-10 text-primary-600" />
              )}
            </div>
            
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop the file here' : 'Upload your meeting recording'}
              </p>
              <p className="text-gray-600">
                Drag and drop your audio file here, or click to select
              </p>
            </div>
            
            <div className="text-sm text-gray-500">
              <p>Supported formats: MP3, M4A, WAV (max 200MB)</p>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-error-50 border border-error-200 rounded-lg flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-error-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-error-800">Upload Failed</h4>
            <p className="text-sm text-error-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mt-4 p-4 bg-success-50 border border-success-200 rounded-lg flex items-start space-x-3">
          <CheckCircle className="h-5 w-5 text-success-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-success-800">Upload Successful</h4>
            <p className="text-sm text-success-700 mt-1">{success}</p>
            <p className="text-sm text-success-600 mt-1">Redirecting to meeting details...</p>
          </div>
        </div>
      )}

      {/* Upload Guidelines */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="text-sm font-medium text-blue-800 mb-2">📝 Upload Guidelines</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Clear audio quality improves transcription accuracy</li>
          <li>• Tamil and Hindi speech will be preserved with English glosses</li>
          <li>• Files are automatically deleted after 24 hours for privacy</li>
          <li>• Processing typically takes 1-3 minutes depending on file length</li>
        </ul>
      </div>
    </div>
  )
}

export default FileUpload