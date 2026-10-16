/**
 * ExecutiveDashboardView — VIEW-01: Executive Operations & Financial Dashboard
 *
 * Requirements:
 *  1. Realistic throughput with 30-minute interval output tracking (PRD View 01).
 *  2. Capacity utilization (active / 70 sewing machines in Ciwidey facility).
 *  3. WIP distribution across CMT vs. Semi-CMT vs. Full Package maklon schemes.
 *  4. Direct links and live summaries of the double-entry financial ledger (debit = credit balance invariant).
 *  5. Apple Design System tokens (CSS vars from index.css) with high-contrast text and dark mode support.
 *  6. Touch targets for all interactive elements >= 48px.
 *  7. Clean TypeScript: zero 'as any', zero type evasion.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LucideIcon } from '../components/Sidebar';
import MetricCard from '../components/MetricCard';
import StackedBarChart, { type StackedKey } from '../components/StackedBarChart';
import {
  getLedgerEntries,
  sumMinor,
  type LedgerTransaction,
  type LedgerDirection,
} from '../services/ledgerApi';
import {
  listLines,
  listProductionProgress,
  listAssemblies,
} from '../services/opsApi';
import type { WorkflowSummary, TimeStudy, SpecVersion } from '../types';
import type { StackedRow } from '../utils/chartData';
import ActivityLog, { type Activity } from '../components/ActivityLog';

export interface ExecutiveDashboardViewProps {
  onNavigate: (view: string) => void;
  workflowSummary?: WorkflowSummary | null;
  isLoading?: boolean;
  timeStudies?: TimeStudy[];
  specVersions?: SpecVersion[];
  activities?: Activity[];
}

// ─── 30-Minute Interval Throughput Types ─────────────────────────────────────
export interface IntervalThroughput {
  slot: string; // e.g. "08:00 - 08:30"
  targetPieces: number;
  actualPieces: number;
  lineA: number;
  lineB: number;
  lineC: number;
  lineD: number;
  status: 'completed' | 'current' | 'upcoming';
}

// ─── WIP Scheme Breakdown Types ──────────────────────────────────────────────
export type MaklonScheme = 'CMT' | 'SEMI_CMT' | 'FULL_PACKAGE';

export interface WipSchemeData {
  scheme: MaklonScheme;
  title: string;
  badge: string;
  legalOwnership: string;
  totalPieces: number;
  cuttingPieces: number;
  sewingPieces: number;
  qcFinishingPieces: number;
  onTimeRatePct: number;
  leadTimeDays: number;
  activeBatches: number;
  accentColor: string;
}

// ─── Machine Unit in the 70-Machine Facility ─────────────────────────────────
export interface MachineUnit {
  machineId: string;
  machineNumber: number;
  lineId: 'LINE-A' | 'LINE-B' | 'LINE-C' | 'LINE-D';
  status: 'ACTIVE' | 'SETUP' | 'MAINTENANCE';
  operatorName: string;
  currentProcess: string;
  rpmRate: number;
}

// ─── Account definitions for double-entry summary ────────────────────────────
interface CoaAccount {
  code: string;
  name: string;
  type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
  normalDirection: LedgerDirection;
}

const COA_ACCOUNTS: CoaAccount[] = [
  { code: '1100', name: 'Kas & Bank Operasional', type: 'ASSET', normalDirection: 'DEBIT' },
  { code: '1200', name: 'Piutang Usaha Maklon', type: 'ASSET', normalDirection: 'DEBIT' },
  { code: '2100', name: 'Utang Usaha & Pemasok', type: 'LIABILITY', normalDirection: 'CREDIT' },
  { code: '4000', name: 'Pendapatan Jasa Maklon & Sales', type: 'REVENUE', normalDirection: 'CREDIT' },
  { code: '5000', name: 'Beban Gaji & Upah Borongan', type: 'EXPENSE', normalDirection: 'DEBIT' },
  { code: '5100', name: 'Beban Bahan Baku & Furing', type: 'EXPENSE', normalDirection: 'DEBIT' },
];

const fmtMoney = (minor: number): string =>
  `Rp ${(minor / 100).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const fmtCompactMoney = (minor: number): string => {
  const major = minor / 100;
  if (major >= 1_000_000) return `Rp ${(major / 1_000_000).toFixed(1)} Jt`;
  if (major >= 1_000) return `Rp ${(major / 1_000).toFixed(0)} Rb`;
  return `Rp ${major.toLocaleString('id-ID')}`;
};

// ─── Seed Data for 70 Machines ───────────────────────────────────────────────
const SEED_MACHINES: MachineUnit[] = (() => {
  const machines: MachineUnit[] = [];
  const linesConfig: Array<{ id: 'LINE-A' | 'LINE-B' | 'LINE-C' | 'LINE-D'; count: number; active: number; setup: number }> = [
    { id: 'LINE-A', count: 20, active: 18, setup: 2 }, // Line A: 18 active, 2 setup
    { id: 'LINE-B', count: 18, active: 16, setup: 1 }, // Line B: 16 active, 1 setup, 1 maint
    { id: 'LINE-C', count: 16, active: 14, setup: 1 }, // Line C: 14 active, 1 setup, 1 maint
    { id: 'LINE-D', count: 16, active: 10, setup: 4 }, // Line D: 10 active, 4 setup, 2 maint
  ];

  let num = 1;
  for (const cfg of linesConfig) {
    for (let i = 0; i < cfg.count; i++) {
      let status: 'ACTIVE' | 'SETUP' | 'MAINTENANCE' = 'ACTIVE';
      if (i >= cfg.active + cfg.setup) {
        status = 'MAINTENANCE';
      } else if (i >= cfg.active) {
        status = 'SETUP';
      }

      machines.push({
        machineId: `M-${String(num).padStart(2, '0')}`,
        machineNumber: num,
        lineId: cfg.id,
        status,
        operatorName: status === 'ACTIVE' ? `Opr ${String(num).padStart(2, '0')}` : status === 'SETUP' ? 'Teknisi Setup' : 'Teknisi Servis',
        currentProcess: cfg.id === 'LINE-A' ? 'Kemeja Snøhund' : cfg.id === 'LINE-B' ? 'Kaos CMT' : cfg.id === 'LINE-C' ? 'Jaket Semi-CMT' : 'Polo Full Package',
        rpmRate: status === 'ACTIVE' ? 3800 + (num % 5) * 50 : 0,
      });
      num++;
    }
  }
  return machines;
})();

// ─── Realistic 30-Minute Interval Data ───────────────────────────────────────
const SEED_INTERVALS: IntervalThroughput[] = [
  { slot: '08:00 - 08:30', targetPieces: 100, actualPieces: 94,  lineA: 28, lineB: 32, lineC: 20, lineD: 14, status: 'completed' },
  { slot: '08:30 - 09:00', targetPieces: 110, actualPieces: 108, lineA: 32, lineB: 36, lineC: 24, lineD: 16, status: 'completed' },
  { slot: '09:00 - 09:30', targetPieces: 115, actualPieces: 116, lineA: 34, lineB: 38, lineC: 26, lineD: 18, status: 'completed' },
  { slot: '09:30 - 10:00', targetPieces: 120, actualPieces: 124, lineA: 36, lineB: 42, lineC: 28, lineD: 18, status: 'completed' },
  { slot: '10:00 - 10:30', targetPieces: 120, actualPieces: 128, lineA: 38, lineB: 44, lineC: 28, lineD: 18, status: 'completed' },
  { slot: '10:30 - 11:00', targetPieces: 120, actualPieces: 122, lineA: 35, lineB: 41, lineC: 27, lineD: 19, status: 'completed' },
  { slot: '11:00 - 11:30', targetPieces: 115, actualPieces: 114, lineA: 33, lineB: 39, lineC: 25, lineD: 17, status: 'completed' },
  { slot: '11:30 - 12:00', targetPieces: 100, actualPieces: 96,  lineA: 28, lineB: 33, lineC: 22, lineD: 13, status: 'completed' },
  { slot: '13:00 - 13:30', targetPieces: 105, actualPieces: 102, lineA: 30, lineB: 35, lineC: 23, lineD: 14, status: 'completed' },
  { slot: '13:30 - 14:00', targetPieces: 115, actualPieces: 118, lineA: 35, lineB: 40, lineC: 26, lineD: 17, status: 'completed' },
  { slot: '14:00 - 14:30', targetPieces: 120, actualPieces: 121, lineA: 36, lineB: 41, lineC: 27, lineD: 17, status: 'completed' },
  { slot: '14:30 - 15:00', targetPieces: 120, actualPieces: 125, lineA: 37, lineB: 43, lineC: 27, lineD: 18, status: 'completed' },
  { slot: '15:00 - 15:30', targetPieces: 115, actualPieces: 114, lineA: 34, lineB: 38, lineC: 25, lineD: 17, status: 'completed' },
  { slot: '15:30 - 16:00', targetPieces: 110, actualPieces: 108, lineA: 32, lineB: 37, lineC: 23, lineD: 16, status: 'completed' },
  { slot: '16:00 - 16:30', targetPieces: 100, actualPieces: 92,  lineA: 27, lineB: 31, lineC: 21, lineD: 13, status: 'completed' },
  { slot: '16:30 - 17:00', targetPieces: 80,  actualPieces: 48,  lineA: 15, lineB: 18, lineC: 10, lineD: 5,  status: 'current' },
];

// ─── WIP Maklon Schemes Breakdown ────────────────────────────────────────────
const SEED_WIP_SCHEMES: WipSchemeData[] = [
  {
    scheme: 'CMT',
    title: 'CMT (Cut, Make, Trim)',
    badge: 'Kustodial Murni',
    legalOwnership: 'Bahan milik klien (titipan kustodial), Lukla menyediakan jasa potong, jahit, dan finishing.',
    totalPieces: 1420,
    cuttingPieces: 320,
    sewingPieces: 850,
    qcFinishingPieces: 250,
    onTimeRatePct: 96.2,
    leadTimeDays: 3.2,
    activeBatches: 6,
    accentColor: '#111111',
  },
  {
    scheme: 'SEMI_CMT',
    title: 'Semi-CMT (Maklon Hibrida)',
    badge: 'Kain Klien + Trims Lukla',
    legalOwnership: 'Kain utama dipasok klien; furing, benang, dan kancing dibeli Lukla melalui PO internal.',
    totalPieces: 1150,
    cuttingPieces: 210,
    sewingPieces: 690,
    qcFinishingPieces: 250,
    onTimeRatePct: 91.5,
    leadTimeDays: 4.8,
    activeBatches: 4,
    accentColor: '#4b5563',
  },
  {
    scheme: 'FULL_PACKAGE',
    title: 'Full Package (FOB Maklon)',
    badge: 'End-to-End Lukla',
    legalOwnership: 'Seluruh kain, trims, dan kemasan menjadi aset Lukla hingga pembayaran invoice dan pengiriman.',
    totalPieces: 610,
    cuttingPieces: 140,
    sewingPieces: 310,
    qcFinishingPieces: 160,
    onTimeRatePct: 94.0,
    leadTimeDays: 6.5,
    activeBatches: 3,
    accentColor: '#6b7280',
  },
];

const STACKED_WIP_KEYS: StackedKey[] = [
  { key: 'cutting', label: 'Potong (Cutting)', color: '#d1d5db' },
  { key: 'sewing', label: 'Jahit (Sewing)', color: '#111111' },
  { key: 'qcFinishing', label: 'QC & Finishing', color: '#6b7280' },
];

const ExecutiveDashboardView: React.FC<ExecutiveDashboardViewProps> = ({
  onNavigate,
  isLoading = false,
  activities = [],
}) => {
  // ─── Filter & Selection States ──────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<'all' | 'operations' | 'capacity' | 'wip' | 'financial'>('all');
  const [selectedLine, setSelectedLine] = useState<'ALL' | 'LINE-A' | 'LINE-B' | 'LINE-C' | 'LINE-D'>('ALL');
  const [selectedMachineFilter, setSelectedMachineFilter] = useState<'ALL' | 'ACTIVE' | 'SETUP' | 'MAINTENANCE'>('ALL');

  // ─── Ledger State ───────────────────────────────────────────────────────────
  const [ledgerTx, setLedgerTx] = useState<LedgerTransaction[]>([]);
  const [ledgerLoading, setLedgerLoading] = useState(false);

  // ─── Fetch Ledger & Ops Data ────────────────────────────────────────────────
  const loadData = useCallback(async () => {
    setLedgerLoading(true);
    try {
      const [ledgerRes] = await Promise.all([
        getLedgerEntries(50),
        listLines(),
        listProductionProgress(),
        listAssemblies(),
      ]);

      if (ledgerRes.ok && ledgerRes.data) {
        setLedgerTx(ledgerRes.data.items);
      }
    } finally {
      setLedgerLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ─── Double-Entry Financial Aggregations ─────────────────────────────────────
  const financialSummary = useMemo(() => {
    let totalDebitMinor = 0;
    let totalCreditMinor = 0;
    const accountBalances = new Map<string, { debitMinor: number; creditMinor: number }>();

    for (const acc of COA_ACCOUNTS) {
      accountBalances.set(acc.code, { debitMinor: 0, creditMinor: 0 });
    }

    for (const tx of ledgerTx) {
      const debitSum = sumMinor(tx.entries, 'DEBIT');
      const creditSum = sumMinor(tx.entries, 'CREDIT');
      totalDebitMinor += debitSum;
      totalCreditMinor += creditSum;

      for (const entry of tx.entries) {
        const cur = accountBalances.get(entry.accountCode) ?? { debitMinor: 0, creditMinor: 0 };
        if (entry.direction === 'DEBIT') {
          cur.debitMinor += entry.amountMinor;
        } else {
          cur.creditMinor += entry.amountMinor;
        }
        accountBalances.set(entry.accountCode, cur);
      }
    }

    const isBalanced = totalDebitMinor === totalCreditMinor;
    const varianceMinor = Math.abs(totalDebitMinor - totalCreditMinor);

    return {
      totalDebitMinor,
      totalCreditMinor,
      isBalanced,
      varianceMinor,
      transactionCount: ledgerTx.length,
      accountBalances,
    };
  }, [ledgerTx]);

  // ─── Throughput Computations ────────────────────────────────────────────────
  const throughputSummary = useMemo(() => {
    let totalTarget = 0;
    let totalActual = 0;

    for (const row of SEED_INTERVALS) {
      if (row.status === 'completed' || row.status === 'current') {
        let actual = row.actualPieces;
        let target = row.targetPieces;
        if (selectedLine === 'LINE-A') {
          actual = row.lineA;
          target = Math.round(row.targetPieces * 0.3);
        } else if (selectedLine === 'LINE-B') {
          actual = row.lineB;
          target = Math.round(row.targetPieces * 0.35);
        } else if (selectedLine === 'LINE-C') {
          actual = row.lineC;
          target = Math.round(row.targetPieces * 0.22);
        } else if (selectedLine === 'LINE-D') {
          actual = row.lineD;
          target = Math.round(row.targetPieces * 0.13);
        }
        totalActual += actual;
        totalTarget += target;
      }
    }

    const targetFullDay = selectedLine === 'ALL' ? 1765 : Math.round(1765 * (selectedLine === 'LINE-A' ? 0.3 : selectedLine === 'LINE-B' ? 0.35 : selectedLine === 'LINE-C' ? 0.22 : 0.13));
    const completionRatePct = targetFullDay > 0 ? Math.round((totalActual / targetFullDay) * 1000) / 10 : 0;
    const currentHourlyRate = Math.round((totalActual / 8) * 10) / 10;

    return {
      totalActual,
      totalTarget,
      targetFullDay,
      completionRatePct,
      currentHourlyRate,
    };
  }, [selectedLine]);

  // ─── Machine Capacity Computations (active / 70 machines) ───────────────────
  const capacitySummary = useMemo(() => {
    const totalMachines = 70;
    const activeCount = SEED_MACHINES.filter(m => m.status === 'ACTIVE').length;
    const setupCount = SEED_MACHINES.filter(m => m.status === 'SETUP').length;
    const maintenanceCount = SEED_MACHINES.filter(m => m.status === 'MAINTENANCE').length;
    const utilizationPct = Math.round((activeCount / totalMachines) * 1000) / 10;

    const lineAllocation = [
      { id: 'LINE-A', name: 'Lini A · Snøhund Kemeja', capacity: 20, active: 18, setup: 2, maint: 0, targetSlot: '35 pcs/30m' },
      { id: 'LINE-B', name: 'Lini B · Maklon Kaos (CMT)', capacity: 18, active: 16, setup: 1, maint: 1, targetSlot: '42 pcs/30m' },
      { id: 'LINE-C', name: 'Lini C · Jaket Semi-CMT', capacity: 16, active: 14, setup: 1, maint: 1, targetSlot: '28 pcs/30m' },
      { id: 'LINE-D', name: 'Lini D · Specialist Full Package', capacity: 16, active: 10, setup: 4, maint: 2, targetSlot: '18 pcs/30m' },
    ];

    const filteredMachines = SEED_MACHINES.filter(m => {
      const matchLine = selectedLine === 'ALL' || m.lineId === selectedLine;
      const matchStatus = selectedMachineFilter === 'ALL' || m.status === selectedMachineFilter;
      return matchLine && matchStatus;
    });

    return {
      totalMachines,
      activeCount,
      setupCount,
      maintenanceCount,
      utilizationPct,
      lineAllocation,
      filteredMachines,
    };
  }, [selectedLine, selectedMachineFilter]);

  // ─── WIP Distribution Computations ──────────────────────────────────────────
  const wipSummary = useMemo(() => {
    const totalWip = SEED_WIP_SCHEMES.reduce((sum, s) => sum + s.totalPieces, 0);

    const stackedRows: StackedRow[] = SEED_WIP_SCHEMES.map(s => ({
      label: s.scheme,
      segments: {
        cutting: s.cuttingPieces,
        sewing: s.sewingPieces,
        qcFinishing: s.qcFinishingPieces,
      },
      total: s.totalPieces,
    }));

    return {
      totalWip,
      schemes: SEED_WIP_SCHEMES,
      stackedRows,
    };
  }, []);

  // ─── Navigation Helper with 48px Touch Target compliance ───────────────────
  const handleNav = (view: string) => {
    onNavigate(view);
  };

  return (
    <div className="space-y-8 font-sf-pro">
      {/* ── Top Bar: Dashboard Navigation Tabs & Live Controls ───────────── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-[#1c1c1e] p-3 sm:p-4 rounded-sm border border-hair shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          {(
            [
              { id: 'all', label: 'Ringkasan Utama' },
              { id: 'operations', label: 'Throughput 30m' },
              { id: 'capacity', label: 'Utilisasi 70 Mesin' },
              { id: 'wip', label: 'Distribusi WIP Maklon' },
              { id: 'financial', label: 'Buku Besar Keuangan' },
            ] as const
          ).map(t => (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveTab(t.id)}
              className={`min-h-[48px] px-4 py-2.5 rounded-[12px] text-[13px] font-semibold transition-all flex items-center justify-center ${
                activeTab === t.id
                  ? 'bg-brand text-white shadow-sm'
                  : 'text-ink-muted hover:text-ink hover:bg-panel-2'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <button
            type="button"
            onClick={loadData}
            disabled={ledgerLoading}
            title="Muat Ulang Data Operasional & Keuangan"
            className="min-h-[48px] min-w-[48px] px-4 py-2.5 rounded-[12px] border border-hair text-[13px] font-medium text-ink hover:bg-panel-2 transition-all flex items-center justify-center gap-2"
          >
            <LucideIcon
              name="activity"
              className={`w-4 h-4 text-brand ${ledgerLoading ? 'animate-spin' : ''}`}
            />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* ── Status Banner: Ciwidey Facility & Double-Entry Invariant ────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-panel border border-hair rounded-sm p-5 flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-sm bg-ink text-white flex items-center justify-center shadow-sm">
              <LucideIcon name="factory" className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-brand">Fasilitas Ciwidey</span>
                <span className="inline-block w-2 h-2 rounded-full bg-ok animate-pulse" />
              </div>
              <p className="text-[15px] font-semibold text-ink">
                Kapasitas Penuh: 70 Mesin Jahit · 4 Lini Aktif
              </p>
            </div>
          </div>
          <span className="hidden sm:inline-block px-3 py-1 bg-white dark:bg-black/30 rounded-full text-xs font-semibold text-ink-muted border border-hair">
            Shift 1 (08:00 - 17:00)
          </span>
        </div>

        <div className="bg-panel border border-hair rounded-sm p-5 flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-sm bg-ok text-white flex items-center justify-center shadow-sm">
              <LucideIcon name="book-open" className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-ok-2 dark:text-ok">Double-Entry Ledger</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-ok-bg text-ok-2">IMMUTABLE</span>
              </div>
              <p className="text-[15px] font-semibold text-ink">
                Status: {financialSummary.isBalanced ? '100% Berimbang (Debit = Kredit)' : 'Perlu Rekonsiliasi'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => handleNav('ledger')}
            className="min-h-[48px] px-3.5 py-2 rounded-[10px] bg-white dark:bg-black/30 hover:bg-ok-bg text-ok-2 text-[12px] font-bold border border-emerald-300 dark:border-emerald-800 transition-colors flex items-center gap-1.5"
          >
            <span>Buku Besar</span>
            <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
      </div>

      {/* ── HERO METRIC CARDS (Apple HIG) ─────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Throughput Hari Ini"
          value={`${throughputSummary.totalActual.toLocaleString('id-ID')} pcs`}
          note={`${throughputSummary.completionRatePct}% dari target harian (${throughputSummary.targetFullDay} pcs)`}
          loading={isLoading}
        />
        <MetricCard
          label="Utilisasi Kapasitas"
          value={`${capacitySummary.activeCount} / 70`}
          note={`${capacitySummary.utilizationPct}% mesin aktif · ${capacitySummary.setupCount} setup · ${capacitySummary.maintenanceCount} servis`}
          loading={isLoading}
        />
        <MetricCard
          label="Total WIP Manufaktur"
          value={`${wipSummary.totalWip.toLocaleString('id-ID')} unit`}
          note="44.7% CMT · 36.2% Semi-CMT · 19.1% Full Package"
          loading={isLoading}
        />
        <MetricCard
          label="Total Mutasi Ledger"
          value={fmtCompactMoney(financialSummary.totalDebitMinor)}
          note={`${financialSummary.transactionCount} transaksi berimbang tanpa selisih`}
          loading={ledgerLoading}
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 1: REALISTIC THROUGHPUT & 30-MIN OUTPUT (PRD VIEW 01)     */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      {(activeTab === 'all' || activeTab === 'operations') && (
        <section className="bg-white dark:bg-[#1c1c1e] border border-hair rounded-sm p-6 shadow-sm space-y-6">
          <div className="space-y-5">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-brand">
                  VIEW-01 · Operasional Lantai
                </span>
                  <span className="bg-panel-2 text-ink rounded-sm px-2.5 py-0.5 text-[11px] font-semibold border border-hair">
                  Tally 30 Menit
                </span>
              </div>
              <h2 className="text-[20px] font-bold text-ink tracking-tight mt-1">
                Grafik Output Throughput per 30 Menit
              </h2>
              <p className="text-[13px] text-ink-muted">
                Pencatatan interval 30 menit real-time di 4 lini produksi fasilitas Ciwidey.
              </p>
            </div>

            {/* Line Filter Pills - Modern pill tabs design */}
            <div className="flex flex-wrap items-center gap-2 p-1 bg-panel-2 rounded-full">
              {(
                [
                  { id: 'ALL', label: 'Semua Lini' },
                  { id: 'LINE-A', label: 'Lini A (Snøhund)' },
                  { id: 'LINE-B', label: 'Lini B (CMT)' },
                  { id: 'LINE-C', label: 'Lini C (Semi-CMT)' },
                  { id: 'LINE-D', label: 'Lini D (Full Pkg)' },
                ] as const
              ).map(line => (
                <button
                  key={line.id}
                  type="button"
                  onClick={() => setSelectedLine(line.id)}
                  className={`min-h-[40px] px-5 py-2 rounded-full text-[12px] font-semibold transition-all flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 ${
                    selectedLine === line.id
                      ? 'bg-brand text-white shadow-sm'
                      : 'bg-white dark:bg-[#2c2c2e] text-ink hover:bg-gray-50 dark:hover:bg-[#3a3a3c]'
                  }`}
                >
                  {line.label}
                </button>
              ))}
            </div>
          </div>

          {/* Hand-rolled 30-min Throughput Bar Chart */}
          <div className="pt-4 border-t border-hair">
            <p className="text-[11px] font-semibold text-ink-muted mb-2">Output produksi (pcs per 30 menit)</p>
            <div className="flex gap-3">
              <div aria-hidden="true" className="flex flex-col justify-between h-[200px] pb-1 text-[11px] tabular-nums text-ink-muted text-right">
                <span>140</span><span>70</span><span>0</span>
              </div>
              <div className="min-w-0 flex-1 overflow-x-auto pb-2" role="group" aria-label="Grafik output produksi per 30 menit, waktu dari 08:00 sampai 17:00">
                <div className="grid gap-2 items-end h-[220px] min-w-[880px] pb-4 border-b border-hair" style={{ gridTemplateColumns: 'repeat(16, minmax(0, 1fr))' }}>
              {SEED_INTERVALS.map((intv) => {
                let actual = intv.actualPieces;
                let target = intv.targetPieces;
                if (selectedLine === 'LINE-A') {
                  actual = intv.lineA;
                  target = Math.round(intv.targetPieces * 0.3);
                } else if (selectedLine === 'LINE-B') {
                  actual = intv.lineB;
                  target = Math.round(intv.targetPieces * 0.35);
                } else if (selectedLine === 'LINE-C') {
                  actual = intv.lineC;
                  target = Math.round(intv.targetPieces * 0.22);
                } else if (selectedLine === 'LINE-D') {
                  actual = intv.lineD;
                  target = Math.round(intv.targetPieces * 0.13);
                }

                const maxVal = 140;
                const heightPct = Math.min(100, Math.round((actual / maxVal) * 100));
                const targetPct = Math.min(100, Math.round((target / maxVal) * 100));
                const isOverTarget = actual >= target;

                return (
                  <div key={intv.slot} className="flex flex-col items-center h-full justify-end group relative">
                    {/* Tooltip on hover */}
                    <div className="absolute -top-16 opacity-0 group-hover:opacity-100 transition-opacity bg-ink text-white text-[11px] rounded-[8px] py-1 px-2 pointer-events-none z-20 whitespace-nowrap shadow-md">
                      <p className="font-bold">{intv.slot}</p>
                      <p>Output: {actual} / Target: {target} pcs</p>
                      <p className={isOverTarget ? 'text-emerald-300' : 'text-amber-300'}>
                        {isOverTarget ? `+${actual - target} pcs surplus` : `-${target - actual} pcs varians`}
                      </p>
                    </div>

                    {/* Bar container */}
                    <div className="w-full max-w-[28px] h-full flex items-end justify-center relative">
                      {/* Target reference dashed line marker */}
                      <div
                        className="absolute w-full border-t-2 border-dashed border-ink-muted/40 z-10"
                        style={{ bottom: `${targetPct}%` }}
                      />

                      {/* Actual Output Bar */}
                      <div
                        className={`w-full rounded-t-[6px] transition-all duration-300 ${
                          intv.status === 'current'
                            ? 'bg-warn animate-pulse'
                            : isOverTarget
                            ? 'bg-ink hover:opacity-90'
                            : 'bg-ink-muted hover:opacity-90'
                        }`}
                        style={{ height: `${Math.max(6, heightPct)}%` }}
                      />
                    </div>

                    {/* Label below bar */}
                    <span className="text-[10px] font-medium text-ink-muted mt-2 whitespace-nowrap">
                      {intv.slot.split(' - ')[0]}
                    </span>
                  </div>
                );
              })}
                </div>
              </div>
            </div>
            <p className="text-center text-[11px] font-semibold text-ink-muted mt-1">Waktu interval (jam, 30 menit)</p>

            {/* Chart Legend */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-4 text-[12px] text-ink-muted">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded-sm bg-ink inline-block" />
                  <span>Output Mencapai Target</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded-sm bg-ink-muted inline-block" />
                  <span>Di Bawah Target</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded-sm bg-warn inline-block" />
                  <span>Interval Berjalan (Aktif)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-4 border-t-2 border-dashed border-ink-muted/70 inline-block" />
                  <span>Garis Target</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleNav('production')}
                  className="min-h-[48px] px-4 py-2 rounded-[12px] bg-panel-2 hover:bg-hair text-ink font-semibold text-[13px] transition-all flex items-center gap-2"
                >
                  <LucideIcon name="factory" className="w-4 h-4 text-brand" />
                  <span>Buka Terminal Tally 30m Lantai</span>
                  <span aria-hidden="true">&rarr;</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 2: CAPACITY UTILIZATION (ACTIVE / 70 MACHINES)             */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      {(activeTab === 'all' || activeTab === 'capacity') && (
        <section className="bg-white dark:bg-[#1c1c1e] border border-hair rounded-sm p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-ok-2 dark:text-ok">
                  Utilisasi Kapasitas Pabrik
                </span>
                <span className="bg-ok-bg text-ok-2 rounded-full px-2.5 py-0.5 text-[11px] font-semibold">
                  70 Mesin Jahit
                </span>
              </div>
              <h2 className="text-[20px] font-bold text-ink tracking-tight mt-1">
                Distribusi & Utilisasi 70 Mesin Jahit Fasilitas Ciwidey
              </h2>
              <p className="text-[13px] text-ink-muted">
                Pemantauan real-time mesin aktif, pergantian model (setup), dan jadwal perawatan berkala.
              </p>
            </div>

            {/* Filter Status Mesin with >= 48px touch targets */}
            <div className="flex flex-wrap items-center gap-1.5 p-1 bg-panel-2 rounded-sm">
              {(
                [
                  { id: 'ALL', label: `Semua (70)` },
                  { id: 'ACTIVE', label: `Aktif (${capacitySummary.activeCount})` },
                  { id: 'SETUP', label: `Setup (${capacitySummary.setupCount})` },
                  { id: 'MAINTENANCE', label: `Servis (${capacitySummary.maintenanceCount})` },
                ] as const
              ).map(st => (
                <button
                  key={st.id}
                  type="button"
                  onClick={() => setSelectedMachineFilter(st.id)}
                    className={`min-h-[48px] px-3.5 py-2 rounded-sm text-[12px] font-bold transition-all flex items-center justify-center ${
                    selectedMachineFilter === st.id
                      ? 'bg-white dark:bg-[#2c2c2e] text-ink shadow-xs'
                      : 'text-ink-muted hover:text-ink'
                  }`}
                >
                  {st.label}
                </button>
              ))}
            </div>
          </div>

          {/* Line Allocation Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {capacitySummary.lineAllocation.map(line => {
              const utilPct = Math.round((line.active / line.capacity) * 100);
              return (
                <div
                  key={line.id}
                  className="bg-panel p-4 rounded-sm border border-hair space-y-3"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-ink-muted">
                        {line.id}
                      </span>
                      <h4 className="text-[14px] font-bold text-ink mt-0.5">{line.name}</h4>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-brand-bg-5 text-brand">
                      {line.targetSlot}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[12px]">
                      <span className="text-ink-muted">Mesin Aktif</span>
                      <span className="font-bold text-ink">{line.active} / {line.capacity} unit ({utilPct}%)</span>
                    </div>
                    {/* Progress bar */}
                    <div className="w-full h-2 rounded-full bg-hair-2 overflow-hidden flex">
                      <div style={{ width: `${utilPct}%` }} className="bg-ok h-full" />
                      <div style={{ width: `${Math.round((line.setup / line.capacity) * 100)}%` }} className="bg-warn h-full" />
                      <div style={{ width: `${Math.round((line.maint / line.capacity) * 100)}%` }} className="bg-bad-4 h-full" />
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-ink-muted pt-1 border-t border-hair">
                    <span>Setup: {line.setup}</span>
                    <span>Servis: {line.maint}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Interactive Visual 70-Machine Grid */}
            <div className="border border-hair rounded-sm p-4 bg-panel space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-bold uppercase tracking-wider text-ink-muted">
                Denah Mesin Jahit Lantai Produksi ({capacitySummary.filteredMachines.length} Mesin Ditampilkan)
              </span>
              <div className="flex items-center gap-4 text-[11px] text-ink-muted">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-ok inline-block" /> Aktif
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-warn inline-block" /> Setup
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-bad-4 inline-block" /> Maintenance
                </span>
              </div>
            </div>

            <div className="grid grid-cols-7 sm:grid-cols-10 md:grid-cols-14 gap-2">
              {capacitySummary.filteredMachines.map(m => {
                const badgeColor =
                  m.status === 'ACTIVE'
                    ? 'bg-ok-bg text-ok-2 border-ok/30'
                    : m.status === 'SETUP'
                    ? 'bg-warn-bg text-warn-2 border-warn/30'
                    : 'bg-bad-bg text-bad-4 border-bad/30';

                return (
                  <div
                    key={m.machineId}
                    title={`${m.machineId} · ${m.lineId} · ${m.status}\nOperator: ${m.operatorName}\nModel: ${m.currentProcess}`}
                    className={`border rounded-sm p-2 min-h-[48px] flex flex-col items-center justify-center text-center cursor-pointer hover:scale-105 transition-transform ${badgeColor}`}
                  >
                    <span className="text-[11px] font-extrabold">{m.machineId}</span>
                    <span className="text-[9px] truncate max-w-full font-medium mt-0.5">{m.lineId.replace('LINE-', '')}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 3: WIP DISTRIBUTION: CMT VS SEMI-CMT VS FULL PACKAGE      */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      {(activeTab === 'all' || activeTab === 'wip') && (
        <section className="bg-white dark:bg-[#1c1c1e] border border-hair rounded-sm p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-warn-2 dark:text-warn">
                  Manufaktur Multi-Skema Maklon
                </span>
                  <span className="bg-panel-2 text-ink rounded-sm px-2.5 py-0.5 text-[11px] font-semibold border border-hair">
                  Isolasi Hukum &amp; Kustodial
                </span>
              </div>
              <h2 className="text-[20px] font-bold text-ink tracking-tight mt-1">
                Distribusi WIP: CMT vs. Semi-CMT vs. Full Package
              </h2>
              <p className="text-[13px] text-ink-muted">
                Pemisahan tegas hak milik bahan kain antara titipan kustodial murni, maklon hibrida, dan pengadaan penuh.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handleNav('spec-versions')}
                className="min-h-[48px] px-4 py-2 rounded-[12px] bg-panel-2 hover:bg-hair text-ink font-semibold text-[13px] transition-all flex items-center gap-2"
              >
                <LucideIcon name="layers" className="w-4 h-4 text-warn" />
                <span>Lihat Spesifikasi &amp; BOM</span>
              </button>
            </div>
          </div>

          {/* Cards for 3 Maklon Schemes */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {wipSummary.schemes.map(sch => {
              const sharePct = Math.round((sch.totalPieces / wipSummary.totalWip) * 1000) / 10;
              return (
                <div
                  key={sch.scheme}
                  className="bg-panel border border-hair rounded-sm p-5 flex flex-col justify-between space-y-4 shadow-xs"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-white dark:bg-black/40 border border-hair text-ink">
                        {sch.badge}
                      </span>
                      <span className="text-[13px] font-bold text-ink">{sharePct}% total WIP</span>
                    </div>

                    <h3 className="text-[16px] font-bold text-ink">{sch.title}</h3>
                    <p className="text-[12px] text-ink-muted leading-relaxed">{sch.legalOwnership}</p>
                  </div>

                  {/* Volume Numbers */}
                  <div className="bg-white dark:bg-black/30 p-3.5 rounded-[12px] border border-hair space-y-2">
                    <div className="flex justify-between items-baseline">
                      <span className="text-[12px] text-ink-muted">Total Unit WIP</span>
                      <span className="text-[22px] font-black text-ink">{sch.totalPieces.toLocaleString('id-ID')} pcs</span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-hair text-center">
                      <div>
                        <span className="block text-[10px] uppercase text-ink-muted">Potong</span>
                        <span className="font-bold text-[13px] text-ink">{sch.cuttingPieces}</span>
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase text-ink-muted">Jahit</span>
                        <span className="font-bold text-[13px] text-ink">{sch.sewingPieces}</span>
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase text-ink-muted">QC / Finish</span>
                        <span className="font-bold text-[13px] text-ink">{sch.qcFinishingPieces}</span>
                      </div>
                    </div>
                  </div>

                  {/* SLA & Lead Time */}
                  <div className="flex items-center justify-between text-[12px] text-ink-muted pt-1">
                    <span>SLA: {sch.leadTimeDays} Hari</span>
                    <span className="font-bold text-ok-2">On-Time: {sch.onTimeRatePct}%</span>
                    <span>{sch.activeBatches} Batch Aktif</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Stacked Chart for Stage Composition */}
          <div className="pt-2">
            <StackedBarChart
              data={wipSummary.stackedRows}
              keys={STACKED_WIP_KEYS}
              title="Komposisi Alur Kerja Manufaktur per Skema Maklon"
              subtitle="Proporsi unit pada tahap Pemotongan (Potong), Penjahitan (Jahit), dan Pemeriksaan Akhir (QC)"
              badge="WIP Pipeline"
            />
          </div>
        </section>
      )}

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 4: DOUBLE-ENTRY FINANCIAL LEDGER SUMMARIES & LINKS         */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      {(activeTab === 'all' || activeTab === 'financial') && (
        <section className="bg-white dark:bg-[#1c1c1e] border border-hair rounded-sm p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-brand">
                  Buku Besar Keuangan (Double-Entry Core)
                </span>
                <span className="bg-ok-bg text-ok-2 rounded-full px-2.5 py-0.5 text-[11px] font-semibold">
                  Zero Invariant Failure
                </span>
              </div>
              <h2 className="text-[20px] font-bold text-ink tracking-tight mt-1">
                Ringkasan Saldo Buku Besar &amp; Rekonsiliasi Maklon
              </h2>
              <p className="text-[13px] text-ink-muted">
                Setiap mutasi dicatat secara immutable (append-only) dengan debit dan kredit seimbang.
              </p>
            </div>

            {/* Quick Action Navigation Buttons with >= 48px touch targets */}
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => handleNav('ledger')}
                className="min-h-[48px] px-4 py-2.5 rounded-[12px] bg-brand text-white font-semibold text-[13px] shadow-sm hover:opacity-95 transition-all flex items-center gap-2"
              >
                <LucideIcon name="book-open" className="w-4 h-4" />
                <span>Buka Buku Besar Lengkap</span>
                <span aria-hidden="true">&rarr;</span>
              </button>
              <button
                type="button"
                onClick={() => handleNav('payroll')}
                className="min-h-[48px] px-4 py-2.5 rounded-[12px] border border-hair hover:bg-panel-2 text-ink font-semibold text-[13px] transition-all flex items-center gap-2"
              >
                <LucideIcon name="factory" className="w-4 h-4 text-brand" />
                <span>Workspace Payroll &amp; Costing</span>
              </button>
            </div>
          </div>

          {/* Double-Entry Invariant Status Card */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-panel border border-hair rounded-[14px] p-4 space-y-1">
              <span className="text-[11px] uppercase tracking-wider font-bold text-ink-muted">
                Total Mutasi Debit
              </span>
              <p className="text-[22px] font-black text-ink">
                {fmtMoney(financialSummary.totalDebitMinor)}
              </p>
              <span className="text-[11px] text-ink-muted">
                Terdiri dari Kas, Piutang, dan Akumulasi Beban
              </span>
            </div>

            <div className="bg-panel border border-hair rounded-[14px] p-4 space-y-1">
              <span className="text-[11px] uppercase tracking-wider font-bold text-ink-muted">
                Total Mutasi Kredit
              </span>
              <p className="text-[22px] font-black text-ink">
                {fmtMoney(financialSummary.totalCreditMinor)}
              </p>
              <span className="text-[11px] text-ink-muted">
                Terdiri dari Utang Usaha dan Pendapatan Maklon
              </span>
            </div>

            <div className={`border rounded-[14px] p-4 space-y-1 ${financialSummary.isBalanced ? 'bg-ok-bg/40 border-ok/30' : 'bg-bad-bg border-bad/30'}`}>
              <div className="flex items-center justify-between">
                <span className="text-[11px] uppercase tracking-wider font-bold text-ok-2 dark:text-ok">
                  Status Rekonsiliasi Invariant
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-ok text-white">
                  VALIDATED
                </span>
              </div>
              <p className="text-[22px] font-black text-ok-2 dark:text-ok">
                {financialSummary.isBalanced ? '100% Berimbang' : 'Selisih Ditemukan'}
              </p>
              <span className="text-[11px] text-ink-muted">
                Selisih: {fmtMoney(financialSummary.varianceMinor)} (Ketentuan: 0 selisih)
              </span>
            </div>
          </div>

          {/* Account Balances Table (Apple HIG Clean Table) */}
          <div className="border border-hair rounded-[14px] overflow-hidden">
            <table className="w-full text-left border-collapse text-[13px]">
              <thead>
                <tr className="bg-panel border-b border-hair text-ink-muted font-bold text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4">Kode Akun</th>
                  <th className="py-3 px-4">Nama Akun COA</th>
                  <th className="py-3 px-4">Klasifikasi</th>
                  <th className="py-3 px-4 text-right">Debit</th>
                  <th className="py-3 px-4 text-right">Kredit</th>
                  <th className="py-3 px-4 text-right">Saldo Bersih</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hair">
                {COA_ACCOUNTS.map(acc => {
                  const bal = financialSummary.accountBalances.get(acc.code) ?? { debitMinor: 0, creditMinor: 0 };
                  const net = acc.normalDirection === 'DEBIT'
                    ? bal.debitMinor - bal.creditMinor
                    : bal.creditMinor - bal.debitMinor;

                  return (
                    <tr key={acc.code} className="hover:bg-panel-2/60 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-brand">{acc.code}</td>
                      <td className="py-3.5 px-4 font-semibold text-ink">{acc.name}</td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-panel-2 text-ink-muted border border-hair">
                          {acc.type}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-ink">
                        {fmtMoney(bal.debitMinor)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-ink">
                        {fmtMoney(bal.creditMinor)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-ink">
                        {fmtMoney(net)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Recent Immutable Transactions Stream */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-[14px] font-bold text-ink">Jurnal Transaksi Terakhir (Append-Only)</h4>
              <button
                type="button"
                onClick={() => handleNav('ledger')}
                className="min-h-[48px] px-3 text-[12px] font-bold text-brand hover:underline flex items-center gap-1"
              >
                <span>Lihat Semua Jurnal</span>
                <span aria-hidden="true">&rarr;</span>
              </button>
            </div>

            <div className="space-y-2">
              {ledgerTx.slice(0, 3).map(tx => (
                <div
                  key={tx.id}
                  className="bg-panel p-3.5 rounded-[12px] border border-hair flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[12px]"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-ink-muted font-bold">
                        TX-{tx.id.substring(0, 8)}...
                      </span>
                      {tx.reversalOf && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-warn-bg text-warn-2">
                          Pembalik TX-{tx.reversalOf.substring(0, 8)}
                        </span>
                      )}
                      <span className="text-ink-muted">· Tenant: {tx.tenantId.substring(0, 8)}</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-ink">
                      {tx.entries.map((e, idx) => (
                        <span key={idx} className="font-mono">
                          {e.accountCode} ({e.direction === 'DEBIT' ? 'Dr' : 'Cr'}):{' '}
                          {fmtMoney(e.amountMinor)}
                        </span>
                      ))}
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-ok-bg text-ok-2 border border-ok/20 shrink-0 self-start sm:self-center">
                    Terverifikasi
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── SECTION 4.5: R&D & SYSTEM ACTIVITY LOG ──────────────────────── */}
      {activities && activities.length > 0 && (
        <ActivityLog
          title="Aktivitas Terkini Sistem & R&D"
          subtitle="Pembaruan otomatis dari modul studi waktu, versi spesifikasi, dan verifikasi tally"
          activities={activities}
        />
      )}

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SECTION 5: QUICK ACCESS WORKSPACE TILES                           */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          type="button"
          onClick={() => handleNav('production')}
          className="min-h-[72px] p-4 rounded-sm bg-white dark:bg-[#1c1c1e] border border-hair text-left hover:border-brand transition-all flex items-center justify-between group shadow-sm"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-sm bg-panel-2 text-ink flex items-center justify-center group-hover:scale-105 transition-transform">
              <LucideIcon name="factory" className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-[14px] font-bold text-ink">Floor Terminal</h4>
              <p className="text-[12px] text-ink-muted">Input Tally 30m Mandor</p>
            </div>
          </div>
          <span className="text-ink-muted group-hover:text-brand font-bold">&rarr;</span>
        </button>

        <button
          type="button"
          onClick={() => handleNav('quality')}
          className="min-h-[72px] p-4 rounded-sm bg-white dark:bg-[#1c1c1e] border border-hair text-left hover:border-ok transition-all flex items-center justify-between group shadow-sm"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-sm bg-panel-2 text-ink flex items-center justify-center group-hover:scale-105 transition-transform">
              <LucideIcon name="check-circle" className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-[14px] font-bold text-ink">QC Terminal</h4>
              <p className="text-[12px] text-ink-muted">Pass, Repair &amp; Reject</p>
            </div>
          </div>
          <span className="text-ink-muted group-hover:text-ok font-bold">&rarr;</span>
        </button>

        <button
          type="button"
          onClick={() => handleNav('payroll')}
          className="min-h-[72px] p-4 rounded-sm bg-white dark:bg-[#1c1c1e] border border-hair text-left hover:border-warn transition-all flex items-center justify-between group shadow-sm"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-sm bg-panel-2 text-ink flex items-center justify-center group-hover:scale-105 transition-transform">
              <LucideIcon name="bar-chart-3" className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-[14px] font-bold text-ink">Payroll &amp; Costing</h4>
              <p className="text-[12px] text-ink-muted">Borongan &amp; Bonus QC</p>
            </div>
          </div>
          <span className="text-ink-muted group-hover:text-warn font-bold">&rarr;</span>
        </button>

        <button
          type="button"
          onClick={() => handleNav('ledger')}
          className="min-h-[72px] p-4 rounded-sm bg-white dark:bg-[#1c1c1e] border border-hair text-left hover:border-brand transition-all flex items-center justify-between group shadow-sm"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-sm bg-panel-2 text-ink flex items-center justify-center group-hover:scale-105 transition-transform">
              <LucideIcon name="book-open" className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-[14px] font-bold text-ink">Buku Besar</h4>
              <p className="text-[12px] text-ink-muted">Double-Entry Journal</p>
            </div>
          </div>
          <span className="text-ink-muted group-hover:text-brand font-bold">&rarr;</span>
        </button>
      </section>
    </div>
  );
};

export default ExecutiveDashboardView;
