/**
 * OrderTrackView — track the signed-in client's own production orders.
 * A row opens a read-only detail modal with the phase timeline.
 */

import React, { useCallback, useEffect, useState } from 'react';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import { getToken } from '../services/authSession';
import * as portalApi from '../services/portalApi';
import { toast } from '../services/toast';
import type { Order } from '../types/portal';
import { matchesQuery } from '../utils/filter';

interface OrderTrackViewProps {
  globalSearch: string;
}

const OrderTrackView: React.FC<OrderTrackViewProps> = ({ globalSearch }) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Order | null>(null);

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    const res = await portalApi.listOrders(token);
    setLoading(false);
    if (res.success && res.data) setOrders(res.data);
    else toast.error(res.error ?? 'Gagal memuat pesanan.');
  }, []);

  useEffect(() => { void load(); }, [load]);

  const filtered = orders.filter(
    (o) =>
      (tab === 'all' || o.status === tab) &&
      matchesQuery(search, o.article_name, o.order_id, o.scheme) &&
      matchesQuery(globalSearch, o.article_name, o.order_id, o.scheme),
  );

  return (
    <div className="space-y-6">
      <div className="surface p-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-[20px] font-semibold" style={{ color: 'var(--c-ink)' }}>Lacak Pesanan</h2>
            <p className="text-[13px] mt-1" style={{ color: 'var(--c-ink-muted)' }}>
              Status dan progres real-time pesanan produksi Anda.
            </p>
          </div>
          <button type="button" onClick={() => void load()} className="btn-secondary">Muat ulang</button>
        </div>
      </div>

      {loading ? (
        <div className="surface p-8 space-y-3">
          {[0, 1, 2].map((i) => <div key={i} className="skeleton h-10 w-full" />)}
        </div>
      ) : (
        <DataTable<Order>
          title="Daftar Pesanan"
          subtitle={`${filtered.length} pesanan`}
          tabs={[
            { id: 'all', label: 'Semua' },
            { id: 'confirmed', label: 'Dikonfirmasi' },
            { id: 'cutting', label: 'Cutting' },
            { id: 'sewing', label: 'Produksi' },
            { id: 'qc', label: 'QC' },
            { id: 'completed', label: 'Selesai' },
          ]}
          activeTab={tab}
          onTabChange={setTab}
          searchValue={search}
          onSearchChange={setSearch}
          columns={[
            { key: 'order_id', label: 'ID Order', render: (v) => <code>{String(v)}</code> },
            { key: 'article_name', label: 'Artikel' },
            { key: 'scheme', label: 'Skema' },
            { key: 'quantity', label: 'Qty' },
            { key: 'target_date', label: 'Target' },
            { key: 'progress', label: 'Progres', render: (v) => `${Number(v)}%` },
            { key: 'status', label: 'Status', render: (v) => <StatusBadge status={String(v)} /> },
            {
              key: 'order_id',
              label: 'Aksi',
              render: (_v, row) => (
                <button type="button" className="btn-pill btn-pill-blue" onClick={() => setSelected(row)}>
                  Detail
                </button>
              ),
            },
          ]}
          data={filtered}
          emptyMessage="Belum ada pesanan untuk filter ini."
        />
      )}

      <Modal
        isOpen={selected !== null}
        title={selected ? `Detail ${selected.order_id}` : 'Detail Order'}
        onClose={() => setSelected(null)}
      >
        {selected && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <Info label="Artikel" value={selected.article_name} />
              <Info label="Skema Maklon" value={selected.scheme} />
              <Info label="Jumlah" value={String(selected.quantity)} />
              <Info label="Target Selesai" value={selected.target_date || '—'} />
              <Info label="Tahap Sekarang" value={selected.current_phase} />
              <div>
                <p className="text-[12px] font-semibold uppercase tracking-wide" style={{ color: 'var(--c-ink-muted)' }}>Status</p>
                <div className="mt-1"><StatusBadge status={selected.status} /></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-[12px] font-semibold uppercase tracking-wide" style={{ color: 'var(--c-ink-muted)' }}>Progres</p>
                <span className="text-[13px] font-semibold" style={{ color: 'var(--c-ink)' }}>{selected.progress}%</span>
              </div>
              <div className="mini-line"><span style={{ width: `${selected.progress}%` }} /></div>
            </div>

            <div>
              <p className="text-[12px] font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--c-ink-muted)' }}>Riwayat Tahap</p>
              <ol className="space-y-3">
                {selected.timeline.map((step, i) => (
                  <li key={`${step.phase}-${i}`} className="flex items-start gap-3">
                    <span
                      className="mt-1 w-2.5 h-2.5 rounded-full shrink-0"
                      style={{
                        background:
                          step.status === 'done'
                            ? 'var(--c-ok)'
                            : step.status === 'active'
                              ? 'var(--c-brand)'
                              : 'var(--c-hair-4)',
                      }}
                      aria-hidden="true"
                    />
                    <div>
                      <p className="text-[13px] font-semibold" style={{ color: 'var(--c-ink)' }}>{step.phase}</p>
                      <p className="text-[12px]" style={{ color: 'var(--c-ink-muted)' }}>
                        {step.status === 'active' ? 'Sedang berjalan' : step.status === 'done' ? 'Selesai' : 'Menunggu'}
                        {step.at ? ` · ${step.at}` : ''}
                      </p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

const Info: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <p className="text-[12px] font-semibold uppercase tracking-wide" style={{ color: 'var(--c-ink-muted)' }}>{label}</p>
    <p className="text-[14px] font-semibold mt-0.5" style={{ color: 'var(--c-ink)' }}>{value}</p>
  </div>
);

export default OrderTrackView;
