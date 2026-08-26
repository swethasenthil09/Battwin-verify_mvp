import React from 'react';
import PredictForm from '../components/PredictForm';
import { Cpu, Terminal } from 'lucide-react';

export default function InferencePage({ isLive }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="glass-panel" style={{ borderLeft: '4px solid var(--ai)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu size={24} style={{ color: 'var(--ai)' }} />
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Real-Time Inference Engine</h3>
            <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '2px' }}>
              Execute the live XGBoost regressor model (`data/soh_model.joblib`) on custom operating feature vectors.
            </p>
          </div>
        </div>
      </div>

      <PredictForm isLive={isLive} />
    </div>
  );
}
