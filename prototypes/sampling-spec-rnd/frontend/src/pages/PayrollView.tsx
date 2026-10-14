/**
 * PayrollView — VIEW-06: dynamic payroll & costing surface (MOD-05).
 *
 * Covers the frozen payroll contract end-to-end: period lifecycle, weekly
 * borongan calculation, itemized statement, three-way QC bonus pool, monthly
 * overhead allocation, and the versioned financial-rule gate. Backed by
 * services/payrollApi.ts (mock by default; contract-shaped for live mode).
 *
 * Domain guardrail: a calculation that references a rule version which is not
 * APPROVED must surface FINANCIAL_RULE_PENDING and show no monetary amount.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LucideIcon } from '../components/Sidebar';
import Modal from '../components/Modal';
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

const inputCls = 'w-full rounded-[10px] px-3 py-2.5 text-[13px]';
const CURRENCY: Currency = 'IDR';

const fmtMoney = (minor: number) =>
  (minor / 100).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const toMinor = (major: string) => Math.round((Number(major) || 0) * 100);

const STATUS_PILL: Record<PeriodStatus, string> = {
  OPEN: 'pill pill-gray',
  CALCULATED: 'pill pill-blue',
  PENDING_RULE: 'pill pill-orange',
  APPROVED: 'pill pill-green',
  PAID: 'pill pill-dark',
};

type Tab = 'periods' | 'run' | 'bonus' | 'overhead' | 'rules';

const TABS: { id: Tab; label: string }[] = [
  { id: 'periods', label: 'Periode' },
  { id: 'run', label: 'Kalkulasi & Slip' },
  { id: 'bonus', label: 'Bonus Pool' },
  { id: 'overhead', label: 'Overhead' },
  { id: 'rules', label: 'Aturan Finansial' },
];

const PayrollView: React.FC = () => {
  const [tab, setTab] = useState<Tab>('periods');
  const [periods, setPeriods] = useState<Period[]>([]);
  const [rules, setRules] = useState<FinancialRule[]>([]);
  const [selectedPeriodId, setSelectedPeriodId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

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

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Payroll &amp; Costing</h2>
          <p className="text-[#6e6e73] text-sm mt-1">
            Upah borongan mingguan, meal allowance, bonus pool QC, dan alokasi overhead bulanan
          </p>
        </div>
        <button onClick={load} className="btn-secondary">
          <LucideIcon name="activity" className="w-4 h-4" /> Refresh
        </button>
      </div>

      {isMockPayroll && (
        <div className="rounded-[14px] border border-[#d5d5da] bg-[#f4f8fd] px-4 py-3 text-[12.5px] text-[#334155]">
          Mode mock aktif — endpoint HTTP payroll belum ada di backend, data di memori.
          Set <code className="font-mono">VITE_LEDGER_MODE=live</code> setelah endpoint tersedia.
        </div>
      )}
      {error && <div className="rounded-[14px] border border-[#fecaca] bg-[#fee2e2] px-4 py-3 text-[13px] text-[#dc2626]">{error}</div>}
      {flash && <div className="rounded-[14px] border border-[#34c759] bg-[#e8f5e9] px-4 py-3 text-[13px] font-medium text-[#1a7a34]">{flash}</div>}

      <div className="inline-flex flex-wrap gap-1 rounded-[12px] bg-[#f0f0f2] p-1">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`min-h-[40px] rounded-[9px] px-4 text-[13px] font-semibold transition-all ${
              tab === t.id ? 'bg-white text-[#1d1d1f] shadow-sm' : 'text-[#626269]'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'periods' && <PeriodsTab periods={periods} loading={loading} onCreated={load} />}
      {tab === 'run' && (
        <RunTab
          periods={periods}
          rules={rules}
          selectedPeriodId={selectedPeriodId}
          onSelectPeriod={setSelectedPeriodId}
        />
      )}
      {tab === 'bonus' && <BonusTab selectedPeriodId={selectedPeriodId} onFlash={setFlash} />}
      {tab === 'overhead' && <OverheadTab periods={periods} approvedRules={approvedRules} onFlash={setFlash} />}
      {tab === 'rules' && <RulesTab rules={rules} onChanged={load} onFlash={setFlash} />}
    </div>
  );
};

// ─── Periods ──────────────────────────────────────────────────────────────────
const PeriodsTab: React.FC<{ periods: Period[]; loading: boolean; onCreated: () => void }> = ({ periods, loading, onCreated }) => {
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState<PeriodRequest>({
    startsOn: '', endsOn: '', timezone: 'Asia/Jakarta', cutoffLocal: '23:59:00', ruleVersion: '',
  });

  const submit = async () => {
    setBusy(true); setErr(null);
    const res = await createPayrollPeriod(form);
    setBusy(false);
    if (!res.ok) { setErr(res.error ?? 'Gagal membuat periode.'); return; }
    setShow(false);
    setForm({ startsOn: '', endsOn: '', timezone: 'Asia/Jakarta', cutoffLocal: '23:59:00', ruleVersion: '' });
    onCreated();
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShow(true)} className="btn-primary inline-flex items-center gap-2">
          <LucideIcon name="plus" className="w-4 h-4" /> Periode Baru
        </button>
      </div>

      <div className="bg-white border border-[#e6e6e9] rounded-[18px] overflow-hidden">
        {loading ? (
          <p className="px-5 py-10 text-[13px] text-[#6e6e73] text-center">Memuat…</p>
        ) : periods.length === 0 ? (
          <p className="px-5 py-10 text-[13px] text-[#6e6e73] text-center">Belum ada periode payroll.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr>{['ID', 'Mulai', 'Selesai', 'Cutoff', 'Timezone', 'Versi Aturan'].map(h => (
                  <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {periods.map(p => (
                  <tr key={p.id}>
                    <td className="px-4 py-3"><code className="text-xs text-[#6e6e73]">{p.id.slice(0, 8)}</code></td>
                    <td className="px-4 py-3">{p.startsOn}</td>
                    <td className="px-4 py-3">{p.endsOn}</td>
                    <td className="px-4 py-3 font-mono text-[#6e6e73]">{p.cutoffLocal}</td>
                    <td className="px-4 py-3">{p.timezone}</td>
                    <td className="px-4 py-3"><code className="text-xs">{p.ruleVersion || '—'}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal isOpen={show} title="Periode Payroll Baru" onClose={() => setShow(false)}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={() => setShow(false)} className="btn-secondary">Batal</button>
          <button onClick={submit} disabled={busy} className="btn-primary">{busy ? 'Menyimpan…' : 'Buat'}</button>
        </div>}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="period-start" className="block text-sm font-medium text-[#1d1d1f] mb-1">Mulai</label>
              <input id="period-start" type="date" value={form.startsOn}
                onChange={e => setForm(f => ({ ...f, startsOn: e.target.value }))} className={inputCls} />
            </div>
            <div>
              <label htmlFor="period-end" className="block text-sm font-medium text-[#1d1d1f] mb-1">Selesai</label>
              <input id="period-end" type="date" value={form.endsOn}
                onChange={e => setForm(f => ({ ...f, endsOn: e.target.value }))} className={inputCls} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="period-cutoff" className="block text-sm font-medium text-[#1d1d1f] mb-1">Cutoff (HH:MM:00)</label>
              <input id="period-cutoff" value={form.cutoffLocal}
                onChange={e => setForm(f => ({ ...f, cutoffLocal: e.target.value }))} className={inputCls} />
            </div>
            <div>
              <label htmlFor="period-rule" className="block text-sm font-medium text-[#1d1d1f] mb-1">Versi Aturan</label>
              <input id="period-rule" value={form.ruleVersion} placeholder="rule-2026-10-01"
                onChange={e => setForm(f => ({ ...f, ruleVersion: e.target.value }))} className={inputCls} />
            </div>
          </div>
          {err && <p className="text-[13px] text-[#dc2626]">{err}</p>}
        </div>
      </Modal>
    </div>
  );
};

// ─── Calculation & statement ────────────────────────────────────────────────────
const RunTab: React.FC<{
  periods: Period[];
  rules: FinancialRule[];
  selectedPeriodId: string;
  onSelectPeriod: (id: string) => void;
}> = ({ periods, rules, selectedPeriodId, onSelectPeriod }) => {
  const [ruleVersion, setRuleVersion] = useState('');
  const [result, setResult] = useState<PayrollResult | null>(null);
  const [statement, setStatement] = useState<PayrollStatement | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [showPayment, setShowPayment] = useState(false);

  useEffect(() => {
    const period = periods.find(p => p.id === selectedPeriodId);
    if (period) setRuleVersion(period.ruleVersion);
  }, [periods, selectedPeriodId]);

  const calculate = async () => {
    if (!selectedPeriodId) { setErr('Pilih periode terlebih dahulu.'); return; }
    setBusy(true); setErr(null); setFlash(null);
    const res = await calculateWeeklyPayroll(selectedPeriodId, { ruleVersion });
    setBusy(false);
    if (!res.ok || !res.data) { setErr(res.error ?? 'Gagal menghitung payroll.'); setResult(null); return; }
    setResult(res.data);
    setFlash(`✓ Payroll dihitung: ${res.data.eligibleUnits} unit eligible`);
    await loadStatement();
  };

  const loadStatement = async () => {
    if (!selectedPeriodId) return;
    const res = await getPayrollStatement(selectedPeriodId);
    if (res.ok && res.data) setStatement(res.data);
    else setStatement(null);
  };

  const approve = async () => {
    if (!statement) return;
    setBusy(true); setErr(null); setFlash(null);
    const res = await approvePayroll(statement.periodId, { version: statement.version, inputHash: statement.inputHash });
    setBusy(false);
    if (!res.ok || !res.data) { setErr(res.error ?? 'Gagal menyetujui payroll.'); return; }
    setStatement(res.data);
    setFlash('✓ Payroll disetujui (version + inputHash terkunci).');
  };

  const totalOf = (s: PayrollStatement) =>
    s.items.reduce((sum, it) => sum + it.base.amountMinor + it.meal.amountMinor + it.bonus.amountMinor, 0);

  return (
    <div className="space-y-4">
      <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="run-period" className="block text-sm font-medium text-[#1d1d1f] mb-1">Periode</label>
            <select id="run-period" value={selectedPeriodId} onChange={e => onSelectPeriod(e.target.value)} className={inputCls}>
              <option value="">— pilih periode —</option>
              {periods.map(p => <option key={p.id} value={p.id}>{p.startsOn} → {p.endsOn}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="run-rule" className="block text-sm font-medium text-[#1d1d1f] mb-1">Versi Aturan</label>
            <select id="run-rule" value={ruleVersion} onChange={e => setRuleVersion(e.target.value)} className={inputCls}>
              <option value="">— pilih versi —</option>
              {rules.map(r => (
                <option key={r.id} value={r.id}>{r.id} · {r.status === 'APPROVED' ? 'disetujui' : 'pending'}</option>
              ))}
            </select>
            <p className="text-[11px] text-[#6e6e73] mt-1">Aturan non-APPROVED akan ditolak dengan <code className="font-mono">FINANCIAL_RULE_PENDING</code>.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button onClick={calculate} disabled={busy} className="btn-primary inline-flex items-center gap-2">
            <LucideIcon name="bar-chart-3" className="w-4 h-4" /> {busy ? 'Menghitung…' : 'Hitung Payroll'}
          </button>
          <button onClick={loadStatement} className="btn-secondary inline-flex items-center gap-2">
            <LucideIcon name="file-text" className="w-4 h-4" /> Muat Slip
          </button>
        </div>
        {err && <p className="text-[13px] text-[#dc2626]">{err}</p>}
        {flash && <p className="text-[13px] text-[#1a7a34]">{flash}</p>}
      </div>

      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 text-center">
            <p className="text-xs text-[#6e6e73] uppercase tracking-wider mb-1">Status</p>
            <p className="text-[16px] font-semibold text-[#1d1d1f]">{result.status}</p>
          </div>
          <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 text-center">
            <p className="text-xs text-[#6e6e73] uppercase tracking-wider mb-1">Unit Eligible</p>
            <p className="text-[26px] font-semibold text-[#0066cc]">{result.eligibleUnits}</p>
          </div>
          <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 text-center">
            <p className="text-xs text-[#6e6e73] uppercase tracking-wider mb-1">Total Upah</p>
            <p className="text-[20px] font-semibold text-[#1d1d1f] font-mono">Rp {fmtMoney(result.totalWages.amountMinor)}</p>
          </div>
        </div>
      )}

      {statement && (
        <div className="bg-white border border-[#e6e6e9] rounded-[18px] overflow-hidden">
          <div className="flex flex-wrap justify-between items-center gap-3 p-5 border-b border-[#f0f0f2]">
            <div>
              <h3 className="text-[16px] font-bold text-[#0f172a]">Slip Upah (Statement)</h3>
              <p className="text-[12px] text-[#64748b] mt-0.5">
                v{statement.version} · inputHash <code className="font-mono">{statement.inputHash}</code> ·
                reserve <span className="font-mono">Rp {fmtMoney(statement.reserve.amountMinor)}</span>
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className={STATUS_PILL[statement.status]}>{statement.status}</span>
              <button onClick={approve} disabled={busy || statement.status !== 'CALCULATED'} className="btn-success !py-1.5 !px-3 !text-xs">
                Setujui
              </button>
              <button onClick={() => setShowPayment(true)} disabled={statement.status !== 'APPROVED'} className="btn-primary !py-1.5 !px-3 !text-xs">
                Rekam Pembayaran
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr>{['Penerima', 'Base', 'Meal', 'Bonus', 'Total'].map(h => (
                  <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {statement.items.map(it => (
                  <tr key={it.recipientId}>
                    <td className="px-4 py-3"><code className="text-xs text-[#6e6e73]">{it.recipientId.slice(0, 8)}</code></td>
                    <td className="px-4 py-3 font-mono">{fmtMoney(it.base.amountMinor)}</td>
                    <td className="px-4 py-3 font-mono">{fmtMoney(it.meal.amountMinor)}</td>
                    <td className="px-4 py-3 font-mono">{fmtMoney(it.bonus.amountMinor)}</td>
                    <td className="px-4 py-3 font-mono font-semibold text-[#1d1d1f]">
                      {fmtMoney(it.base.amountMinor + it.meal.amountMinor + it.bonus.amountMinor)}
                    </td>
                  </tr>
                ))}
                <tr>
                  <td className="px-4 py-3 font-semibold text-[#1d1d1f]" colSpan={4}>Total</td>
                  <td className="px-4 py-3 font-mono font-semibold text-[#1d1d1f]">{fmtMoney(totalOf(statement))}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showPayment && statement && (
        <PaymentModal periodId={statement.periodId} onClose={() => setShowPayment(false)}
          onDone={s => { setStatement(s); setFlash('✓ Pembayaran direkam — statement berstatus PAID.'); }} />
      )}
    </div>
  );
};

const PaymentModal: React.FC<{ periodId: string; onClose: () => void; onDone: (s: PayrollStatement) => void }> =
  ({ periodId, onClose, onDone }) => {
    const [externalReference, setExternalReference] = useState('');
    const [evidenceFileId, setEvidenceFileId] = useState('');
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    const submit = async () => {
      setBusy(true); setErr(null);
      const res = await recordPayrollPayment(periodId, { externalReference, evidenceFileId });
      setBusy(false);
      if (!res.ok || !res.data) { setErr(res.error ?? 'Gagal merekam pembayaran.'); return; }
      onDone(res.data);
      onClose();
    };

    return (
      <Modal isOpen title="Rekam Pembayaran Eksternal" onClose={onClose}
        footer={<div className="flex gap-3 justify-end">
          <button onClick={onClose} className="btn-secondary">Batal</button>
          <button onClick={submit} disabled={busy} className="btn-primary">{busy ? 'Menyimpan…' : 'Simpan'}</button>
        </div>}>
        <div className="space-y-4">
          <p className="text-[13px] text-[#334155]">Sistem hanya mencatat bukti pembayaran; transfer bank dilakukan di luar aplikasi.</p>
          <div>
            <label htmlFor="pay-ref" className="block text-sm font-medium text-[#1d1d1f] mb-1">Referensi Eksternal</label>
            <input id="pay-ref" value={externalReference} placeholder="mis. TRF-20261012-001"
              onChange={e => setExternalReference(e.target.value)} className={inputCls} />
          </div>
          <div>
            <label htmlFor="pay-file" className="block text-sm font-medium text-[#1d1d1f] mb-1">Evidence File ID</label>
            <input id="pay-file" value={evidenceFileId} placeholder="uuid berkas bukti"
              onChange={e => setEvidenceFileId(e.target.value)} className={inputCls} />
          </div>
          {err && <p className="text-[13px] text-[#dc2626]">{err}</p>}
        </div>
      </Modal>
    );
  };

// ─── Bonus pool ─────────────────────────────────────────────────────────────────
const BonusTab: React.FC<{ selectedPeriodId: string; onFlash: (s: string | null) => void }> = ({ selectedPeriodId, onFlash }) => {
  const [pool, setPool] = useState<BonusPool | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setBusy(true); setErr(null); onFlash(null);
    const res = await getBonusPool(selectedPeriodId);
    setBusy(false);
    if (!res.ok || !res.data) { setErr(res.error ?? 'Bonus pool belum tersedia.'); setPool(null); return; }
    setPool(res.data);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={load} disabled={busy || !selectedPeriodId} className="btn-primary inline-flex items-center gap-2">
          <LucideIcon name="badge-check" className="w-4 h-4" /> {busy ? 'Memuat…' : 'Muat Bonus Pool'}
        </button>
      </div>
      {err && <div className="rounded-[14px] border border-[#fde68a] bg-[#fef3c7] px-4 py-3 text-[13px] text-[#b45309]">{err}</div>}
      {pool && (
        <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-[16px] font-bold text-[#0f172a]">Three-way Bonus Pool</h3>
            <span className="pill pill-blue">{pool.status}</span>
          </div>
          <p className="text-[13px] text-[#64748b]">
            Pool <span className="font-mono font-semibold text-[#1d1d1f]">Rp {fmtMoney(pool.pool.amountMinor)}</span> dibagi
            tepat ke tiga penerima.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {pool.recipients.map(r => (
              <div key={r.recipientId} className="rounded-[14px] border border-[#e6e6e9] p-4 text-center">
                <p className="text-[11px] text-[#6e6e73] uppercase tracking-wider mb-1">Penerima</p>
                <code className="text-xs text-[#64748b]">{r.recipientId.slice(0, 8)}</code>
                <p className="text-[18px] font-semibold font-mono text-[#1d1d1f] mt-2">Rp {fmtMoney(r.amount.amountMinor)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Overhead ───────────────────────────────────────────────────────────────────
const OverheadTab: React.FC<{ periods: Period[]; approvedRules: FinancialRule[]; onFlash: (s: string | null) => void }> =
  ({ periods, approvedRules, onFlash }) => {
    const [periodId, setPeriodId] = useState('');
    const [kind, setKind] = useState('');
    const [amount, setAmount] = useState('');
    const [allocation, setAllocation] = useState<OverheadAllocation | null>(null);
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    useEffect(() => { if (!periodId && periods[0]) setPeriodId(periods[0].id); }, [periods, periodId]);

    const record = async () => {
      setBusy(true); setErr(null); onFlash(null);
      const res = await recordOverhead({ periodId, kind, amount: toMoney(toMinor(amount), CURRENCY) });
      setBusy(false);
      if (!res.ok) { setErr(res.error ?? 'Gagal merekam overhead.'); return; }
      onFlash('✓ Overhead dicatat.');
      setKind(''); setAmount('');
    };

    const allocate = async () => {
      const rule = approvedRules[0];
      if (!rule) { setErr('Tidak ada aturan APPROVED untuk alokasi.'); return; }
      setBusy(true); setErr(null); onFlash(null);
      const res = await calculateOverhead(periodId, { ruleVersion: rule.id });
      setBusy(false);
      if (!res.ok || !res.data) { setErr(res.error ?? 'Gagal menghitung alokasi.'); setAllocation(null); return; }
      setAllocation(res.data);
    };

    return (
      <div className="space-y-4">
        <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="oh-period" className="block text-sm font-medium text-[#1d1d1f] mb-1">Periode</label>
              <select id="oh-period" value={periodId} onChange={e => setPeriodId(e.target.value)} className={inputCls}>
                <option value="">— pilih periode —</option>
                {periods.map(p => <option key={p.id} value={p.id}>{p.startsOn} → {p.endsOn}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="oh-kind" className="block text-sm font-medium text-[#1d1d1f] mb-1">Jenis</label>
              <input id="oh-kind" value={kind} placeholder="mis. LISTRIK"
                onChange={e => setKind(e.target.value)} className={inputCls} />
            </div>
            <div>
              <label htmlFor="oh-amount" className="block text-sm font-medium text-[#1d1d1f] mb-1">Nominal (Rp)</label>
              <input id="oh-amount" type="number" min={0} step="0.01" value={amount} placeholder="0.00"
                onChange={e => setAmount(e.target.value)} className={inputCls} />
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <button onClick={record} disabled={busy || !periodId} className="btn-primary inline-flex items-center gap-2">
              <LucideIcon name="plus" className="w-4 h-4" /> Catat Overhead
            </button>
            <button onClick={allocate} disabled={busy || !periodId} className="btn-secondary inline-flex items-center gap-2">
              <LucideIcon name="bar-chart-3" className="w-4 h-4" /> Hitung Alokasi / Unit
            </button>
          </div>
          {err && <p className="text-[13px] text-[#dc2626]">{err}</p>}
        </div>

        {allocation && (
          <div className="bg-white border border-[#e6e6e9] rounded-[18px] p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-[16px] font-bold text-[#0f172a]">Alokasi Overhead</h3>
              <span className={allocation.status === 'ALLOCATED' ? 'pill pill-green' : 'pill pill-orange'}>{allocation.status}</span>
            </div>
            {allocation.status === 'NO_OUTPUT' ? (
              <p className="text-[13px] text-[#6e6e73] mt-2">Zero production — tidak ada alokasi per unit (NO_OUTPUT).</p>
            ) : (
              <p className="text-[15px] text-[#1d1d1f] mt-2">
                Alokasi per unit:{' '}
                <span className="font-mono font-semibold">Rp {fmtMoney(allocation.amountPerUnit?.amountMinor ?? 0)}</span>
              </p>
            )}
          </div>
        )}
      </div>
    );
  };

// ─── Financial rules ────────────────────────────────────────────────────────────
const RulesTab: React.FC<{ rules: FinancialRule[]; onChanged: () => void; onFlash: (s: string | null) => void }> =
  ({ rules, onChanged, onFlash }) => {
    const [showPropose, setShowPropose] = useState(false);
    const [approveTarget, setApproveTarget] = useState<FinancialRule | null>(null);
    const [evidenceFileId, setEvidenceFileId] = useState('');
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    const [form, setForm] = useState<FinancialRuleRequest>({
      effectiveFrom: '', mealBasis: 'VERIFIED_WAGES_PROPOSED', mealBasisPoints: 1200,
      mealDistribution: 'PROPORTIONAL_PROPOSED', bonusRate: toMoney(150000, CURRENCY),
      bonusRecipientIds: [...MOCK_RECIPIENTS], remainderPolicy: 'BLOCK_NON_DIVISIBLE',
      cutoffLocal: '23:59:00', overheadBasis: 'FIRST_PASS_FINISHED_UNITS_PROPOSED',
    });

    const propose = async () => {
      setBusy(true); setErr(null);
      const res = await proposeFinancialRule(form);
      setBusy(false);
      if (!res.ok) { setErr(res.error ?? 'Gagal mengajukan aturan.'); return; }
      setShowPropose(false);
      onFlash('✓ Aturan diajukan (status PENDING).');
      onChanged();
    };

    const approve = async () => {
      if (!approveTarget) return;
      setBusy(true); setErr(null);
      const res = await approveFinancialRule(approveTarget.id, { evidenceFileId });
      setBusy(false);
      if (!res.ok) { setErr(res.error ?? 'Gagal menyetujui aturan.'); return; }
      setApproveTarget(null); setEvidenceFileId('');
      onFlash('✓ Aturan disetujui (APPROVED).');
      onChanged();
    };

    return (
      <div className="space-y-4">
        <div className="flex justify-end">
          <button onClick={() => setShowPropose(true)} className="btn-primary inline-flex items-center gap-2">
            <LucideIcon name="plus" className="w-4 h-4" /> Ajukan Aturan
          </button>
        </div>

        <div className="bg-white border border-[#e6e6e9] rounded-[18px] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr>{['Versi/ID', 'Efektif', 'Meal', 'Bonus/Unit', 'Remainder', 'Status', 'Aksi'].map(h => (
                  <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {rules.map(r => (
                  <tr key={r.id}>
                    <td className="px-4 py-3"><code className="text-xs">{r.id}</code></td>
                    <td className="px-4 py-3">{r.effectiveFrom}</td>
                    <td className="px-4 py-3">{(r.mealBasisPoints / 100).toFixed(1)}%</td>
                    <td className="px-4 py-3 font-mono">Rp {fmtMoney(r.bonusRate.amountMinor)}</td>
                    <td className="px-4 py-3 text-[12px] text-[#6e6e73]">{r.remainderPolicy}</td>
                    <td className="px-4 py-3">
                      <span className={r.status === 'APPROVED' ? 'pill pill-green' : 'pill pill-orange'}>{r.status}</span>
                    </td>
                    <td className="px-4 py-3">
                      {r.status === 'PENDING' && (
                        <button onClick={() => { setApproveTarget(r); setEvidenceFileId(''); setErr(null); }}
                          className="btn-secondary !py-1.5 !px-3 !text-xs">Setujui</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <Modal isOpen={showPropose} title="Ajukan Aturan Finansial" onClose={() => setShowPropose(false)}
          footer={<div className="flex gap-3 justify-end">
            <button onClick={() => setShowPropose(false)} className="btn-secondary">Batal</button>
            <button onClick={propose} disabled={busy} className="btn-primary">{busy ? 'Mengirim…' : 'Ajukan'}</button>
          </div>}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="rule-effective" className="block text-sm font-medium text-[#1d1d1f] mb-1">Efektif Dari</label>
                <input id="rule-effective" type="date" value={form.effectiveFrom}
                  onChange={e => setForm(f => ({ ...f, effectiveFrom: e.target.value }))} className={inputCls} />
              </div>
              <div>
                <label htmlFor="rule-meal" className="block text-sm font-medium text-[#1d1d1f] mb-1">Meal Basis Points</label>
                <input id="rule-meal" type="number" min={1000} max={1500} value={form.mealBasisPoints}
                  onChange={e => setForm(f => ({ ...f, mealBasisPoints: parseInt(e.target.value) || 1200 }))} className={inputCls} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="rule-bonus" className="block text-sm font-medium text-[#1d1d1f] mb-1">Bonus / Unit (Rp)</label>
                <input id="rule-bonus" type="number" min={0} value={form.bonusRate.amountMinor / 100}
                  onChange={e => setForm(f => ({ ...f, bonusRate: toMoney(toMinor(e.target.value), CURRENCY) }))} className={inputCls} />
              </div>
              <div>
                <label htmlFor="rule-remainder" className="block text-sm font-medium text-[#1d1d1f] mb-1">Remainder Policy</label>
                <select id="rule-remainder" value={form.remainderPolicy}
                  onChange={e => setForm(f => ({ ...f, remainderPolicy: e.target.value as FinancialRuleRequest['remainderPolicy'] }))}
                  className={inputCls}>
                  <option value="BLOCK_NON_DIVISIBLE">BLOCK_NON_DIVISIBLE</option>
                  <option value="RESERVE_PROPOSED">RESERVE_PROPOSED</option>
                </select>
              </div>
            </div>
            <div>
              <label htmlFor="rule-dist" className="block text-sm font-medium text-[#1d1d1f] mb-1">Meal Distribution</label>
              <select id="rule-dist" value={form.mealDistribution}
                onChange={e => setForm(f => ({ ...f, mealDistribution: e.target.value as FinancialRuleRequest['mealDistribution'] }))}
                className={inputCls}>
                <option value="PROPORTIONAL_PROPOSED">PROPORTIONAL_PROPOSED</option>
                <option value="EQUAL_ACTIVE_PROPOSED">EQUAL_ACTIVE_PROPOSED</option>
              </select>
            </div>
            <p className="text-[11px] text-[#6e6e73]">Aturan baru dibuat dengan status <strong>PENDING</strong> dan wajib bukti persetujuan sebelum dipakai.</p>
            {err && <p className="text-[13px] text-[#dc2626]">{err}</p>}
          </div>
        </Modal>

        <Modal isOpen={approveTarget !== null} title="Setujui Aturan Finansial" onClose={() => setApproveTarget(null)}
          footer={<div className="flex gap-3 justify-end">
            <button onClick={() => setApproveTarget(null)} className="btn-secondary">Batal</button>
            <button onClick={approve} disabled={busy || !evidenceFileId.trim()} className="btn-primary">{busy ? 'Menyimpan…' : 'Setujui'}</button>
          </div>}>
          <div className="space-y-4">
            <p className="text-[13px] text-[#334155]">
              Menyetujui <code className="font-mono">{approveTarget?.id}</code>. Approval butuh bukti otorisasi eksternal.
            </p>
            <div>
              <label htmlFor="rule-evidence" className="block text-sm font-medium text-[#1d1d1f] mb-1">Evidence File ID</label>
              <input id="rule-evidence" value={evidenceFileId} placeholder="uuid berkas bukti"
                onChange={e => setEvidenceFileId(e.target.value)} className={inputCls} />
            </div>
            {err && <p className="text-[13px] text-[#dc2626]">{err}</p>}
          </div>
        </Modal>
      </div>
    );
  };

export default PayrollView;
