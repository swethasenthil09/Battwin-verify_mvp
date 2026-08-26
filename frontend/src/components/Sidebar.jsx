import React from 'react';
import { Cpu, Battery, Wifi, LayoutDashboard, ShieldCheck, Database, Sparkles } from 'lucide-react';

export default function Sidebar({ selectedBattery, setSelectedBattery, activeTab, setActiveTab, isLive, batteries }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'reliability', label: 'Reliability & Audit', icon: ShieldCheck },
    { id: 'inference', label: 'Live AI Inference', icon: Cpu },
    { id: 'analytics', label: 'Battery & SoC Analytics', icon: Database },
    { id: 'explainability', label: 'Explainability & Domain', icon: Sparkles },
  ];


  return (
    <aside style={{
      width: '260px',
      background: 'rgba(18, 22, 27, 0.95)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      borderRight: '1px solid var(--panel-border)',
      padding: '24px 16px',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 100,
      justifySpace: 'space-between'
    }}>
      <div>
        {/* Brand Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', paddingLeft: '8px' }}>
          <Cpu style={{ color: 'var(--ai)' }} size={28} />
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.1 }}>
              BATTWIN<span style={{ color: 'var(--ai)' }}>-VERIFY</span>
            </h1>
            <span style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginTop: '2px' }}>
              Digital Twin Intelligence
            </span>
          </div>
        </div>

        {/* Battery Selector */}
        <div style={{
          background: '#0D1114',
          border: '1px solid var(--panel-border)',
          borderRadius: '8px',
          padding: '10px 12px',
          marginBottom: '24px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <Battery size={14} style={{ color: 'var(--ai)' }} />
            <span style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '0.05em', fontWeight: 600 }}>
              SELECT BATTERY
            </span>
          </div>
          <select
            value={selectedBattery}
            onChange={(e) => setSelectedBattery(e.target.value)}
            style={{
              width: '100%',
              background: 'transparent',
              color: 'var(--ai)',
              border: 'none',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer',
              outline: 'none'
            }}
            className="mono"
          >
            {batteries.map((b) => (
              <option key={b.battery_id} value={b.battery_id}>
                {b.battery_id} ({b.role.includes('held-out') ? 'Held-out' : 'Train'})
              </option>
            ))}
          </select>
        </div>

        {/* Navigation List */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '0.05em', fontWeight: 600, paddingLeft: '8px', marginBottom: '4px' }}>
            NAVIGATION
          </span>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '11px 14px',
                  borderRadius: '8px',
                  border: '1px solid',
                  borderColor: isActive ? 'rgba(79, 209, 197, 0.4)' : 'transparent',
                  background: isActive ? 'rgba(79, 209, 197, 0.12)' : 'transparent',
                  color: isActive ? 'var(--ai)' : 'var(--muted)',
                  fontWeight: isActive ? 700 : 500,
                  fontSize: '13px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={18} style={{ color: isActive ? 'var(--ai)' : 'var(--muted)' }} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Status Badge */}
      <div style={{
        background: '#0D1114',
        border: '1px solid var(--panel-border)',
        borderRadius: '8px',
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isLive ? <span className="pulse-dot" /> : <Wifi size={14} style={{ color: 'var(--warn)' }} />}
          <span style={{ fontSize: '11px', fontWeight: 700, color: isLive ? 'var(--good)' : 'var(--warn)' }} className="mono">
            {isLive ? 'LIVE BACKEND' : 'SNAPSHOT MODE'}
          </span>
        </div>
        <span style={{ fontSize: '10px', color: 'var(--muted)' }}>
          {isLive ? 'Connected to http://localhost:8000' : 'Offline embedded payload active'}
        </span>
      </div>
    </aside>
  );
}
