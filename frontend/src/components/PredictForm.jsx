import React, { useState } from 'react';
import { Play, Sparkles, AlertCircle, CheckCircle } from 'lucide-react';

export default function PredictForm({ isLive }) {
  const [formData, setFormData] = useState({
    discharge_cycle_index: 80,
    ambient_temperature_C: 24.0,
    voltage_mean: 3.52,
    voltage_min: 2.71,
    voltage_max: 4.19,
    current_mean: -1.48,
    current_min: -1.98,
    temperature_mean: 29.4,
    temperature_max: 33.2,
    discharge_duration_s: 3450.0,
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: parseFloat(value) || 0,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch('http://localhost:8000/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Prediction request failed' }));
        throw new Error(errData.detail || 'Inference error');
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Could not connect to FastAPI live backend at http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel glow-accent" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={18} style={{ color: 'var(--ai)' }} />
            Live AI Model Inference (`/api/predict`)
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
            Test the live XGBoost model on custom per-cycle operating inputs (on-demand execution)
          </p>
        </div>
        <span className={`badge ${isLive ? 'badge-good' : 'badge-warn'}`}>
          {isLive ? 'ONLINE -- LIVE INFERENCE READY' : 'BACKEND OFFLINE'}
        </span>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Cycle Index
            </label>
            <input
              type="number"
              name="discharge_cycle_index"
              value={formData.discharge_cycle_index}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Ambient Temp (°C)
            </label>
            <input
              type="number"
              step="0.1"
              name="ambient_temperature_C"
              value={formData.ambient_temperature_C}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Voltage Mean (V)
            </label>
            <input
              type="number"
              step="0.01"
              name="voltage_mean"
              value={formData.voltage_mean}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Voltage Min (V)
            </label>
            <input
              type="number"
              step="0.01"
              name="voltage_min"
              value={formData.voltage_min}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Voltage Max (V)
            </label>
            <input
              type="number"
              step="0.01"
              name="voltage_max"
              value={formData.voltage_max}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Current Mean (A)
            </label>
            <input
              type="number"
              step="0.01"
              name="current_mean"
              value={formData.current_mean}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Current Min (A)
            </label>
            <input
              type="number"
              step="0.01"
              name="current_min"
              value={formData.current_min}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Temp Mean (°C)
            </label>
            <input
              type="number"
              step="0.1"
              name="temperature_mean"
              value={formData.temperature_mean}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Temp Max (°C)
            </label>
            <input
              type="number"
              step="0.1"
              name="temperature_max"
              value={formData.temperature_max}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Duration (s)
            </label>
            <input
              type="number"
              step="10"
              name="discharge_duration_s"
              value={formData.discharge_duration_s}
              onChange={handleChange}
              className="form-input mono"
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button type="submit" className="btn-primary" disabled={loading}>
            <Play size={16} />
            {loading ? 'Running XGBoost Inference...' : 'Run Live Prediction'}
          </button>
        </div>
      </form>

      {/* Output Display */}
      {result && (
        <div style={{
          marginTop: '16px',
          background: 'rgba(79, 209, 197, 0.08)',
          border: '1px solid rgba(79, 209, 197, 0.3)',
          borderRadius: '8px',
          padding: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <CheckCircle size={24} style={{ color: 'var(--ai)' }} />
          <div>
            <span style={{ fontSize: '12px', color: 'var(--muted)' }}>LIVE INFERENCE RESULT:</span>
            <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--ai)' }} className="mono">
              Predicted SoH: {result.predicted_soh_pct}%
            </div>
            <span style={{ fontSize: '11px', color: 'var(--muted)' }}>{result.note}</span>
          </div>
        </div>
      )}

      {error && (
        <div style={{
          marginTop: '16px',
          background: 'rgba(248, 113, 113, 0.08)',
          border: '1px solid rgba(248, 113, 113, 0.3)',
          borderRadius: '8px',
          padding: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <AlertCircle size={24} style={{ color: 'var(--bad)' }} />
          <div>
            <span style={{ fontSize: '12px', color: 'var(--bad)', fontWeight: 600 }}>INFERENCE ERROR</span>
            <p style={{ fontSize: '12px', color: 'var(--text)', marginTop: '2px' }}>{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
