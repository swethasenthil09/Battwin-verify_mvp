import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Database, Search } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function AnalyticsPage({ analysis, selectedBattery }) {
  const [searchTerm, setSearchTerm] = useState('');

  if (!analysis || analysis.length === 0) {
    return <div className="glass-panel">Loading cycle telemetry analytics...</div>;
  }

  const labels = analysis.map((d) => `C${d.discharge_cycle_index}`);
  const socData = analysis.map((d) => d.coulomb_counting_soc_pct ?? 100.0);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Coulomb Counting State of Charge (SoC %)',
        data: socData,
        borderColor: '#6366F1',
        backgroundColor: '#6366F1',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#E7E9EC', font: { family: 'Space Grotesk', size: 12 } },
      },
      tooltip: {
        backgroundColor: '#12161B',
        borderColor: '#232A31',
        borderWidth: 1,
        titleColor: '#6366F1',
        bodyColor: '#E7E9EC',
        titleFont: { family: 'IBM Plex Mono' },
        bodyFont: { family: 'IBM Plex Mono' },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(35, 42, 49, 0.6)' },
        ticks: { color: '#7C8590', font: { family: 'IBM Plex Mono', size: 11 }, maxTicksLimit: 12 },
      },
      y: {
        grid: { color: 'rgba(35, 42, 49, 0.6)' },
        ticks: { color: '#7C8590', font: { family: 'IBM Plex Mono', size: 11 } },
        title: {
          display: true,
          text: 'State of Charge (SoC %)',
          color: '#7C8590',
          font: { family: 'Space Grotesk', size: 12 },
        },
      },
    },
  };

  const filteredData = analysis.filter((row) =>
    row.discharge_cycle_index.toString().includes(searchTerm)
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* SoC Coulomb Counting Chart */}
      <div className="glass-panel" style={{ height: '340px', display: 'flex', flexDirection: 'column' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>
          State of Charge (SoC) Coulomb Counting Decay Trace — {selectedBattery}
        </h3>
        <div style={{ flex: 1, position: 'relative' }}>
          <Line data={chartData} options={options} />
        </div>
      </div>

      {/* Cycle Telemetry Datatable */}
      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={18} style={{ color: 'var(--ai)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Battery Telemetry Datatable ({filteredData.length} cycles)</h3>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#0D1114', border: '1px solid var(--panel-border)', borderRadius: '6px', padding: '4px 10px' }}>
            <Search size={14} style={{ color: 'var(--muted)' }} />
            <input
              type="text"
              placeholder="Search cycle index..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="mono"
              style={{ background: 'transparent', border: 'none', color: 'var(--text)', outline: 'none', fontSize: '12px' }}
            />
          </div>
        </div>

        <div style={{ overflowX: 'auto', maxHeight: '420px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }} className="mono">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--panel-border)', color: 'var(--muted)', background: '#0D1114' }}>
                <th style={{ padding: '10px 12px' }}>Cycle</th>
                <th style={{ padding: '10px 12px' }}>Observed SoH (%)</th>
                <th style={{ padding: '10px 12px' }}>AI SoH (%)</th>
                <th style={{ padding: '10px 12px' }}>Physics SoH (%)</th>
                <th style={{ padding: '10px 12px' }}>SoC (%)</th>
                <th style={{ padding: '10px 12px' }}>Volt Mean (V)</th>
                <th style={{ padding: '10px 12px' }}>Curr Mean (A)</th>
                <th style={{ padding: '10px 12px' }}>Temp Mean (°C)</th>
                <th style={{ padding: '10px 12px' }}>Duration (s)</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.slice(0, 100).map((row, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(35, 42, 49, 0.4)' }}>
                  <td style={{ padding: '8px 12px', color: 'var(--ai)', fontWeight: 'bold' }}>C{row.discharge_cycle_index}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--measured)' }}>{row.SoH_pct !== undefined ? row.SoH_pct.toFixed(2) : row.observed_soh_pct.toFixed(2)}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--ai)' }}>{row.SoH_pred !== undefined ? row.SoH_pred.toFixed(2) : row.predicted_soh_pct.toFixed(2)}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--physics)' }}>{row.physics_SoH_pred !== undefined ? row.physics_SoH_pred.toFixed(2) : row.physics_soh_pct.toFixed(2)}</td>
                  <td style={{ padding: '8px 12px', color: '#6366F1' }}>{row.coulomb_counting_soc_pct !== undefined ? row.coulomb_counting_soc_pct.toFixed(1) : '100.0'}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>{row.voltage_mean ? row.voltage_mean.toFixed(2) : '3.50'}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>{row.current_mean ? row.current_mean.toFixed(2) : '-1.50'}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>{row.temperature_mean ? row.temperature_mean.toFixed(1) : '25.0'}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>{row.discharge_duration_s ? row.discharge_duration_s.toFixed(0) : '3600'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
