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
import LuklaLogo from './components/LuklaLogo';
import type { Activity } from './components/ActivityLog';
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
import CopilotView         from './pages/CopilotView';
import WarehouseInventoryView from './pages/WarehouseInventoryView';
import ExecutiveDashboardView from './pages/ExecutiveDashboardView';
import PortalAuthView      from './pages/PortalAuthView';
import PortalAdminView     from './pages/PortalAdminView';
import type { TimeStudy, SpecVersion, WorkflowSummary, ExportCSV } from './types';
import * as api from './services/api';
import { logout as authLogout } from './services/authApi';
import { allowedViewsForRole, isKnownRole, landingViewForRole, navKeyForRole } from './services/access';
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
      { id: 'overview',  label: 'Executive Dashboard', icon: 'layout-dashboard', view: 'overview' },
      { id: 'warehouse', label: 'Inventaris Gudang', icon: 'warehouse', view: 'warehouse' },
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

// Roleless/unknown accounts get no operational navigation. Settings is the
// authorized landing view so the redirect effect cannot loop.
const rolelessChapters: NavChapter[] = [
  {
    id: 'roleless-akun',
    label: 'Akun & Profil',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan', icon: 'settings', view: 'settings' },
    ],
  },
];

// Client-scoped navigation chapters for B2B Maklon clients.
// Restricts access to approval workflows, production tracking, and consigned inventory only.
const clientChapters: NavChapter[] = [
  {
    id: 'klien-portal',
    label: 'Portal Klien (B2B)',
    icon: 'layers',
    items: [
      { id: 'sample-versions', label: 'Persetujuan Sample & Spec', icon: 'layers', view: 'sample-versions' },
      { id: 'production', label: 'Monitoring Produksi Order', icon: 'factory', view: 'production' },
      { id: 'warehouse', label: 'Bahan Baku Titipan (Maklon)', icon: 'warehouse', view: 'warehouse' },
    ],
  },
  {
    id: 'klien-sistem',
    label: 'Akun Klien',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan Akun', icon: 'settings', view: 'settings' },
    ],
  },
];

// QC Inspector navigation chapters (Slide 04: Periksa barang jadi, Set status lolos/reject/repair, Catat jenis cacat)
// Prohibited: "Tidak dapat mengubah harga borongan atau data order klien"
const qcInspectorChapters: NavChapter[] = [
  {
    id: 'qc-mutu',
    label: 'Penjaminan Mutu (QC)',
    icon: 'check-circle',
    items: [
      { id: 'quality', label: 'Quality Control', icon: 'check-circle', view: 'quality' },
      { id: 'production', label: 'Inspeksi & Tally Hasil', icon: 'factory', view: 'production' },
    ],
  },
  {
    id: 'qc-referensi',
    label: 'Standar & Spesifikasi',
    icon: 'badge-check',
    items: [
      { id: 'spec-list', label: 'Daftar Standar Toleransi', icon: 'bar-chart-3', view: 'spec-list' },
    ],
  },
  {
    id: 'qc-sistem',
    label: 'Akun & Profil',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan Akun', icon: 'settings', view: 'settings' },
    ],
  },
];

// Finance & Payroll navigation chapters (Slide 04: Buat/setujui PO bahan, Terbitkan invoice, Hitung gaji mingguan & bulanan)
// Prohibited: "Tidak dapat mengubah fisik stok di gudang"
const financePayrollChapters: NavChapter[] = [
  {
    id: 'fin-ringkasan',
    label: 'Ringkasan Eksekutif',
    icon: 'layout-dashboard',
    items: [
      { id: 'overview', label: 'Executive Dashboard', icon: 'layout-dashboard', view: 'overview' },
    ],
  },
  {
    id: 'fin-operasional',
    label: 'Keuangan & Penggajian',
    icon: 'factory',
    items: [
      { id: 'payroll', label: 'Payroll & Costing Borongan', icon: 'factory', view: 'payroll' },
      { id: 'ledger', label: 'Buku Besar & Jurnal Finansial', icon: 'book-open', view: 'ledger' },
      { id: 'reports', label: 'Laporan Keuangan & PO', icon: 'bar-chart-3', view: 'reports' },
    ],
  },
  {
    id: 'fin-sistem',
    label: 'Akun & Profil',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan Akun', icon: 'settings', view: 'settings' },
    ],
  },
];

