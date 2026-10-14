/**
 * App — Sampling & Spec R&D Module
 * Navigation: Dashboard | Time Study | Spec Version
 */

import React, { Suspense, useState, useEffect } from 'react';
import TimeStudyPage from '@/pages/TimeStudyPage';
import SpecVersionPage from '@/pages/SpecVersionPage';
import { checkHealth, getWorkflowSummary } from '@/services/api';
import type { WorkflowSummary } from '@/types';
import '@/styles/globals.css';

type Tab = 'dashboard' | 'study' | 'spec';

// ─── Dashboard ────────────────────────────────────────────────────────────────
function DashboardPage({ isConnected }: { isConnected: boolean }) {
  const [summary, setSummary] = useState<WorkflowSummary | null>(null);

  useEffect(() => {
    if (isConnected) {
      getWorkflowSummary('default').then((r) => {
        if (r.success && r.data) setSummary(r.data);
      });
    }
  }, [isConnected]);

  return (
    <div className="space-y-6">
      {/* Hero - Apple HIG style */}
      <div className="p-8 bg-white rounded-2xl shadow-sm">
        <p className="text-xs uppercase tracking-wider text-apple-gray mb-2 font-medium">Lukla Operations Engine</p>
        <h2 className="text-3xl font-bold mb-2 text-gray-900">Sampling &amp; Spec R&amp;D</h2>
        <p className="text-apple-secondary text-base">Pencatatan studi waktu &amp; pelacakan versi spesifikasi manufaktur</p>
      </div>

      {/* Summary cards - borderless with shadow */}
      {summary ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {[
            { label: 'Studi Aktif',       value: summary.active_studies,    color: 'text-accent-blue',   bg: 'bg-blue-50'   },
            { label: 'Studi Selesai',     value: summary.completed_studies,  color: 'text-accent-green',  bg: 'bg-green-50'  },
            { label: 'Spec Aktif',        value: summary.active_specs,       color: 'text-accent-purple', bg: 'bg-purple-50' },
            { label: 'Spec dalam Review', value: summary.specs_in_review,    color: 'text-accent-orange',  bg: 'bg-orange-50'  },
            { label: 'Total Drift',       value: summary.total_drifts,       color: 'text-accent-orange', bg: 'bg-orange-50' },
            { label: 'Drift Kritis',      value: summary.critical_drifts,    color: 'text-accent-red',    bg: 'bg-red-50'    },
          ].map((c) => (
            <div key={c.label} className={`${c.bg} rounded-2xl p-6 shadow-sm`}>
              <p className="text-sm text-apple-gray mb-2 font-medium">{c.label}</p>
              <p className={`text-4xl font-bold ${c.color}`}>{c.value}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className={`p-5 rounded-2xl shadow-sm text-sm ${
          isConnected
            ? 'bg-white text-apple-gray'
            : 'bg-amber-50 text-amber-800'
        }`}>
          {isConnected
            ? 'Memuat ringkasan…'
            : '⚠️ Backend tidak terdeteksi. Pastikan uvicorn berjalan di port 8009.'}
        </div>
      )}

      {/* Quick guide - clean Apple style */}
      <div className="p-6 bg-white rounded-2xl shadow-sm">
        <p className="text-base font-semibold text-gray-900 mb-4">Panduan Cepat</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p className="font-semibold text-gray-900 mb-3 text-sm flex items-center gap-2">
              <span>⏱</span>
              <span>Time Study</span>
            </p>
            <ol className="list-decimal list-inside space-y-2 text-sm text-apple-secondary leading-relaxed">
              <li>Tab <strong className="text-gray-900">Time Study</strong> → isi nama proses → Buat Studi</li>
              <li>Klik <strong className="text-gray-900">▶ Mulai</strong> di kartu studi</li>
              <li>Input waktu siklus (ms) → <strong className="text-gray-900">+ Tambah Sampel</strong></li>
              <li>Ulangi minimal 30 sampel untuk validitas statistik</li>
              <li>Klik <strong className="text-gray-900">✓ Selesai</strong> untuk finalisasi</li>
            </ol>
          </div>
          <div>
            <p className="font-semibold text-gray-900 mb-3 text-sm flex items-center gap-2">
              <span>📄</span>
              <span>Spec Version</span>
            </p>
            <ol className="list-decimal list-inside space-y-2 text-sm text-apple-secondary leading-relaxed">
              <li>Tab <strong className="text-gray-900">Spec Version</strong> → isi nama spec → Buat Spec</li>
              <li>Tab <strong className="text-gray-900">Catat Perubahan</strong> untuk parameter baru/berubah</li>
              <li>Tab <strong className="text-gray-900">Catat Drift</strong> jika ada deviasi dari batas spec</li>
              <li>Klik <strong className="text-gray-900">Submit Review</strong> → <strong className="text-gray-900">Setujui</strong> → <strong className="text-gray-900">Aktifkan</strong></li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Root App ─────────────────────────────────────────────────────────────────
const App: React.FC = () => {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    checkHealth().then((r) => setIsConnected(r.success));
    const interval = setInterval(() => {
      checkHealth().then((r) => setIsConnected(r.success));
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'dashboard', label: 'Dashboard',    icon: '🏠' },
    { id: 'study',     label: 'Time Study',   icon: '⏱️' },
    { id: 'spec',      label: 'Spec Version', icon: '📄' },
  ];

  return (
    <div className="min-h-screen bg-apple-gray6">
      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-40 bg-white/90 backdrop-blur-xl border-b border-gray-200/30 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">

            {/* Logo */}
            <div className="flex items-center gap-2.5">
              <span className="text-2xl">🧵</span>
              <div className="hidden sm:block">
                <p className="text-sm font-semibold text-gray-900 leading-tight">Lukla Ops Engine</p>
                <p className="text-xs text-apple-gray leading-tight">Sampling &amp; Spec R&amp;D</p>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    tab === t.id
                      ? 'bg-accent-purple/10 text-purple-700'
                      : 'text-apple-gray hover:text-gray-800 hover:bg-gray-100'
                  }`}
                >
                  <span>{t.icon}</span>
                  <span className="hidden sm:inline">{t.label}</span>
                </button>
              ))}
            </div>

            {/* Status */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
              isConnected ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
            }`}>
              <span className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-accent-green animate-pulse' : 'bg-accent-orange'
              }`} />
              <span className="hidden sm:inline">
                {isConnected ? 'Connected' : 'Local Mode'}
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* ── Content ────────────────────────────────────────────────────── */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <Suspense fallback={
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600" />
          </div>
        }>
          {tab === 'dashboard' && <DashboardPage isConnected={isConnected} />}
          {tab === 'study'     && <TimeStudyPage />}
          {tab === 'spec'      && <SpecVersionPage />}
        </Suspense>
      </main>
    </div>
  );
};

export default App;
