/**
 * Header — page title + search + profile
 * High-contrast text, animated search field and bell button
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
}) => (
  <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5 mb-8">
    {/* Title block */}
    <div>
      <p className="text-[11px] font-bold uppercase tracking-[.14em] text-[#64748b] mb-1">
        {subtitle}
      </p>
      <h1 className="text-[30px] font-bold text-[#0f172a] tracking-tight leading-tight">
        {title}
      </h1>
      {caption && (
        <div className="flex items-center gap-2 mt-1.5">
          {caption.startsWith('Backend terhubung') && (
            <span className="pulse-dot" aria-hidden="true" />
          )}
          <p
            className={`text-[13px] font-medium ${
              caption.startsWith('Backend terhubung') ? 'text-[#15803d]' : 'text-[#dc2626]'
            }`}
            aria-live="polite"
          >
            {caption}
          </p>
        </div>
      )}
    </div>

    {/* Right tools */}
    <div className="flex items-center gap-3 w-full lg:w-auto flex-wrap">
      {/* Search */}
      <div className="relative flex-1 lg:flex-initial">
        <LucideIcon
          name="search"
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#94a3b8] pointer-events-none"
        />
        <label htmlFor="global-search" className="sr-only">Pencarian global</label>
        <input
          id="global-search"
          type="search"
          placeholder="Cari studi atau spec..."
          value={globalSearch}
          onChange={e => onGlobalSearchChange(e.target.value)}
          className="pl-9 w-full lg:w-56 rounded-[10px] text-[13px] min-h-[40px]"
        />
      </div>

      {/* Bell */}
      {onNotificationsClick && (
        <button
          type="button"
          aria-label="Lihat notifikasi"
          onClick={onNotificationsClick}
          className="btn-secondary w-10 h-10 !p-0 justify-center rounded-[10px]"
        >
          <LucideIcon name="bell" className="w-[17px] h-[17px]" />
        </button>
      )}

      {/* Avatar */}
      <div className="flex items-center gap-2">
        <span
          className="w-9 h-9 rounded-full bg-[#dbeafe] text-[#1d4ed8] grid place-items-center text-[12px] font-bold ring-2 ring-[#bfdbfe]"
          aria-hidden="true"
        >
          {profileInitials}
        </span>
        <span className="text-[13px] font-semibold text-[#0f172a] hidden lg:block">
          {profileName}
        </span>
      </div>
    </div>
  </header>
);

export default Header;