// Owner/Eksekutif navigation chapters (Slide 04: Analitik tinggi & konfigurasi sistem, Ubah rate card)
// Prohibited: "Tidak dapat mengubah histori transaksi yang dikunci"
const ownerChapters: NavChapter[] = [
  {
    id: 'owner-ringkasan',
    label: 'Ringkasan Eksekutif',
    icon: 'layout-dashboard',
    items: [
      { id: 'overview', label: 'Executive Dashboard', icon: 'layout-dashboard', view: 'overview' },
    ],
  },
  {
    id: 'owner-keuangan',
    label: 'Finansial & Rate Card',
    icon: 'factory',
    items: [
      { id: 'payroll', label: 'Payroll & Costing Borongan', icon: 'factory', view: 'payroll' },
      { id: 'ledger', label: 'Buku Besar & Jurnal Finansial', icon: 'book-open', view: 'ledger' },
      { id: 'reports', label: 'Laporan Keuangan & PO', icon: 'bar-chart-3', view: 'reports' },
    ],
  },
  {
    id: 'owner-operasional',
    label: 'Operasional & Gudang',
    icon: 'warehouse',
    items: [
      { id: 'warehouse', label: 'Inventaris Gudang', icon: 'warehouse', view: 'warehouse' },
      { id: 'spec-versions', label: 'Versi Spec & BOM', icon: 'badge-check', view: 'spec-versions' },
    ],
  },
  {
    id: 'owner-sistem',
    label: 'Sistem & Konfigurasi',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Konfigurasi Sistem', icon: 'settings', view: 'settings' },
    ],
  },
];

// Tim Sample/Adis navigation chapters (Slide 04: Catat pemakaian bahan sample, Input time study, Setujui versi sample)
// Prohibited: "Tidak dapat menyetujui pesanan massal tanpa konfirmasi"
const sampleChapters: NavChapter[] = [
  {
    id: 'sample-persetujuan',
    label: 'Sample & Spesifikasi',
    icon: 'layers',
    items: [
      { id: 'sample-versions', label: 'Versi Sample & Persetujuan', icon: 'layers', view: 'sample-versions' },
      { id: 'spec-versions', label: 'Versi Spec', icon: 'badge-check', view: 'spec-versions' },
      { id: 'spec-list', label: 'Daftar Standar Toleransi', icon: 'bar-chart-3', view: 'spec-list' },
      { id: 'drift-analysis', label: 'Analisis Drift Desain', icon: 'activity', view: 'drift-analysis' },
    ],
  },
  {
    id: 'sample-studi',
    label: 'Studi Waktu & Stopwatch',
    icon: 'clock',
    items: [
      { id: 'stopwatch', label: 'Digital Stopwatch', icon: 'clock', view: 'stopwatch' },
      { id: 'active-studies', label: 'Studi Waktu Aktif', icon: 'activity', view: 'active-studies' },
      { id: 'time-studies', label: 'Kelola Time Studies', icon: 'clipboard-list', view: 'time-studies' },
      { id: 'study-list', label: 'Daftar Studi', icon: 'boxes', view: 'study-list' },
    ],
  },
  {
    id: 'sample-sistem',
    label: 'Akun & Profil',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan Akun', icon: 'settings', view: 'settings' },
    ],
  },
];

// Gudang/Warehouse navigation chapters (Slide 04: Terima bahan + titipan klien, Keluarkan bahan ke cutting, Stok opname)
// Prohibited: "Dilarang mengeluarkan bahan jika ID Klien/Pesanan tidak cocok"
const warehouseChapters: NavChapter[] = [
  {
    id: 'gudang-stok',
    label: 'Inventaris & Titipan',
    icon: 'warehouse',
    items: [
      { id: 'warehouse', label: 'Inventaris Gudang & Titipan', icon: 'warehouse', view: 'warehouse' },
    ],
  },
  {
    id: 'gudang-sistem',
    label: 'Akun & Profil',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan Akun', icon: 'settings', view: 'settings' },
    ],
  },
];

