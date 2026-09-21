import React from 'react';
import Disclaimer from '../components/Disclaimer';
import ReportSummary from '../components/ReportSummary';
import ParameterTable from '../components/ParameterTable';
import ExplanationCard from '../components/ExplanationCard';
import ChatBox from '../components/ChatBox';

export default function ReportAnalysis({
  reportData,
  reportId,
  explanationData,
  onGetExplanation,
  onSendChat,
  isExplaining,
  isChatting,
}) {
  if (!reportData) return null;

  const metadata = reportData.report_metadata || {};
  const parameters = reportData.parameters || [];
  const retrievedKnowledge = reportData.retrieved_knowledge || [];

  return (
    <div className="analysis-page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a' }}>
            Report Analysis & Context
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
            Report ID: <code style={{ backgroundColor: '#f1f5f9', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>{reportId}</code>
          </p>
        </div>
      </div>

      <Disclaimer customText={reportData.disclaimer} />

      {/* Section 1: Overview Metadata & Extracted Text */}
      <ReportSummary
        reportMetadata={metadata}
        extractedText={reportData.extracted_text}
        extractionMethod={reportData.extraction_method}
      />

      {/* Section 2: Structured Parameter Results */}
      <ParameterTable parameters={parameters} />

      {/* Section 3: AI Explanation Card */}
      <ExplanationCard
        reportId={reportId}
        explanationData={explanationData}
        onGetExplanation={onGetExplanation}
        isLoading={isExplaining}
      />

      {/* Section 4: Retrieved MedQuAD Reference Knowledge */}
      {retrievedKnowledge.length > 0 && (
        <div className="card">
          <h2 className="card-title">📚 Retrieved Medical Information (MedQuAD Knowledge)</h2>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
            General medical reference records matching your report findings. These are retrieved from the MedQuAD medical knowledge base and do not originate from your patient report.
          </p>

          {retrievedKnowledge.map((item, idx) => (
            <div key={idx} className="rag-card">
              <div className="rag-header">
                <span>Source Row ID: {item.source_row_id}</span>
                <span>Similarity Score: {(item.similarity * 100).toFixed(1)}%</span>
              </div>
              <div className="rag-question">Q: {item.question}</div>
              <div className="rag-answer">{item.answer}</div>
            </div>
          ))}
        </div>
      )}

      {/* Section 5: Interactive Report Chatbot */}
      <ChatBox
        reportId={reportId}
        onSendChat={onSendChat}
        isLoading={isChatting}
      />
    </div>
  );
}
