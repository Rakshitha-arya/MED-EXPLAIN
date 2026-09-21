import React, { useState } from 'react';
import Disclaimer from './Disclaimer';

export default function ExplanationCard({ reportId, explanationData, onGetExplanation, isLoading }) {
  const [questionInput, setQuestionInput] = useState('Can you explain my blood test results?');

  const handleFetchExplanation = (e) => {
    e.preventDefault();
    if (onGetExplanation && !isLoading) {
      onGetExplanation(questionInput);
    }
  };

  const isConfigured = explanationData && explanationData.status !== 'not_configured';

  return (
    <div className="card">
      <h2 className="card-title">🤖 AI Report Explanation</h2>

      <form onSubmit={handleFetchExplanation} style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            className="chat-input"
            value={questionInput}
            onChange={(e) => setQuestionInput(e.target.value)}
            placeholder="Ask a question about your report results..."
            disabled={isLoading}
          />
          <button className="btn-primary" type="submit" disabled={isLoading || !questionInput.trim()}>
            {isLoading ? 'Generating...' : 'Explain Results'}
          </button>
        </div>
      </form>

      {explanationData && (
        <div>
          {!isConfigured && (
            <div
              style={{
                backgroundColor: '#fffbebf5',
                border: '1px solid #fde68a',
                color: '#92400e',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.9rem',
                marginBottom: '1rem',
              }}
            >
              ℹ️ <strong>LLM Not Configured:</strong> Automated natural language answer generation is disabled until LLM_API_KEY or GEMINI_API_KEY is configured in the environment. Structured context and retrieved MedQuAD knowledge are displayed below.
            </div>
          )}

          {explanationData.answer && (
            <div
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '1.25rem',
                marginBottom: '1.25rem',
              }}
            >
              <h3 style={{ fontSize: '1rem', color: '#0f172a', marginBottom: '0.5rem' }}>
                💡 Educational Explanation
              </h3>
              <p style={{ whiteSpace: 'pre-line', color: '#334155', fontSize: '0.95rem' }}>
                {explanationData.answer}
              </p>
            </div>
          )}

          {/* Section 1: From Your Report */}
          {explanationData.report_context && (
            <div style={{ marginBottom: '1.25rem' }}>
              <h4
                style={{
                  fontSize: '0.9rem',
                  textTransform: 'uppercase',
                  color: '#2563eb',
                  letterSpacing: '0.05em',
                  marginBottom: '0.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                }}
              >
                📌 From Your Report
              </h4>
              <div
                style={{
                  backgroundColor: '#eff6ff',
                  border: '1px solid #bfdbfe',
                  borderRadius: '8px',
                  padding: '0.85rem 1rem',
                  fontSize: '0.9rem',
                  color: '#1e3a8a',
                }}
              >
                {explanationData.report_context.parameters &&
                explanationData.report_context.parameters.length > 0 ? (
                  <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                    {explanationData.report_context.parameters.map((p, idx) => (
                      <li key={idx}>
                        <strong>{p.test_name}</strong>: {p.result_value} {p.unit || ''} (Status: {p.status})
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Extracted report text snippet available in overview.</p>
                )}
              </div>
            </div>
          )}

          {/* Section 2: Supporting Medical Information */}
          {explanationData.retrieved_context &&
            explanationData.retrieved_context.length > 0 && (
              <div style={{ marginBottom: '1.25rem' }}>
                <h4
                  style={{
                    fontSize: '0.9rem',
                    textTransform: 'uppercase',
                    color: '#0d9488',
                    letterSpacing: '0.05em',
                    marginBottom: '0.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}
                >
                  📚 Supporting Medical Information (MedQuAD Reference)
                </h4>
                {explanationData.retrieved_context.map((rec, idx) => (
                  <div key={idx} className="rag-card">
                    <div className="rag-header">
                      <span>Source Row ID: {rec.source_row_id}</span>
                      <span>Similarity: {(rec.similarity * 100).toFixed(1)}%</span>
                    </div>
                    <div className="rag-question">Q: {rec.question}</div>
                    <div className="rag-answer">{rec.answer}</div>
                  </div>
                ))}
              </div>
            )}

          <Disclaimer customText={explanationData.disclaimer} />
        </div>
      )}
    </div>
  );
}
