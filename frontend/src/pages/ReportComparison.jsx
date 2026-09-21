import React, { useState, useEffect } from 'react';
import Disclaimer from '../components/Disclaimer';
import ReportSelector from '../components/ReportSelector';
import ComparisonTable from '../components/ComparisonTable';
import TrendChart from '../components/TrendChart';
import { getReports, compareReports } from '../services/api';

export default function ReportComparison() {
  const [availableReports, setAvailableReports] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [selectedParameter, setSelectedParameter] = useState('');

  const [isLoadingReports, setIsLoadingReports] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchAvailableReports();
  }, []);

  const fetchAvailableReports = async () => {
    setIsLoadingReports(true);
    setErrorMessage('');
    try {
      const data = await getReports();
      const list = data.reports || [];
      setAvailableReports(list);

      // Pre-select first 2 reports if available
      if (list.length >= 2) {
        setSelectedIds([list[0].report_id, list[1].report_id]);
      } else if (list.length === 1) {
        setSelectedIds([list[0].report_id]);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Failed to load available reports.');
    } finally {
      setIsLoadingReports(false);
    }
  };

  const handleToggleSelect = (reportId) => {
    setSelectedIds((prev) => {
      if (prev.includes(reportId)) {
        return prev.filter((id) => id !== reportId);
      } else {
        return [...prev, reportId];
      }
    });
  };

  const handleRunComparison = async () => {
    if (selectedIds.length < 2) {
      setErrorMessage('Please select at least 2 reports for comparison.');
      return;
    }

    setIsComparing(true);
    setErrorMessage('');
    try {
      const result = await compareReports(selectedIds);
      setComparisonData(result);

      // Default selected parameter for trend chart to first common parameter if available
      const common = result.common_parameters || [];
      if (common.length > 0) {
        setSelectedParameter(common[0]);
      } else if (result.comparison && result.comparison.length > 0) {
        setSelectedParameter(result.comparison[0].parameter);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Comparison failed.');
    } finally {
      setIsComparing(false);
    }
  };

  // Find currently selected parameter item in comparisonData
  const activeParamObj =
    comparisonData && comparisonData.comparison
      ? comparisonData.comparison.find((item) => item.parameter === selectedParameter)
      : null;

  return (
    <div className="comparison-page">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a' }}>
          Multi-Report Comparison & Trend Analysis
        </h1>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
          Track numerical changes across different report dates.
        </p>
      </div>

      <Disclaimer customText="This comparison shows numerical changes between uploaded reports. It does not provide a medical diagnosis or treatment recommendation." />

      {errorMessage && <div className="error-alert" style={{ marginBottom: '1rem' }}>{errorMessage}</div>}

      {/* Report Selector Component */}
      <ReportSelector
        availableReports={availableReports}
        selectedIds={selectedIds}
        onToggleSelect={handleToggleSelect}
        onCompare={handleRunComparison}
        isLoading={isComparing || isLoadingReports}
      />

      {comparisonData && (
        <div style={{ marginTop: '1.5rem' }}>
          {/* Common Parameters Selector */}
          {comparisonData.comparison && comparisonData.comparison.length > 0 && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 className="card-title">🔍 Select Parameter to Graph</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                {comparisonData.comparison.map((item, idx) => {
                  const isSelected = item.parameter === selectedParameter;
                  return (
                    <button
                      key={idx}
                      className={`chip ${isSelected ? 'active' : ''}`}
                      style={{
                        backgroundColor: isSelected ? '#2563eb' : '#f1f5f9',
                        color: isSelected ? 'white' : '#334155',
                        fontWeight: isSelected ? 600 : 400,
                      }}
                      onClick={() => setSelectedParameter(item.parameter)}
                    >
                      {item.parameter} {item.is_common ? '⭐' : ''}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Trend Chart Component */}
          {activeParamObj && (
            <TrendChart
              parameterName={activeParamObj.parameter}
              unit={activeParamObj.unit}
              measurements={activeParamObj.measurements}
            />
          )}

          {/* Comparison Table Component */}
          <ComparisonTable comparisonItems={comparisonData.comparison} />
        </div>
      )}
    </div>
  );
}
