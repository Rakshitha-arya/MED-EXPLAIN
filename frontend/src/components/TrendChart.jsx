import React from 'react';

export default function TrendChart({ parameterName, unit, measurements = [] }) {
  const numericPoints = measurements.filter(
    (m) => m.value !== null && m.value !== undefined && !isNaN(Number(m.value))
  );

  if (!numericPoints || numericPoints.length < 2) {
    return (
      <div className="card">
        <h3 className="card-title">📈 Trend Visualization: {parameterName}</h3>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
          At least 2 numeric measurements with compatible units are required to render a
          trend chart for {parameterName}.
        </p>
      </div>
    );
  }

  // SVG dimensions
  const svgWidth = 650;
  const svgHeight = 260;
  const padLeft = 60;
  const padRight = 40;
  const padTop = 30;
  const padBottom = 50;

  const chartW = svgWidth - padLeft - padRight;
  const chartH = svgHeight - padTop - padBottom;

  const yValues = numericPoints.map((p) => Number(p.value));
  let minY = Math.min(...yValues);
  let maxY = Math.max(...yValues);

  if (minY === maxY) {
    minY = minY * 0.9;
    maxY = maxY * 1.1 || 1.0;
  } else {
    const range = maxY - minY;
    minY = Math.max(0, minY - range * 0.15);
    maxY = maxY + range * 0.15;
  }

  const getX = (index) => {
    if (numericPoints.length === 1) return padLeft + chartW / 2;
    return padLeft + (index / (numericPoints.length - 1)) * chartW;
  };

  const getY = (val) => {
    return padTop + chartH - ((val - minY) / (maxY - minY)) * chartH;
  };

  // Build SVG path string
  const pathD = numericPoints
    .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${getX(idx)} ${getY(p.value)}`)
    .join(' ');

  // Check if reference ranges vary between measurements
  const ranges = Array.from(new Set(numericPoints.map((p) => p.reference_range)));
  const rangeNotice =
    ranges.length > 1
      ? `Note: Report-specific reference ranges vary across dates (${ranges.join(', ')}).`
      : `Report Reference Range: ${ranges[0] || 'Not specified'}`;

  return (
    <div className="card">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.75rem',
        }}
      >
        <h3 className="card-title" style={{ margin: 0 }}>
          📈 Numerical Trend: {parameterName} {unit ? `(${unit})` : ''}
        </h3>
        <span
          style={{
            fontSize: '0.8rem',
            backgroundColor: '#eff6ff',
            color: '#2563eb',
            padding: '0.25rem 0.65rem',
            borderRadius: '9999px',
            fontWeight: 600,
          }}
        >
          {numericPoints.length} Measurements
        </span>
      </div>

      <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '1rem' }}>
        {rangeNotice}
      </p>

      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: '100%', height: 'auto', backgroundColor: '#fafafa', borderRadius: '8px' }}
        >
          {/* Y-axis gridlines */}
          {[0, 0.33, 0.66, 1].map((ratio, idx) => {
            const val = minY + (maxY - minY) * (1 - ratio);
            const y = padTop + ratio * chartH;
            return (
              <g key={idx}>
                <line
                  x1={padLeft}
                  y1={y}
                  x2={svgWidth - padRight}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeDasharray="4 4"
                />
                <text
                  x={padLeft - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="#64748b"
                >
                  {val.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Line connecting points */}
          <path d={pathD} fill="none" stroke="#2563eb" strokeWidth="3" />

          {/* Data Points */}
          {numericPoints.map((p, idx) => {
            const cx = getX(idx);
            const cy = getY(p.value);
            return (
              <g key={idx}>
                <circle
                  cx={cx}
                  cy={cy}
                  r="6"
                  fill="#0d9488"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
                {/* Value label above point */}
                <text
                  x={cx}
                  y={cy - 12}
                  textAnchor="middle"
                  fontSize="12"
                  fontWeight="700"
                  fill="#0f172a"
                >
                  {p.value} {p.unit || ''}
                </text>
                {/* Date label below X axis */}
                <text
                  x={cx}
                  y={svgHeight - padBottom + 20}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#334155"
                  fontWeight="500"
                >
                  {p.date || 'Unknown'}
                </text>
              </g>
            );
          })}

          {/* X Axis line */}
          <line
            x1={padLeft}
            y1={svgHeight - padBottom}
            x2={svgWidth - padRight}
            y2={svgHeight - padBottom}
            stroke="#cbd5e1"
            strokeWidth="2"
          />
        </svg>
      </div>
    </div>
  );
}