// Kepala Produksi/Mandor navigation chapters (Slide 04: Atur line + alokasi penjahit, Tentukan rate card komponen, Catat output 30 menit)
// Prohibited: "Tidak dapat mengubah formula penggajian atau hasil QC final"
const mandorChapters: NavChapter[] = [
  {
    id: 'mandor-line',
    label: 'Supervisi Line Produksi',
    icon: 'factory',
    items: [
      { id: 'production', label: 'Produksi & Tally Output', icon: 'factory', view: 'production' },
      { id: 'active-studies', label: 'Studi Line Aktif', icon: 'activity', view: 'active-studies' },
      { id: 'spec-list', label: 'Toleransi Komponen', icon: 'bar-chart-3', view: 'spec-list' },
    ],
  },
  {
    id: 'mandor-sistem',
    label: 'Akun & Profil',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan Akun', icon: 'settings', view: 'settings' },
    ],
  },
];

// Penjahit/Tailor navigation chapters (Slide 04: Lihat tugas komponen, Laporkan hasil kerja)
// Prohibited: "Tidak dapat mengedit catatan output yang sudah diverifikasi"
const tailorChapters: NavChapter[] = [
  {
    id: 'tailor-stasiun',
    label: 'Stasiun Operator Jahit',
    icon: 'factory',
    items: [
      { id: 'production', label: 'Tugas & Lapor Kerja', icon: 'factory', view: 'production' },
    ],
  },
  {
    id: 'tailor-sistem',
    label: 'Akun & Profil',
    icon: 'settings',
    items: [
      { id: 'settings', label: 'Pengaturan Akun', icon: 'settings', view: 'settings' },
    ],
  },
];

// ─────────────────────────────────────────────────────────────────────────────

