/**
 * StatusPanel — status distribution with progress bars
 * High-contrast labels + animated gradient bars
 */
import React from 'react';

interface StatusItem { label: string; count: number; }

interface StatusPanelProps {
  title: string;
  subtitle: string;
  items: StatusItem[];
}

const BAR_COLORS = [
  'linear-gradient(90deg,#0071e3 0%,#38bdf8 100%)',
  'linear-gradient(90deg,#16a34a 0%,#4ade80 100%)',
  'linear-gradient(90deg,#d97706 0%,#fbbf24 100%)',
  'linear-gradient(90deg,#dc2626 0%,#f87171 100%)',
];

const StatusPanel: React.FC<StatusPanelProps> = ({ title, subtitle, items }) => {
  const total = items.reduce((s, i) => s + i.count, 0) || 1;

  return (
    <section className="surface bg-white border border-[#e2e8f0] rounded-[18px] p-5 h-full">
      <h2 className="text-[16px] font-bold text-[#0f172a]">{title}</h2>
      <p className="text-[12px] font-medium text-[#64748b] mt-0.5 mb-6">{subtitle}</p>

      <div className="space-y-5">
        {items.map((item, idx) => {
          const pct = Math.round((item.count / total) * 100);
          return (
            <div key={idx}>
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-[13px] font-semibold text-[#334155]">{item.label}</span>
                <span className="text-[13px] font-bold text-[#0f172a]">{item.count}</span>
              </div>
              <div className="mini-line">
                <span style={{ width: `${pct}%`, background: BAR_COLORS[idx % BAR_COLORS.length] }} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default StatusPanel;
