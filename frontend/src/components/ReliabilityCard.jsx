import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react';

export default function ReliabilityCard({ reliability }) {
  if (!reliability) return null;

  const components = reliability.component_ratings || {
    data_completeness: { score_pct: 100, rating: 'Excellent', status: '✓ Excellent', badge: 'good' },
    domain_similarity: { score_pct: 100, rating: 'Excellent', status: '✓ Excellent', badge: 'good' },
    ai_agreement: { score_pct: 90.4, rating: 'Excellent', status: '✓ Excellent', badge: 'good' },
    sim_fidelity: { score_pct: 74.4, rating: 'Moderate', status: '⚠ Moderate', badge: 'warn' },
    cross_model_agreement: { score_pct: 82.2, rating: 'Good', status: '✓ Strong', badge: 'good' },
    uncertainty_quality: { score_pct: 17.4, rating: 'Poor', status: '⚠ Needs Improvement', badge: 'bad' },
  };

  const weights = reliability.weights || {
    data_completeness: 0.15,
    domain_similarity: 0.15,
    ai_agreement: 0.25,
    sim_fidelity: 0.20,
    cross_model_agreement: 0.10,
    uncertainty_quality: 0.15,
  };

  const titles = {
    data_completeness: 'Data Completeness',
    domain_similarity: 'Domain Similarity',
    ai_agreement: 'AI Prediction Accuracy',
    sim_fidelity: 'Physics Model Fidelity',
    cross_model_agreement: 'AI vs Physics Agreement',
    uncertainty_quality: 'Uncertainty Calibration',
  };

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Reliability Component Audit</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
            Weighted multi-pillar verification framework
          </p>
        </div>
        {reliability.reliability_warning && (
          <span className="badge badge-warn">
            {reliability.reliability_warning}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
        {Object.entries(components).map(([key, item]) => {
          const w = (weights[key] || 0) * 100;
          const badgeClass = item.badge === 'good' ? 'badge-good' : item.badge === 'warn' ? 'badge-warn' : 'badge-bad';
          const progressColor = item.badge === 'good' ? 'var(--good)' : item.badge === 'warn' ? 'var(--warn)' : 'var(--bad)';

          return (
            <div
              key={key}
              style={{
                background: '#0D1114',
                border: '1px solid var(--panel-border)',
                borderRadius: '8px',
                padding: '14px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600 }}>{titles[key] || key}</span>
                <span className={`badge ${badgeClass}`}>{item.rating}</span>
              </div>

              {/* Progress Bar */}
              <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '4px', height: '6px', overflow: 'hidden', margin: '8px 0' }}>
                <div
                  style={{
                    width: `${Math.min(100, Math.max(0, item.score_pct))}%`,
                    height: '100%',
                    background: progressColor,
                    borderRadius: '4px',
                    transition: 'width 0.4s ease'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--muted)' }} className="mono">
                <span>Score: {item.score_pct}%</span>
                <span>Weight: {w}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
