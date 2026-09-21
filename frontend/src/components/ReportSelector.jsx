import React from 'react';

export default function ReportSelector({
  availableReports = [],
  selectedIds = [],
  onToggleSelect,
  onCompare,
  isLoading,
}) {
  if (!availableReports || availableReports.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">📋 Select Reports to Compare</h2>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
          No stored medical reports found. Please analyze or upload at least two reports first.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="card-title">📋 Select Reports to Compare</h2>
      <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
        Select two or more medical reports to track lab parameter changes over time.
      </p>

      <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1.25rem' }}>
        {availableReports.map((r) => {
          const isSelected = selectedIds.includes(r.report_id);
          return (
            <div
              key={r.report_id}
              onClick={() => onToggleSelect(r.report_id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.85rem 1rem',
                backgroundColor: isSelected ? '#eff6ff' : '#f8fafc',
                border: `1px solid ${isSelected ? '#bfdbfe' : '#e2e8f0'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {}}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <div>
                  <p style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.95rem' }}>
                    {r.original_filename || r.filename}
                  </p>
                  <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    Date: <strong>{r.report_date || 'Unknown'}</strong> | Parameters:{' '}
                    {r.parameter_count || 0}
                  </p>
                </div>
              </div>
              <span
                style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: isSelected ? '#2563eb' : '#64748b',
                }}
              >
                {isSelected ? '✓ Selected' : 'Select'}
              </span>
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.9rem', color: '#475569' }}>
          Selected: <strong>{selectedIds.length}</strong> report(s)
        </span>
        <button
          className="btn-primary"
          onClick={onCompare}
          disabled={selectedIds.length < 2 || isLoading}
        >
          {isLoading ? 'Comparing...' : 'Compare Selected Reports →'}
        </button>
      </div>
    </div>
  );
}
