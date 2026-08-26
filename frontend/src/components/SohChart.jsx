import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function SohChart({ analysisData }) {
  if (!analysisData || analysisData.length === 0) {
    return <div className="glass-panel">Loading cycle degradation analysis...</div>;
  }

  const labels = analysisData.map((d) => `C${d.discharge_cycle_index}`);

  const observed = analysisData.map((d) =>
    d.observed_soh_pct !== undefined ? d.observed_soh_pct : d.SoH_pct
  );
  const predicted = analysisData.map((d) =>
    d.predicted_soh_pct !== undefined ? d.predicted_soh_pct : d.SoH_pred
  );
  const physics = analysisData.map((d) =>
    d.physics_soh_pct !== undefined ? d.physics_soh_pct : d.physics_SoH_pred
  );

  // Uncertainty bounds if available in records
  const lowerBounds = analysisData.map((d) => d.lower80 ?? null);
  const upperBounds = analysisData.map((d) => d.upper80 ?? null);
  const hasBounds = lowerBounds.some((v) => v !== null);

  const datasets = [
    {
      label: 'Observed (Ground Truth)',
      data: observed,
      borderColor: '#F2EFE9',
      backgroundColor: '#F2EFE9',
      borderWidth: 2.5,
      pointRadius: 0,
      pointHoverRadius: 4,
      tension: 0.1,
    },
    {
      label: 'AI Model (XGBoost)',
      data: predicted,
      borderColor: '#4FD1C5',
      backgroundColor: '#4FD1C5',
      borderWidth: 2,
      borderDash: [4, 4],
      pointRadius: 0,
      pointHoverRadius: 4,
      tension: 0.1,
    },
    {
      label: 'Physics Reference Model',
      data: physics,
      borderColor: '#E8935B',
      backgroundColor: '#E8935B',
      borderWidth: 1.5,
      borderDash: [2, 2],
      pointRadius: 0,
      tension: 0.1,
    },
  ];

  if (hasBounds) {
    datasets.push({
      label: 'Upper 80% Conformal Bound',
      data: upperBounds,
      borderColor: 'rgba(99, 102, 241, 0.3)',
      borderWidth: 1,
      pointRadius: 0,
      fill: false,
    });
    datasets.push({
      label: 'Lower 80% Conformal Bound',
      data: lowerBounds,
      borderColor: 'rgba(99, 102, 241, 0.3)',
      backgroundColor: 'rgba(99, 102, 241, 0.12)',
      borderWidth: 1,
      pointRadius: 0,
      fill: '-1', // fill to upper bound
    });
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#E7E9EC',
          font: { family: 'Space Grotesk', size: 12 },
          usePointStyle: true,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: '#12161B',
        borderColor: '#232A31',
        borderWidth: 1,
        titleColor: '#4FD1C5',
        bodyColor: '#E7E9EC',
        titleFont: { family: 'IBM Plex Mono', weight: 'bold' },
        bodyFont: { family: 'IBM Plex Mono' },
        callbacks: {
          label: (context) => `${context.dataset.label}: ${context.parsed.y?.toFixed(2)}%`,
        },
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
          text: 'State of Health (SoH %)',
          color: '#7C8590',
          font: { family: 'Space Grotesk', size: 12 },
        },
      },
    },
  };

  return (
    <div className="glass-panel" style={{ height: '420px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
          Capacity Degradation Trajectory (SoH %)
        </h3>
        <span style={{ fontSize: '12px', color: 'var(--muted)' }} className="mono">
          EOL Threshold: 70.0%
        </span>
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        <Line data={{ labels, datasets }} options={options} />
      </div>
    </div>
  );
}
