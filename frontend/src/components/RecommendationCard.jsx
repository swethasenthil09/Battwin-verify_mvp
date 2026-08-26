import React from 'react';
import { ShieldAlert, CheckCircle, AlertOctagon } from 'lucide-react';

export default function RecommendationCard({ recommendation }) {
  if (!recommendation) return null;

  const action = recommendation.action || 'normal';
  const chargeRate = recommendation.max_charge_rate_C || 1.0;
  const dischargeRate = recommendation.max_discharge_rate_C || 1.0;
  const reasons = recommendation.reasons || ['All checks nominal -- normal operating policy applies.'];

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Operational Policy &amp; Safety Recommendation</h3>
        <span className={`badge ${action === 'normal' ? 'badge-good' : action === 'cautious' ? 'badge-warn' : 'badge-bad'}`}>
          {action.toUpperCase()} MODE
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: '#0D1114', border: '1px solid var(--panel-border)', borderRadius: '8px', padding: '12px' }}>
          <span style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '0.05em' }}>MAX CHARGE RATE</span>
          <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--ai)', marginTop: '4px' }} className="mono">
            {chargeRate} C
          </div>
        </div>

        <div style={{ background: '#0D1114', border: '1px solid var(--panel-border)', borderRadius: '8px', padding: '12px' }}>
          <span style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '0.05em' }}>MAX DISCHARGE RATE</span>
          <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--physics)', marginTop: '4px' }} className="mono">
            {dischargeRate} C
          </div>
        </div>
      </div>

      <div style={{ fontSize: '13px' }}>
        <span style={{ color: 'var(--muted)', fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
          POLICY AUDIT &amp; DECISION REASONS:
        </span>
        <ul style={{ listStyleType: 'none', padding: 0 }}>
          {reasons.map((reason, idx) => (
            <li
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                marginBottom: '8px',
                color: 'var(--text)',
                lineHeight: 1.4
              }}
            >
              {action === 'normal' ? (
                <CheckCircle size={16} style={{ color: 'var(--good)', marginTop: '2px', flexShrink: 0 }} />
              ) : (
                <AlertOctagon size={16} style={{ color: 'var(--warn)', marginTop: '2px', flexShrink: 0 }} />
              )}
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
