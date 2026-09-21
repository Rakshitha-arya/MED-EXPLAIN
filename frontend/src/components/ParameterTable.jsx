import React from 'react';

export default function ParameterTable({ parameters = [] }) {
  if (!parameters || parameters.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">🧪 Extracted Lab Results</h2>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
          No structured lab parameters were detected in this report text.
        </p>
      </div>
    );
  }

  const getStatusClass = (status) => {
    switch (status) {
      case 'Low':
        return 'status-low';
      case 'Normal':
        return 'status-normal';
      case 'High':
        return 'status-high';
      default:
        return 'status-unknown';
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">🧪 Extracted Lab Results</h2>
      <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
        Note: Status classification is evaluated strictly against explicit reference ranges
        present in your report.
      </p>

      <div className="table-responsive">
        <table className="parameter-table">
          <thead>
            <tr>
              <th>Test / Parameter</th>
              <th>Result</th>
              <th>Unit</th>
              <th>Reference Range</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {parameters.map((param, index) => (
              <tr key={index}>
                <td style={{ fontWeight: 600, color: '#0f172a' }}>
                  {param.test_name}
                </td>
                <td style={{ fontWeight: 600 }}>{param.result_value}</td>
                <td style={{ color: '#64748b' }}>{param.unit || '—'}</td>
                <td style={{ color: '#475569' }}>
                  {param.reference_range || 'Not specified'}
                </td>
                <td>
                  <span className={`status-badge ${getStatusClass(param.status)}`}>
                    {param.status || 'Unknown'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
