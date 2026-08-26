import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import OverviewPage from './pages/OverviewPage';
import ReliabilityPage from './pages/ReliabilityPage';
import InferencePage from './pages/InferencePage';
import AnalyticsPage from './pages/AnalyticsPage';
import ExplainabilityPage from './pages/ExplainabilityPage';
import { EMBEDDED_DATA } from './data/embeddedData';

export default function App() {
  const [selectedBattery, setSelectedBattery] = useState('B0018');
  const [activeTab, setActiveTab] = useState('overview');
  const [isLive, setIsLive] = useState(false);
  const [batteries, setBatteries] = useState([
    { battery_id: 'B0018', role: 'held-out test battery', n_cycles: 132 },
    { battery_id: 'B0005', role: 'training battery', n_cycles: 168 },
    { battery_id: 'B0006', role: 'training battery', n_cycles: 168 },
    { battery_id: 'B0007', role: 'training battery', n_cycles: 168 },
    { battery_id: 'CALCE_CS2_35', role: 'cross-dataset evaluation', n_cycles: 150 },
  ]);


  const [analysisData, setAnalysisData] = useState([]);
  const [reliabilityData, setReliabilityData] = useState(null);
  const [rulData, setRulData] = useState(null);
  const [recommendationData, setRecommendationData] = useState(null);
  const [shapData, setShapData] = useState(null);
  const [calceData, setCalceData] = useState(null);
  const [ecmData, setEcmData] = useState(null);
  const [maskingData, setMaskingData] = useState(null);

  // Check live API server connection
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) {
          setIsLive(true);
        } else {
          setIsLive(false);
        }
      } catch (err) {
        setIsLive(false);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch data for selected battery
  useEffect(() => {
    let ignore = false;

    async function loadData() {
      if (isLive) {
        try {
          const [anRes, relRes, rulRes, recRes, shapRes, calceRes, ecmRes, maskRes] = await Promise.all([
            fetch(`http://localhost:8000/api/battery/${selectedBattery}/analysis`),
            fetch(`http://localhost:8000/api/battery/${selectedBattery}/reliability`),
            fetch(`http://localhost:8000/api/battery/${selectedBattery}/rul`),
            fetch(`http://localhost:8000/api/battery/${selectedBattery}/recommendation`),
            fetch(`http://localhost:8000/api/battery/${selectedBattery}/explainability`),
            fetch(`http://localhost:8000/api/domain-shift/cross-dataset`),
            fetch(`http://localhost:8000/api/battery/${selectedBattery}/ecm-simulation`),
            fetch(`http://localhost:8000/api/experiments/data-masking`),
          ]);

          if (!ignore && anRes.ok) setAnalysisData(await anRes.json());
          if (!ignore && relRes.ok) setReliabilityData(await relRes.json());
          if (!ignore && rulRes.ok) setRulData(await rulRes.json());
          if (!ignore && recRes.ok) setRecommendationData(await recRes.json());
          if (!ignore && shapRes.ok) setShapData(await shapRes.json());
          if (!ignore && calceRes.ok) setCalceData(await calceRes.json());
          if (!ignore && ecmRes.ok) setEcmData(await ecmRes.json());
          if (!ignore && maskRes.ok) setMaskingData(await maskRes.json());
          return;
        } catch (e) {
          console.warn('Live API fetch failed, falling back to embedded snapshot:', e);
        }
      }

      // Fallback: embedded snapshot data
      if (!ignore && EMBEDDED_DATA) {
        const key = selectedBattery.toLowerCase();
        setAnalysisData(EMBEDDED_DATA.analyses?.[selectedBattery] || EMBEDDED_DATA.full_analysis?.[key] || EMBEDDED_DATA.full_analysis?.b0018 || []);
        setReliabilityData(EMBEDDED_DATA.reliability?.[selectedBattery] || EMBEDDED_DATA.all_reliability?.[selectedBattery] || EMBEDDED_DATA.reliability_summary || null);
        setRulData(EMBEDDED_DATA.rul?.[selectedBattery] || EMBEDDED_DATA.all_rul?.[selectedBattery] || EMBEDDED_DATA.rul_summary || null);
        setRecommendationData(EMBEDDED_DATA.recommendations?.[selectedBattery] || EMBEDDED_DATA.recommendation || null);
        setShapData(EMBEDDED_DATA.shap_explainability || null);
        setCalceData(EMBEDDED_DATA.calce_domain_shift || null);
        setEcmData(EMBEDDED_DATA.ecm_physics || null);
        setMaskingData(EMBEDDED_DATA.data_masking_experiment || null);
      }
    }

    loadData();
    return () => {
      ignore = true;
    };
  }, [selectedBattery, isLive]);

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Left Sidebar Navigation */}
      <Sidebar
        selectedBattery={selectedBattery}
        setSelectedBattery={setSelectedBattery}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isLive={isLive}
        batteries={batteries}
      />

      {/* Main Right Content Panel */}
      <div style={{
        marginLeft: '260px',
        flex: 1,
        padding: '32px 40px',
        maxWidth: 'calc(100vw - 260px)',
        minHeight: '100vh',
        boxSizing: 'border-box'
      }}>
        <Navbar
          selectedBattery={selectedBattery}
          activeTab={activeTab}
          reliability={reliabilityData}
        />

        <main>
          {activeTab === 'overview' && (
            <OverviewPage
              reliability={reliabilityData}
              rul={rulData}
              recommendation={recommendationData}
              analysis={analysisData}
            />
          )}

          {activeTab === 'reliability' && (
            <ReliabilityPage reliability={reliabilityData} />
          )}

          {activeTab === 'inference' && (
            <InferencePage isLive={isLive} />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsPage analysis={analysisData} selectedBattery={selectedBattery} />
          )}

          {activeTab === 'explainability' && (
            <ExplainabilityPage
              shapData={shapData}
              calceData={calceData}
              ecmData={ecmData}
              maskingData={maskingData}
            />
          )}
        </main>

        <footer style={{
          marginTop: '40px',
          paddingTop: '16px',
          borderTop: '1px solid var(--panel-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '11px',
          color: 'var(--muted)',
          fontFamily: 'IBM Plex Mono, monospace',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <div>
            <span>Last Generated: <strong style={{ color: 'var(--text)' }}>2026-08-19 15:13 UTC</strong></span>
            <span style={{ margin: '0 8px' }}>|</span>
            <span>Pipeline Version: <strong style={{ color: 'var(--ai)' }}>v1.0.0-mvp-verified (hash: e4b89c7)</strong></span>
          </div>
          <div>
            <span>Dataset: <strong style={{ color: 'var(--text)' }}>NASA Ames PCoE / CALCE CS2</strong></span>
            <span style={{ margin: '0 8px' }}>|</span>
            <span>Engine: <strong style={{ color: 'var(--accent)' }}>XGBoost + 2-RC ECM Physics</strong></span>
          </div>
        </footer>
      </div>
    </div>
  );
}


