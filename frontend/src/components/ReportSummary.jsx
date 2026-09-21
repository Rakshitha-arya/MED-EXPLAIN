import React, { useState } from 'react';

export default function ReportSummary({ reportMetadata, extractedText, extractionMethod }) {
  const [showRawText, setShowRawText] = useState(false);

  if (!reportMetadata) return null;

  const getMethodBadge = (method) => {
    if (method === 'pdf_text') return 'PDF Direct Text';
    if (method === 'pdf_ocr') return 'PDF Scanned (OCR)';
    if (method === 'image_ocr') return 'Image OCR';
    return method || 'Unknown';
  };

  return (
    <div className="card">
      <h2 className="card-title">📋 Report Overview</h2>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          backgroundColor: '#f8fafc',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
        }}
      >
        <div>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>File Name</span>
          <p style={{ fontWeight: 600, color: '#0f172a' }}>
            {reportMetadata.original_filename || reportMetadata.filename}
          </p>
        </div>

        <div>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Report Date</span>
          <p style={{ fontWeight: 600, color: '#0f172a' }}>
            {reportMetadata.report_date || 'Not specified'}
          </p>
        </div>

        <div>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>File Type</span>
          <p style={{ fontWeight: 600, color: '#0f172a', textTransform: 'uppercase' }}>
            {reportMetadata.file_type} ({reportMetadata.page_count || 1} page
            {(reportMetadata.page_count || 1) > 1 ? 's' : ''})
          </p>
        </div>

        <div>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Extraction Method</span>
          <p style={{ fontWeight: 600, color: '#0d9488' }}>
            {getMethodBadge(extractionMethod)}
          </p>
        </div>
      </div>

      <div
        className="collapsible-header"
        onClick={() => setShowRawText(!showRawText)}
      >
        <span>🔍 View Extracted Report Text</span>
        <span>{showRawText ? '▲ Hide' : '▼ Expand'}</span>
      </div>

      {showRawText && (
        <div className="collapsible-content">
          {extractedText || 'No text extracted.'}
        </div>
      )}
    </div>
  );
}
