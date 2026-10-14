/**
 * StatusPanel Component — Status Distribution
 * Matches Garment Backoffice HTML template design
 */

import React from 'react';

interface StatusItem {
  label: string;
  count: number;
}

interface StatusPanelProps {
  title: string;
  subtitle: string;
  items: StatusItem[];
}

const StatusPanel: React.FC<StatusPanelProps> = ({ title, subtitle, items }) => {
  const total = items.reduce((sum, item) => sum + item.count, 0) || 1;

  return (
    <section className="surface bg-white border border-[#e6e6e9] rounded-[18px] p-5">
      <h2 className="text-[17px] font-semibold tracking-[-0.02em] text-[#1d1d1f]">
        {title}
      </h2>
      <p className="text-[#6e6e73] text-xs mt-1 mb-6">{subtitle}</p>

      <div id="status-summary" className="space-y-4">
        {items.map((item, idx) => {
          const widthPercent = (item.count / total) * 100;

          return (
            <div key={idx}>
              {/* Label and count */}
              <div className="flex justify-between text-sm mb-2">
                <span className="text-[#1d1d1f]">{item.label}</span>
                <strong className="font-semibold text-[#1d1d1f]">{item.count}</strong>
              </div>

              {/* Progress bar */}
              <div className="mini-line h-[7px] bg-[#ededf0] rounded-full overflow-hidden">
                <span
                  className="block h-full bg-[#0071e3] rounded-full transition-all duration-300"
                  style={{ width: `${widthPercent}%` }}
                  role="presentation"
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default StatusPanel;
