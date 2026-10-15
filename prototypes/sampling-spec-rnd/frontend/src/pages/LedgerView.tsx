/**
 * LedgerView — Immutable double-entry ledger (VIEW-06 finance surface).
 *
 * Reads, posts, and reverses balanced transactions through the ledger API
 * client. Backed by the in-memory mock by default (see services/ledgerApi.ts);
 * the UI never treats cached data as authoritative and only reflects what the
 * server/mock returns.
 */

import React, { useState, useEffect, useCallback } from 'react';
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

const ACCOUNTS = [
  { code: '1100', name: 'Kas' },
  { code: '1200', name: 'Piutang Usaha' },
  { code: '2100', name: 'Utang Usaha' },
  { code: '4000', name: 'Pendapatan Penjualan' },
  { code: '5000', name: 'Beban Gaji' },
  { code: '5100', name: 'Beban Bahan' },
];

const accountLabel = (code: string) => {
  const acc = ACCOUNTS.find(a => a.code === code);
  return acc ? `${acc.code} · ${acc.name}` : code;
};

const fmtMoney = (minor: number) =>
  (minor / 100).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const inputCls = 'w-full rounded-[10px] px-3 py-2.5 text-[13px]';

interface DraftLine {
  accountCode: string;
  direction: LedgerDirection;
  amount: string; // major units, converted to minor on submit
}

const emptyLine = (direction: LedgerDirection): DraftLine => ({
  accountCode: direction === 'DEBIT' ? '1100' : '4000',
  direction,
  amount: '',
});

