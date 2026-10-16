/**
 * PortalDashboardView — KPI dashboard for the signed-in external client.
 * Every number comes from the client-scoped `/summary` and `/orders` endpoints.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import MetricCard from '../components/MetricCard';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import { getToken } from '../services/authSession';
import * as portalApi from '../services/portalApi';
import { toast } from '../services/toast';
import type { Order, PortalSummary } from '../types/portal';
import { matchesQuery } from '../utils/filter';

interface PortalDashboardViewProps {
  globalSearch: string;
}

const PortalDashboardView: React.FC<PortalDashboardViewProps> = ({ globalSearch }) => {
  const [summary, setSummary] = useState<PortalSummary | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    const [summaryRes, ordersRes] = await Promise.all([
      portalApi.getSummary(token),
      portalApi.listOrders(token),
    ]);
    setLoading(false);
    if (summaryRes.success && summaryRes.data) setSummary(summaryRes.data.summary);
    else toast.error(summaryRes.error ?? 'Gagal memuat ringkasan.');
    if (ordersRes.success && ordersRes.data) setOrders(ordersRes.data);
    else toast.error(ordersRes.error ?? 'Gagal memuat pesanan.');
  }, []);

  useEffect(() => { void load(); }, [load]);

  const filtered = useMemo(
    () =>
      orders.filter(
        (o) =>
          (tab === 'all' || o.status === tab) &&
          matchesQuery(search, o.article_name, o.order_id) &&
          matchesQuery(globalSearch, o.article_name, o.order_id),
      ),
    [orders, tab, search, globalSearch],
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard label="Order Aktif" value={summary?.active_orders ?? 0} note="Pesanan sedang berjalan" loading={loading} />
        <MetricCard label="Order Selesai" value={summary?.completed_orders ?? 0} note="Pesanan yang telah selesai" loading={loading} />
        <MetricCard label="Pengajuan Menunggu" value={summary?.pending_requests ?? 0} note="Menunggu peninjauan tim internal" loading={loading} />
        <MetricCard label="Lot Stok Titipan" value={summary?.consigned_lots ?? 0} note="Jenis bahan titipan Anda" loading={loading} />
      </div>

      <DataTable<Order>
        title="Pesanan Terbaru"
        subtitle="Progres produksi pesanan Anda"
        tabs={[
          { id: 'all', label: 'Semua' },
          { id: 'confirmed', label: 'Dikonfirmasi' },
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
          { key: 'quantity', label: 'Qty' },
          { key: 'current_phase', label: 'Tahap' },
          { key: 'progress', label: 'Progres', render: (v) => `${Number(v)}%` },
          { key: 'status', label: 'Status', render: (v) => <StatusBadge status={String(v)} /> },
        ]}
        data={filtered.slice(0, 8)}
        emptyMessage="Belum ada pesanan."
      />
    </div>
  );
};

export default PortalDashboardView;
