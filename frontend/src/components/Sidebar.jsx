import React from 'react';

const NAV_ITEMS = [
  { id: 'upload',    icon: '📁', label: 'Docs'  },
  { id: 'chat',      icon: '💬', label: 'Chat'  },
  { id: 'testgen',   icon: '🧪', label: 'Tests' },
  { id: 'sources',   icon: '🔍', label: 'Sources' },
];

export default function Sidebar({ activePanel, setActivePanel }) {
  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      {/* Logo */}
      <div className="sidebar-logo" title="ERP Copilot Lite">🤖</div>
      <div className="sidebar-divider" />

      {/* Nav items */}
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          id={`nav-${item.id}`}
          className={`nav-item ${activePanel === item.id ? 'active' : ''}`}
          onClick={() => setActivePanel(item.id)}
          title={item.label}
          aria-label={item.label}
          aria-current={activePanel === item.id ? 'page' : undefined}
        >
          <span>{item.icon}</span>
          <span className="nav-label">{item.label}</span>
        </button>
      ))}

      {/* Bottom — version */}
      <div className="sidebar-bottom">
        <div className="sidebar-divider" />
        <div
          style={{
            fontSize: '9px',
            color: 'var(--text-muted)',
            textAlign: 'center',
            fontWeight: 600,
            letterSpacing: '0.5px',
          }}
        >
          v1.0
        </div>
      </div>
    </aside>
  );
}
