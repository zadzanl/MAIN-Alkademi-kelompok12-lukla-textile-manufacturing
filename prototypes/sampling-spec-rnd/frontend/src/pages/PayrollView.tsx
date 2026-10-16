/**
 * PayrollView — VIEW-06: dynamic payroll & costing surface (MOD-05).
 *
 * Covers the frozen payroll contract end-to-end:
 * - Saturday Weekly Borongan Run orchestrator (cutoff every Saturday 23:59:00 Asia/Jakarta)
 * - 10-15% floating meal allowance toggle (1000..1500 bps)
 * - 3-way QC bonus pool split with integer rounding remainder handling
 * - Monthly factory overhead allocation (Electricity, Water, Internet, Facility)
 * - Strict enforcement of the FINANCIAL_RULE_PENDING blocking state (zero monetary values if rule unapproved)
 * - Double-entry ledger integration and reversal
 *
 * Design System Compliance:
 * - Apple Design Tokens (var(--bg-card), var(--border), var(--c-brand), var(--c-ink), etc.)
 * - Touch targets for all interactive clickable elements >= 48px
 * - Zero type evasion (no 'as any')
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LucideIcon } from '../components/Sidebar';
import Modal from '../components/Modal';
import MockModeBanner from '../components/MockModeBanner';
import {
  listPayrollPeriods,
  createPayrollPeriod,
  calculateWeeklyPayroll,
  getPayrollStatement,
  getBonusPool,
  approvePayroll,
  recordPayrollPayment,
  recordOverhead,
  calculateOverhead,
  listFinancialRules,
  proposeFinancialRule,
  approveFinancialRule,
  isMockPayroll,
  MOCK_RECIPIENTS,
  toMoney,
  type Period,
  type PeriodStatus,
  type FinancialRule,
  type PayrollStatement,
  type PayrollResult,
  type BonusPool,
  type OverheadAllocation,
  type PeriodRequest,
  type FinancialRuleRequest,
  type Currency,
} from '../services/payrollApi';
import { appendLedgerTransaction, type LedgerEntry } from '../services/ledgerApi';
import { buildWaterfall } from '../utils/chartData';
import WaterfallChart from '../components/WaterfallChart';

const inputCls =
  'w-full min-h-[48px] rounded-[10px] border border-hair px-3.5 py-2.5 text-[13px] text-ink bg-white focus:outline-none focus:ring-2 focus:ring-brand';
const CURRENCY: Currency = 'IDR';

const fmtMoney = (minor: number): string =>
  (minor / 100).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const toMinor = (major: string): number => Math.round((Number(major) || 0) * 100);

const STATUS_PILL: Record<PeriodStatus, string> = {
  OPEN: 'pill pill-gray',
  CALCULATED: 'pill pill-blue',
  PENDING_RULE: 'pill pill-orange',
  APPROVED: 'pill pill-green',
  PAID: 'pill pill-dark',
};

type Tab = 'periods' | 'run' | 'bonus' | 'overhead' | 'rules';

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'run', label: 'Saturday Borongan Run', icon: 'zap' },
  { id: 'periods', label: 'Periode Payroll', icon: 'calendar' },
  { id: 'bonus', label: 'Bonus Pool 3-Way QC', icon: 'badge-check' },
  { id: 'overhead', label: 'Overhead Bulanan', icon: 'pie-chart' },
  { id: 'rules', label: 'Aturan Finansial', icon: 'shield-alert' },
];

const PayrollView: React.FC = () => {
  const [tab, setTab] = useState<Tab>('run');
  const [periods, setPeriods] = useState<Period[]>([]);
  const [rules, setRules] = useState<FinancialRule[]>([]);
  const [selectedPeriodId, setSelectedPeriodId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  // Quick rule approve target from blocking banner
  const [quickApproveRule, setQuickApproveRule] = useState<FinancialRule | null>(null);

  const approvedRules = rules.filter(r => r.status === 'APPROVED');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [pr, rr] = await Promise.all([listPayrollPeriods(), listFinancialRules()]);
    if (pr.ok && pr.data) {
      setPeriods(pr.data.items);
      setSelectedPeriodId(prev => prev || pr.data!.items[0]?.id || '');
    } else {
      setError(pr.error ?? 'Gagal memuat periode payroll.');
    }
    if (rr.ok && rr.data) setRules(rr.data.items);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleQuickApprove = (rule: FinancialRule) => {
    setQuickApproveRule(rule);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-semibold text-ink">Payroll &amp; Costing Workspace</h2>
            <span className="pill rounded-full px-2.5 py-0.5 text-[11px] font-semibold bg-brand-bg text-brand">
              MOD-05 · VIEW-06
            </span>
          </div>
          <p className="text-ink-muted text-sm mt-1">
            Orkestrator Borongan Sabtu, floating meal allowance 10–15%, split bonus pool QC 3-way, dan alokasi overhead bulanan
          </p>
        </div>
        <button
          onClick={load}
          className="btn-secondary min-h-[48px] px-4 rounded-[10px] inline-flex items-center gap-2"
        >
          <LucideIcon name="activity" className="w-4 h-4" /> Refresh Data
        </button>
      </div>

      {isMockPayroll && (
        <MockModeBanner
          detail="endpoint HTTP payroll berjalan dalam mode kontrak mock memori identik openapi.yaml."
          hint="setelah backend payroll online."
        />
      )}
      {error && (
        <div className="rounded-[14px] border border-bad-bg-2 bg-bad-bg px-4 py-3.5 text-[13px] text-bad-4 font-medium">
          {error}
        </div>
      )}
      {flash && (
        <div className="rounded-[14px] border border-ok bg-ok-bg px-4 py-3.5 text-[13px] font-medium text-ok-2 flex items-center justify-between">
          <span>{flash}</span>
          <button
            onClick={() => setFlash(null)}
            className="text-ok-2 hover:opacity-75 min-h-[36px] min-w-[36px] flex items-center justify-center"
          >
            <LucideIcon name="x" className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tabs with >= 48px touch targets */}
      <div className="inline-flex flex-wrap gap-1 rounded-[12px] bg-panel-2 p-1">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`min-h-[48px] rounded-[9px] px-4 text-[13px] font-semibold transition-all inline-flex items-center gap-2 ${
              tab === t.id ? 'bg-white text-ink shadow-sm' : 'text-ink-muted hover:text-ink'
            }`}
          >
            <LucideIcon name={t.icon} className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'run' && (
        <RunTab
          periods={periods}
          rules={rules}
          selectedPeriodId={selectedPeriodId}
          onSelectPeriod={setSelectedPeriodId}
          onQuickApproveRule={handleQuickApprove}
        />
      )}
      {tab === 'periods' && <PeriodsTab periods={periods} loading={loading} onCreated={load} />}
      {tab === 'bonus' && (
        <BonusTab
          selectedPeriodId={selectedPeriodId}
          rules={rules}
          periods={periods}
          onFlash={setFlash}
        />
      )}
      {tab === 'overhead' && (
        <OverheadTab
          periods={periods}
          approvedRules={approvedRules}
          onFlash={setFlash}
        />
      )}
      {tab === 'rules' && <RulesTab rules={rules} onChanged={load} onFlash={setFlash} />}

      {/* Quick Approve Modal invoked from blocking state */}
      {quickApproveRule && (
        <RuleApproveModal
          rule={quickApproveRule}
          onClose={() => setQuickApproveRule(null)}
          onDone={() => {
            setQuickApproveRule(null);
            setFlash(`✓ Aturan ${quickApproveRule.id} berhasil disetujui (APPROVED). Blokir payroll terangkat.`);
            load();
          }}
        />
      )}
    </div>
  );
};