function App() {
  // ── view state ──────────────────────────────────────────────────────────────
  const [currentView, setCurrentView] = useState('overview');
  const [globalSearch, setGlobalSearch] = useState('');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // ── portal session (auth gate: unauthenticated users see the login page) ───
  const [session, setSession] = useState<AuthSession | null>(() => getSession());
  useEffect(() => subscribeAuth(setSession), []);

  const handleLogout = useCallback(async () => {
    const token = getSession()?.token;
    if (token) await authLogout(token);
    clearSession();
  }, []);

  const role = session?.actor.role;
  const isClient = role === 'client';
  const isAdmin = role === 'admin';
  const isQcInspector = role === 'QCInspector' || role === 'qc' || role === 'qc_inspector';
  const isFinancePayroll = role === 'FinancePayroll' || role === 'finance' || role === 'finance_payroll';
  const isOwner = role === 'Owner' || role === 'owner';
  const isSample = role === 'Sample' || role === 'sample' || role === 'tim_sample';
  const isWarehouse = role === 'Warehouse' || role === 'warehouse' || role === 'gudang';
  const isMandor = role === 'Mandor' || role === 'mandor' || role === 'kepala_produksi';
  const isTailor = role === 'Tailor' || role === 'tailor' || role === 'penjahit';

  // Role default landing view — exact canonical role, roleless lands on settings.
  const defaultLandingView = useMemo(() => landingViewForRole(role), [role]);

  // Explicit view authorization matrix based strictly on Slide 04 IZIN & PEMBATASAN.
  // Authorization uses exact canonical roles; alias flags are cosmetic only.
  const isViewAuthorized = useMemo(() => {
    const allowed = allowedViewsForRole(role);
    if (allowed === 'all') return true;
    return allowed.has(currentView);
  }, [role, currentView]);

  // Automatically switch away from unauthorized views upon login
  // Note: 'copilot' and 'settings' are allowed across all roles for demo purposes.
  // TODO (Future): Dedicated role-scoped AI copilot experience with role-specific prompt and data filters.
  useEffect(() => {
    if (!isViewAuthorized) {
      setCurrentView(defaultLandingView);
    }
  }, [isViewAuthorized, defaultLandingView]);

  // Role-based navigation chapters — driven by the same exact role keys as the
  // authorization matrix. Unknown roles must not fall through to full `chapters`.
  const navChapters = useMemo<NavChapter[]>(() => {
    switch (navKeyForRole(role)) {
      case 'client': return clientChapters;
      case 'qc': return qcInspectorChapters;
      case 'finance': return financePayrollChapters;
      case 'owner': return ownerChapters;
      case 'sample': return sampleChapters;
      case 'warehouse': return warehouseChapters;
      case 'mandor': return mandorChapters;
      case 'tailor': return tailorChapters;
      case 'admin':
        return [
          ...chapters,
          {
            id: 'administrasi', label: 'Administrasi', icon: 'badge-check',
            items: [
              { id: 'access-approvals', label: 'Persetujuan Akses', icon: 'check-circle', view: 'access-approvals' },
            ],
          },
        ];
      default: return rolelessChapters;
    }
  }, [role]);

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
  const currentLabel = currentView === 'copilot'
    ? 'Lukla Assistant'
    : (navChapters.flatMap(c => c.items).find(n => n.view === currentView)?.label ?? 'Overview');

  // ── shared style constants ────────────────────────────────────────────────────
  const inputCls  = "w-full rounded-[10px] px-3 py-2.5 text-[13px]";
  const btnPrimary   = "btn-primary";
  const btnSecondary = "btn-secondary";

  // ── render ────────────────────────────────────────────────────────────────────

  // Rules of Hooks: every hook below must execute on the pre-login render too.
  // Pre-login all role flags are false, so these memos fall through to neutral
  // defaults; the auth gate return lives after the final hook.
  const profileName = session?.actor.displayName ?? '';

  const brandLabel = useMemo(() => {
    if (isClient) return 'Lukla B2B Client Portal';
    if (isQcInspector) return 'Lukla Quality Control';
    if (isFinancePayroll) return 'Lukla Finance & Payroll';
    if (isOwner) return 'Lukla Executive Suite';
    if (isSample) return 'Lukla Sampling & R&D';
    if (isWarehouse) return 'Lukla Gudang & Logistik';
    if (isMandor) return 'Lukla Supervisi Produksi';
    if (isTailor) return 'Lukla Stasiun Penjahit';
    if (isAdmin) return 'Lukla IT Operations';
    return 'Lukla Ops Engine';
  }, [isClient, isQcInspector, isFinancePayroll, isOwner, isSample, isWarehouse, isMandor, isTailor, isAdmin]);

  const portalBadge = useMemo(() => {
    if (isClient) return { label: 'Portal Klien (B2B)', style: { borderColor: 'var(--c-brand)', color: 'var(--c-brand)', background: 'var(--c-brand-bg)' } };
    if (isQcInspector) return { label: 'QC Inspector · Quality', style: { borderColor: 'var(--c-ok-2)', color: 'var(--c-ok-2)', background: 'var(--c-ok-bg)' } };
    if (isFinancePayroll) return { label: 'Finance & Payroll · Finance', style: { borderColor: 'var(--blue)', color: 'var(--blue)', background: 'var(--blue-light)' } };
    if (isOwner) return { label: 'Owner · Eksekutif', style: { borderColor: '#d97706', color: '#d97706', background: 'rgba(217, 119, 6, 0.1)' } };
    if (isSample) return { label: 'Tim Sample · Sample', style: { borderColor: '#0284c7', color: '#0284c7', background: 'rgba(2, 132, 199, 0.1)' } };
    if (isWarehouse) return { label: 'Gudang · Stok', style: { borderColor: '#ea580c', color: '#ea580c', background: 'rgba(234, 88, 12, 0.1)' } };
    if (isMandor) return { label: 'Mandor · Line', style: { borderColor: '#7c3aed', color: '#7c3aed', background: 'rgba(124, 58, 237, 0.1)' } };
    if (isTailor) return { label: 'Penjahit · Operator', style: { borderColor: 'var(--c-hair)', color: 'var(--c-ink-muted)', background: 'var(--c-hair)' } };
    return { label: 'Portal Internal · Staf', style: { borderColor: 'var(--c-hair)', color: 'var(--c-ink-muted)', background: 'transparent' } };
  }, [isClient, isQcInspector, isFinancePayroll, isOwner, isSample, isWarehouse, isMandor, isTailor]);

  const headerSubtitle = useMemo(() => {
    if (isClient) return 'PORTAL KLIEN / B2B MAKLON';
    if (isQcInspector) return 'PENJAMINAN MUTU / QC INSPECTION';
    if (isFinancePayroll) return 'KEUANGAN, INVOICE & PENGGAJIAN';
    if (isOwner) return 'EKSEKUTIF / OWNER PORTAL';
    if (isSample) return 'R&D / TIM SAMPLE & ADIS';
    if (isWarehouse) return 'LOGISTIK / GUDANG & BAHAN TITIPAN';
    if (isMandor) return 'SUPERVISI LINE / KEPALA PRODUKSI';
    if (isTailor) return 'OPERATOR / PENJAHIT BORONGAN';
    return 'DASHBOARD / OPERASIONAL PABRIK';
  }, [isClient, isQcInspector, isFinancePayroll, isOwner, isSample, isWarehouse, isMandor, isTailor]);

  const headerCaption = useMemo(() => {
    if (isClient) return `Login aktif sebagai ${profileName} · Akses Klien B2B Terverifikasi`;
    if (isQcInspector) return `Login aktif sebagai ${profileName} · Otorisasi Inspeksi, Lolos/Reject & Cacat (Slide 04)`;
    if (isFinancePayroll) return `Login aktif sebagai ${profileName} · Otorisasi PO Bahan, Invoice & Hitung Gaji (Slide 04)`;
    if (isOwner) return `Login aktif sebagai ${profileName} · Otorisasi Analitik Tinggi & Konfigurasi Rate Card (Slide 04)`;
    if (isSample) return `Login aktif sebagai ${profileName} · Otorisasi Pemakaian Bahan & Time Study Sample (Slide 04)`;
    if (isWarehouse) return `Login aktif sebagai ${profileName} · Otorisasi Terima Titipan & Pengeluaran Cutting (Slide 04)`;
    if (isMandor) return `Login aktif sebagai ${profileName} · Otorisasi Line, Alokasi & Output 30 Menit (Slide 04)`;
    if (isTailor) return `Login aktif sebagai ${profileName} · Stasiun Operator & Pelaporan Hasil Kerja (Slide 04)`;
    return isConnected
      ? `Backend terhubung · ${timeStudies.length} studi · ${specVersions.length} spec`
      : 'Backend tidak terhubung — pastikan server berjalan di port 8009';
  }, [isClient, isQcInspector, isFinancePayroll, isOwner, isSample, isWarehouse, isMandor, isTailor, isConnected, profileName, timeStudies.length, specVersions.length]);

  const roleRestrictionReason = useMemo(() => {
    if (isClient) return 'Akun klien B2B Anda hanya diizinkan untuk melihat Persetujuan Sample, Monitoring Order Produksi, dan Inventaris Bahan Titipan sendiri.';
    if (isQcInspector) return 'Sesuai Slide 04, peran QC Inspector memiliki izin untuk inspeksi barang jadi, penetapan status lolos/reject/repair, dan jenis cacat. Peran ini dibatasi untuk tidak dapat mengubah harga borongan, data payroll/buku besar, atau data order klien.';
    if (isFinancePayroll) return 'Sesuai Slide 04, peran Finance & Payroll memiliki izin untuk membuat/menyetujui PO bahan, menerbitkan invoice, dan menghitung gaji mingguan/bulanan. Peran ini dibatasi untuk tidak dapat mengubah fisik stok gudang secara langsung atau mengakses instrumen studi waktu lantai produksi.';
    if (isOwner) return 'Sesuai Slide 04, peran Owner/Eksekutif memiliki akses analitik tinggi, konfigurasi sistem, dan rate card. Dibatasi untuk tidak dapat mengubah histori transaksi atau jurnal yang telah dikunci.';
    if (isSample) return 'Sesuai Slide 04, peran Tim Sample/Adis memiliki izin untuk mencatat pemakaian bahan sample, input time study komponen, dan persetujuan sample. Dibatasi tidak dapat menyetujui pesanan massal tanpa konfirmasi atau memodifikasi modul keuangan/payroll.';
    if (isWarehouse) return 'Sesuai Slide 04, peran Gudang/Warehouse berwenang atas stok fisik gudang, terima titipan klien, dan pengeluaran ke cutting. Dilarang mengeluarkan bahan jika ID Klien/Pesanan tidak cocok dan tidak memiliki akses ke modul finansial, time study, atau penetapan rate card.';
    if (isMandor) return 'Sesuai Slide 04, peran Kepala Produksi/Mandor berwenang mengatur line, alokasi penjahit, rate card komponen, dan pencatatan output 30 menit. Dibatasi tidak dapat mengubah formula penggajian, hasil QC final, atau inventaris gudang.';
    if (isTailor) return 'Sesuai Slide 04, peran Penjahit/Tailor hanya berwenang melihat tugas komponen dan lapor hasil kerja borongan. Dibatasi tidak dapat mengedit catatan output yang sudah diverifikasi mandor dan tidak memiliki akses manajerial/finansial.';
    return 'Modul ini dibatasi untuk staf dengan otorisasi khusus.';
  }, [isClient, isQcInspector, isFinancePayroll, isOwner, isSample, isWarehouse, isMandor, isTailor]);

  // Auth gate: unauthenticated users see the portal entry page only.
  if (!session) {
    return <PortalAuthView onAuthenticated={setSession} />;
  }

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
          isClient={isClient}
          isQcInspector={isQcInspector}
          isFinancePayroll={isFinancePayroll}
          brandLabel={brandLabel}
        />
      </div>

      <main className="flex-1 overflow-y-auto page-stage flex flex-col">
        <header className="border-b" style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}>
          <div className="max-w-[1440px] mx-auto px-6 lg:px-8 flex items-center justify-between gap-4 py-3">
            <LuklaLogo size={26} />
            <span
              className="rounded-full border px-3 py-1 text-[12px] font-semibold"
              style={portalBadge.style}
            >
              {portalBadge.label}
            </span>
          </div>
        </header>

        <div className="max-w-[1440px] mx-auto p-6 lg:p-8 flex-1 w-full">

          <Header
            title={currentLabel}
            subtitle={headerSubtitle}
            caption={headerCaption}
            globalSearch={globalSearch}
            onGlobalSearchChange={setGlobalSearch}
            onMenuClick={() => setMobileNavOpen(true)}
            profileName={profileName}
            profileInitials={profileInitials}
            onLogout={handleLogout}
          />

          {/* key={currentView} remounts this wrapper on navigation so the
              page-turn animation replays for the newly opened view. */}
          <div
            key={currentView}
            className={`page-turn ${currentView === 'production' ? 'page-turn-static' : ''}`}
          >
            <ErrorBoundary>

          {/* ── ROLELESS NOTICE (DEF-002) ────────────────────────────────────── */}
          {!isKnownRole(role) && (
            <div
              role="status"
              className="surface p-4 mb-4 rounded-[12px] flex items-start gap-3"
              style={{ borderColor: '#d97706', background: 'rgba(217, 119, 6, 0.08)' }}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                fill="none" stroke="#d97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" x2="12" y1="8" y2="12" />
                <line x1="12" x2="12.01" y1="16" y2="16" />
              </svg>
              <p className="text-[13px] font-medium" style={{ color: 'var(--c-ink)' }}>
                Akun Anda belum memiliki peran operasional. Hubungi Admin IT untuk penetapan peran.
              </p>
            </div>
          )}

          {/* ── ROLE ACCESS RESTRICTION BARRIER (Slide 04) ──────────────────── */}
          {!isViewAuthorized && (
            <div className="surface p-8 max-w-[640px] mx-auto text-center rounded-[14px]">
              <div className="w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-4" style={{ background: 'var(--c-bad-bg)', color: 'var(--c-bad-4)' }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </div>
              <h2 className="text-[20px] font-bold mb-2 text-ink">Akses Dibatasi ({portalBadge.label})</h2>
              <p className="text-[14px] text-ink-muted mb-6 leading-relaxed">
                {roleRestrictionReason}
              </p>
              <button
                type="button"
                onClick={() => setCurrentView(defaultLandingView)}
                className="btn-primary justify-center text-[14px]"
              >
                Kembali ke Modul Utama
              </button>
            </div>
          )}

          {/* ── OVERVIEW (VIEW-01: Executive Operations & Financial Dashboard) ── */}
          {isViewAuthorized && currentView === 'overview' && (
            <ExecutiveDashboardView
              onNavigate={(view) => setCurrentView(view)}
              workflowSummary={workflowSummary}
              isLoading={isLoading}
              timeStudies={timeStudies}
              specVersions={specVersions}
              activities={activities}
            />
          )}

          {/* ── SAMPLE VERSIONS ───────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'sample-versions' && (
            <SampleVersionView onExportCSV={exportToCSV} />
          )}

          {/* ── STOPWATCH ─────────────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'stopwatch' && <DigitalStopwatchView />}

          {/* ── ACTIVE STUDIES ────────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'active-studies' && <ActiveStudiesView />}

          {/* ── PRODUCTION & TALLY (VIEW-04 floor terminal + admin) ───────────── */}
          {isViewAuthorized && currentView === 'production' && <ProductionView />}

          {/* ── TIME STUDIES (create + manage) ────────────────────────────────── */}
          {isViewAuthorized && currentView === 'time-studies' && (
            <TimeStudiesView
              studies={filteredStudies}
              tab={studyTab} onTabChange={setStudyTab}
              search={studySearch} onSearchChange={setStudySearch}
              onCreate={() => setShowCreateStudyModal(true)}
              onExportCSV={exportToCSV}
            />
          )}

          {/* ── STUDY LIST ────────────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'study-list' && <StudyListView onExportCSV={exportToCSV} globalSearch={globalSearch} />}

          {/* ── SPEC VERSIONS (create + manage) ───────────────────────────────── */}
          {isViewAuthorized && currentView === 'spec-versions' && (
            <SpecVersionsView
              specs={filteredSpecs}
              tab={specTab} onTabChange={setSpecTab}
              search={specSearch} onSearchChange={setSpecSearch}
              onCreate={() => setShowCreateSpecModal(true)}
              onExportCSV={exportToCSV}
            />
          )}

          {/* ── SPEC LIST ─────────────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'spec-list' && <SpecListView onExportCSV={exportToCSV} globalSearch={globalSearch} />}

          {/* ── DRIFT ANALYSIS ────────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'drift-analysis' && <DriftAnalysisView />}

          {/* ── REPORTS ───────────────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'reports' && <ReportsView onExportCSV={exportToCSV} />}

          {/* ── QUALITY CONTROL ───────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'quality' && <QualityView />}

          {/* ── LEDGER ────────────────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'ledger' && <LedgerView />}

          {/* ── PAYROLL & COSTING ─────────────────────────────────────────────── */}
          {isViewAuthorized && currentView === 'payroll' && <PayrollView />}

          {/* ── COPILOT ───────────────────────────────────────────────────────── */}
          {currentView === 'copilot' && <CopilotView isDark={isDark} onNavigate={setCurrentView} />}

          {/* ── WAREHOUSE INVENTORY (VIEW-03) ─────────────────────────────────── */}
          {isViewAuthorized && (currentView === 'warehouse' || currentView === 'view-03') && <WarehouseInventoryView />}

          {/* ── SETTINGS ──────────────────────────────────────────────────────── */}
          {currentView === 'settings' && (
            <SettingsView
              isDark={isDark}
              onToggleDark={toggleDark}
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

        <footer className="border-t mt-6" style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}>
          <div className="max-w-[1440px] mx-auto px-6 lg:px-8 py-8">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 lg:gap-8">
              <LuklaLogo size={30} />

              <span className="hidden lg:block w-px h-11 shrink-0" style={{ background: 'var(--c-hair)' }} aria-hidden="true" />

              <div className="flex-1">
                <p className="text-[15px] font-semibold" style={{ color: 'var(--c-ink)' }}>Lukla Operations Engine</p>
                <p className="text-[13px]" style={{ color: 'var(--c-ink-muted)' }}>Operational Garment Management System</p>
                <p className="text-[13px]" style={{ color: 'var(--c-ink-muted)' }}>Multi-client Manufacturing · Dynamic Payroll</p>
              </div>

              <span className="hidden lg:block w-px h-11 shrink-0" style={{ background: 'var(--c-hair)' }} aria-hidden="true" />

              <div className="flex items-start gap-2.5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--c-brand)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4 mt-0.5 shrink-0"
                  aria-hidden="true"
                >
                  <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <div>
                  <p className="text-[12px] font-semibold uppercase tracking-[.12em]" style={{ color: 'var(--c-ink-muted)' }}>
                    Lukla Manufacturing × Snøhund
                  </p>
                  <p className="text-[12px] uppercase tracking-[.12em]" style={{ color: 'var(--c-ink-muted)' }}>
                    Ciwidey Production Facility
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t flex justify-end" style={{ borderColor: 'var(--c-hair)' }}>
              <p className="text-[13px]" style={{ color: 'var(--c-ink-muted)' }}>
                © 2026 Lukla Manufacturing · Internal Operations System
              </p>
            </div>
          </div>
        </footer>
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
