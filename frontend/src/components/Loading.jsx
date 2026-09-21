import React from 'react';

export default function Loading({ message = 'Analyzing report...' }) {
  return (
    <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
      <div
        className="spinner"
        style={{
          margin: '0 auto 1rem',
          borderColor: 'rgba(37, 99, 235, 0.2)',
          borderTopColor: '#2563eb',
          width: '36px',
          height: '36px',
        }}
      ></div>
      <p style={{ color: '#475569', fontWeight: 500 }}>{message}</p>
    </div>
  );
}