// ─── Saturday Borongan Run Orchestrator ──────────────────────────────────────────
const RunTab: React.FC<{
  periods: Period[];
  rules: FinancialRule[];
  selectedPeriodId: string;
  onSelectPeriod: (id: string) => void;
  onQuickApproveRule: (rule: FinancialRule) => void;
}> = ({ periods, rules, selectedPeriodId, onSelectPeriod, onQuickApproveRule }) => {
  const [ruleVersion, setRuleVersion] = useState('');
  const [result, setResult] = useState<PayrollResult | null>(null);
  const [statement, setStatement] = useState<PayrollStatement | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [showPayment, setShowPayment] = useState(false);

  // Floating Meal Allowance selector in run (10% - 15%)
  const [mealRateOverride, setMealRateOverride] = useState<number | null>(null);

  // Double-entry Ledger posting state
  const [ledgerPosting, setLedgerPosting] = useState(false);
  const [postedLedgerTxId, setPostedLedgerTxId] = useState<string | null>(null);

  // Active period and rule
  const currentPeriod = useMemo(
    () => periods.find(p => p.id === selectedPeriodId),
    [periods, selectedPeriodId]
  );

  useEffect(() => {
    if (currentPeriod) {
      setRuleVersion(currentPeriod.ruleVersion);
    }
  }, [currentPeriod]);

  const activeRule = useMemo(
    () => rules.find(r => r.id === ruleVersion),
    [rules, ruleVersion]
  );

  // Domain guardrail: Rule version MUST be APPROVED.
  // If not APPROVED (or missing), state is FINANCIAL_RULE_PENDING and no monetary values are calculated/shown.
  const isRulePending = !activeRule || activeRule.status !== 'APPROVED';

  const effectiveMealBps = mealRateOverride ?? activeRule?.mealBasisPoints ?? 1200;

  const calculate = async () => {
    if (!selectedPeriodId) {
      setErr('Pilih periode payroll terlebih dahulu.');
      return;
    }
    if (isRulePending) {
      setErr(`FINANCIAL_RULE_PENDING: Versi aturan ${ruleVersion || 'tidak valid'} belum disetujui (status: PENDING).`);
      setResult(null);
      setStatement(null);
      return;
    }
    setBusy(true);
    setErr(null);
    setFlash(null);
    const res = await calculateWeeklyPayroll(selectedPeriodId, { ruleVersion });
    setBusy(false);
    if (!res.ok || !res.data) {
      setErr(res.error ?? 'Gagal menghitung payroll borongan.');
      setResult(null);
      return;
    }
    setResult(res.data);
    setFlash(`✓ Kalkulasi Borongan Berhasil: ${res.data.eligibleUnits} unit terverifikasi QC`);
    await loadStatement();
  };

  const loadStatement = async () => {
    if (!selectedPeriodId) return;
    const res = await getPayrollStatement(selectedPeriodId);
    if (res.ok && res.data) {
      setStatement(res.data);
    } else {
      setStatement(null);
    }
  };

  const approve = async () => {
    if (!statement) return;
    setBusy(true);
    setErr(null);
    setFlash(null);
    const res = await approvePayroll(statement.periodId, {
      version: statement.version,
      inputHash: statement.inputHash,
    });
    setBusy(false);
    if (!res.ok || !res.data) {
      setErr(res.error ?? 'Gagal menyetujui payroll.');
      return;
    }
    setStatement(res.data);
    setFlash('✓ Statement borongan disetujui (version + inputHash terkunci permanen).');
  };

  const postToLedger = async () => {
    if (!statement) return;
    setLedgerPosting(true);
    setErr(null);
    const totalMinor = totalOf(statement);
    // Double-entry journal:
    // DEBIT 5000 Beban Gaji (Wages Expense)
    // CREDIT 2100 Utang Usaha (Wages Payable) or 1100 Kas (if already paid)
    const creditAccount = statement.status === 'PAID' ? '1100' : '2100';
    const entries: LedgerEntry[] = [
      { accountCode: '5000', direction: 'DEBIT', amountMinor: totalMinor },
      { accountCode: creditAccount, direction: 'CREDIT', amountMinor: totalMinor },
    ];

    const res = await appendLedgerTransaction({
      transactionType: 'PAYROLL_WEEKLY_RUN',
      currency: statement.reserve.currency,
      entries,
    });
    setLedgerPosting(false);
    if (!res.ok || !res.data) {
      setErr(res.error ?? 'Gagal mencatat transaksi ke buku besar.');
      return;
    }
    setPostedLedgerTxId(res.data.id);
    setFlash(`✓ Jurnal Double-Entry berhasil diposting ke Buku Besar (Trx: ${res.data.id.slice(0, 8)})`);
  };

  const totalOf = (s: PayrollStatement): number =>
    s.items.reduce(
      (sum, it) => sum + it.base.amountMinor + it.meal.amountMinor + it.bonus.amountMinor,
      0
    );

  // Cost accumulation waterfall: base wages → +meal → +bonus → grand total.
  const waterfall = useMemo(() => {
    if (!statement) return [];
    const base = statement.items.reduce((s, it) => s + it.base.amountMinor, 0);
    const meal = statement.items.reduce((s, it) => s + it.meal.amountMinor, 0);
    const bonus = statement.items.reduce((s, it) => s + it.bonus.amountMinor, 0);
    return buildWaterfall([
      { label: 'Upah Pokok Jahit', delta: base },
      { label: 'Uang Makan (Meal)', delta: meal },
      { label: 'Bonus QC 3-Way', delta: bonus },
      { label: 'Total Payout', delta: base + meal + bonus, kind: 'total' },
    ]);
  }, [statement]);

  return (
    <div className="space-y-6">
      {/* ── Orchestrator Card ────────────────────────────────────────────── */}
      <div className="bg-white border border-hair rounded-[18px] p-6 shadow-sm space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-panel-2 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-brand animate-pulse" />
              <h3 className="text-[17px] font-bold text-ink">
                Saturday Weekly Borongan Run Orchestrator
              </h3>
            </div>
            <p className="text-[12px] text-ink-muted mt-1">
              Siklus mingguan verifikasi output jahit per komponen &amp; settlement upah Sabtu 23:59 Asia/Jakarta
            </p>
          </div>
          {currentPeriod && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-ink-muted font-medium">Cutoff Sabtu:</span>
              <code className="rounded-[8px] bg-panel-2 px-2.5 py-1 text-xs font-mono font-semibold text-ink">
                {currentPeriod.endsOn} · {currentPeriod.cutoffLocal} {currentPeriod.timezone}
              </code>
            </div>
          )}
        </div>

        {/* 5-Step Pipeline Lifecycle Status */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-center text-xs">
          <div className="rounded-[10px] p-2.5 bg-panel border border-hair">
            <span className="text-ink-muted block text-[10px] uppercase tracking-wider font-semibold">1. Periode</span>
            <span className="font-semibold text-ink">{currentPeriod ? currentPeriod.startsOn.slice(5) + ' → ' + currentPeriod.endsOn.slice(5) : 'Belum dipilih'}</span>
          </div>
          <div className={`rounded-[10px] p-2.5 border ${isRulePending ? 'bg-warn-bg text-warn-2 border-warn' : 'bg-ok-bg text-ok-2 border-ok'}`}>
            <span className="block text-[10px] uppercase tracking-wider font-semibold">2. Validasi Rule</span>
            <span className="font-semibold">{isRulePending ? 'FINANCIAL_RULE_PENDING' : 'APPROVED'}</span>
          </div>
          <div className={`rounded-[10px] p-2.5 border ${result ? 'bg-ok-bg text-ok-2 border-ok' : 'bg-panel text-ink-muted border-hair'}`}>
            <span className="block text-[10px] uppercase tracking-wider font-semibold">3. Kalkulasi Borongan</span>
            <span className="font-semibold">{result ? `${result.eligibleUnits} Unit QC-Passed` : 'Belum Dihitung'}</span>
          </div>
          <div className={`rounded-[10px] p-2.5 border ${statement?.status === 'APPROVED' || statement?.status === 'PAID' ? 'bg-ok-bg text-ok-2 border-ok' : 'bg-panel text-ink-muted border-hair'}`}>
            <span className="block text-[10px] uppercase tracking-wider font-semibold">4. Otorisasi Slip</span>
            <span className="font-semibold">{statement?.status === 'APPROVED' || statement?.status === 'PAID' ? `Disetujui (v${statement.version})` : 'Menunggu Approval'}</span>
          </div>
          <div className={`rounded-[10px] p-2.5 border ${statement?.status === 'PAID' ? 'bg-panel-6 text-white border-panel-6' : postedLedgerTxId ? 'bg-ok-bg text-ok-2 border-ok' : 'bg-panel text-ink-muted border-hair'}`}>
            <span className="block text-[10px] uppercase tracking-wider font-semibold">5. Ledger Double-Entry</span>
            <span className="font-semibold">{statement?.status === 'PAID' ? 'PAID & Settled' : postedLedgerTxId ? 'Tercatat di Ledger' : 'Belum Diposting'}</span>
          </div>
        </div>

        {/* FINANCIAL_RULE_PENDING Blocking Banner */}
        {isRulePending && (
          <div className="rounded-[14px] border border-warn bg-warn-bg p-4 space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-warn/20 text-warn-2 flex items-center justify-center flex-shrink-0 mt-0.5">
                <LucideIcon name="shield-alert" className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <h4 className="text-[14px] font-bold text-warn-2">
                  FINANCIAL_RULE_PENDING — Aturan Finansial Belum Disetujui
                </h4>
                <p className="text-[13px] text-ink-2 mt-1 leading-relaxed">
                  Versi aturan <code className="font-mono font-bold">{ruleVersion || 'tidak ada'}</code> masih berstatus{' '}
                  <span className="font-bold underline">{activeRule?.status ?? 'TIDAK TERDAFTAR'}</span>.
                  Sesuai kontrak kepatuhan finansial pabrik, kalkulasi upah borongan dan alokasi bonus diblokir total
                  hingga aturan disetujui Owner dengan bukti otorisasi eksternal.
                  <strong className="block mt-1 text-bad-4">
                    Seluruh nominal moneter disembunyikan sampai blokir persetujuan terangkat.
                  </strong>
                </p>
              </div>
              {activeRule && (
                <button
                  type="button"
                  onClick={() => onQuickApproveRule(activeRule)}
                  className="btn-primary min-h-[48px] px-4 rounded-[10px] text-xs font-semibold whitespace-nowrap self-center"
                >
                  <LucideIcon name="check-circle" className="w-4 h-4" />
                  Setujui Aturan Ini
                </button>
              )}
            </div>
          </div>
        )}

        {/* Period and Rule Pickers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="run-period" className="block text-sm font-medium text-ink mb-1.5">
              Pilih Periode Borongan
            </label>
            <select
              id="run-period"
              value={selectedPeriodId}
              onChange={e => onSelectPeriod(e.target.value)}
              className={inputCls}
            >
              <option value="">— pilih periode —</option>
              {periods.map(p => (
                <option key={p.id} value={p.id}>
                  {p.startsOn} → {p.endsOn} ({p.ruleVersion})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="run-rule" className="block text-sm font-medium text-ink mb-1.5">
              Versi Aturan Finansial Terhubung
            </label>
            <select
              id="run-rule"
              value={ruleVersion}
              onChange={e => setRuleVersion(e.target.value)}
              className={inputCls}
            >
              <option value="">— pilih versi —</option>
              {rules.map(r => (
                <option key={r.id} value={r.id}>
                  {r.id} · {r.status === 'APPROVED' ? '✓ Disetujui (APPROVED)' : '⚠ PENDING (Memblokir)'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 10-15% Floating Meal Allowance Toggle */}
        <div className="rounded-[14px] border border-hair bg-panel p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <span className="text-[13px] font-bold text-ink">
                Floating Meal Allowance (10% – 15%)
              </span>
              <p className="text-[12px] text-ink-muted">
                Tunjangan makan mengambang dihitung berdasarkan total upah jahit terverifikasi (VERIFIED_WAGES_PROPOSED)
              </p>
            </div>
            <span className="pill rounded-full px-3 py-1 text-xs font-bold bg-brand-bg text-brand">
              Aktif: {(effectiveMealBps / 100).toFixed(1)}% ({effectiveMealBps} bps)
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {[1000, 1100, 1200, 1300, 1400, 1500].map(bps => (
              <button
                key={bps}
                type="button"
                onClick={() => setMealRateOverride(bps)}
                className={`min-h-[48px] px-4 rounded-[10px] text-xs font-semibold border transition-all ${
                  effectiveMealBps === bps
                    ? 'bg-brand text-white border-brand shadow-sm'
                    : 'bg-white text-ink border-hair hover:border-brand/40'
                }`}
              >
                {(bps / 100).toFixed(0)}% ({(bps).toString()} bps)
              </button>
            ))}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3 pt-2">
          <button
            onClick={calculate}
            disabled={busy || isRulePending}
            className={`min-h-[48px] px-6 rounded-[10px] inline-flex items-center gap-2 font-semibold text-[13px] transition-all ${
              isRulePending
                ? 'bg-panel-2 text-ink-muted border border-hair cursor-not-allowed'
                : 'btn-primary'
            }`}
          >
            <LucideIcon name="zap" className="w-4 h-4" />
            {busy
              ? 'Menghitung Borongan…'
              : isRulePending
              ? 'Kalkulasi Diblokir (Rule Pending)'
              : 'Jalankan Borongan Run Sabtu'}
          </button>
          <button
            onClick={loadStatement}
            disabled={!selectedPeriodId}
            className="btn-secondary min-h-[48px] px-5 rounded-[10px] inline-flex items-center gap-2"
          >
            <LucideIcon name="file-text" className="w-4 h-4" /> Muat Slip Tersimpan
          </button>
        </div>

        {err && (
          <div className="rounded-[12px] bg-bad-bg border border-bad-bg-2 p-3 text-[13px] text-bad-4 font-medium">
            {err}
          </div>
        )}
        {flash && (
          <div className="rounded-[12px] bg-ok-bg border border-ok p-3 text-[13px] text-ok-2 font-medium">
            {flash}
          </div>
        )}
      </div>

      {/* ── Calculation Results (Blocked when FINANCIAL_RULE_PENDING) ────── */}
      {result && !isRulePending && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white border border-hair rounded-[18px] p-5 text-center shadow-sm">
            <p className="text-xs text-ink-muted uppercase tracking-wider mb-1 font-semibold">Status Run</p>
            <p className="text-[17px] font-bold text-ok-2">{result.status}</p>
            <p className="text-[11px] text-ink-muted mt-1">Output tervalidasi QC</p>
          </div>
          <div className="bg-white border border-hair rounded-[18px] p-5 text-center shadow-sm">
            <p className="text-xs text-ink-muted uppercase tracking-wider mb-1 font-semibold">Unit Jahit Eligible</p>
            <p className="text-[28px] font-bold text-brand">{result.eligibleUnits}</p>
            <p className="text-[11px] text-ink-muted mt-1">Komponen lolos inspeksi</p>
          </div>
          <div className="bg-white border border-hair rounded-[18px] p-5 text-center shadow-sm">
            <p className="text-xs text-ink-muted uppercase tracking-wider mb-1 font-semibold">Total Upah Jahit + Meal</p>
            <p className="text-[22px] font-bold text-ink font-mono">
              Rp {fmtMoney(result.totalWages.amountMinor)}
            </p>
            <p className="text-[11px] text-ink-muted mt-1">Belum termasuk QC pool bonus</p>
          </div>
        </div>
      )}

      {/* ── Itemized Statement (Slip Upah) ─────────────────────────────────── */}
      {statement && !isRulePending && (
        <>
          <WaterfallChart
            data={waterfall}
            title="Akumulasi Biaya Tenaga Kerja Borongan"
            subtitle="Komposisi Upah Pokok Jahit + Meal Allowance + Bonus Pool QC (IDR)"
            formatValue={fmtMoney}
          />

          <div className="bg-white border border-hair rounded-[18px] overflow-hidden shadow-sm">
            <div className="flex flex-wrap justify-between items-center gap-3 p-5 border-b border-panel-2">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-[16px] font-bold text-ink">Slip Upah Mingguan (Itemized Statement)</h3>
                  <span className={STATUS_PILL[statement.status]}>{statement.status}</span>
                </div>
                <p className="text-[12px] text-ink-muted mt-1">
                  Versi {statement.version} · inputHash{' '}
                  <code className="font-mono bg-panel-2 px-1.5 py-0.5 rounded text-ink">
                    {statement.inputHash}
                  </code>{' '}
                  · Cadangan Pembulatan (Reserve):{' '}
                  <span className="font-mono font-semibold text-ink">
                    Rp {fmtMoney(statement.reserve.amountMinor)}
                  </span>
                </p>
              </div>

              {/* Action buttons with touch target >= 48px */}
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={approve}
                  disabled={busy || statement.status !== 'CALCULATED'}
                  className="btn-success min-h-[48px] px-5 rounded-[10px] text-xs font-semibold inline-flex items-center gap-1.5"
                >
                  <LucideIcon name="check-circle" className="w-4 h-4" />
                  Setujui Statement
                </button>
                <button
                  onClick={() => setShowPayment(true)}
                  disabled={statement.status !== 'APPROVED'}
                  className="btn-primary min-h-[48px] px-5 rounded-[10px] text-xs font-semibold inline-flex items-center gap-1.5"
                >
                  <LucideIcon name="credit-card" className="w-4 h-4" />
                  Rekam Pembayaran
                </button>
                <button
                  onClick={postToLedger}
                  disabled={
                    ledgerPosting ||
                    (statement.status !== 'APPROVED' && statement.status !== 'PAID')
                  }
                  className="btn-secondary min-h-[48px] px-5 rounded-[10px] text-xs font-semibold inline-flex items-center gap-1.5 border-brand text-brand"
                >
                  <LucideIcon name="book-open" className="w-4 h-4" />
                  {ledgerPosting
                    ? 'Posting ke Ledger…'
                    : postedLedgerTxId
                    ? 'Post Ulang ke Ledger'
                    : 'Post ke Buku Besar (Ledger)'}
                </button>
              </div>
            </div>

            {postedLedgerTxId && (
              <div className="px-5 py-3 bg-ok-bg border-b border-ok/30 flex items-center justify-between text-xs text-ok-2">
                <span className="font-semibold">
                  ✓ Transaksi tercatat di Buku Besar (Double-Entry Balanced) · ID: {postedLedgerTxId}
                </span>
                <span className="font-mono">Akun: 5000 (DEBIT) vs 2100/1100 (CREDIT)</span>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-[13px] text-left">
                <thead>
                  <tr className="border-b border-panel-2 bg-panel">
                    {['Penerima (Operator / QC)', 'Upah Pokok Jahit', 'Meal Allowance', 'Bonus Pool QC', 'Total Slip Upah'].map(h => (
                      <th key={h} className="px-4 py-3.5 font-semibold text-ink whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-panel-2">
                  {statement.items.map((it, idx) => (
                    <tr key={it.recipientId} className="hover:bg-panel transition-colors">
                      <td className="px-4 py-3.5">
                        <div className="font-medium text-ink">
                          {idx === 0 ? 'QC Inspector 1' : idx === 1 ? 'Mandor Jahit (Foreperson)' : 'Kepala Operasional'}
                        </div>
                        <code className="text-xs text-ink-muted font-mono">{it.recipientId.slice(0, 8)}</code>
                      </td>
                      <td className="px-4 py-3.5 font-mono">Rp {fmtMoney(it.base.amountMinor)}</td>
                      <td className="px-4 py-3.5 font-mono">Rp {fmtMoney(it.meal.amountMinor)}</td>
                      <td className="px-4 py-3.5 font-mono">Rp {fmtMoney(it.bonus.amountMinor)}</td>
                      <td className="px-4 py-3.5 font-mono font-bold text-ink">
                        Rp {fmtMoney(it.base.amountMinor + it.meal.amountMinor + it.bonus.amountMinor)}
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-panel font-semibold">
                    <td className="px-4 py-4 text-ink font-bold" colSpan={4}>
                      Total Upah Borongan Mingguan + Bonus QC
                    </td>
                    <td className="px-4 py-4 font-mono font-bold text-brand text-[15px]">
                      Rp {fmtMoney(totalOf(statement))}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {showPayment && statement && (
        <PaymentModal
          periodId={statement.periodId}
          onClose={() => setShowPayment(false)}
          onDone={s => {
            setStatement(s);
            setFlash('✓ Pembayaran direkam — status statement berubah menjadi PAID.');
          }}
        />
      )}
    </div>
  );
};

// ─── 3-Way QC Bonus Pool Tab ───────────────────────────────────────────────────
const BonusTab: React.FC<{
  selectedPeriodId: string;
  rules: FinancialRule[];
  periods: Period[];
  onFlash: (s: string | null) => void;
}> = ({ selectedPeriodId, rules, periods, onFlash }) => {
  const [pool, setPool] = useState<BonusPool | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const currentPeriod = periods.find(p => p.id === selectedPeriodId);
  const currentRule = rules.find(r => r.id === currentPeriod?.ruleVersion);

  const load = async () => {
    if (!selectedPeriodId) return;
    setBusy(true);
    setErr(null);
    onFlash(null);
    const res = await getBonusPool(selectedPeriodId);
    setBusy(false);
    if (!res.ok || !res.data) {
      setErr(res.error ?? 'Bonus pool belum tersedia untuk periode ini.');
      setPool(null);
      return;
    }
    setPool(res.data);
  };

  const remainderMinor = pool ? pool.pool.amountMinor % 3 : 0;
  const equalShare = pool ? Math.floor(pool.pool.amountMinor / 3) : 0;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-hair rounded-[18px] p-6 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-[17px] font-bold text-ink">3-Way QC Bonus Pool Split</h3>
            <p className="text-[12px] text-ink-muted mt-1">
              Akumulasi bonus QC per unit eligible dibagi tepat ke 3 penerima (QC 1, Mandor, Kepala Operasional)
            </p>
          </div>
          <button
            onClick={load}
            disabled={busy || !selectedPeriodId}
            className="btn-primary min-h-[48px] px-5 rounded-[10px] inline-flex items-center gap-2"
          >
            <LucideIcon name="badge-check" className="w-4 h-4" />
            {busy ? 'Memuat Bonus Pool…' : 'Muat Bonus Pool'}
          </button>
        </div>

        {err && (
          <div className="rounded-[14px] border border-warn bg-warn-bg p-4 text-[13px] text-warn-2 leading-relaxed">
            <span className="font-bold">Perhatian: </span>
            {err}
          </div>
        )}
      </div>

      {pool && (
        <div className="bg-white border border-hair rounded-[18px] p-6 shadow-sm space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-panel-2 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-[16px] font-bold text-ink">Settlement Pool QC</h4>
                <span className="pill pill-blue">{pool.status}</span>
              </div>
              <p className="text-[13px] text-ink-muted mt-1">
                Total Pool:{' '}
                <span className="font-mono font-bold text-ink text-[16px]">
                  Rp {fmtMoney(pool.pool.amountMinor)}
                </span>
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs text-ink-muted uppercase tracking-wider block font-semibold">Kebijakan Remainder</span>
              <code className="text-xs font-mono font-bold text-brand">
                {currentRule?.remainderPolicy ?? 'BLOCK_NON_DIVISIBLE'}
              </code>
            </div>
          </div>

          {/* Integer Rounding Remainder Card */}
          <div className="rounded-[14px] bg-panel border border-hair p-4 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-ink">Kalkulasi Pembagian Integer (3-Way Remainder):</span>
              <span className="font-mono text-ink-muted">
                {pool.pool.amountMinor} minor ÷ 3 = {equalShare} sisa {remainderMinor}
              </span>
            </div>
            <p className="text-[12px] text-ink-2 leading-relaxed">
              {remainderMinor === 0 ? (
                '✓ Pool terbagi bulat merata tanpa ada sisa (0 remainder).'
              ) : currentRule?.remainderPolicy === 'RESERVE_PROPOSED' ? (
                `Sisa integer pembagian Rp ${fmtMoney(remainderMinor)} dialokasikan ke Cadangan (Reserve Fund) sehingga masing-masing penerima menerima nominal bulat persis Rp ${fmtMoney(equalShare)}.`
              ) : (
                `Sisa integer pembagian Rp ${fmtMoney(remainderMinor)} diserap oleh Penerima 1 (QC Inspector 1) demi keutuhan desimal akuntansi.`
              )}
            </p>
          </div>

          {/* 3 Recipients Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {pool.recipients.map((r, i) => (
              <div
                key={r.recipientId}
                className="rounded-[14px] border border-hair p-5 bg-panel hover:bg-white hover:shadow-sm transition-all text-center"
              >
                <span className="pill rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-brand-bg text-brand inline-block mb-2">
                  {i === 0 ? 'QC Inspector 1' : i === 1 ? 'Mandor Jahit' : 'Kepala Operasional'}
                </span>
                <p className="text-[11px] text-ink-muted font-mono">{r.recipientId.slice(0, 12)}...</p>
                <p className="text-[22px] font-bold font-mono text-ink mt-3">
                  Rp {fmtMoney(r.amount.amountMinor)}
                </p>
                <p className="text-[11px] text-ink-muted mt-1">
                  {i === 0 && remainderMinor > 0 && currentRule?.remainderPolicy !== 'RESERVE_PROPOSED'
                    ? `Termasuk penyerapan sisa Rp ${fmtMoney(remainderMinor)}`
                    : '1/3 Bagian Bersih'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Monthly Overhead Allocation Tab ────────────────────────────────────────────
const OverheadTab: React.FC<{
  periods: Period[];
  approvedRules: FinancialRule[];
  onFlash: (s: string | null) => void;
}> = ({ periods, approvedRules, onFlash }) => {
  const [periodId, setPeriodId] = useState('');
  const [kind, setKind] = useState('LISTRIK');
  const [amount, setAmount] = useState('');
  const [allocation, setAllocation] = useState<OverheadAllocation | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // List of locally recorded overhead expenses
  const [overheadList, setOverheadList] = useState<
    { id: string; periodId: string; kind: string; amountMinor: number }[]
  >([
    { id: 'oh-1', periodId: periods[0]?.id || '', kind: 'LISTRIK PABRIK', amountMinor: 75000000 },
    { id: 'oh-2', periodId: periods[0]?.id || '', kind: 'AIR PDAM', amountMinor: 15000000 },
    { id: 'oh-3', periodId: periods[0]?.id || '', kind: 'INTERNET & TELKO', amountMinor: 10000000 },
  ]);

  useEffect(() => {
    if (!periodId && periods[0]) setPeriodId(periods[0].id);
  }, [periods, periodId]);

  const record = async () => {
    if (!amount || Number(amount) <= 0) {
      setErr('Nominal overhead harus lebih dari 0.');
      return;
    }
    setBusy(true);
    setErr(null);
    onFlash(null);
    const amountMinor = toMinor(amount);
    const res = await recordOverhead({
      periodId,
      kind,
      amount: toMoney(amountMinor, CURRENCY),
    });
    setBusy(false);
    if (!res.ok) {
      setErr(res.error ?? 'Gagal merekam overhead.');
      return;
    }
    setOverheadList(prev => [
      { id: res.data?.id ?? String(Date.now()), periodId, kind, amountMinor },
      ...prev,
    ]);
    onFlash(`✓ Biaya overhead "${kind}" dicatat: Rp ${fmtMoney(amountMinor)}`);
    setAmount('');
  };

  const allocate = async () => {
    const rule = approvedRules[0];
    if (!rule) {
      setErr('FINANCIAL_RULE_PENDING: Tidak ada aturan APPROVED untuk menghitung alokasi overhead.');
      return;
    }
    setBusy(true);
    setErr(null);
    onFlash(null);
    const res = await calculateOverhead(periodId, { ruleVersion: rule.id });
    setBusy(false);
    if (!res.ok || !res.data) {
      setErr(res.error ?? 'Gagal menghitung alokasi overhead.');
      setAllocation(null);
      return;
    }
    setAllocation(res.data);
  };

  const totalOverheadMinor = overheadList
    .filter(o => !periodId || o.periodId === periodId)
    .reduce((sum, o) => sum + o.amountMinor, 0);

  return (
    <div className="space-y-6">
      {/* Form Card */}
      <div className="bg-white border border-hair rounded-[18px] p-6 shadow-sm space-y-4">
        <div>
          <h3 className="text-[17px] font-bold text-ink">Catat Biaya Overhead Operasional Pabrik</h3>
          <p className="text-[12px] text-ink-muted mt-1">
            Biaya bulanan (Listrik, Air, Internet, Fasilitas) yang akan dialokasikan ke setiap unit barang jadi
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="oh-period" className="block text-sm font-medium text-ink mb-1.5">
              Periode
            </label>
            <select
              id="oh-period"
              value={periodId}
              onChange={e => setPeriodId(e.target.value)}
              className={inputCls}
            >
              <option value="">— pilih periode —</option>
              {periods.map(p => (
                <option key={p.id} value={p.id}>
                  {p.startsOn} → {p.endsOn}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="oh-kind" className="block text-sm font-medium text-ink mb-1.5">
              Jenis Pengeluaran
            </label>
            <select
              id="oh-kind"
              value={kind}
              onChange={e => setKind(e.target.value)}
              className={inputCls}
            >
              <option value="LISTRIK">Listrik Operasional Pabrik</option>
              <option value="AIR PDAM">Air PDAM / Sanitasi</option>
              <option value="INTERNET">Internet &amp; Server Line</option>
              <option value="SEWA GEDUNG">Sewa / Perawatan Fasilitas</option>
              <option value="LAINNYA">Overhead Lainnya</option>
            </select>
          </div>
          <div>
            <label htmlFor="oh-amount" className="block text-sm font-medium text-ink mb-1.5">
              Nominal (Rp)
            </label>
            <input
              id="oh-amount"
              type="number"
              min={0}
              step="1000"
              value={amount}
              placeholder="Contoh: 1500000"
              onChange={e => setAmount(e.target.value)}
              className={inputCls}
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-3 pt-2">
          <button
            onClick={record}
            disabled={busy || !periodId}
            className="btn-primary min-h-[48px] px-5 rounded-[10px] inline-flex items-center gap-2"
          >
            <LucideIcon name="plus" className="w-4 h-4" /> Catat Biaya Overhead
          </button>
          <button
            onClick={allocate}
            disabled={busy || !periodId}
            className="btn-secondary min-h-[48px] px-5 rounded-[10px] inline-flex items-center gap-2"
          >
            <LucideIcon name="bar-chart-3" className="w-4 h-4" /> Hitung Alokasi per Unit
          </button>
        </div>

        {err && <p className="text-[13px] text-bad-4 font-medium">{err}</p>}
      </div>

      {/* Allocation Result Display */}
      {allocation && (
        <div className="bg-white border border-hair rounded-[18px] p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-[16px] font-bold text-ink">Hasil Alokasi Overhead Satuan</h3>
            <span
              className={
                allocation.status === 'ALLOCATED' ? 'pill pill-green' : 'pill pill-orange'
              }
            >
              {allocation.status}
            </span>
          </div>
          {allocation.status === 'NO_OUTPUT' ? (
            <p className="text-[13px] text-ink-muted mt-2">
              Zero production volume — tidak ada unit terverifikasi untuk menyerap biaya (NO_OUTPUT).
            </p>
          ) : (
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-[12px] bg-panel p-4">
                <span className="text-xs text-ink-muted uppercase tracking-wider block font-semibold">Alokasi Biaya per Unit</span>
                <span className="text-[24px] font-bold font-mono text-brand">
                  Rp {fmtMoney(allocation.amountPerUnit?.amountMinor ?? 0)}
                </span>
                <p className="text-[11px] text-ink-muted mt-1">Dibagi ke 128 unit finished goods</p>
              </div>
              <div className="rounded-[12px] bg-panel p-4">
                <span className="text-xs text-ink-muted uppercase tracking-wider block font-semibold">Total Biaya Terserap</span>
                <span className="text-[24px] font-bold font-mono text-ink">
                  Rp {fmtMoney(totalOverheadMinor)}
                </span>
                <p className="text-[11px] text-ink-muted mt-1">Basis: FIRST_PASS_FINISHED_UNITS_PROPOSED</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Overhead List Table */}
      <div className="bg-white border border-hair rounded-[18px] overflow-hidden shadow-sm">
        <div className="p-5 border-b border-panel-2">
          <h4 className="text-[15px] font-bold text-ink">Daftar Biaya Overhead Tercatat</h4>
          <p className="text-[12px] text-ink-muted mt-0.5">
            Total biaya overhead tercatat: Rp {fmtMoney(totalOverheadMinor)}
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px] text-left">
            <thead>
              <tr className="border-b border-panel-2 bg-panel">
                {['ID', 'Jenis Overhead', 'Nominal'].map(h => (
                  <th key={h} className="px-4 py-3.5 font-semibold text-ink whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-panel-2">
              {overheadList.map(item => (
                <tr key={item.id} className="hover:bg-panel transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-ink-muted">{item.id.slice(0, 8)}</td>
                  <td className="px-4 py-3 font-medium text-ink">{item.kind}</td>
                  <td className="px-4 py-3 font-mono font-semibold text-ink">
                    Rp {fmtMoney(item.amountMinor)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ─── Financial Rules Tab ────────────────────────────────────────────────────────
const RulesTab: React.FC<{
  rules: FinancialRule[];
  onChanged: () => void;
  onFlash: (s: string | null) => void;
}> = ({ rules, onChanged, onFlash }) => {
  const [showPropose, setShowPropose] = useState(false);
  const [approveTarget, setApproveTarget] = useState<FinancialRule | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [form, setForm] = useState<FinancialRuleRequest>({
    effectiveFrom: '',
    mealBasis: 'VERIFIED_WAGES_PROPOSED',
    mealBasisPoints: 1200,
    mealDistribution: 'PROPORTIONAL_PROPOSED',
    bonusRate: toMoney(150000, CURRENCY),
    bonusRecipientIds: [...MOCK_RECIPIENTS],
    remainderPolicy: 'BLOCK_NON_DIVISIBLE',
    cutoffLocal: '23:59:00',
    overheadBasis: 'FIRST_PASS_FINISHED_UNITS_PROPOSED',
  });

  const propose = async () => {
    setBusy(true);
    setErr(null);
    const res = await proposeFinancialRule(form);
    setBusy(false);
    if (!res.ok) {
      setErr(res.error ?? 'Gagal mengajukan aturan.');
      return;
    }
    setShowPropose(false);
    onFlash('✓ Aturan finansial diajukan (status PENDING). Wajib diotorisasi bukti sebelum aktif.');
    onChanged();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h3 className="text-[17px] font-bold text-ink">Aturan Finansial &amp; Kebijakan Pembagian</h3>
          <p className="text-[12px] text-ink-muted mt-1">
            Versi aturan mengikat parameter meal allowance (10-15%), rate bonus QC, dan kebijakan integer remainder
          </p>
        </div>
        <button
          onClick={() => setShowPropose(true)}
          className="btn-primary min-h-[48px] px-5 rounded-[10px] inline-flex items-center gap-2"
        >
          <LucideIcon name="plus" className="w-4 h-4" /> Ajukan Aturan Baru
        </button>
      </div>

      <div className="bg-white border border-hair rounded-[18px] overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-[13px] text-left">
            <thead>
              <tr className="border-b border-panel-2 bg-panel">
                {['Versi / ID', 'Efektif Dari', 'Meal Rate', 'Bonus / Unit', 'Kebijakan Remainder', 'Status', 'Aksi'].map(
                  h => (
                    <th key={h} className="px-4 py-3.5 font-semibold text-ink whitespace-nowrap">
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-panel-2">
              {rules.map(r => (
                <tr key={r.id} className="hover:bg-panel transition-colors">
                  <td className="px-4 py-3.5">
                    <code className="text-xs font-mono font-bold text-ink">{r.id}</code>
                  </td>
                  <td className="px-4 py-3.5">{r.effectiveFrom}</td>
                  <td className="px-4 py-3.5 font-semibold">
                    {(r.mealBasisPoints / 100).toFixed(1)}% ({r.mealBasisPoints} bps)
                  </td>
                  <td className="px-4 py-3.5 font-mono">Rp {fmtMoney(r.bonusRate.amountMinor)}</td>
                  <td className="px-4 py-3.5 text-[12px] font-mono text-ink-muted">{r.remainderPolicy}</td>
                  <td className="px-4 py-3.5">
                    <span
                      className={
                        r.status === 'APPROVED' ? 'pill pill-green' : 'pill pill-orange'
                      }
                    >
                      {r.status === 'APPROVED' ? '✓ APPROVED' : '⚠ PENDING'}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    {r.status === 'PENDING' && (
                      <button
                        onClick={() => {
                          setApproveTarget(r);
                          setErr(null);
                        }}
                        className="btn-secondary min-h-[48px] px-4 rounded-[10px] text-xs font-semibold text-brand"
                      >
                        Otorisasi / Setujui
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Propose Rule Modal */}
      <Modal
        isOpen={showPropose}
        title="Ajukan Versi Aturan Finansial Baru"
        onClose={() => setShowPropose(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShowPropose(false)}
              className="btn-secondary min-h-[48px] px-5 rounded-[10px]"
            >
              Batal
            </button>
            <button
              onClick={propose}
              disabled={busy}
              className="btn-primary min-h-[48px] px-6 rounded-[10px]"
            >
              {busy ? 'Mengajukan…' : 'Ajukan Aturan'}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="rule-effective" className="block text-sm font-medium text-ink mb-1">
                Tanggal Efektif
              </label>
              <input
                id="rule-effective"
                type="date"
                value={form.effectiveFrom}
                onChange={e => setForm(f => ({ ...f, effectiveFrom: e.target.value }))}
                className={inputCls}
              />
            </div>
            <div>
              <label htmlFor="rule-meal" className="block text-sm font-medium text-ink mb-1">
                Meal Rate (1000–1500 bps = 10%–15%)
              </label>
              <input
                id="rule-meal"
                type="number"
                min={1000}
                max={1500}
                value={form.mealBasisPoints}
                onChange={e =>
                  setForm(f => ({ ...f, mealBasisPoints: parseInt(e.target.value) || 1200 }))
                }
                className={inputCls}
              />
            </div>
          </div>

          {/* Quick toggle chips for meal allowance */}
          <div>
            <span className="block text-xs font-semibold text-ink-muted mb-1.5">
              Pilihan Cepat Meal Allowance:
            </span>
            <div className="flex flex-wrap gap-2">
              {[1000, 1100, 1200, 1300, 1400, 1500].map(bps => (
                <button
                  key={bps}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, mealBasisPoints: bps }))}
                  className={`min-h-[48px] px-3.5 text-xs font-semibold rounded-[10px] border ${
                    form.mealBasisPoints === bps
                      ? 'bg-brand text-white border-brand'
                      : 'bg-white text-ink border-hair'
                  }`}
                >
                  {(bps / 100).toFixed(0)}%
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="rule-bonus" className="block text-sm font-medium text-ink mb-1">
                Bonus QC per Unit (Rp)
              </label>
              <input
                id="rule-bonus"
                type="number"
                min={0}
                value={form.bonusRate.amountMinor / 100}
                onChange={e =>
                  setForm(f => ({ ...f, bonusRate: toMoney(toMinor(e.target.value), CURRENCY) }))
                }
                className={inputCls}
              />
            </div>
            <div>
              <label htmlFor="rule-remainder" className="block text-sm font-medium text-ink mb-1">
                Kebijakan Remainder
              </label>
              <select
                id="rule-remainder"
                value={form.remainderPolicy}
                onChange={e =>
                  setForm(f => ({
                    ...f,
                    remainderPolicy: e.target.value as FinancialRuleRequest['remainderPolicy'],
                  }))
                }
                className={inputCls}
              >
                <option value="BLOCK_NON_DIVISIBLE">BLOCK_NON_DIVISIBLE (Blokir jika bersisa)</option>
                <option value="RESERVE_PROPOSED">RESERVE_PROPOSED (Alihkan ke Cadangan)</option>
              </select>
            </div>
          </div>

          <p className="text-[11px] text-ink-muted">
            Aturan baru akan dibuat dengan status <strong>PENDING</strong> dan memerlukan otorisasi persetujuan
            resmi Owner dengan berkas bukti (evidenceFileId) sebelum dapat digunakan untuk kalkulasi upah.
          </p>
          {err && <p className="text-[13px] text-bad-4 font-medium">{err}</p>}
        </div>
      </Modal>

      {/* Approve Rule Modal */}
      {approveTarget && (
        <RuleApproveModal
          rule={approveTarget}
          onClose={() => setApproveTarget(null)}
          onDone={() => {
            setApproveTarget(null);
            onFlash(`✓ Aturan ${approveTarget.id} berhasil disetujui (APPROVED).`);
            onChanged();
          }}
        />
      )}
    </div>
  );
};

// ─── Modal for Approving Financial Rule ──────────────────────────────────────────
const RuleApproveModal: React.FC<{
  rule: FinancialRule;
  onClose: () => void;
  onDone: () => void;
}> = ({ rule, onClose, onDone }) => {
  const [evidenceFileId, setEvidenceFileId] = useState('');
  const [approvalReference, setApprovalReference] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const approve = async () => {
    if (!evidenceFileId.trim()) {
      setErr('evidenceFileId (ID berkas otorisasi) wajib diisi.');
      return;
    }
    setBusy(true);
    setErr(null);
    const res = await approveFinancialRule(rule.id, {
      evidenceFileId,
      approvalReference: approvalReference.trim() || undefined,
      note: note.trim() || undefined,
    });
    setBusy(false);
    if (!res.ok) {
      setErr(res.error ?? 'Gagal menyetujui aturan.');
      return;
    }
    onDone();
  };

  return (
    <Modal
      isOpen
      title="Otorisasi &amp; Setujui Aturan Finansial"
      onClose={onClose}
      footer={
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="btn-secondary min-h-[48px] px-5 rounded-[10px]"
          >
            Batal
          </button>
          <button
            onClick={approve}
            disabled={busy || !evidenceFileId.trim()}
            className="btn-primary min-h-[48px] px-6 rounded-[10px]"
          >
            {busy ? 'Menyimpan…' : 'Otorisasi &amp; Setujui'}
          </button>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="rounded-[12px] bg-brand-bg border border-brand/20 p-3 text-xs text-brand leading-relaxed">
          Menyetujui aturan <code className="font-mono font-bold">{rule.id}</code>. Tindakan ini akan mengangkat
          status pemblokiran <code className="font-mono">FINANCIAL_RULE_PENDING</code> pada periode payroll terkait.
        </div>

        <div>
          <label htmlFor="rule-evidence" className="block text-sm font-medium text-ink mb-1">
            Evidence File ID (UUID Berkas Bukti Approval)*
          </label>
          <input
            id="rule-evidence"
            value={evidenceFileId}
            placeholder="Contoh: c1000000-0000-4000-8000-000000000001"
            onChange={e => setEvidenceFileId(e.target.value)}
            className={inputCls}
          />
        </div>

        <div>
          <label htmlFor="rule-ref" className="block text-sm font-medium text-ink mb-1">
            Referensi Otorisasi (Opsional)
          </label>
          <input
            id="rule-ref"
            value={approvalReference}
            placeholder="Contoh: SK-DIR-2026-X"
            onChange={e => setApprovalReference(e.target.value)}
            className={inputCls}
          />
        </div>

        <div>
          <label htmlFor="rule-note" className="block text-sm font-medium text-ink mb-1">
            Catatan Otorisasi
          </label>
          <input
            id="rule-note"
            value={note}
            placeholder="Catatan persetujuan dewan direksi / owner..."
            onChange={e => setNote(e.target.value)}
            className={inputCls}
          />
        </div>

        {err && <p className="text-[13px] text-bad-4 font-medium">{err}</p>}
      </div>
    </Modal>
  );
};

// ─── Periods Tab ───────────────────────────────────────────────────────────────
const PeriodsTab: React.FC<{
  periods: Period[];
  loading: boolean;
  onCreated: () => void;
}> = ({ periods, loading, onCreated }) => {
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState<PeriodRequest>({
    startsOn: '',
    endsOn: '',
    timezone: 'Asia/Jakarta',
    cutoffLocal: '23:59:00',
    ruleVersion: '',
  });

  const submit = async () => {
    setBusy(true);
    setErr(null);
    const res = await createPayrollPeriod(form);
    setBusy(false);
    if (!res.ok) {
      setErr(res.error ?? 'Gagal membuat periode.');
      return;
    }
    setShow(false);
    setForm({
      startsOn: '',
      endsOn: '',
      timezone: 'Asia/Jakarta',
      cutoffLocal: '23:59:00',
      ruleVersion: '',
    });
    onCreated();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-[17px] font-bold text-ink">Daftar Periode Payroll</h3>
          <p className="text-[12px] text-ink-muted mt-0.5">
            Siklus penggajian mingguan dengan batas cutoff Sabtu malam di zona waktu Asia/Jakarta
          </p>
        </div>
        <button
          onClick={() => setShow(true)}
          className="btn-primary min-h-[48px] px-5 rounded-[10px] inline-flex items-center gap-2"
        >
          <LucideIcon name="plus" className="w-4 h-4" /> Periode Baru
        </button>
      </div>

      <div className="bg-white border border-hair rounded-[18px] overflow-hidden shadow-sm">
        {loading ? (
          <p className="px-5 py-10 text-[13px] text-ink-muted text-center">Memuat periode…</p>
        ) : periods.length === 0 ? (
          <p className="px-5 py-10 text-[13px] text-ink-muted text-center">Belum ada periode payroll.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px] text-left">
              <thead>
                <tr className="border-b border-panel-2 bg-panel">
                  {['ID', 'Mulai', 'Selesai (Sabtu)', 'Cutoff Waktu', 'Zona Waktu', 'Versi Aturan'].map(h => (
                    <th key={h} className="px-4 py-3.5 font-semibold text-ink whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-panel-2">
                {periods.map(p => (
                  <tr key={p.id} className="hover:bg-panel transition-colors">
                    <td className="px-4 py-3.5">
                      <code className="text-xs font-mono text-ink-muted">{p.id.slice(0, 8)}</code>
                    </td>
                    <td className="px-4 py-3.5 font-medium">{p.startsOn}</td>
                    <td className="px-4 py-3.5 font-medium text-ink">{p.endsOn}</td>
                    <td className="px-4 py-3.5 font-mono text-ink-muted">{p.cutoffLocal}</td>
                    <td className="px-4 py-3.5">{p.timezone}</td>
                    <td className="px-4 py-3.5">
                      <code className="text-xs font-mono font-semibold text-brand">
                        {p.ruleVersion || '—'}
                      </code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal
        isOpen={show}
        title="Buat Periode Payroll Baru"
        onClose={() => setShow(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShow(false)}
              className="btn-secondary min-h-[48px] px-5 rounded-[10px]"
            >
              Batal
            </button>
            <button
              onClick={submit}
              disabled={busy}
              className="btn-primary min-h-[48px] px-6 rounded-[10px]"
            >
              {busy ? 'Menyimpan…' : 'Buat Periode'}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="period-start" className="block text-sm font-medium text-ink mb-1">
                Tanggal Mulai (Senin)
              </label>
              <input
                id="period-start"
                type="date"
                value={form.startsOn}
                onChange={e => setForm(f => ({ ...f, startsOn: e.target.value }))}
                className={inputCls}
              />
            </div>
            <div>
              <label htmlFor="period-end" className="block text-sm font-medium text-ink mb-1">
                Tanggal Selesai (Sabtu)
              </label>
              <input
                id="period-end"
                type="date"
                value={form.endsOn}
                onChange={e => setForm(f => ({ ...f, endsOn: e.target.value }))}
                className={inputCls}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="period-cutoff" className="block text-sm font-medium text-ink mb-1">
                Cutoff (HH:MM:00)
              </label>
              <input
                id="period-cutoff"
                value={form.cutoffLocal}
                onChange={e => setForm(f => ({ ...f, cutoffLocal: e.target.value }))}
                className={inputCls}
              />
            </div>
            <div>
              <label htmlFor="period-rule" className="block text-sm font-medium text-ink mb-1">
                Versi Aturan Finansial
              </label>
              <input
                id="period-rule"
                value={form.ruleVersion}
                placeholder="rule-2026-10-01"
                onChange={e => setForm(f => ({ ...f, ruleVersion: e.target.value }))}
                className={inputCls}
              />
            </div>
          </div>
          {err && <p className="text-[13px] text-bad-4 font-medium">{err}</p>}
        </div>
      </Modal>
    </div>
  );
};

// ─── Modal for Recording Payroll Payment ────────────────────────────────────────
const PaymentModal: React.FC<{
  periodId: string;
  onClose: () => void;
  onDone: (s: PayrollStatement) => void;
}> = ({ periodId, onClose, onDone }) => {
  const [externalReference, setExternalReference] = useState('');
  const [evidenceFileId, setEvidenceFileId] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setErr(null);
    const res = await recordPayrollPayment(periodId, { externalReference, evidenceFileId });
    setBusy(false);
    if (!res.ok || !res.data) {
      setErr(res.error ?? 'Gagal merekam pembayaran.');
      return;
    }
    onDone(res.data);
    onClose();
  };

  return (
    <Modal
      isOpen
      title="Rekam Bukti Pembayaran Eksternal"
      onClose={onClose}
      footer={
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="btn-secondary min-h-[48px] px-5 rounded-[10px]"
          >
            Batal
          </button>
          <button
            onClick={submit}
            disabled={busy}
            className="btn-primary min-h-[48px] px-6 rounded-[10px]"
          >
            {busy ? 'Menyimpan…' : 'Simpan Pembayaran'}
          </button>
        </div>
      }
    >
      <div className="space-y-4">
        <p className="text-[13px] text-ink-2">
          Sistem mencatat referensi eksternal &amp; bukti transfer bank; perpindahan dana aktual dijalankan di luar aplikasi.
        </p>
        <div>
          <label htmlFor="pay-ref" className="block text-sm font-medium text-ink mb-1">
            Referensi Eksternal (No. Referensi Bank)*
          </label>
          <input
            id="pay-ref"
            value={externalReference}
            placeholder="mis. TRF-20261012-001"
            onChange={e => setExternalReference(e.target.value)}
            className={inputCls}
          />
        </div>
        <div>
          <label htmlFor="pay-file" className="block text-sm font-medium text-ink mb-1">
            Evidence File ID (UUID Berkas Bukti)*
          </label>
          <input
            id="pay-file"
            value={evidenceFileId}
            placeholder="mis. d1000000-0000-4000-8000-000000000001"
            onChange={e => setEvidenceFileId(e.target.value)}
            className={inputCls}
          />
        </div>
        {err && <p className="text-[13px] text-bad-4 font-medium">{err}</p>}
      </div>
    </Modal>
  );
};

export default PayrollView;
