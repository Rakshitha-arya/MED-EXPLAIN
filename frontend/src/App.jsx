import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import ReportAnalysis from './pages/ReportAnalysis';
import ReportComparison from './pages/ReportComparison';
import { analyzeReport, getReportExplanation, sendReportChat } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [reportData, setReportData] = useState(null);
  const [reportId, setReportId] = useState(null);
  const [explanationData, setExplanationData] = useState(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const handleUploadAndAnalyze = async (file) => {
    setIsAnalyzing(true);
    setUploadError('');
    try {
      const analysisResult = await analyzeReport(file);
      setReportData(analysisResult);

      const filename = analysisResult.report_metadata?.filename;
      setReportId(filename);
      setActiveTab('analysis');

      if (filename) {
        try {
          setIsExplaining(true);
          const explanation = await getReportExplanation(
            filename,
            'Can you explain my blood test results in simple terms?'
          );
          setExplanationData(explanation);
        } catch (expErr) {
          console.warn('Initial explanation fetch notice:', expErr);
        } finally {
          setIsExplaining(false);
        }
      }
    } catch (err) {
      setUploadError(err.message || 'Failed to upload and analyze report.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGetExplanation = async (question) => {
    if (!reportId) return;
    setIsExplaining(true);
    try {
      const result = await getReportExplanation(reportId, question);
      setExplanationData(result);
    } catch (err) {
      console.error('Explanation request error:', err);
    } finally {
      setIsExplaining(false);
    }
  };

  const handleSendChat = async (question) => {
    if (!reportId) throw new Error('No active report available.');
    setIsChatting(true);
    try {
      return await sendReportChat(reportId, question);
    } finally {
      setIsChatting(false);
    }
  };

  const handleReset = () => {
    setReportData(null);
    setReportId(null);
    setExplanationData(null);
    setUploadError('');
    setActiveTab('home');
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        hasActiveReport={Boolean(reportData)}
        onReset={handleReset}
      />

      <main className="main-content">
        {activeTab === 'home' && (
          <Home
            onUpload={handleUploadAndAnalyze}
            isLoading={isAnalyzing}
            uploadError={uploadError}
          />
        )}

        {activeTab === 'analysis' && reportData && (
          <ReportAnalysis
            reportData={reportData}
            reportId={reportId}
            explanationData={explanationData}
            onGetExplanation={handleGetExplanation}
            onSendChat={handleSendChat}
            isExplaining={isExplaining}
            isChatting={isChatting}
          />
        )}

        {activeTab === 'comparison' && <ReportComparison />}
      </main>

      <footer className="site-footer">
        <p>
          <strong>MedExplain Educational Platform</strong> — Medical Report
          Ingestion, FAISS RAG Retrieval, GenAI Explanation & Multi-Report Comparison
        </p>
      </footer>
    </div>
  );
}
