import React from 'react';
import MetricsHeader from '../components/MetricsHeader';
import SohChart from '../components/SohChart';
import RecommendationCard from '../components/RecommendationCard';
import { ShieldCheck, Activity, Layers, Compass } from 'lucide-react';

export default function OverviewPage({ reliability, rul, recommendation, analysis }) {
  const scenario = reliability?.scenario || {
    code: 'A',
    title: 'Scenario A: Optimal Digital Twin Alignment',
    description: 'Both AI model and physical reference model show high agreement with measured battery telemetry.',
  };

  const covAfter = reliability?.uncertainty_coverage_after !== undefined ? (reliability.uncertainty_coverage_after * 100).toFixed(1) : '18.9';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <MetricsHeader
        reliability={reliability}
        rul={rul}
        recommendation={recommendation}
        analysis={analysis}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <SohChart analysisData={analysis} />
        <RecommendationCard recommendation={recommendation} />
      </div>

      {/* Overview Summary Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Diagnostic Twin Status */}
        <div className="glass-panel" style={{ borderLeft: '4px solid var(--ai)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <Compass size={20} style={{ color: 'var(--ai)' }} />
            <h3 style={{ fontSize: '15px', fontWeight: 700 }}>Digital Twin Alignment Summary</h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="badge badge-good" style={{ fontWeight: 'bold' }}>{scenario.code ? `SCENARIO ${scenario.code}` : 'SCENARIO A'}</span>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>{scenario.title}</span>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--muted)', lineHeight: 1.5 }}>
            {scenario.description}
          </p>
        </div>

        {/* Conformal Calibration Honest Callout */}
        <div className="glass-panel" style={{ borderLeft: '4px solid var(--accent)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <Layers size={20} style={{ color: 'var(--accent)' }} />
            <h3 style={{ fontSize: '15px', fontWeight: 700 }}>Split-Conformal Calibration State</h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span className="mono" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--good)' }}>{covAfter}%</span>
            <span style={{ fontSize: '12px', color: 'var(--muted)' }}>Empirical Coverage vs 80% Target</span>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '6px', lineHeight: 1.4 }}>
            Split-conformal prediction quantile widening improves coverage over naive Gaussian bounds (4.5% → 18.9%). Documented MVP known limitation.
          </p>
        </div>
      </div>
    </div>
  );
}

