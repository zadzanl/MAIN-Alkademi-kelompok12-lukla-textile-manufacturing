/**
 * Sampling & Spec R&D — Main Application
 *
 * Views:
 *   overview          — KPI dashboard
 *   sample-versions   — Article versioning (v1→v2→order) [NEW]
 *   stopwatch         — Digital stopwatch per component  [NEW]
 *   active-studies    — Live study monitor + controls    [NEW]
 *   time-studies      — Create / manage time studies
 *   study-list        — Full study list + export         [NEW]
 *   spec-versions     — Create / manage spec versions
 *   spec-list         — Full spec list + actions         [NEW]
 *   drift-analysis    — Drift record / resolve           [NEW]
 *   reports           — Rate cards, costing, handoff     [NEW]
 *   settings          — Placeholder
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import Sidebar, { NavChapter } from './components/Sidebar';
import Header from './components/Header';
import MetricCard from './components/MetricCard';
import Chart from './components/Chart';
import StatusPanel from './components/StatusPanel';
import DataTable from './components/DataTable';
import StatusBadge from './components/StatusBadge';
import ActivityLog, { Activity } from './components/ActivityLog';
import Modal from './components/Modal';
import { FontKey } from './components/FontSelector';
import Toaster from './components/Toaster';
import ErrorBoundary from './components/ErrorBoundary';
import SampleVersionView   from './pages/SampleVersionView';
import DigitalStopwatchView from './pages/DigitalStopwatchView';
import ActiveStudiesView   from './pages/ActiveStudiesView';
import ProductionView      from './pages/ProductionView';
import StudyListView       from './pages/StudyListView';
import SpecListView        from './pages/SpecListView';
import DriftAnalysisView   from './pages/DriftAnalysisView';
import ReportsView         from './pages/ReportsView';
import LedgerView          from './pages/LedgerView';
import QualityView         from './pages/QualityView';
import PayrollView         from './pages/PayrollView';
import TimeStudiesView     from './pages/TimeStudiesView';
import SpecVersionsView    from './pages/SpecVersionsView';
import SettingsView        from './pages/SettingsView';
import PortalAuthView      from './pages/PortalAuthView';
import PortalAdminView     from './pages/PortalAdminView';
import type { TimeStudy, SpecVersion, WorkflowSummary, ExportCSV } from './types';
import * as api from './services/api';
import { logout as authLogout } from './services/authApi';
import { clearSession, getSession, subscribe as subscribeAuth, type AuthSession } from './services/authSession';
import { toast } from './services/toast';
import { TENANT_ID, actor } from './services/identity';
import { matchesQuery } from './utils/filter';

// ─── Shared form helper — hoisted outside App to avoid remount on every render
// Bug-fix #8
interface FormFieldProps { id: string; label: string; children: React.ReactNode }
const FormField: React.FC<FormFieldProps> = ({ id, label, children }) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-ink mb-1">{label}</label>
    {children}
  </div>
);

// ─── Navigation chapters ("bab") — module-scoped so the array identity is stable
// for the Sidebar accordion. Grouping mirrors the R&D workflow.
const chapters: NavChapter[] = [
  {
    id: 'ringkasan', label: 'Ringkasan', icon: 'layout-dashboard',
    items: [
      { id: 'overview', label: 'Overview', icon: 'layout-dashboard', view: 'overview' },
    ],
  },
  {
    id: 'sampling-studi', label: 'Sampling & Studi', icon: 'clock',
    items: [
      { id: 'sample-versions', label: 'Versi Sample', icon: 'layers', view: 'sample-versions' },
      { id: 'stopwatch',       label: 'Stopwatch',    icon: 'clock',  view: 'stopwatch' },
      { id: 'active-studies',  label: 'Studi Aktif',  icon: 'activity', view: 'active-studies' },
      { id: 'production',      label: 'Produksi & Tally', icon: 'factory', view: 'production' },
      { id: 'time-studies',    label: 'Studi Waktu',  icon: 'clipboard-list', view: 'time-studies' },
      { id: 'study-list',      label: 'Daftar Studi', icon: 'boxes', view: 'study-list' },
    ],
  },
  {
    id: 'spesifikasi', label: 'Spesifikasi', icon: 'badge-check',
    items: [
      { id: 'spec-versions',  label: 'Versi Spec',     icon: 'badge-check', view: 'spec-versions' },
      { id: 'spec-list',      label: 'Daftar Spec',    icon: 'bar-chart-3', view: 'spec-list' },
      { id: 'drift-analysis', label: 'Analisis Drift', icon: 'activity',    view: 'drift-analysis' },
    ],
  },
  {
    id: 'kualitas-keuangan', label: 'Kualitas & Keuangan', icon: 'check-circle',
    items: [
      { id: 'quality', label: 'Quality Control',   icon: 'check-circle', view: 'quality' },
      { id: 'reports', label: 'Laporan',           icon: 'bar-chart-3',  view: 'reports' },
      { id: 'ledger',  label: 'Buku Besar',        icon: 'book-open',    view: 'ledger' },
      { id: 'payroll', label: 'Payroll & Costing', icon: 'factory',      view: 'payroll' },
    ],
  },
  {
    id: 'sistem', label: 'Sistem', icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan', icon: 'settings', view: 'settings' },
    ],
  },
];

// ─────────────────────────────────────────────────────────────────────────────

function App() {
  // ── view state ──────────────────────────────────────────────────────────────
  const [currentView, setCurrentView] = useState('overview');
  const [globalSearch, setGlobalSearch] = useState('');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // ── portal session (auth gate) ───────────────────────────────────────────────
  const [session, setSession] = useState<AuthSession | null>(() => getSession());
  useEffect(() => subscribeAuth(setSession), []);

  const handleLogout = useCallback(async () => {
    const token = getSession()?.token;
    if (token) await authLogout(token);
    clearSession();
  }, []);

  // Admin IT sees an extra "Administrasi" chapter for access approvals.
  const navChapters = useMemo<NavChapter[]>(() => {
    if (session?.actor.role !== 'admin') return chapters;
    return [
      ...chapters,
      {
        id: 'administrasi', label: 'Administrasi', icon: 'badge-check',
        items: [
          { id: 'access-approvals', label: 'Persetujuan Akses', icon: 'check-circle', view: 'access-approvals' },
        ],
      },
    ];
  }, [session]);

  // ── dark mode ────────────────────────────────────────────────────────────────
  const [isDark, setIsDark] = useState<boolean>(() => {
    const stored = localStorage.getItem('ui-dark');
    if (stored !== null) return stored === 'true';
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
  });

  const transitionTimer = useRef<number | undefined>(undefined);

  // Apply / remove 'dark' class on <html> and persist preference
  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('ui-dark', String(isDark));
  }, [isDark]);

  // Toggle theme with a soft colour cross-fade (via .theme-transition)
  const toggleDark = useCallback(() => {
    const root = document.documentElement;
    root.classList.add('theme-transition');
    setIsDark(d => !d);

    if (transitionTimer.current !== undefined) window.clearTimeout(transitionTimer.current);
    transitionTimer.current = window.setTimeout(() => {
      root.classList.remove('theme-transition');
      transitionTimer.current = undefined;
    }, 900);
  }, []);

  // Clear any pending timer on unmount
  useEffect(() => () => {
    if (transitionTimer.current !== undefined) window.clearTimeout(transitionTimer.current);
  }, []);

  // ── font preference ──────────────────────────────────────────────────────────
  const [uiFont, setUiFont] = useState<FontKey>(() => {
    return (localStorage.getItem('ui-font') as FontKey) ?? 'sf-pro';
  });

  // Apply font to <html> immediately on mount and whenever it changes
  useEffect(() => {
    document.documentElement.setAttribute('data-font', uiFont);
    localStorage.setItem('ui-font', uiFont);
  }, [uiFont]);

  // ── backend state ────────────────────────────────────────────────────────────
  const [isConnected, setIsConnected]   = useState(false);
  const [isLoading, setIsLoading]       = useState(true);
  const [workflowSummary, setWorkflowSummary] = useState<WorkflowSummary | null>(null);
  const [timeStudies, setTimeStudies]   = useState<TimeStudy[]>([]);
  const [specVersions, setSpecVersions] = useState<SpecVersion[]>([]);
  const [activities, setActivities]     = useState<Activity[]>([]);

  // ── table filter state (used in Overview mini-tables) ───────────────────────
  const [studyTab, setStudyTab]   = useState('all');
  const [studySearch, setStudySearch] = useState('');
  const [specTab, setSpecTab]     = useState('all');
  const [specSearch, setSpecSearch] = useState('');

  // ── create-study modal ───────────────────────────────────────────────────────
  const [showCreateStudyModal, setShowCreateStudyModal] = useState(false);
  const [newStudy, setNewStudy] = useState({
    process_id: '', process_name: '',
    target_sample_size: 30, confidence_level: 95,
    allowance_percent: 15, operator_id: '', notes: '',
  });

  // ── create-spec modal ────────────────────────────────────────────────────────
  const [showCreateSpecModal, setShowCreateSpecModal] = useState(false);
  const [newSpec, setNewSpec] = useState({
    spec_id: '', spec_name: '', version_number: '1.0.0',
    materials: '', process_steps: '', notes: '',
  });

  // ── API helpers ───────────────────────────────────────────────────────────────

  const checkHealth = useCallback(async () => {
    const res = await api.checkHealth();
    setIsConnected(res.success);
    return res.success;
  }, []);

  const fetchWorkflowSummary = useCallback(async () => {
    const res = await api.getWorkflowSummary(TENANT_ID);
    if (res.success && res.data) setWorkflowSummary(res.data);
  }, []);

  const fetchTimeStudies = useCallback(async () => {
    const res = await api.listStudies(TENANT_ID);
    setTimeStudies(res.success && res.data ? res.data : []);
  }, []);

  const fetchSpecVersions = useCallback(async () => {
    const res = await api.listSpecs(TENANT_ID);
    setSpecVersions(res.success && res.data ? res.data : []);
  }, []);

  const createTimeStudy = async () => {
    if (!newStudy.process_id || !newStudy.process_name) {
      toast.error('ID Proses dan Nama Proses wajib diisi.'); return;
    }
    const res = await api.createStudy({
      tenant_id: TENANT_ID,
      process_id: newStudy.process_id,
      process_name: newStudy.process_name,
      operator_id: newStudy.operator_id || 'default',
      target_sample_size: newStudy.target_sample_size,
    });
    if (res.success && res.data) {
      toast.success(`Studi dibuat: ${res.data.study_id.substring(0,8)}`);
      setShowCreateStudyModal(false);
      setNewStudy({ process_id:'', process_name:'', target_sample_size:30, confidence_level:95, allowance_percent:15, operator_id:'', notes:'' });
      fetchTimeStudies(); fetchWorkflowSummary();
    } else { toast.error(res.error ?? 'Gagal membuat studi.'); }
  };

  const createSpecVersion = async () => {
    if (!newSpec.spec_id || !newSpec.spec_name) {
      toast.error('ID Spec dan Nama Spec wajib diisi.'); return;
    }
    const res = await api.createSpec({
      tenant_id: TENANT_ID, spec_id: newSpec.spec_id,
      spec_name: newSpec.spec_name, created_by: actor(),
      version_number: newSpec.version_number,
    });
    if (res.success && res.data) {
      toast.success(`Spec dibuat: ${res.data.version_id.substring(0,8)}`);
      setShowCreateSpecModal(false);
      setNewSpec({ spec_id:'', spec_name:'', version_number:'1.0.0', materials:'', process_steps:'', notes:'' });
      fetchSpecVersions(); fetchWorkflowSummary();
    } else { toast.error(res.error ?? 'Gagal membuat spec.'); }
  };

  // ── CSV export (UTF-8 BOM) ────────────────────────────────────────────────────

  const exportToCSV: ExportCSV = (data, filename) => {
    if (!data.length) { toast.info('Tidak ada data untuk diekspor.'); return; }
    const headers = Object.keys(data[0] as Record<string, unknown>);
    const rows = data.map(item => {
      const row = item as Record<string, unknown>;
      return headers.map(h => {
        const v = row[h];
        const s = typeof v === 'object' ? JSON.stringify(v) : String(v ?? '');
        return `"${s.replace(/"/g, '""')}"`;
      }).join(',');
    });
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + [headers.join(','), ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${filename}_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
  };

  // ── effects ───────────────────────────────────────────────────────────────────

  useEffect(() => {
    (async () => {
      setIsLoading(true);
      const ok = await checkHealth();
      if (ok) await Promise.all([fetchWorkflowSummary(), fetchTimeStudies(), fetchSpecVersions()]);
      setIsLoading(false);
    })();
  }, [checkHealth, fetchWorkflowSummary, fetchTimeStudies, fetchSpecVersions]);

  useEffect(() => {
    const newActs: Activity[] = [];
    [...timeStudies].sort((a,b) => b.updated_at.localeCompare(a.updated_at)).slice(0,3).forEach(s => {
      newActs.push({ icon:'clock', title:`Studi: ${s.process_name}`, detail:`Status: ${s.status}`, time: relTime(s.updated_at) });
    });
    [...specVersions].sort((a,b) => b.updated_at.localeCompare(a.updated_at)).slice(0,2).forEach(s => {
      newActs.push({ icon:'layers', title:`Spec: ${s.spec_name}`, detail:`v${s.version_number}`, time: relTime(s.updated_at) });
    });
    setActivities(newActs.slice(0,5));
  }, [timeStudies, specVersions]);

  // ── helpers ───────────────────────────────────────────────────────────────────

  const relTime = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const m = Math.floor(diff/60000), h = Math.floor(diff/3600000), d = Math.floor(diff/86400000);
    if (m < 1) return 'Baru saja';
    if (m < 60) return `${m}m lalu`;
    if (h < 24) return `${h}j lalu`;
    if (d < 7) return `${d}h lalu`;
    return new Date(iso).toLocaleDateString('id-ID');
  };

  // ── computed ──────────────────────────────────────────────────────────────────

  // Global header search ("Cari studi atau spec...") narrows both tables.
  const filteredStudies = timeStudies.filter(s =>
    (studyTab === 'all' || s.status === studyTab) &&
    matchesQuery(studySearch, s.process_name) &&
    matchesQuery(globalSearch, s.process_name, s.process_id)
  );

  const filteredSpecs = specVersions.filter(s =>
    (specTab === 'all' || s.status === specTab) &&
    matchesQuery(specSearch, s.spec_name) &&
    matchesQuery(globalSearch, s.spec_name, s.spec_id)
  );

  /**
   * Build weekly chart from real backend data.
   * Each completed/in-progress study has a created_at timestamp.
   * We count how many studies were active or completed on each ISO weekday
   * (Mon=0 … Sun=6), then express as % of the total.
   *
   * Today's weekday is highlighted; future weekdays are marked isFuture.
   */
  const chartData = (() => {
    const DAYS = ['Sen','Sel','Rab','Kam','Jum','Sab','Min'];
    // JS getDay(): 0=Sun,1=Mon,...,6=Sat  →  map to Mon-first (0=Mon,6=Sun)
    const todayJs  = new Date().getDay();                   // 0(Sun)–6(Sat)
    const todayIdx = todayJs === 0 ? 6 : todayJs - 1;     // Mon-first index

    const counts = Array(7).fill(0);
    const total  = timeStudies.length || 1;

    timeStudies.forEach(study => {
      const d  = new Date(study.created_at);
      const js = d.getDay();
      const i  = js === 0 ? 6 : js - 1;
      counts[i]++;
    });

    return DAYS.map((label, i) => ({
      label,
      value:     i <= todayIdx ? Math.round((counts[i] / total) * 100) : 0,
      isCurrent: i === todayIdx,
      isFuture:  i > todayIdx,
    }));
  })();

  const statusItems = [
    { label:'Draft',       count: timeStudies.filter(s=>s.status==='draft').length },
    { label:'In Progress', count: timeStudies.filter(s=>s.status==='in_progress').length },
    { label:'Paused',      count: timeStudies.filter(s=>s.status==='paused').length },
    { label:'Completed',   count: timeStudies.filter(s=>s.status==='completed').length },
  ];

  const currentLabel = navChapters.flatMap(c => c.items).find(n => n.view === currentView)?.label ?? 'Overview';

  // ── shared style constants ────────────────────────────────────────────────────
  const inputCls  = "w-full rounded-[10px] px-3 py-2.5 text-[13px]";
  const btnPrimary   = "btn-primary";
  const btnSecondary = "btn-secondary";

  // ── render ────────────────────────────────────────────────────────────────────

  // Auth gate: unauthenticated users see the portal entry page only.
  if (!session) {
    return <PortalAuthView onAuthenticated={setSession} />;
  }

  const profileName = session.actor.displayName;
  const profileInitials = profileName
    .split(/\s+/)
    .filter(Boolean)
    .map(w => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div
      className="flex h-screen overflow-hidden font-sf-pro"
      style={{ background: 'var(--bg-page)' }}
    >
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
          chapters={navChapters}
          onNavigate={(view) => { setCurrentView(view); setMobileNavOpen(false); }}
          isDark={isDark}
          onToggleDark={toggleDark}
        />
      </div>

      <main className="flex-1 overflow-y-auto page-stage">
        <div className="max-w-[1440px] mx-auto p-6 lg:p-8">

          <Header
            title={currentLabel}
            subtitle="DASHBOARD / SAMPLING & SPEC R&D"
            caption={isConnected
              ? `Backend terhubung · ${timeStudies.length} studi · ${specVersions.length} spec`
              : 'Backend tidak terhubung — pastikan server berjalan di port 8009'}
            globalSearch={globalSearch}
            onGlobalSearchChange={setGlobalSearch}
            onMenuClick={() => setMobileNavOpen(true)}
            profileName={profileName}
            profileInitials={profileInitials}
            onLogout={handleLogout}
          />

          {/* key={currentView} remounts this wrapper on navigation so the
              page-turn animation replays for the newly opened view. */}
          <div key={currentView} className="page-turn">
            <ErrorBoundary>

          {/* ── OVERVIEW ──────────────────────────────────────────────────────── */}
          {currentView === 'overview' && (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <MetricCard label="Studi Aktif"      value={workflowSummary?.active_studies ?? 0}        note="Studi yang sedang berjalan"      loading={isLoading} accent="blue" />
                <MetricCard label="Studi Selesai"    value={workflowSummary?.completed_studies ?? 0}     note="Studi yang telah diselesaikan"   loading={isLoading} accent="green" />
                <MetricCard label="Versi Sample"     value={workflowSummary?.total_sample_versions ?? 0} note="Artikel dalam sistem versioning"  loading={isLoading} accent="orange" />
                <MetricCard label="Drift Kritis"     value={workflowSummary?.critical_drifts ?? 0}       note="Memerlukan perhatian segera"      loading={isLoading} accent="red" />
              </div>

              {/* Chart + Status */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
                <div className="lg:col-span-2">
                  <Chart data={chartData} title="Tingkat Penyelesaian Studi" subtitle="Persentase sampel terkumpul per hari (estimasi)" />
                </div>
                <StatusPanel title="Status Studi" subtitle="Distribusi status studi waktu" items={statusItems} />
              </div>

              {/* Mini tables */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                <DataTable
                  title="Studi Waktu Terbaru" subtitle="5 studi terakhir"
                  tabs={[{id:'all',label:'Semua'},{id:'in_progress',label:'Berjalan'},{id:'completed',label:'Selesai'}]}
                  activeTab={studyTab} onTabChange={setStudyTab}
                  searchValue={studySearch} onSearchChange={setStudySearch}
                  columns={[
                    { key:'process_name', label:'Proses' },
                    { key:'status',       label:'Status', render: v => <StatusBadge status={String(v)} /> },
                    { key:'total_cycles', label:'Siklus',  render: (v, row: TimeStudy) => `${Number(v??0)}/${row.target_sample_size}` },
                  ]}
                  data={filteredStudies.slice(0,5)}
                />
                <DataTable
                  title="Versi Spec Terbaru" subtitle="5 spec terakhir"
                  tabs={[{id:'all',label:'Semua'},{id:'active',label:'Aktif'},{id:'review',label:'Review'}]}
                  activeTab={specTab} onTabChange={setSpecTab}
                  searchValue={specSearch} onSearchChange={setSpecSearch}
                  columns={[
                    { key:'spec_name',      label:'Nama Spec' },
                    { key:'version_number', label:'Versi' },
                    { key:'status',         label:'Status', render: v => <StatusBadge status={String(v)} /> },
                  ]}
                  data={filteredSpecs.slice(0,5)}
                />
              </div>

              <ActivityLog title="Aktivitas Terbaru" subtitle="Aktivitas terbaru dalam sistem" activities={activities} />
            </>
          )}

          {/* ── SAMPLE VERSIONS ───────────────────────────────────────────────── */}
          {currentView === 'sample-versions' && (
            <SampleVersionView onExportCSV={exportToCSV} />
          )}

          {/* ── STOPWATCH ─────────────────────────────────────────────────────── */}
          {currentView === 'stopwatch' && <DigitalStopwatchView />}

          {/* ── ACTIVE STUDIES ────────────────────────────────────────────────── */}
          {currentView === 'active-studies' && <ActiveStudiesView />}

          {/* ── PRODUCTION & TALLY (VIEW-04 floor terminal + admin) ───────────── */}
          {currentView === 'production' && <ProductionView />}

          {/* ── TIME STUDIES (create + manage) ────────────────────────────────── */}
          {currentView === 'time-studies' && (
            <TimeStudiesView
              studies={filteredStudies}
              tab={studyTab} onTabChange={setStudyTab}
              search={studySearch} onSearchChange={setStudySearch}
              onCreate={() => setShowCreateStudyModal(true)}
              onExportCSV={exportToCSV}
            />
          )}

          {/* ── STUDY LIST ────────────────────────────────────────────────────── */}
          {currentView === 'study-list' && <StudyListView onExportCSV={exportToCSV} globalSearch={globalSearch} />}

          {/* ── SPEC VERSIONS (create + manage) ───────────────────────────────── */}
          {currentView === 'spec-versions' && (
            <SpecVersionsView
              specs={filteredSpecs}
              tab={specTab} onTabChange={setSpecTab}
              search={specSearch} onSearchChange={setSpecSearch}
              onCreate={() => setShowCreateSpecModal(true)}
              onExportCSV={exportToCSV}
            />
          )}

          {/* ── SPEC LIST ─────────────────────────────────────────────────────── */}
          {currentView === 'spec-list' && <SpecListView onExportCSV={exportToCSV} globalSearch={globalSearch} />}

          {/* ── DRIFT ANALYSIS ────────────────────────────────────────────────── */}
          {currentView === 'drift-analysis' && <DriftAnalysisView />}

          {/* ── REPORTS ───────────────────────────────────────────────────────── */}
          {currentView === 'reports' && <ReportsView onExportCSV={exportToCSV} />}

          {/* ── QUALITY CONTROL ───────────────────────────────────────────────── */}
          {currentView === 'quality' && <QualityView />}

          {/* ── LEDGER ────────────────────────────────────────────────────────── */}
          {currentView === 'ledger' && <LedgerView />}

          {/* ── PAYROLL & COSTING ─────────────────────────────────────────────── */}
          {currentView === 'payroll' && <PayrollView />}

          {/* ── SETTINGS ──────────────────────────────────────────────────────── */}
          {currentView === 'settings' && (
            <SettingsView
              isDark={isDark}
              onToggleDark={toggleDark}
              font={uiFont}
              onFontChange={setUiFont}
              onCheckHealth={checkHealth}
              onLoggedOut={handleLogout}
            />
          )}

          {/* ── ADMIN: ACCESS APPROVALS (admin role only) ─────────────────────── */}
          {currentView === 'access-approvals' && session.actor.role === 'admin' && (
            <PortalAdminView />
          )}

            </ErrorBoundary>
          </div>
        </div>
      </main>

      {/* ── Create Study Modal ─────────────────────────────────────────────── */}
      <Modal isOpen={showCreateStudyModal} title="Buat Studi Waktu Baru"
        onClose={() => setShowCreateStudyModal(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowCreateStudyModal(false)} className={btnSecondary}>Batal</button>
            <button onClick={createTimeStudy} className={btnPrimary}>Buat Studi</button>
          </div>
        }>
        <div className="space-y-4">
          <FormField id="process_id" label="ID Proses *">
            <input id="process_id" value={newStudy.process_id} placeholder="e.g. PROC-001"
              onChange={e => setNewStudy(f => ({...f, process_id: e.target.value}))} className={inputCls} />
          </FormField>
          <FormField id="process_name" label="Nama Proses *">
            <input id="process_name" value={newStudy.process_name} placeholder="e.g. Pasang Kerah"
              onChange={e => setNewStudy(f => ({...f, process_name: e.target.value}))} className={inputCls} />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField id="target_sample_size" label="Target Sampel">
              <input id="target_sample_size" type="number" min={5} value={newStudy.target_sample_size}
                onChange={e => setNewStudy(f => ({...f, target_sample_size: parseInt(e.target.value)||30}))} className={inputCls} />
            </FormField>
            <FormField id="operator_id" label="ID Operator">
              <input id="operator_id" value={newStudy.operator_id} placeholder="OPR-001"
                onChange={e => setNewStudy(f => ({...f, operator_id: e.target.value}))} className={inputCls} />
            </FormField>
          </div>
          <FormField id="study_notes" label="Catatan">
            <textarea id="study_notes" rows={2} value={newStudy.notes}
              onChange={e => setNewStudy(f => ({...f, notes: e.target.value}))} className={inputCls} />
          </FormField>
        </div>
      </Modal>

      {/* ── Create Spec Modal ──────────────────────────────────────────────── */}
      <Modal isOpen={showCreateSpecModal} title="Buat Spec Version Baru"
        onClose={() => setShowCreateSpecModal(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowCreateSpecModal(false)} className={btnSecondary}>Batal</button>
            <button onClick={createSpecVersion} className={btnPrimary}>Buat Spec</button>
          </div>
        }>
        <div className="space-y-4">
          <FormField id="spec_id" label="Spec ID *">
            <input id="spec_id" value={newSpec.spec_id} placeholder="e.g. SPEC-001"
              onChange={e => setNewSpec(f => ({...f, spec_id: e.target.value}))} className={inputCls} />
          </FormField>
          <FormField id="spec_name" label="Nama Spec *">
            <input id="spec_name" value={newSpec.spec_name} placeholder="e.g. Kaos Snøhund v1"
              onChange={e => setNewSpec(f => ({...f, spec_name: e.target.value}))} className={inputCls} />
          </FormField>
          <FormField id="version_number" label="Version Number">
            <input id="version_number" value={newSpec.version_number} placeholder="1.0.0"
              onChange={e => setNewSpec(f => ({...f, version_number: e.target.value}))} className={inputCls} />
          </FormField>
          <FormField id="spec_notes" label="Catatan">
            <textarea id="spec_notes" rows={2} value={newSpec.notes}
              onChange={e => setNewSpec(f => ({...f, notes: e.target.value}))} className={inputCls} />
          </FormField>
        </div>
      </Modal>

      <Toaster />
    </div>
  );
}

export default App;
