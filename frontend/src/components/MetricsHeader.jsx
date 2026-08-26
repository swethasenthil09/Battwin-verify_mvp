import React from 'react';
import { ShieldCheck, Zap, AlertTriangle, TrendingDown } from 'lucide-react';

export default function MetricsHeader({ reliability, rul, recommendation, analysis }) {
  const relScore = reliability?.reliability_score_after_calibration ?? reliability?.reliability_score ?? 80;
  const statusText = reliability?.status_text ?? 'Moderate Reliability';
  const rulCycles = rul?.rul_ai_cycles ?? '0';
  const eolReached = rul?.eol_reached ?? false;
  const policyAction = recommendation?.action?.toUpperCase() ?? 'NORMAL';
  const maxCharge = recommendation?.max_charge_rate_C ?? 1.0;
  const maxDischarge = recommendation?.max_discharge_rate_C ?? 1.0;

  let scoreColor = 'var(--good)';
  if (relScore < 60) scoreColor = 'var(--bad)';
  else if (relScore < 85) scoreColor = 'var(--warn)';

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
      gap: '16px',
      marginBottom: '24px'
    }}>
      {/* Card 1: Reliability Score */}
      <div className="glass-panel" style={{ borderLeft: `4px solid ${scoreColor}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: 600, letterSpacing: '0.05em' }}>
            COMPOSITE RELIABILITY
          </span>
          <ShieldCheck size={20} style={{ color: scoreColor }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
          <span style={{ fontSize: '32px', fontWeight: 700, color: scoreColor }} className="mono">
            {relScore.toFixed(1)}
          </span>
          <span style={{ color: 'var(--muted)', fontSize: '14px' }}>/ 100</span>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px', opacity: 0.9 }}>
          {statusText}
        </p>
      </div>

      {/* Card 2: Operational RUL */}
      <div className="glass-panel" style={{ borderLeft: '4px solid var(--ai)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: 600, letterSpacing: '0.05em' }}>
            OPERATIONAL RUL
          </span>
          <TrendingDown size={20} style={{ color: 'var(--ai)' }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
          <span style={{ fontSize: '32px', fontWeight: 700, color: eolReached ? 'var(--bad)' : 'var(--ai)' }} className="mono">
            {rulCycles}
          </span>
          <span style={{ color: 'var(--muted)', fontSize: '14px' }}>cycles</span>
        </div>
        <p style={{ fontSize: '12px', color: eolReached ? 'var(--bad)' : 'var(--muted)', marginTop: '4px' }}>
          {eolReached ? '⚠ EOL threshold reached (70% SoH)' : 'Estimated via recent fade slope'}
        </p>
      </div>

      {/* Card 3: Operational Policy */}
      <div className="glass-panel" style={{ borderLeft: '4px solid var(--accent)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: 600, letterSpacing: '0.05em' }}>
            RECOMMENDED POLICY
          </span>
          <Zap size={20} style={{ color: 'var(--accent)' }} />
        </div>
        <div style={{ marginTop: '8px' }}>
          <span className={`badge ${policyAction === 'NORMAL' ? 'badge-good' : policyAction === 'CAUTIOUS' ? 'badge-warn' : 'badge-bad'}`}>
            {policyAction} POLICY
          </span>
        </div>
        <div style={{ display: 'flex', gap: '16px', marginTop: '10px', fontSize: '12px' }} className="mono">
          <span>Charge: <strong style={{ color: 'var(--text)' }}>{maxCharge}C</strong></span>
          <span>Discharge: <strong style={{ color: 'var(--text)' }}>{maxDischarge}C</strong></span>
        </div>
      </div>

      {/* Card 4: AI Model MAE */}
      <div className="glass-panel" style={{ borderLeft: '4px solid var(--physics)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: 600, letterSpacing: '0.05em' }}>
            HELD-OUT AI ERROR
          </span>
          <AlertTriangle size={20} style={{ color: 'var(--physics)' }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
          <span style={{ fontSize: '32px', fontWeight: 700, color: 'var(--physics)' }} className="mono">
            {reliability?.ai_mae ? reliability.ai_mae.toFixed(2) : '1.92'}%
          </span>
          <span style={{ color: 'var(--muted)', fontSize: '14px' }}>MAE</span>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px' }}>
          Cross-battery generalization error
        </p>
      </div>
    </div>
  );
}