const LedgerView: React.FC = () => {
  const [items, setItems] = useState<LedgerTransaction[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => { load(); }, [load]);

  // ── draft totals ──────────────────────────────────────────────────────────
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
    if (!res.ok) { setPostError(res.error ?? 'Gagal menyimpan transaksi.'); return; }
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
    if (!res.ok) { setReverseError(res.error ?? 'Gagal membuat reversal.'); return; }
    setReverseTarget(null);
    setReverseReason('');
    await load();
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Buku Besar (Ledger)</h2>
          <p className="text-[#6e6e73] text-sm mt-1">
            Double-entry immutable — setiap transaksi harus balance, koreksi hanya lewat reversal
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => load()} className="btn-secondary">
            <LucideIcon name="activity" className="w-4 h-4" /> Refresh
          </button>
          <button onClick={() => { resetPost(); setShowPost(true); }} className="btn-primary inline-flex items-center gap-2">
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
        <div className="rounded-[14px] border border-[#fecaca] bg-[#fee2e2] px-4 py-3 text-[13px] text-[#dc2626]">
          {error}
        </div>
      )}

      {/* Transactions */}
      <section className="bg-white border border-[#e2e8f0] rounded-[18px] overflow-hidden">
        <div className="p-5 border-b border-[#f1f5f9]">
          <h3 className="text-[16px] font-bold text-[#0f172a]">Transaksi Terbaru</h3>
          <p className="text-[12px] font-medium text-[#64748b] mt-0.5">
            {items.length} transaksi dimuat
          </p>
        </div>

        {loading && items.length === 0 ? (
          <p className="px-5 py-10 text-[13px] text-[#64748b] text-center">Memuat…</p>
        ) : items.length === 0 ? (
          <p className="px-5 py-10 text-[13px] text-[#64748b] text-center">Belum ada transaksi.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead>
                <tr>
                  {['ID', 'Tipe', 'Baris (Debit / Kredit)', 'Aksi'].map(h => (
                    <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map(tx => (
                  <tr key={tx.id}>
                    <td className="px-4 py-3 whitespace-nowrap align-top">
                      <code className="text-xs text-[#64748b]">{tx.id.slice(0, 8)}</code>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap align-top">
                      {tx.reversalOf ? (
                        <span className="pill rounded-full px-2 py-0.5 text-[11px] font-semibold bg-[#fff4e6] text-[#b86800]">
                          Reversal · {tx.reversalOf.slice(0, 8)}
                        </span>
                      ) : (
                        <span className="pill rounded-full px-2 py-0.5 text-[11px] font-semibold bg-[#e8f2ff] text-[#0066cc]">
                          Normal
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 align-top">
                      <div className="space-y-1">
                        {tx.entries.map((e, i) => (
                          <div key={i} className="flex items-center gap-2 whitespace-nowrap">
                            <span className={`w-[58px] font-semibold text-[11px] ${
                              e.direction === 'DEBIT' ? 'text-[#0066cc]' : 'text-[#b86800]'
                            }`}>{e.direction}</span>
                            <span className="text-[#334155]">{accountLabel(e.accountCode)}</span>
                            <span className="font-mono text-[#1d1d1f]">{fmtMoney(e.amountMinor)}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap align-top">
                      <button
                        onClick={() => { setReverseTarget(tx); setReverseReason(''); setReverseError(null); }}
                        className="btn-secondary !py-1.5 !px-3 !text-xs"
                      >
                        Reverse
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {nextCursor && (
          <div className="p-4 border-t border-[#f1f5f9] text-center">
            <button onClick={() => load(nextCursor)} disabled={loading} className="btn-secondary">
              {loading ? 'Memuat…' : 'Muat lebih banyak'}
            </button>
          </div>
        )}
      </section>

      {/* ── Post transaction modal ─────────────────────────────────────────── */}
      <Modal
        isOpen={showPost}
        title="Post Transaksi Baru"
        onClose={() => setShowPost(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowPost(false)} className="btn-secondary">Batal</button>
            <button onClick={submitPost} disabled={!balanced || posting} className="btn-primary">
              {posting ? 'Menyimpan…' : 'Post'}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="ledger-type" className="block text-sm font-medium text-[#1d1d1f] mb-1">Tipe Transaksi</label>
              <input id="ledger-type" value={txType} onChange={e => setTxType(e.target.value)} className={inputCls} />
            </div>
            <div>
              <label htmlFor="ledger-currency" className="block text-sm font-medium text-[#1d1d1f] mb-1">Mata Uang</label>
              <select id="ledger-currency" value={currency} onChange={e => setCurrency(e.target.value)} className={inputCls}>
                <option value="IDR">IDR</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-[#1d1d1f]">Baris Jurnal</span>
              <button
                onClick={() => setLines(prev => [...prev, emptyLine(prev.length % 2 === 0 ? 'DEBIT' : 'CREDIT')])}
                className="btn-ghost !py-1 !px-2 !text-xs"
              >
                + Tambah baris
              </button>
            </div>

            <div className="space-y-2">
              {lines.map((line, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <select
                    value={line.accountCode}
                    onChange={e => updateLine(idx, { accountCode: e.target.value })}
                    aria-label={`Akun baris ${idx + 1}`}
                    className={inputCls + ' flex-1'}
                  >
                    {ACCOUNTS.map(a => <option key={a.code} value={a.code}>{a.code} · {a.name}</option>)}
                  </select>
                  <select
                    value={line.direction}
                    onChange={e => updateLine(idx, { direction: e.target.value as LedgerDirection })}
                    aria-label={`Arah baris ${idx + 1}`}
                    className={inputCls + ' w-[110px]'}
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
                    className={inputCls + ' w-[130px]'}
                  />
                  <button
                    onClick={() => setLines(prev => prev.filter((_, i) => i !== idx))}
                    disabled={lines.length <= 2}
                    aria-label="Hapus baris"
                    className="btn-ghost !p-2 disabled:opacity-30"
                  >
                    <LucideIcon name="x" className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Balance summary */}
          <div className={`rounded-[12px] px-4 py-3 text-[13px] flex justify-between ${
            balanced ? 'bg-[#f0fbf4] text-[#1a7a34]' : 'bg-[#fff4e6] text-[#b86800]'
          }`}>
            <span>Debit: <strong className="font-mono">{fmtMoney(totalDebit)}</strong></span>
            <span>Kredit: <strong className="font-mono">{fmtMoney(totalCredit)}</strong></span>
            <span className="font-semibold">{balanced ? '✓ Balance' : '⚠ Tidak balance'}</span>
          </div>

          {postError && <p className="text-[13px] text-[#dc2626]">{postError}</p>}
        </div>
      </Modal>

      {/* ── Reverse modal ──────────────────────────────────────────────────── */}
      <Modal
        isOpen={reverseTarget !== null}
        title="Reversal Transaksi"
        onClose={() => setReverseTarget(null)}
        footer={
          <div className="flex gap-3 justify-end">
            <button onClick={() => setReverseTarget(null)} className="btn-secondary">Batal</button>
            <button onClick={submitReverse} disabled={!reverseReason.trim() || reversing} className="btn-primary">
              {reversing ? 'Memproses…' : 'Buat Reversal'}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <p className="text-[13px] text-[#334155]">
            Ledger bersifat immutable. Reversal membuat transaksi kompensasi baru untuk
            membatalkan <code className="font-mono">{reverseTarget?.id.slice(0, 8)}</code>; data asli tidak diubah.
          </p>
          <div>
            <label htmlFor="ledger-reason" className="block text-sm font-medium text-[#1d1d1f] mb-1">Alasan</label>
            <textarea
              id="ledger-reason"
              rows={3}
              value={reverseReason}
              onChange={e => setReverseReason(e.target.value)}
              className={inputCls}
            />
          </div>
          {reverseError && <p className="text-[13px] text-[#dc2626]">{reverseError}</p>}
        </div>
      </Modal>
    </div>
  );
};

export default LedgerView;
