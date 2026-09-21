import React from 'react';

export default function Navbar({ activeTab, setActiveTab, hasActiveReport, onReset }) {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand" onClick={() => setActiveTab('home')}>
          <div className="brand-icon">Mx</div>
          <span>MedExplain</span>
        </div>
        <nav className="navbar-nav">
          <button
            className={`nav-link ${activeTab === 'home' ? 'active' : ''}`}
            onClick={() => setActiveTab('home')}
          >
            Dashboard
          </button>

          {hasActiveReport && (
            <button
              className={`nav-link ${activeTab === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveTab('analysis')}
            >
              Analyze Report
            </button>
          )}

          <button
            className={`nav-link ${activeTab === 'comparison' ? 'active' : ''}`}
            onClick={() => setActiveTab('comparison')}
          >
            Compare Reports
          </button>

          {hasActiveReport && (
            <button className="nav-link" onClick={onReset} style={{ color: '#dc2626' }}>
              Upload New
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
