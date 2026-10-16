/**
 * UHUY B2B — External Client Portal (main application shell).
 *
 * This is the EXTERNAL portal, separate from the internal Sampling & Spec R&D
 * dashboard. It is gated by external client authentication and every data view
 * is scoped to the signed-in client (server-side client_id).
 *
 * Views:
 *   overview        — client KPI dashboard
 *   orders          — track own production orders
 *   order-request   — submit a new production order request
 *   sample-request  — submit a new design/sample request
 *   requests        — own request history
 *   stock           — own consigned material
 *   settings        — change password / account info
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import Sidebar, { type NavItem } from './components/Sidebar';
import Header from './components/Header';
import Toaster from './components/Toaster';
import ErrorBoundary from './components/ErrorBoundary';
import PortalBadge from './components/PortalBadge';
import PortalLoginView from './pages/PortalLoginView';
import PortalDashboardView from './pages/PortalDashboardView';
import OrderTrackView from './pages/OrderTrackView';
import NewOrderRequestView from './pages/NewOrderRequestView';
import NewSampleRequestView from './pages/NewSampleRequestView';
import RequestsView from './pages/RequestsView';
import ConsignedStockView from './pages/ConsignedStockView';
import PortalSettingsView from './pages/PortalSettingsView';
import { logout as portalLogout, health as portalHealth } from './services/portalApi';
import {
  clearSession,
  getSession,
  subscribe as subscribeAuth,
  type AuthSession,
} from './services/authSession';

const navItems: NavItem[] = [
  { id: 'overview',       label: 'Dashboard',       icon: 'layout-dashboard', view: 'overview' },
  { id: 'orders',         label: 'Lacak Pesanan',   icon: 'boxes',            view: 'orders' },
  { id: 'order-request',  label: 'Ajukan Order',    icon: 'plus',             view: 'order-request' },
  { id: 'sample-request', label: 'Ajukan Sample',   icon: 'layers',           view: 'sample-request' },
  { id: 'requests',       label: 'Pengajuan Saya',  icon: 'clipboard-list',   view: 'requests' },
  { id: 'stock',          label: 'Bahan Saya',      icon: 'factory',          view: 'stock' },
  { id: 'settings',       label: 'Pengaturan',      icon: 'settings',         view: 'settings' },
];

function App() {
  const [currentView, setCurrentView] = useState('overview');
  const [globalSearch, setGlobalSearch] = useState('');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // ── external client session (auth gate) ─────────────────────────────────────
  const [session, setSession] = useState<AuthSession | null>(() => getSession());
  useEffect(() => subscribeAuth(setSession), []);

  const [isConnected, setIsConnected] = useState(false);

  const handleLogout = useCallback(async () => {
    const token = getSession()?.token;
    if (token) await portalLogout(token);
    clearSession();
  }, []);

  const handleNavigate = useCallback((view: string) => {
    setCurrentView(view);
    setMobileNavOpen(false);
  }, []);

  // ── dark mode ────────────────────────────────────────────────────────────────
  const [isDark, setIsDark] = useState<boolean>(() => {
    const stored = localStorage.getItem('ui-dark');
    if (stored !== null) return stored === 'true';
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
  });

  const transitionTimer = useRef<number | undefined>(undefined);

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) root.classList.add('dark');
    else root.classList.remove('dark');
    localStorage.setItem('ui-dark', String(isDark));
  }, [isDark]);

  const toggleDark = useCallback(() => {
    const root = document.documentElement;
    root.classList.add('theme-transition');
    setIsDark((d) => !d);
    if (transitionTimer.current !== undefined) window.clearTimeout(transitionTimer.current);
    transitionTimer.current = window.setTimeout(() => {
      root.classList.remove('theme-transition');
      transitionTimer.current = undefined;
    }, 900);
  }, []);

  useEffect(() => () => {
    if (transitionTimer.current !== undefined) window.clearTimeout(transitionTimer.current);
  }, []);

  // ── backend connectivity (shown in the header caption) ──────────────────────
  useEffect(() => {
    let active = true;
    void (async () => {
      const ok = await portalHealth();
      if (active) setIsConnected(ok);
    })();
    return () => { active = false; };
  }, []);

  const currentLabel =
    navItems.find((n) => n.view === currentView)?.label ?? 'Dashboard';

  // Auth gate: unauthenticated users see the external portal entry page only.
  if (!session) {
    return <PortalLoginView onAuthenticated={setSession} />;
  }

  const profileName = session.actor.companyName || session.actor.displayName;
  const profileInitials = (session.actor.companyName || session.actor.displayName)
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div className="flex flex-col h-screen overflow-hidden font-sf-pro" style={{ background: 'var(--bg-page)' }}>
      {/* External-portal ribbon — the permanent marker that this is NOT the internal app */}
      <div className="portal-ribbon shrink-0">
        <strong>UHUY B2B</strong>
        <span aria-hidden="true">·</span>
        <span>Portal Klien Eksternal — data dibatasi per klien</span>
      </div>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Mobile nav backdrop */}
        {mobileNavOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/40 lg:hidden"
            onClick={() => setMobileNavOpen(false)}
            aria-hidden="true"
          />
        )}

        <div
          className={`${mobileNavOpen ? 'fixed inset-y-0 left-0 z-50 flex' : 'hidden'} lg:flex lg:flex-none lg:static lg:z-auto`}
        >
          <Sidebar
            currentView={currentView}
            items={navItems}
            onNavigate={handleNavigate}
            isDark={isDark}
            onToggleDark={toggleDark}
          />
        </div>

      <main className="flex-1 overflow-y-auto page-stage">
        <div className="w-full max-w-[1760px] mx-auto p-4 lg:p-6">
          <div className="mb-3">
            <PortalBadge />
          </div>

          <Header
            title={currentLabel}
            subtitle="PORTAL KLIEN EKSTERNAL / UHUY B2B"
            caption={
              isConnected
                ? `Backend terhubung · ${session.actor.companyName}`
                : 'Backend tidak terhubung — pastikan server berjalan di port 8010'
            }
            globalSearch={globalSearch}
            onGlobalSearchChange={setGlobalSearch}
            onMenuClick={() => setMobileNavOpen(true)}
            profileName={profileName}
            profileInitials={profileInitials}
            onLogout={handleLogout}
          />

          <div key={currentView} className="page-turn">
            <ErrorBoundary>
              {currentView === 'overview' && <PortalDashboardView globalSearch={globalSearch} />}
              {currentView === 'orders' && <OrderTrackView globalSearch={globalSearch} />}
              {currentView === 'order-request' && (
                <NewOrderRequestView onSubmitted={() => setCurrentView('requests')} />
              )}
              {currentView === 'sample-request' && (
                <NewSampleRequestView onSubmitted={() => setCurrentView('requests')} />
              )}
              {currentView === 'requests' && <RequestsView globalSearch={globalSearch} />}
              {currentView === 'stock' && <ConsignedStockView globalSearch={globalSearch} />}
              {currentView === 'settings' && <PortalSettingsView onLoggedOut={handleLogout} />}
            </ErrorBoundary>
          </div>
        </div>
      </main>
      </div>

      <Toaster />
    </div>
  );
}

export default App;
