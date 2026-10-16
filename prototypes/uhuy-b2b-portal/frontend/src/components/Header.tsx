/**
 * Header — page title + search + profile + dark mode awareness
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
  onMenuClick?: () => void;
  profileName?: string;
  profileInitials?: string;
  onLogout?: () => void;
}

const Header: React.FC<HeaderProps> = ({
  title,
  subtitle = 'DASHBOARD / OPERASIONAL',
  caption,
  globalSearch,
  onGlobalSearchChange,
  onNotificationsClick,
  onMenuClick,
  profileName = 'Admin Produksi',
  profileInitials = 'AD',
  onLogout,
}) => (
  <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5 mb-5">
    {/* Title block */}
    <div className="flex items-start gap-3">
      {onMenuClick && (
        <button
          type="button"
          aria-label="Buka navigasi"
          onClick={onMenuClick}
          className="btn-secondary w-10 h-10 !p-0 justify-center rounded-[10px] lg:hidden"
        >
          <LucideIcon name="menu" className="w-[18px] h-[18px]" />
        </button>
      )}
      <div>
      <p
        className="text-[13px] font-bold uppercase tracking-[.14em] mb-1"
        style={{ color: 'var(--c-ink-muted)' }}
      >
        {subtitle}
      </p>
      <h1
        className="text-[32px] font-bold tracking-tight leading-tight"
        style={{ color: 'var(--c-ink)' }}
      >
        {title}
      </h1>
      {caption && (
        <div className="flex items-center gap-2 mt-1.5">
          {caption.startsWith('Backend terhubung') && (
            <span className="pulse-dot" aria-hidden="true" />
          )}
          <p
            className="text-[15px] font-medium"
            style={{
              color: caption.startsWith('Backend terhubung')
                ? 'var(--c-ok-2)'
                : 'var(--c-bad-4)',
            }}
            aria-live="polite"
          >
            {caption}
          </p>
        </div>
      )}
      </div>
    </div>

    {/* Right tools */}
    <div className="flex items-center gap-3 w-full lg:w-auto flex-wrap">
      {/* Search */}
      <div className="relative flex-1 lg:flex-initial">
        <LucideIcon
          name="search"
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
          style={{ color: 'var(--c-ink-faint)' } as React.CSSProperties}
        />
        <label htmlFor="global-search" className="sr-only">Pencarian global</label>
        <input
          id="global-search"
          type="search"
          placeholder="Cari studi atau spec..."
          value={globalSearch}
          onChange={e => onGlobalSearchChange(e.target.value)}
          className="pl-9 w-full lg:w-72 rounded-[10px] text-[15px] min-h-[40px]"
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
          className="w-9 h-9 rounded-full grid place-items-center text-[14px] font-bold ring-2"
          style={{
            background: 'var(--c-brand-bg-5)',
            color: 'var(--c-brand)',
            outlineColor: 'var(--c-brand-bg-5)',
          }}
          aria-hidden="true"
        >
          {profileInitials}
        </span>
        <span
          className="text-[15px] font-semibold hidden lg:block"
          style={{ color: 'var(--c-ink)' }}
        >
          {profileName}
        </span>
        {onLogout && (
          <button
            type="button"
            aria-label="Keluar dari portal"
            onClick={onLogout}
            className="btn-secondary w-10 h-10 !p-0 justify-center rounded-[10px]"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                 className="w-[17px] h-[17px]">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" x2="9" y1="12" y2="12"/>
            </svg>
          </button>
        )}
      </div>
    </div>
  </header>
);

export default React.memo(Header);
