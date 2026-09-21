import React from 'react';
import FileUpload from '../components/FileUpload';
import Disclaimer from '../components/Disclaimer';

export default function Home({ onUpload, isLoading, uploadError }) {
  return (
    <div className="home-page">
      <section className="hero-section">
        <h1 className="hero-title">
          <span>MedExplain</span>
        </h1>
        <p className="hero-description">
          Understand your medical reports with AI-powered explanations.
        </p>

        <Disclaimer />

        <div className="workflow-steps">
          <div className="workflow-step">
            <div className="step-num">1</div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#0f172a' }}>
              Upload
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>
              Upload PDF, JPG, or PNG lab reports securely.
            </p>
          </div>

          <div className="workflow-step">
            <div className="step-num">2</div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#0f172a' }}>
              Analyze
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>
              Extract lab parameters and compare explicit reference ranges.
            </p>
          </div>

          <div className="workflow-step">
            <div className="step-num">3</div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#0f172a' }}>
              Understand
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>
              Read plain-language AI explanations grounded in MedQuAD knowledge.
            </p>
          </div>
        </div>
      </section>

      <section style={{ maxWidth: '750px', margin: '0 auto' }}>
        <FileUpload onUpload={onUpload} isLoading={isLoading} />
        {uploadError && <div className="error-alert">{uploadError}</div>}
      </section>
    </div>
  );
}
