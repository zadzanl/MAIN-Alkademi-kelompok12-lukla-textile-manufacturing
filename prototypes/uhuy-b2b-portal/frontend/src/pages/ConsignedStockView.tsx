/**
 * ConsignedStockView — the signed-in client's own consigned (titipan) material.
 * Server-scoped to the client's client_id.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import DataTable from '../components/DataTable';
import { getToken } from '../services/authSession';
import * as portalApi from '../services/portalApi';
import { toast } from '../services/toast';
import type { StockLot } from '../types/portal';
import { matchesQuery } from '../utils/filter';

interface ConsignedStockViewProps {
  globalSearch: string;
}

const ConsignedStockView: React.FC<ConsignedStockViewProps> = ({ globalSearch }) => {
  const [lots, setLots] = useState<StockLot[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    const res = await portalApi.listStock(token);
    setLoading(false);
    if (res.success && res.data) setLots(res.data);
    else toast.error(res.error ?? 'Gagal memuat stok titipan.');
  }, []);

  useEffect(() => { void load(); }, [load]);

  const filtered = useMemo(
    () =>
      lots.filter(
        (l) =>
          matchesQuery(search, l.material_name, l.material_code) &&
          matchesQuery(globalSearch, l.material_name, l.material_code),
      ),
    [lots, search, globalSearch],
  );

  const total = filtered.reduce((sum, l) => sum + l.quantity_available, 0);

  return (
    <div className="space-y-4">
      <div className="surface p-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-[22px] font-semibold" style={{ color: 'var(--c-ink)' }}>Stok Bahan Titipan</h2>
            <p className="text-[15px] mt-1" style={{ color: 'var(--c-ink-muted)' }}>
              Bahan milik Anda yang tersimpan di gudang Lukla.
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
        <DataTable<StockLot>
          title="Daftar Lot Bahan"
          subtitle={`${filtered.length} lot · total ${total} unit tersedia`}
          tabs={[{ id: 'all', label: 'Semua' }]}
          activeTab="all"
          onTabChange={() => undefined}
          searchValue={search}
          onSearchChange={setSearch}
          columns={[
            { key: 'material_code', label: 'Kode', render: (v) => <code>{String(v)}</code> },
            { key: 'material_name', label: 'Bahan' },
            { key: 'quantity_available', label: 'Tersedia' },
            { key: 'unit', label: 'Satuan' },
            { key: 'received_at', label: 'Diterima' },
          ]}
          data={filtered}
          emptyMessage="Belum ada bahan titipan tercatat."
        />
      )}
    </div>
  );
};

export default ConsignedStockView;
