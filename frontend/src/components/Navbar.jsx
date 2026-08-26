import React from 'react';
import { Battery, ShieldCheck } from 'lucide-react';

export default function Navbar({ selectedBattery, activeTab, reliability }) {
  const titles = {
    overview: 'Executive Dashboard & Capacity Trajectory',
    reliability: 'Cross-Fidelity & Reliability Score Audit',
    inference: 'Live AI Model Inference Engine (`/api/predict`)',
    analytics: 'Battery Telemetry & State of Charge (SoC) Analytics',
    explainability: 'SHAP Explainability, CALCE Domain Shift & 2-RC ECM Physics',
  };


  const relScore = reliability?.reliability_score_after_calibration ?? reliability?.reliability_score ?? 80;

  return (
    <header style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingBottom: '16px',
      marginBottom: '24px',
      borderBottom: '1px solid var(--panel-border)',
      flexWrap: 'wrap',
      gap: '16px'
    }}>
      <div>
        <h2 style={{ fontSize: '22px', fontWeight: 700, letterSpacing: '-0.02em' }}>
          {titles[activeTab] || 'Dashboard'}
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: '13px', marginTop: '2px' }}>
          Reliability-Aware Battery Energy Storage Management &amp; RUL Intelligence
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: '#0D1114',
          border: '1px solid var(--panel-border)',
          borderRadius: '6px',
          padding: '6px 12px'
        }}>
          <Battery size={16} style={{ color: 'var(--ai)' }} />
          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>Active Battery:</span>
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--ai)' }} className="mono">
            {selectedBattery}
          </span>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'rgba(79, 209, 197, 0.12)',
          border: '1px solid rgba(79, 209, 197, 0.3)',
          borderRadius: '6px',
          padding: '6px 12px'
        }}>
          <ShieldCheck size={16} style={{ color: 'var(--ai)' }} />
          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--ai)' }} className="mono">
            Score: {relScore.toFixed(1)}/100
          </span>
        </div>
      </div>
    </header>
  );
}
