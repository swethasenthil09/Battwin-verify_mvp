import React from 'react';
import { AlertTriangle, TrendingUp, Clock, Activity, BarChart3, Target } from 'lucide-react';

/**
 * Late-Life Prediction Reliability Analysis Page.
 *
 * Visualizes phase-segmented error metrics, EOL detection delay,
 * drift onset, and hypothesis evaluation for the selected battery.
 */
export default function LateLifePage({ lateLifeData, selectedBattery }) {
  if (!lateLifeData) {
    return <div className="glass-panel">Loading late-life analysis data...</div>;
  }

  const phases = lateLifeData.phase_metrics || {};
  const eol = lateLifeData.eol_detection_delay || {};
  const drift = lateLifeData.drift_onset || {};
  const hypothesis = lateLifeData.hypothesis_evaluation || {};
  const overest = lateLifeData.late_life_overestimation || {};
  const amplification = lateLifeData.error_amplification_factor;

  const phaseOrder = ['early', 'mid', 'late'];
  const phaseLabels = { early: 'Early Life', mid: 'Mid Life', late: 'Late Life' };
  const phaseColors = { early: '#4FD1C5', mid: '#6366F1', late: '#EF4444' };

  // Find the max MAE across phases for chart scaling
  const maxMae = Math.max(
    ...phaseOrder.map((p) => phases[p]?.mae ?? 0),
    0.01
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* Hypothesis Banner */}
      <div
        className="glass-panel"
        style={{
          borderLeft: `6px solid ${hypothesis.supported ? '#EF4444' : '#4FD1C5'}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
          <AlertTriangle size={22} style={{ color: hypothesis.supported ? '#EF4444' : '#4FD1C5' }} />
          <h3 style={{ fontSize: '18px', fontWeight: 700 }}>
            Late-Life Prediction Reliability — {selectedBattery}
          </h3>
          <span
            className={`badge ${hypothesis.supported ? 'badge-bad' : 'badge-good'}`}
            style={{ marginLeft: 'auto', fontSize: '12px', padding: '4px 12px' }}
          >
            {hypothesis.supported
              ? `HYPOTHESIS SUPPORTED (${hypothesis.criteria_met}/${hypothesis.criteria_total})`
              : `NOT SUPPORTED (${hypothesis.criteria_met}/${hypothesis.criteria_total})`}
          </span>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.5, marginBottom: '8px' }}>
          <strong>Hypothesis:</strong> {hypothesis.hypothesis}
        </p>
        <p style={{ fontSize: '13px', color: 'var(--muted)', lineHeight: 1.5 }}>
          <strong>Conclusion:</strong> {hypothesis.conclusion}
        </p>
      </div>

      {/* Phase-Segmented Error Metrics — 3-column grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
        {phaseOrder.map((phase) => {
          const m = phases[phase] || {};
          const barPct = m.mae != null ? Math.min((m.mae / maxMae) * 100, 100) : 0;
          return (
            <div
              className="glass-panel"
              key={phase}
              style={{ borderTop: `4px solid ${phaseColors[phase]}` }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <BarChart3 size={16} style={{ color: phaseColors[phase] }} />
                <h4 style={{ fontSize: '14px', fontWeight: 700, color: phaseColors[phase] }}>
                  {phaseLabels[phase]}
                </h4>
                <span style={{ fontSize: '11px', color: 'var(--muted)', marginLeft: 'auto' }} className="mono">
                  {m.n_cycles ?? 0} cycles
                </span>
              </div>

              {m.cycle_range && (
                <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '10px' }} className="mono">
                  Cycles {m.cycle_range[0]} – {m.cycle_range[1]}
                </div>
              )}

              {/* MAE Bar */}
              <div style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>
                  <span>MAE</span>
                  <span className="mono" style={{ color: phaseColors[phase], fontWeight: 700 }}>
                    {m.mae != null ? `${m.mae.toFixed(3)}%` : '—'}
                  </span>
                </div>
                <div style={{ height: '8px', background: '#0D1114', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${barPct}%`,
                      height: '100%',
                      background: phaseColors[phase],
                      borderRadius: '4px',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>

              {/* Metric Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                <MetricCell label="RMSE" value={m.rmse != null ? `${m.rmse.toFixed(3)}%` : '—'} />
                <MetricCell label="Bias" value={m.signed_bias != null ? `${m.signed_bias >= 0 ? '+' : ''}${m.signed_bias.toFixed(3)}%` : '—'}
                  color={m.signed_bias > 0 ? '#EF4444' : m.signed_bias < 0 ? '#4FD1C5' : 'var(--text)'} />
                <MetricCell label="Max Error" value={m.max_abs_error != null ? `${m.max_abs_error.toFixed(3)}%` : '—'} />
                <MetricCell label="Overest." value={m.overestimation_rate != null ? `${(m.overestimation_rate * 100).toFixed(1)}%` : '—'}
                  color={m.overestimation_rate > 0.7 ? '#EF4444' : 'var(--text)'} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom row: EOL Delay + Drift Onset + Amplification */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>

        {/* EOL Detection Delay */}
        <div className="glass-panel" style={{ borderLeft: '4px solid #F59E0B' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Clock size={18} style={{ color: '#F59E0B' }} />
            <h4 style={{ fontSize: '14px', fontWeight: 700 }}>EOL Detection Delay</h4>
          </div>

          {eol.actual_permanent_eol_cycle != null ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '8px' }}>
                <span className="mono" style={{
                  fontSize: '28px', fontWeight: 700,
                  color: eol.detection_delay_cycles > 0 ? '#EF4444'
                    : eol.detection_delay_cycles === 0 ? '#4FD1C5'
                    : '#F59E0B',
                }}>
                  {eol.detection_delay_cycles != null
                    ? (eol.detection_delay_is_lower_bound ? '≥' : (eol.detection_delay_cycles > 0 ? '+' : '')) + eol.detection_delay_cycles
                    : '—'}
                </span>
                <span style={{ fontSize: '13px', color: 'var(--muted)' }}>cycles</span>
              </div>

              <div style={{ fontSize: '11px', color: 'var(--muted)', display: 'flex', flexDirection: 'column', gap: '4px' }} className="mono">
                <span>Actual Perm. EOL: <strong style={{ color: 'var(--text)' }}>Cycle {eol.actual_permanent_eol_cycle}</strong></span>
                <span>Actual First Touch: <strong style={{ color: 'var(--text)' }}>{eol.actual_first_touch_eol_cycle != null ? `Cycle ${eol.actual_first_touch_eol_cycle}` : 'N/A'}</strong></span>
                <span>Predicted Perm. EOL: <strong style={{ color: 'var(--text)' }}>{eol.predicted_permanent_eol_cycle != null ? `Cycle ${eol.predicted_permanent_eol_cycle}` : 'Never crossed'}</strong></span>
                <span>Predicted First Touch: <strong style={{ color: 'var(--text)' }}>{eol.predicted_first_touch_eol_cycle != null ? `Cycle ${eol.predicted_first_touch_eol_cycle}` : 'Never crossed'}</strong></span>
              </div>
            </div>
          ) : (
            <p style={{ fontSize: '12px', color: 'var(--muted)' }}>
              Battery did not reach permanent EOL within recorded data.
            </p>
          )}

          <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '10px', lineHeight: 1.4 }}>
            {eol.delay_interpretation}
          </p>
        </div>

        {/* Drift Onset */}
        <div className="glass-panel" style={{ borderLeft: '4px solid #A78BFA' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <TrendingUp size={18} style={{ color: '#A78BFA' }} />
            <h4 style={{ fontSize: '14px', fontWeight: 700 }}>Drift Onset Detection</h4>
          </div>

          {drift.drift_onset_cycle != null ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '8px' }}>
                <span className="mono" style={{ fontSize: '28px', fontWeight: 700, color: '#A78BFA' }}>
                  Cycle {drift.drift_onset_cycle}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }} className="mono">
                {drift.drift_onset_lifecycle_pct != null
                  ? `${(drift.drift_onset_lifecycle_pct * 100).toFixed(1)}% of lifecycle`
                  : ''}
              </div>
            </div>
          ) : (
            <div>
              <span className="mono" style={{ fontSize: '18px', fontWeight: 700, color: '#4FD1C5' }}>
                No systematic drift
              </span>
            </div>
          )}

          <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '8px', lineHeight: 1.4 }}>
            {drift.note}
          </p>

          {drift.parameters && (
            <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '8px', borderTop: '1px solid var(--panel-border)', paddingTop: '6px' }} className="mono">
              Window: {drift.parameters.rolling_window} cycles |
              Sustained: {drift.parameters.sustained_count} |
              σ: {drift.parameters.threshold_sigma}
            </div>
          )}
        </div>

        {/* Error Amplification & Late-Life Overestimation */}
        <div className="glass-panel" style={{ borderLeft: '4px solid #EF4444' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Activity size={18} style={{ color: '#EF4444' }} />
            <h4 style={{ fontSize: '14px', fontWeight: 700 }}>Late-Life Overestimation</h4>
          </div>

          {amplification != null && (
            <div style={{ marginBottom: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--muted)' }}>Error Amplification Factor</span>
              <div className="mono" style={{
                fontSize: '28px', fontWeight: 700,
                color: amplification > 1.5 ? '#EF4444' : amplification > 1.0 ? '#F59E0B' : '#4FD1C5',
              }}>
                {amplification.toFixed(2)}×
              </div>
              <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
                Late MAE ÷ Early MAE
              </span>
            </div>
          )}

          {overest && overest.n_late_cycles != null && (
            <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }} className="mono">
              <span style={{ color: 'var(--muted)' }}>
                Rate: <strong style={{ color: overest.overestimation_rate > 0.7 ? '#EF4444' : 'var(--text)' }}>
                  {(overest.overestimation_rate * 100).toFixed(1)}%
                </strong> of late-life cycles
              </span>
              <span style={{ color: 'var(--muted)' }}>
                Mean: <strong style={{ color: '#EF4444' }}>+{overest.mean_overestimation_pct?.toFixed(2)}%</strong> SoH
              </span>
              <span style={{ color: 'var(--muted)' }}>
                Max: <strong style={{ color: '#EF4444' }}>+{overest.max_overestimation_pct?.toFixed(2)}%</strong> SoH
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Hypothesis Findings Detail */}
      {hypothesis.findings && hypothesis.findings.length > 0 && (
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Target size={18} style={{ color: 'var(--ai)' }} />
            <h4 style={{ fontSize: '14px', fontWeight: 700 }}>Detailed Findings</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {hypothesis.findings.map((finding, idx) => (
              <div
                key={idx}
                style={{
                  fontSize: '12px',
                  color: 'var(--text)',
                  padding: '10px 14px',
                  background: '#0D1114',
                  border: '1px solid var(--panel-border)',
                  borderRadius: '6px',
                  lineHeight: 1.5,
                }}
              >
                <span style={{ color: 'var(--ai)', fontWeight: 700, marginRight: '8px' }}>
                  #{idx + 1}
                </span>
                {finding}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCell({ label, value, color }) {
  return (
    <div style={{ background: '#0D1114', borderRadius: '6px', padding: '8px 10px' }}>
      <div style={{ fontSize: '10px', color: 'var(--muted)', marginBottom: '2px' }}>{label}</div>
      <div className="mono" style={{ fontSize: '13px', fontWeight: 700, color: color || 'var(--text)' }}>
        {value}
      </div>
    </div>
  );
}
