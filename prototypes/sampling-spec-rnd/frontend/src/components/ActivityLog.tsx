/**
 * ActivityLog — recent activity feed
 * High-contrast titles + time labels
 */
import React from 'react';
import { LucideIcon } from './Sidebar';

export interface Activity {
  icon: string;
  title: string;
  detail: string;
  time: string;
}

interface ActivityLogProps {
  title: string;
  subtitle: string;
  activities: Activity[];
}

const ActivityLog: React.FC<ActivityLogProps> = ({ title, subtitle, activities }) => (
  <section className="surface bg-white border border-[#e2e8f0] rounded-[18px] p-5">
    <h2 className="text-[16px] font-bold text-[#0f172a]">{title}</h2>
    <p className="text-[12px] font-medium text-[#64748b] mt-0.5 mb-4">{subtitle}</p>

    <div className="space-y-0 divide-y divide-[#f1f5f9]">
      {activities.length > 0 ? activities.map((a, idx) => (
        <div key={idx} className="flex gap-3 py-3 first:pt-0 last:pb-0">
          <div className="w-8 h-8 rounded-[10px] bg-[#eff6ff] flex items-center justify-center shrink-0">
            <LucideIcon name={a.icon} className="w-[15px] h-[15px] text-[#1d4ed8]" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[13px] font-semibold text-[#0f172a] leading-tight">{a.title}</p>
            <p className="text-[11.5px] font-medium text-[#64748b] mt-0.5">{a.detail}</p>
          </div>
          <span className="text-[11px] font-semibold text-[#94a3b8] whitespace-nowrap pt-0.5">
            {a.time}
          </span>
        </div>
      )) : (
        <p className="text-[13px] font-medium text-[#94a3b8] text-center py-6">
          Belum ada aktivitas terbaru.
        </p>
      )}
    </div>
  </section>
);

export default ActivityLog;
