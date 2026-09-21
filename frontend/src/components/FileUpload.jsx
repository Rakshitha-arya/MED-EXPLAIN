import React, { useState, useRef } from 'react';

const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16MB

export default function FileUpload({ onUpload, isLoading }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    if (!file) return false;
    const name = file.name.toLowerCase();
    const isAllowed = ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));

    if (!isAllowed) {
      setErrorMessage(
        `Invalid file type "${file.name}". Supported formats: PDF, JPG, PNG.`
      );
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage('File size exceeds the 16MB limit.');
      return false;
    }

    setErrorMessage('');
    return true;
  };

  const handleFileSelect = (file) => {
    if (validateFile(file)) {
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedFile && !isLoading) {
      onUpload(selectedFile);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="card">
      <h2 className="card-title">📁 Upload Medical Report</h2>

      <div
        className={`upload-card ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="file-input-hidden"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />

        <div className="upload-icon">📄</div>
        <p style={{ fontWeight: 600, color: '#1e293b', marginBottom: '0.25rem' }}>
          Drag & drop your medical report here
        </p>
        <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
          Supports PDF, JPG, PNG (Max 16MB)
        </p>

        {selectedFile && (
          <div
            style={{
              marginTop: '1rem',
              padding: '0.75rem',
              backgroundColor: '#f1f5f9',
              borderRadius: '8px',
              display: 'inline-block',
            }}
          >
            <p style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.95rem' }}>
              Selected: {selectedFile.name}
            </p>
            <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Size: {formatFileSize(selectedFile.size)}
            </p>
          </div>
        )}
      </div>

      {errorMessage && <div className="error-alert">{errorMessage}</div>}

      <div style={{ marginTop: '1.25rem', textAlign: 'right' }}>
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!selectedFile || isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner" style={{ width: '16px', height: '16px' }}></span>
              Analyzing Report...
            </>
          ) : (
            'Analyze Report →'
          )}
        </button>
      </div>
    </div>
  );
}
