/**
 * Sidebar — fixed 226px navigation, scrollable.
 * Chapter accordion ("bab"): nav items are grouped into collapsible chapters;
 * clicking a chapter reveals its items, clicking an item opens its view.
 * Exports LucideIcon for use in pages.
 * Dark mode toggle button added at the bottom.
 */
import React, { useState, useEffect } from 'react';

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  view: string;
}

export interface NavChapter {
  id: string;
  label: string;
  icon: string;
  items: NavItem[];
}

interface SidebarProps {
  currentView: string;
  chapters: NavChapter[];
  onNavigate: (view: string) => void;
  isDark: boolean;
  onToggleDark: () => void;
}

const findChapterId = (chapters: NavChapter[], view: string): string | null =>
  chapters.find(c => c.items.some(i => i.view === view))?.id ?? null;

const Sidebar: React.FC<SidebarProps> = ({ currentView, chapters, onNavigate, isDark, onToggleDark }) => {
  const [openChapter, setOpenChapter] = useState<string | null>(() => findChapterId(chapters, currentView));

  // Keep the chapter of the active view open when navigation changes it.
  useEffect(() => {
    setOpenChapter(findChapterId(chapters, currentView));
  }, [chapters, currentView]);

  return (
  <aside
    className="flex flex-col w-[226px] flex-none border-r"
    style={{
      height: '100%',
      background: 'var(--bg-card)',
      borderColor: 'var(--c-hair)',
    }}
  >
    {/* Brand — fixed at top */}
    <div className="px-6 pt-6 pb-4 shrink-0">
      <div
        className="w-9 h-9 rounded-xl flex items-center justify-center mb-4"
        style={{ background: isDark ? 'var(--c-brand)' : 'var(--c-ink)', color: '#fff' }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/>
          <path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/>
          <path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>
        </svg>
      </div>
      <p className="text-[11px] uppercase tracking-[.16em] font-bold" style={{ color: 'var(--c-ink)' }}>
        UHUY B2B
      </p>
      <p className="text-[10px] uppercase tracking-[.14em] font-semibold mt-0.5" style={{ color: 'var(--c-brand)' }}>
        Portal Klien · Eksternal
      </p>
    </div>

    {/* Nav — chapter accordion; scrollable so every item stays reachable */}
    <nav className="flex-1 overflow-y-auto px-3 pb-3" aria-label="Navigasi utama">
      {chapters.map((chapter) => {
        const isOpen = openChapter === chapter.id;
        const hasActive = chapter.items.some(i => i.view === currentView);
        return (
          <div key={chapter.id} className="mb-0.5">
            {/* Chapter header — toggles the accordion */}
            <button type="button"
              onClick={() => setOpenChapter(open => (open === chapter.id ? null : chapter.id))}
              aria-expanded={isOpen}
              style={{ color: hasActive ? 'var(--c-brand)' : 'var(--c-ink-muted)' }}
              className="w-full flex items-center gap-2.5 text-left rounded-[10px] px-3 py-2 text-[11px] font-semibold uppercase tracking-[.08em] transition-colors">
              <LucideIcon name={chapter.icon} className="w-[14px] h-[14px] shrink-0" />
              <span className="flex-1 truncate">{chapter.label}</span>
              <LucideIcon name="chevron-down"
                className={`w-3.5 h-3.5 shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-0' : '-rotate-90'}`} />
            </button>

            {/* Chapter items — revealed on click/touch */}
            {isOpen && (
              <div className="animate-slideDown mt-0.5 space-y-0.5">
                {chapter.items.map((item) => {
                  const active = currentView === item.view;
                  return (
                    <button key={item.id} type="button"
                      onClick={() => onNavigate(item.view)}
                      aria-current={active ? 'page' : undefined}
                      style={active
                        ? { background: 'var(--c-brand-bg)', color: 'var(--c-brand)' }
                        : { color: 'var(--c-ink-muted)' }
                      }
                      className={`w-full flex items-center gap-2.5 text-left rounded-[10px] pl-7 pr-3 py-2.5 text-[13px] font-medium transition-colors ${
                        active ? 'font-semibold' : isDark ? 'hover:bg-panel-6 hover:text-ink' : 'hover:bg-page hover:text-ink'
                      }`}>
                      <LucideIcon name={item.icon} className="w-[15px] h-[15px] shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </nav>

    {/* Dark mode toggle — pinned to bottom */}
    <div
      className="px-4 py-4 shrink-0 border-t"
      style={{ borderColor: 'var(--c-hair)' }}
    >
      <button
        type="button"
        onClick={onToggleDark}
        aria-label={isDark ? 'Aktifkan light mode' : 'Aktifkan dark mode'}
        className="w-full flex items-center gap-2.5 rounded-[10px] px-3 py-2.5 text-[13px] font-medium transition-colors"
        style={{
          background: 'var(--c-page)',
          color: 'var(--c-ink-muted)',
          border: 'none',
        }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLButtonElement).style.background = 'var(--c-hair)';
          (e.currentTarget as HTMLButtonElement).style.color = 'var(--c-ink)';
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLButtonElement).style.background = 'var(--c-page)';
          (e.currentTarget as HTMLButtonElement).style.color = 'var(--c-ink-muted)';
        }}
      >
        <span className="theme-icon-wrap" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
               className="theme-icon theme-icon--sun">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
          </svg>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
               className="theme-icon theme-icon--moon">
            <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
          </svg>
        </span>
        <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>
      </button>
    </div>
  </aside>
  );
};

/* ── Icon registry ─────────────────────────────────────────────────────────── */

type IconProps = { className?: string; style?: React.CSSProperties };

const icons: Record<string, React.FC<IconProps>> = {
  'layout-dashboard': ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect width="7" height="9" x="3" y="3" rx="1"/>
      <rect width="7" height="5" x="14" y="3" rx="1"/>
      <rect width="7" height="9" x="14" y="12" rx="1"/>
      <rect width="7" height="5" x="3" y="16" rx="1"/>
    </svg>
  ),
  clock: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  ),
  layers: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/>
      <path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/>
      <path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>
    </svg>
  ),
  activity: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>
    </svg>
  ),
  'clipboard-list': ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
      <path d="M12 11h4"/><path d="M12 16h4"/>
      <path d="M8 11h.01"/><path d="M8 16h.01"/>
    </svg>
  ),
  boxes: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M2.97 12.92A2 2 0 0 0 2 14.63v3.24a2 2 0 0 0 .97 1.71l3 1.8a2 2 0 0 0 2.06 0L12 19v-5.5l-5-3-4.03 2.42Z"/>
      <path d="m7 16.5-4.74-2.85"/><path d="m7 16.5 5-3"/><path d="M7 16.5v5.17"/>
      <path d="M12 13.5V19l3.97 2.38a2 2 0 0 0 2.06 0l3-1.8a2 2 0 0 0 .97-1.71v-3.24a2 2 0 0 0-.97-1.71L17 10.5l-5 3Z"/>
      <path d="m17 16.5-5-3"/><path d="m17 16.5 4.74-2.85"/><path d="M17 16.5v5.17"/>
      <path d="M7.97 4.42A2 2 0 0 0 7 6.13v4.37l5 3 5-3V6.13a2 2 0 0 0-.97-1.71l-3-1.8a2 2 0 0 0-2.06 0l-3 1.8Z"/>
      <path d="M12 8 7.26 5.15"/><path d="m12 8 4.74-2.85"/><path d="M12 13.5V8"/>
    </svg>
  ),
  'badge-check': ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/>
      <path d="m9 12 2 2 4-4"/>
    </svg>
  ),
  'bar-chart-3': ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M3 3v16a2 2 0 0 0 2 2h16"/>
      <path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>
    </svg>
  ),
  settings: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  ),
  'chevron-down': ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="m6 9 6 6 6-6"/>
    </svg>
  ),
  search: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="11" cy="11" r="8"/>
      <path d="m21 21-4.3-4.3"/>
    </svg>
  ),
  bell: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
    </svg>
  ),
  download: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" x2="12" y1="15" y2="3"/>
    </svg>
  ),
  plus: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M5 12h14"/><path d="M12 5v14"/>
    </svg>
  ),
  x: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
    </svg>
  ),
  'file-text': ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" x2="8" y1="13" y2="13"/>
      <line x1="16" x2="8" y1="17" y2="17"/>
      <line x1="10" x2="8" y1="9" y2="9"/>
    </svg>
  ),
  'book-open': ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
    </svg>
  ),
  factory: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/>
      <path d="M17 18h1"/><path d="M12 18h1"/><path d="M7 18h1"/>
    </svg>
  ),
  'check-circle': ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
      <path d="m9 11 3 3L22 4"/>
    </svg>
  ),
  menu: ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <line x1="4" x2="20" y1="6" y2="6"/>
      <line x1="4" x2="20" y1="12" y2="12"/>
      <line x1="4" x2="20" y1="18" y2="18"/>
    </svg>
  ),
};

const LucideIcon: React.FC<{ name: string; className?: string; style?: React.CSSProperties }> = ({ name, className = 'w-4 h-4', style }) => {
  const Icon = icons[name];
  const el = Icon ? <Icon className={className} /> : <>{icons['layers']({ className })}</>;
  if (style) return <span style={{ display: 'inline-flex', alignItems: 'center', ...style }}>{el}</span>;
  return el;
};

export { LucideIcon };
export default Sidebar;
