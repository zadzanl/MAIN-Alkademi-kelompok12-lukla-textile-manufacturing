/**
 * RequestsView — the signed-in client's own request history (orders + samples).
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import { getToken } from '../services/authSession';
import * as portalApi from '../services/portalApi';
import { toast } from '../services/toast';
import type { PortalRequest } from '../types/portal';
import { matchesQuery } from '../utils/filter';

interface RequestsViewProps {
  globalSearch: string;
}

const KIND_LABEL: Record<string, string> = { order: 'Order', sample: 'Sample' };

const RequestsView: React.FC<RequestsViewProps> = ({ globalSearch }) => {
  const [requests, setRequests] = useState<PortalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<PortalRequest | null>(null);

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    const res = await portalApi.listRequests(token);
    setLoading(false);
    if (res.success && res.data) setRequests(res.data);
    else toast.error(res.error ?? 'Gagal memuat pengajuan.');
  }, []);

  useEffect(() => { void load(); }, [load]);

  const filtered = useMemo(
    () =>
      requests.filter(
        (r) =>
          (tab === 'all' || r.kind === tab) &&
          matchesQuery(search, r.article_name, r.scheme) &&
          matchesQuery(globalSearch, r.article_name, r.scheme),
      ),
    [requests, tab, search, globalSearch],
  );

  return (
    <div className="space-y-4">
      <div className="surface p-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-[22px] font-semibold" style={{ color: 'var(--c-ink)' }}>Pengajuan Saya</h2>
            <p className="text-[15px] mt-1" style={{ color: 'var(--c-ink-muted)' }}>
              Riwayat pengajuan order dan permintaan sample Anda.
            </p>
          </div>
          <button type="button" onClick={() => void load()} className="btn-secondary">Muat ulang</button>
        </div>
      </div>

      {loading ? (
        <div className="surface p-4 space-y-3">
          {[0, 1, 2].map((i) => <div key={i} className="skeleton h-10 w-full" />)}
        </div>
      ) : (
        <DataTable<PortalRequest>
          title="Daftar Pengajuan"
          subtitle={`${filtered.length} pengajuan`}
          tabs={[
            { id: 'all', label: 'Semua' },
            { id: 'order', label: 'Order' },
            { id: 'sample', label: 'Sample' },
          ]}
          activeTab={tab}
          onTabChange={setTab}
          searchValue={search}
          onSearchChange={setSearch}
          columns={[
            { key: 'kind', label: 'Jenis', render: (v) => KIND_LABEL[String(v)] ?? String(v) },
            { key: 'article_name', label: 'Artikel' },
            { key: 'scheme', label: 'Skema' },
            { key: 'quantity', label: 'Qty' },
            { key: 'target_date', label: 'Target', render: (v) => String(v || '—') },
            { key: 'status', label: 'Status', render: (v) => <StatusBadge status={String(v)} /> },
            {
              key: 'request_id',
              label: 'Aksi',
              render: (_v, row) => (
                <button type="button" className="btn-pill btn-pill-blue" onClick={() => setSelected(row)}>
                  Detail
                </button>
              ),
            },
          ]}
          data={filtered}
          emptyMessage="Belum ada pengajuan."
        />
      )}

      <Modal
        isOpen={selected !== null}
        title="Detail Pengajuan"
        onClose={() => setSelected(null)}
      >
        {selected && (
          <div className="grid grid-cols-2 gap-3">
            <Info label="Jenis" value={KIND_LABEL[selected.kind] ?? selected.kind} />
            <Info label="Artikel" value={selected.article_name} />
            <Info label="Skema" value={selected.scheme} />
            <Info label="Jumlah" value={String(selected.quantity)} />
            <Info label="Target" value={selected.target_date || '—'} />
            <div>
              <p className="text-[14px] font-semibold uppercase tracking-wide" style={{ color: 'var(--c-ink-muted)' }}>Status</p>
              <div className="mt-1"><StatusBadge status={selected.status} /></div>
            </div>
            <div className="col-span-2">
              <p className="text-[14px] font-semibold uppercase tracking-wide" style={{ color: 'var(--c-ink-muted)' }}>Catatan</p>
              <p className="text-[15px] mt-1" style={{ color: 'var(--c-ink)' }}>{selected.notes || '—'}</p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

const Info: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <p className="text-[14px] font-semibold uppercase tracking-wide" style={{ color: 'var(--c-ink-muted)' }}>{label}</p>
    <p className="text-[15px] font-semibold mt-0.5" style={{ color: 'var(--c-ink)' }}>{value}</p>
  </div>
);

export default RequestsView;
