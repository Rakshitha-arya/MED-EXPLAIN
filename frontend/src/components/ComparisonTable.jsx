import React from 'react';

export default function ComparisonTable({ comparisonItems = [] }) {
  if (!comparisonItems || comparisonItems.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">📊 Multi-Report Parameter Comparison</h2>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
          Select parameters to display comparison measurements.
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
      <h2 className="card-title">📊 Multi-Report Parameter Comparison</h2>
      <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
        Note: Measurements are ordered chronologically by report date. Report-specific
        reference ranges are preserved for each individual measurement.
      </p>

      <div className="table-responsive">
        <table className="parameter-table">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Date</th>
              <th>Result</th>
              <th>Unit</th>
              <th>Reference Range</th>
              <th>Status</th>
              <th>Change</th>
            </tr>
          </thead>
          <tbody>
            {comparisonItems.map((item, itemIdx) => {
              const { parameter, measurements = [], trends = [] } = item;
              return measurements.map((m, mIdx) => {
                const trend = mIdx > 0 ? trends[mIdx - 1] : null;

                let changeText = '—';
                if (trend) {
                  if (trend.units_compatible && trend.absolute_change !== null) {
                    const sign = trend.absolute_change > 0 ? '+' : '';
                    const pctText =
                      trend.percentage_change !== null
                        ? ` (${sign}${trend.percentage_change}%)`
                        : '';
                    changeText = `${sign}${trend.absolute_change}${pctText}`;
                  } else {
                    changeText = 'Incompatible units';
                  }
                }

                return (
                  <tr key={`${itemIdx}-${mIdx}`}>
                    {mIdx === 0 && (
                      <td
                        rowSpan={measurements.length}
                        style={{
                          fontWeight: 700,
                          color: '#0f172a',
                          verticalAlign: 'top',
                          borderRight: '1px solid #e2e8f0',
                        }}
                      >
                        {parameter}
                      </td>
                    )}
                    <td style={{ fontWeight: 600 }}>{m.date || 'Unknown'}</td>
                    <td style={{ fontWeight: 600 }}>{m.result_value || m.value}</td>
                    <td style={{ color: '#64748b' }}>{m.unit || '—'}</td>
                    <td style={{ color: '#475569' }}>
                      {m.reference_range || 'Not specified'}
                    </td>
                    <td>
                      <span className={`status-badge ${getStatusClass(m.status)}`}>
                        {m.status || 'Unknown'}
                      </span>
                    </td>
                    <td
                      style={{
                        fontWeight: 600,
                        color:
                          trend && trend.absolute_change !== null
                            ? trend.absolute_change > 0
                              ? '#2563eb'
                              : trend.absolute_change < 0
                              ? '#d97706'
                              : '#475569'
                            : '#64748b',
                      }}
                    >
                      {changeText}
                    </td>
                  </tr>
                );
              });
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
