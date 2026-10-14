/**
 * Header Component — Search, Notifications, Profile
 * Matches Garment Backoffice HTML template design
 */

import React from 'react';
import { LucideIcon } from './Sidebar';

interface HeaderProps {
  title: string;
  subtitle?: string;
  caption?: string;
  globalSearch: string;
  onGlobalSearchChange: (value: string) => void;
  onNotificationsClick?: () => void;
  profileName?: string;
  profileInitials?: string;
}

const Header: React.FC<HeaderProps> = ({
  title,
  subtitle = 'DASHBOARD / OPERASIONAL',
  caption,
  globalSearch,
  onGlobalSearchChange,
  onNotificationsClick,
  profileName = 'Admin Produksi',
  profileInitials = 'AD',
}) => {
  return (
    <header className="header-row flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5 mb-8">
      {/* Left side - Title */}
      <div>
        <p className="text-xs font-semibold text-[#6e6e73] mb-1 uppercase tracking-wider">
          {subtitle}
        </p>
        <h1 className="text-[32px] font-semibold text-[#1d1d1f] tracking-tight leading-tight">
          {title}
        </h1>
        {caption && (
          <p className="text-[#6e6e73] text-sm mt-1" aria-live="polite">
            {caption}
          </p>
        )}
      </div>

      {/* Right side - Tools */}
      <div className="header-tools flex items-center gap-3 w-full lg:w-auto flex-wrap">
        {/* Search box */}
        <div className="searchbox relative flex-1 lg:flex-initial">
          <LucideIcon
            name="search"
            className="absolute left-3 top-3 w-4 h-4 text-[#86868b] pointer-events-none"
          />
          <label htmlFor="global-search" className="sr-only">
            Pencarian global
          </label>
          <input
            id="global-search"
            type="search"
            placeholder="Cari studi atau spec..."
            value={globalSearch}
            onChange={(e) => onGlobalSearchChange(e.target.value)}
            className="field pl-9 w-full lg:w-52 bg-white border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] min-h-[41px] focus:outline-2 focus:outline-[#80baff]"
          />
        </div>

        {/* Notifications */}
        {onNotificationsClick && (
          <button
            id="notifications"
            type="button"
            aria-label="Lihat aktivitas terbaru"
            onClick={onNotificationsClick}
            className="secondary border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] px-3 py-2.5 font-semibold text-[13px] inline-flex items-center justify-center hover:bg-[#f4f8fd] transition-colors"
          >
            <LucideIcon name="bell" className="w-4 h-4" />
          </button>
        )}

        {/* Profile */}
        <div className="flex items-center gap-2 pl-1">
          <span
            className="w-9 h-9 rounded-full bg-[#eaf3fe] text-[#0066cc] grid place-items-center text-xs font-semibold"
            aria-hidden="true"
          >
            {profileInitials}
          </span>
          <span className="text-sm font-medium text-[#1d1d1f] hidden lg:block">
            {profileName}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Header;
