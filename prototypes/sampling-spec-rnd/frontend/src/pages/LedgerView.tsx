/**
 * LedgerView — Immutable double-entry ledger (VIEW-06 finance surface).
 *
 * Reads, posts, and reverses balanced transactions through the ledger API
 * client. Backed by the in-memory mock by default (see services/ledgerApi.ts);
 * the UI never treats cached data as authoritative and only reflects what the
 * server/mock returns.
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
  getLedgerEntries,
  appendLedgerTransaction,
  reverseLedgerTransaction,
  sumMinor,
  isMockLedger,
  type LedgerTransaction,
  type LedgerEntry,
  type LedgerDirection,
} from '../services/ledgerApi';

export const LEDGER_ACCOUNTS = [
  { code: '1100', name: 'Kas' },
  { code: '1200', name: 'Piutang Usaha' },
  { code: '2100', name: 'Utang Usaha' },
  { code: '4000', name: 'Pendapatan Penjualan' },
  { code: '5000', name: 'Beban Gaji' },
  { code: '5100', name: 'Beban Bahan / Pabrik' },
];

export const accountLabel = (code: string): string => {
  const acc = LEDGER_ACCOUNTS.find(a => a.code === code);
  return acc ? `${acc.code} · ${acc.name}` : code;
};

export const fmtMoney = (minor: number): string =>
  (minor / 100).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const inputCls =
  'w-full min-h-[48px] rounded-[10px] border border-hair px-3.5 py-2.5 text-[13px] text-ink bg-white focus:outline-none focus:ring-2 focus:ring-brand';

export interface DraftLine {
  accountCode: string;
  direction: LedgerDirection;
  amount: string; // major units, converted to minor on submit
}

const emptyLine = (direction: LedgerDirection): DraftLine => ({
  accountCode: direction === 'DEBIT' ? '1100' : '4000',
  direction,
  amount: '',
});

type FilterKind = 'ALL' | 'NORMAL' | 'REVERSAL';

const LedgerView: React.FC = () => {
  const [items, setItems] = useState<LedgerTransaction[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filterKind, setFilterKind] = useState<FilterKind>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const [showPost, setShowPost] = useState(false);
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState<string | null>(null);
  const [txType, setTxType] = useState('MANUAL');
  const [currency, setCurrency] = useState('IDR');
  const [lines, setLines] = useState<DraftLine[]>([emptyLine('DEBIT'), emptyLine('CREDIT')]);

  const [reverseTarget, setReverseTarget] = useState<LedgerTransaction | null>(null);
  const [reverseReason, setReverseReason] = useState('');
  const [reversing, setReversing] = useState(false);
  const [reverseError, setReverseError] = useState<string | null>(null);

  const load = useCallback(async (cursor?: string) => {
    setLoading(true);
    setError(null);
    const res = await getLedgerEntries(50, cursor);
    if (res.ok && res.data) {
      setItems(prev => (cursor ? [...prev, ...res.data!.items] : res.data!.items));
      setNextCursor(res.data.nextCursor);
    } else {
      setError(res.error ?? 'Gagal memuat buku besar.');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // ── Metrics Calculation ───────────────────────────────────────────────────
  const metrics = useMemo(() => {
    let totalDebitMinor = 0;
    let totalCreditMinor = 0;
    let reversalCount = 0;

    for (const tx of items) {
      if (tx.reversalOf) reversalCount++;
      for (const e of tx.entries) {
        if (e.direction === 'DEBIT') totalDebitMinor += e.amountMinor;
        else totalCreditMinor += e.amountMinor;
      }
    }

    const isSystemBalanced = totalDebitMinor === totalCreditMinor;
    return {
      txCount: items.length,
      reversalCount,
      totalDebitMinor,
      totalCreditMinor,
      isSystemBalanced,
    };
  }, [items]);

  // ── Filtered items ────────────────────────────────────────────────────────
  const filteredItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return items.filter(tx => {
      if (filterKind === 'NORMAL' && tx.reversalOf) return false;
      if (filterKind === 'REVERSAL' && !tx.reversalOf) return false;
      if (!q) return true;
      if (tx.id.toLowerCase().includes(q)) return true;
      if (tx.reversalOf && tx.reversalOf.toLowerCase().includes(q)) return true;
      return tx.entries.some(
        e =>
          e.accountCode.includes(q) ||
          accountLabel(e.accountCode).toLowerCase().includes(q) ||
          e.direction.toLowerCase().includes(q)
      );
    });
  }, [items, filterKind, searchQuery]);

  // ── Draft totals ──────────────────────────────────────────────────────────
  const draftEntries: LedgerEntry[] = lines.map(l => ({
    accountCode: l.accountCode,
    direction: l.direction,
    amountMinor: Math.round((Number(l.amount) || 0) * 100),
  }));
  const totalDebit = sumMinor(draftEntries, 'DEBIT');
  const totalCredit = sumMinor(draftEntries, 'CREDIT');
  const balanced = totalDebit > 0 && totalDebit === totalCredit;

  const updateLine = (idx: number, patch: Partial<DraftLine>) =>
    setLines(prev => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));

  const applyTemplate = (name: 'PAYROLL' | 'OVERHEAD' | 'PAYMENT' | 'SALES') => {
    if (name === 'PAYROLL') {
      setTxType('PAYROLL_RUN');
      setLines([
        { accountCode: '5000', direction: 'DEBIT', amount: '1000000' },
        { accountCode: '2100', direction: 'CREDIT', amount: '1000000' },
      ]);
    } else if (name === 'PAYMENT') {
      setTxType('PAYROLL_PAYMENT');
      setLines([
        { accountCode: '2100', direction: 'DEBIT', amount: '1000000' },
        { accountCode: '1100', direction: 'CREDIT', amount: '1000000' },
      ]);
    } else if (name === 'OVERHEAD') {
      setTxType('OVERHEAD_EXPENSE');
      setLines([
        { accountCode: '5100', direction: 'DEBIT', amount: '500000' },
        { accountCode: '1100', direction: 'CREDIT', amount: '500000' },
      ]);
    } else {
      setTxType('SALES_MAKLON');
      setLines([
        { accountCode: '1100', direction: 'DEBIT', amount: '2500000' },
        { accountCode: '4000', direction: 'CREDIT', amount: '2500000' },
      ]);
    }
  };

  const resetPost = () => {
    setTxType('MANUAL');
    setCurrency('IDR');
    setLines([emptyLine('DEBIT'), emptyLine('CREDIT')]);
    setPostError(null);
  };

  const submitPost = async () => {
    setPosting(true);
    setPostError(null);
    const res = await appendLedgerTransaction({
      transactionType: txType.trim() || 'MANUAL',
      currency,
      entries: draftEntries,
    });
    setPosting(false);
    if (!res.ok) {
      setPostError(res.error ?? 'Gagal menyimpan transaksi.');
      return;
    }
    setShowPost(false);
    resetPost();
    await load();
  };

  const submitReverse = async () => {
    if (!reverseTarget) return;
    setReversing(true);
    setReverseError(null);
    const res = await reverseLedgerTransaction(reverseTarget.id, reverseReason);
    setReversing(false);
    if (!res.ok) {
      setReverseError(res.error ?? 'Gagal membuat reversal.');
      return;
    }
    setReverseTarget(null);
    setReverseReason('');
    await load();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-ink">Buku Besar (Ledger)</h2>
          <p className="text-ink-muted text-sm mt-1">
            Double-entry immutable — setiap transaksi harus balance, koreksi hanya melalui reversal
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => load()}
            className="btn-secondary min-h-[48px] px-4 rounded-[10px] inline-flex items-center gap-2"
          >
            <LucideIcon name="activity" className="w-4 h-4" /> Refresh
          </button>
          <button
            onClick={() => {
              resetPost();
              setShowPost(true);
            }}
            className="btn-primary min-h-[48px] px-5 rounded-[10px] inline-flex items-center gap-2"
          >
            <LucideIcon name="plus" className="w-4 h-4" /> Post Transaksi
          </button>
        </div>
      </div>

      {isMockLedger && (
        <MockModeBanner
          detail="data disimpan di memori dan hilang saat halaman di-reload."
          hint="untuk memakai service ledger asli."
        />
      )}

      {error && (
        <div className="rounded-[14px] border border-bad-bg-2 bg-bad-bg px-4 py-3 text-[13px] text-bad-4">
          {error}
        </div>
      )}

      {/* KPI Cards / Metrics Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-hair rounded-[18px] p-5 shadow-sm">
          <p className="text-xs text-ink-muted uppercase tracking-wider mb-1 font-semibold">Total Transaksi</p>
          <p className="text-[26px] font-bold text-ink">{metrics.txCount}</p>
          <p className="text-[12px] text-ink-muted mt-1">{metrics.reversalCount} transaksi reversal</p>
        </div>
        <div className="bg-white border border-hair rounded-[18px] p-5 shadow-sm">
          <p className="text-xs text-ink-muted uppercase tracking-wider mb-1 font-semibold">Akumulasi Debit</p>
          <p className="text-[20px] font-bold text-ink font-mono">Rp {fmtMoney(metrics.totalDebitMinor)}</p>
          <p className="text-[12px] text-ink-muted mt-1">Total debit masuk</p>
        </div>
        <div className="bg-white border border-hair rounded-[18px] p-5 shadow-sm">
          <p className="text-xs text-ink-muted uppercase tracking-wider mb-1 font-semibold">Akumulasi Kredit</p>
          <p className="text-[20px] font-bold text-ink font-mono">Rp {fmtMoney(metrics.totalCreditMinor)}</p>
          <p className="text-[12px] text-ink-muted mt-1">Total kredit keluar</p>
        </div>
        <div className="bg-white border border-hair rounded-[18px] p-5 shadow-sm">
          <p className="text-xs text-ink-muted uppercase tracking-wider mb-1 font-semibold">Integritas Ledger</p>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`pill rounded-full px-2.5 py-1 text-[12px] font-semibold ${
                metrics.isSystemBalanced ? 'bg-ok-bg text-ok-2' : 'bg-bad-bg text-bad-4'
              }`}
            >
              {metrics.isSystemBalanced ? '✓ 100% Balanced' : '⚠ Tidak Seimbang'}
            </span>
          </div>
          <p className="text-[12px] text-ink-muted mt-1.5">Sesuai standar double-entry</p>
        </div>
      </div>

      {/* Transactions Section */}
      <section className="bg-white border border-hair rounded-[18px] overflow-hidden shadow-sm">
        <div className="p-5 border-b border-panel-2 flex flex-wrap justify-between items-center gap-3">
          <div>
            <h3 className="text-[16px] font-bold text-ink">Jurnal Transaksi Keuangan</h3>
            <p className="text-[12px] font-medium text-ink-muted mt-0.5">
              Menampilkan {filteredItems.length} dari {items.length} transaksi
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Filter buttons with touch target >= 48px */}
            <div className="inline-flex rounded-[12px] bg-panel-2 p-1">
              {(
                [
                  { id: 'ALL', label: 'Semua' },
                  { id: 'NORMAL', label: 'Normal' },
                  { id: 'REVERSAL', label: 'Reversal' },
                ] as const
              ).map(f => (
                <button
                  key={f.id}
                  onClick={() => setFilterKind(f.id)}
                  className={`min-h-[48px] rounded-[9px] px-3.5 text-[12px] font-semibold transition-all ${
                    filterKind === f.id ? 'bg-white text-ink shadow-sm' : 'text-ink-muted'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <input
              type="text"
              placeholder="Cari ID transaksi atau akun..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="min-h-[48px] rounded-[10px] border border-hair px-3.5 text-[13px] text-ink bg-white focus:outline-none focus:ring-2 focus:ring-brand w-56 sm:w-64"
            />
          </div>
        </div>

        {loading && items.length === 0 ? (
          <p className="px-5 py-10 text-[13px] text-ink-muted text-center">Memuat transaksi…</p>
        ) : filteredItems.length === 0 ? (
          <p className="px-5 py-10 text-[13px] text-ink-muted text-center">Tidak ada transaksi ditemukan.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead>
                <tr className="border-b border-panel-2 bg-panel">
                  {['ID Transaksi', 'Tipe & Sifat', 'Baris Jurnal (Debit / Kredit)', 'Aksi'].map(h => (
                    <th key={h} className="px-4 py-3.5 font-semibold text-ink whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-panel-2">
                {filteredItems.map(tx => (
                  <tr key={tx.id} className="hover:bg-panel transition-colors">
                    <td className="px-4 py-3.5 whitespace-nowrap align-top">
                      <div className="font-mono text-xs font-semibold text-ink">{tx.id.slice(0, 8)}</div>
                      <div className="text-[11px] text-ink-muted font-mono">{tx.id.slice(8, 20)}...</div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap align-top">
                      {tx.reversalOf ? (
                        <span className="pill rounded-full px-2.5 py-1 text-[11px] font-semibold bg-warn-bg text-warn-2 inline-flex items-center gap-1">
                          <LucideIcon name="corner-up-left" className="w-3 h-3" />
                          Reversal · {tx.reversalOf.slice(0, 8)}
                        </span>
                      ) : (
                        <span className="pill rounded-full px-2.5 py-1 text-[11px] font-semibold bg-brand-bg text-brand">
                          Normal
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 align-top">
                      <div className="space-y-1.5">
                        {tx.entries.map((e, i) => (
                          <div key={i} className="flex items-center gap-3 whitespace-nowrap text-[12px]">
                            <span
                              className={`w-[60px] font-bold text-[11px] uppercase tracking-wider ${
                                e.direction === 'DEBIT' ? 'text-brand' : 'text-warn-2'
                              }`}
                            >
                              {e.direction}
                            </span>
                            <span className="text-ink-2 font-medium">{accountLabel(e.accountCode)}</span>
                            <span className="font-mono font-semibold text-ink">Rp {fmtMoney(e.amountMinor)}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap align-top">
                      {!tx.reversalOf && (
                        <button
                          onClick={() => {
                            setReverseTarget(tx);
                            setReverseReason('');
                            setReverseError(null);
                          }}
                          className="btn-secondary min-h-[48px] px-4 rounded-[10px] text-xs font-semibold inline-flex items-center gap-1.5 text-warn-2 border-warn"
                        >
                          <LucideIcon name="corner-up-left" className="w-3.5 h-3.5" />
                          Reverse
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {nextCursor && (
          <div className="p-4 border-t border-panel-2 text-center">
            <button
              onClick={() => load(nextCursor)}
              disabled={loading}
              className="btn-secondary min-h-[48px] px-6 rounded-[10px]"
            >
              {loading ? 'Memuat…' : 'Muat lebih banyak'}
            </button>
          </div>
        )}
      </section>

      {/* ── Post Transaction Modal ─────────────────────────────────────────── */}
      <Modal
        isOpen={showPost}
        title="Post Transaksi Jurnal Baru"
        onClose={() => setShowPost(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShowPost(false)}
              className="btn-secondary min-h-[48px] px-5 rounded-[10px]"
            >
              Batal
            </button>
            <button
              onClick={submitPost}
              disabled={!balanced || posting}
              className="btn-primary min-h-[48px] px-6 rounded-[10px]"
            >
              {posting ? 'Menyimpan…' : 'Post Transaksi'}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          {/* Quick template buttons */}
          <div>
            <label className="block text-xs font-semibold text-ink-muted uppercase tracking-wider mb-2">
              Template Transaksi Cepat
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => applyTemplate('PAYROLL')}
                className="min-h-[48px] px-3.5 text-xs font-semibold rounded-[10px] border border-hair bg-panel hover:bg-panel-2 text-ink"
              >
                Upah Borongan
              </button>
              <button
                type="button"
                onClick={() => applyTemplate('PAYMENT')}
                className="min-h-[48px] px-3.5 text-xs font-semibold rounded-[10px] border border-hair bg-panel hover:bg-panel-2 text-ink"
              >
                Bayar Kas Gaji
              </button>
              <button
                type="button"
                onClick={() => applyTemplate('OVERHEAD')}
                className="min-h-[48px] px-3.5 text-xs font-semibold rounded-[10px] border border-hair bg-panel hover:bg-panel-2 text-ink"
              >
                Overhead Pabrik
              </button>
              <button
                type="button"
                onClick={() => applyTemplate('SALES')}
                className="min-h-[48px] px-3.5 text-xs font-semibold rounded-[10px] border border-hair bg-panel hover:bg-panel-2 text-ink"
              >
                Penjualan Maklon
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="ledger-type" className="block text-sm font-medium text-ink mb-1">
                Tipe Transaksi
              </label>
              <input
                id="ledger-type"
                value={txType}
                onChange={e => setTxType(e.target.value)}
                className={inputCls}
                placeholder="MANUAL / PAYROLL_RUN"
              />
            </div>
            <div>
              <label htmlFor="ledger-currency" className="block text-sm font-medium text-ink mb-1">
                Mata Uang
              </label>
              <select
                id="ledger-currency"
                value={currency}
                onChange={e => setCurrency(e.target.value)}
                className={inputCls}
              >
                <option value="IDR">IDR (Rupiah)</option>
                <option value="USD">USD (US Dollar)</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-ink">Baris Jurnal Akuntansi</span>
              <button
                type="button"
                onClick={() =>
                  setLines(prev => [...prev, emptyLine(prev.length % 2 === 0 ? 'DEBIT' : 'CREDIT')])
                }
                className="btn-ghost min-h-[48px] px-3 text-xs font-semibold text-brand inline-flex items-center gap-1"
              >
                <LucideIcon name="plus" className="w-3.5 h-3.5" />
                Tambah baris
              </button>
            </div>

            <div className="space-y-2.5">
              {lines.map((line, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <select
                    value={line.accountCode}
                    onChange={e => updateLine(idx, { accountCode: e.target.value })}
                    aria-label={`Akun baris ${idx + 1}`}
                    className={inputCls + ' flex-1'}
                  >
                    {LEDGER_ACCOUNTS.map(a => (
                      <option key={a.code} value={a.code}>
                        {a.code} · {a.name}
                      </option>
                    ))}
                  </select>
                  <select
                    value={line.direction}
                    onChange={e => updateLine(idx, { direction: e.target.value as LedgerDirection })}
                    aria-label={`Arah baris ${idx + 1}`}
                    className={inputCls + ' w-[120px] font-semibold'}
                  >
                    <option value="DEBIT">DEBIT</option>
                    <option value="CREDIT">CREDIT</option>
                  </select>
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    placeholder="0.00"
                    value={line.amount}
                    onChange={e => updateLine(idx, { amount: e.target.value })}
                    aria-label={`Nominal baris ${idx + 1}`}
                    className={inputCls + ' w-[140px] font-mono text-right'}
                  />
                  <button
                    type="button"
                    onClick={() => setLines(prev => prev.filter((_, i) => i !== idx))}
                    disabled={lines.length <= 2}
                    aria-label="Hapus baris"
                    className="min-h-[48px] min-w-[48px] rounded-[10px] border border-hair text-bad-4 hover:bg-bad-bg flex items-center justify-center disabled:opacity-30 transition-all"
                  >
                    <LucideIcon name="x" className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Balance summary */}
          <div
            className={`rounded-[14px] px-4 py-3.5 text-[13px] flex justify-between items-center ${
              balanced ? 'bg-ok-bg text-ok-2 border border-ok' : 'bg-warn-bg text-warn-2 border border-warn'
            }`}
          >
            <span>
              Total Debit: <strong className="font-mono text-[14px]">Rp {fmtMoney(totalDebit)}</strong>
            </span>
            <span>
              Total Kredit: <strong className="font-mono text-[14px]">Rp {fmtMoney(totalCredit)}</strong>
            </span>
            <span className="font-bold flex items-center gap-1">
              {balanced ? '✓ Seimbang (Balanced)' : '⚠ Tidak Seimbang'}
            </span>
          </div>

          {postError && <p className="text-[13px] text-bad-4 font-medium">{postError}</p>}
        </div>
      </Modal>

      {/* ── Reverse Modal ──────────────────────────────────────────────────── */}
      <Modal
        isOpen={reverseTarget !== null}
        title="Reversal Transaksi Ledger"
        onClose={() => setReverseTarget(null)}
        footer={
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setReverseTarget(null)}
              className="btn-secondary min-h-[48px] px-5 rounded-[10px]"
            >
              Batal
            </button>
            <button
              onClick={submitReverse}
              disabled={!reverseReason.trim() || reversing}
              className="btn-danger min-h-[48px] px-6 rounded-[10px]"
            >
              {reversing ? 'Memproses…' : 'Konfirmasi Reversal'}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="rounded-[14px] bg-warn-bg border border-warn p-4 text-[13px] text-warn-2 leading-relaxed">
            <p className="font-semibold mb-1">Prinsip Immutability Buku Besar:</p>
            Buku besar bersifat double-entry permanen. Transaksi tidak pernah dihapus atau diedit.
            Reversal akan menciptakan transaksi kompensasi baru yang membalik seluruh DEBIT menjadi KREDIT dan
            sebaliknya untuk membatalkan transaksi{' '}
            <code className="font-mono font-bold">{reverseTarget?.id.slice(0, 8)}</code>.
          </div>

          {reverseTarget && (
            <div className="rounded-[12px] border border-hair p-3 bg-panel space-y-1.5 text-xs">
              <p className="font-semibold text-ink">Entri yang akan dibalik:</p>
              {reverseTarget.entries.map((e, idx) => (
                <div key={idx} className="flex justify-between font-mono text-ink-muted">
                  <span>
                    {e.direction === 'DEBIT' ? 'CREDIT' : 'DEBIT'} (kebalikan dari {e.direction})
                  </span>
                  <span>
                    {accountLabel(e.accountCode)} · Rp {fmtMoney(e.amountMinor)}
                  </span>
                </div>
              ))}
            </div>
          )}

          <div>
            <label htmlFor="ledger-reason" className="block text-sm font-medium text-ink mb-1">
              Alasan Reversal (Wajib)
            </label>
            <textarea
              id="ledger-reason"
              rows={3}
              placeholder="Contoh: Koreksi entri ganda atau pembatalan verifikasi QC..."
              value={reverseReason}
              onChange={e => setReverseReason(e.target.value)}
              className="w-full rounded-[10px] border border-hair p-3 text-[13px] text-ink bg-white focus:outline-none focus:ring-2 focus:ring-brand"
            />
          </div>
          {reverseError && <p className="text-[13px] text-bad-4 font-medium">{reverseError}</p>}
        </div>
      </Modal>
    </div>
  );
};

export default LedgerView;
