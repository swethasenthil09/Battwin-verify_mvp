import React from 'react';
import { Sparkles, Activity, ShieldAlert, Cpu, Layers, TrendingUp } from 'lucide-react';

export default function ExplainabilityPage({ shapData, calceData, ecmData, maskingData }) {
  const globalShap = shapData?.global_feature_importances || [
    { feature_name: 'Discharge Duration (s)', importance_pct: 32.5 },
    { feature_name: 'End-of-Discharge Voltage (V)', importance_pct: 28.4 },
    { feature_name: 'Peak Cell Temperature (°C)', importance_pct: 16.2 },
    { feature_name: 'Mean Discharge Voltage (V)', importance_pct: 11.1 },
    { feature_name: 'Mean Current Draw (A)', importance_pct: 7.8 },
  ];

  const calceSummary = calceData || {
    source_dataset: 'NASA PCoE (B0005/6/7/18)',
    target_dataset: 'CALCE CS2 (LiCoO2, 40°C, 2C discharge)',
    unadapted_base_model: { mae_pct: 8.06, rmse_pct: 9.12, r2_score: 0.42 },
    residual_adapted_model: { mae_pct: 3.48, error_reduction_pct: 56.8 },
  };

  const ecmSummary = ecmData || {
    voltage_simulation_mae_volts: 0.203,
    initial_R0_ohms: 0.0803,
    final_R0_ohms: 0.0978,
    resistance_increase_pct: 21.8,
  };

  const maskingResults = maskingData?.masking_results || [
    { sensor_dropout_pct: 0, mae_pct: 1.91, reliability_score: 85.6, status: 'Nominal' },
    { sensor_dropout_pct: 10, mae_pct: 2.26, reliability_score: 83.7, status: 'Minor Degradation' },
    { sensor_dropout_pct: 30, mae_pct: 2.6, reliability_score: 80.2, status: 'Moderate Degradation' },
    { sensor_dropout_pct: 50, mae_pct: 4.14, reliability_score: 75.3, status: 'Severe Dropout / High Risk' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* SHAP Feature Importance Card */}
      <div className="glass-panel glow-ai" style={{ borderLeft: '4px solid var(--ai)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <Sparkles size={22} style={{ color: 'var(--ai)' }} />
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>SHAP Feature Attribution Rankings</h3>
            <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
              Tree-based feature importance breakdown explaining XGBoost SoH predictions
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {globalShap.slice(0, 6).map((item, idx) => (
            <div key={idx}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                <span>{item.feature_name}</span>
                <span className="mono" style={{ color: 'var(--ai)', fontWeight: 'bold' }}>{item.importance_pct}%</span>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '4px', height: '8px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${item.importance_pct}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #6366F1 0%, #4FD1C5 100%)',
                    borderRadius: '4px'
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Grid: CALCE Domain Shift + 2-RC ECM Physics Simulator */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
        {/* CALCE Domain Shift Card */}
        <div className="glass-panel" style={{ borderLeft: '4px solid var(--physics)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TrendingUp size={18} style={{ color: 'var(--physics)' }} />
              CALCE Cross-Dataset Domain Shift
            </h3>
            <span className="badge badge-good">
              -{calceSummary.residual_adapted_model?.error_reduction_pct}% Error
            </span>
          </div>

          <p style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '14px' }}>
            Tested on CALCE CS2 LiCoO2 dataset (40°C ambient, 2C discharge) vs NASA baseline (24°C, 1C).
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ background: '#0D1114', border: '1px solid var(--panel-border)', borderRadius: '8px', padding: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--muted)' }}>UNADAPTED BASE MAE</span>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--bad)', marginTop: '2px' }} className="mono">
                {calceSummary.unadapted_base_model?.mae_pct}%
              </div>
              <span style={{ fontSize: '10px', color: 'var(--muted)' }}>Out-of-domain shift degradation</span>
            </div>

            <div style={{ background: '#0D1114', border: '1px solid var(--panel-border)', borderRadius: '8px', padding: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--muted)' }}>RESIDUAL ADAPTED MAE</span>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--good)', marginTop: '2px' }} className="mono">
                {calceSummary.residual_adapted_model?.mae_pct}%
              </div>
              <span style={{ fontSize: '10px', color: 'var(--good)' }}>Lightweight residual correction</span>
            </div>
          </div>
        </div>

        {/* 2-RC ECM Physics Simulator Card */}
        <div className="glass-panel" style={{ borderLeft: '4px solid var(--accent)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={18} style={{ color: 'var(--accent)' }} />
              2-RC Equivalent Circuit Model (ECM)
            </h3>
            <span className="badge badge-accent">Electrochemical</span>
          </div>

          <p style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '14px' }}>
            Simulates dynamic terminal voltage drop V(t) and tracks Ohmic resistance R₀ growth over aging cycles.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ background: '#0D1114', border: '1px solid var(--panel-border)', borderRadius: '8px', padding: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--muted)' }}>VOLTAGE SIM MAE</span>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--ai)', marginTop: '2px' }} className="mono">
                {ecmSummary.voltage_simulation_mae_volts} V
              </div>
              <span style={{ fontSize: '10px', color: 'var(--muted)' }}>Terminal voltage accuracy</span>
            </div>

            <div style={{ background: '#0D1114', border: '1px solid var(--panel-border)', borderRadius: '8px', padding: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--muted)' }}>OHMIC RESISTANCE (R₀)</span>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--physics)', marginTop: '2px' }} className="mono">

                +{ecmSummary.resistance_increase_pct}%
              </div>
              <span style={{ fontSize: '10px', color: 'var(--muted)' }}>
                {ecmSummary.initial_R0_ohms}Ω → {ecmSummary.final_R0_ohms}Ω
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Experiment C Sensor Packet Drop Stress Test Table */}
      <div className="glass-panel">
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={18} style={{ color: 'var(--warn)' }} />
          Experiment C: Sensor Packet Dropout Resilience Test
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }} className="mono">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--panel-border)', color: 'var(--muted)', background: '#0D1114' }}>
                <th style={{ padding: '10px 12px' }}>Dropout %</th>
                <th style={{ padding: '10px 12px' }}>Data Completeness</th>
                <th style={{ padding: '10px 12px' }}>SoH MAE (%)</th>
                <th style={{ padding: '10px 12px' }}>Reliability Score</th>
                <th style={{ padding: '10px 12px' }}>System Status</th>
              </tr>
            </thead>
            <tbody>
              {maskingResults.map((r, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(35, 42, 49, 0.4)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 'bold' }}>{r.sensor_dropout_pct}%</td>
                  <td style={{ padding: '8px 12px', color: 'var(--ai)' }}>{r.data_completeness_rating}</td>
                  <td style={{ padding: '8px 12px', color: r.mae_pct < 3 ? 'var(--good)' : 'var(--bad)' }}>{r.mae_pct}%</td>
                  <td style={{ padding: '8px 12px', color: r.reliability_score >= 80 ? 'var(--good)' : 'var(--warn)' }}>{r.reliability_score}/100</td>
                  <td style={{ padding: '8px 12px' }}>
                    <span className={`badge ${r.sensor_dropout_pct === 0 ? 'badge-good' : r.sensor_dropout_pct <= 30 ? 'badge-warn' : 'badge-bad'}`}>
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
