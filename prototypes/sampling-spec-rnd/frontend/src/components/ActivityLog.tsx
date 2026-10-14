/**
 * ActivityLog Component — Recent Activities
 * Matches Garment Backoffice HTML template design
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

const ActivityLog: React.FC<ActivityLogProps> = ({ title, subtitle, activities }) => {
  return (
    <section className="surface bg-white border border-[#e6e6e9] rounded-[18px] p-5">
      <h2 className="text-[17px] font-semibold tracking-[-0.02em] text-[#1d1d1f]">
        {title}
      </h2>
      <p className="text-[#6e6e73] text-xs mt-1 mb-5">{subtitle}</p>

      <div id="activity-list" className="space-y-0">
        {activities.length > 0 ? (
          activities.map((activity, idx) => (
            <div
              key={idx}
              className="flex gap-3 py-3 border-b border-[#f0f0f2] last:border-0"
            >
              {/* Icon */}
              <div className="w-8 h-8 rounded-lg bg-[#f5f5f7] flex items-center justify-center shrink-0">
                <LucideIcon name={activity.icon} className="w-4 h-4 text-[#0066cc]" />
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-[#1d1d1f]">{activity.title}</p>
                <p className="text-xs text-[#6e6e73] mt-1">{activity.detail}</p>
              </div>

              {/* Time */}
              <span className="text-xs text-[#6e6e73] whitespace-nowrap">
                {activity.time}
              </span>
            </div>
          ))
        ) : (
          <p className="text-sm text-[#6e6e73] text-center py-4">
            Belum ada aktivitas terbaru.
          </p>
        )}
      </div>
    </section>
  );
};

export default ActivityLog;
