/**
 * WarehouseInventoryView — View 03: Multi-Client Warehouse Inventory Grid.
 *
 * Contract & Specification:
 * - Matching prototypes/design-mocks/lukla-ui-mock.html (view-03).
 * - Multi-client inventory grid with client filtering and lot tag search.
 * - Table columns: Item, Owner, Allocated, Balance, Action (Dispatch).
 * - FR-6.2 Cross-Client Ownership Guardrail: Hard rejection if stock owner != order client.
 * - Apple Design System tokens with >= 48px touch targets and zero type evasion.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LucideIcon } from '../components/Sidebar';
import {
  listInventoryLots,
  executeDispatch,
  DEFAULT_PRODUCTION_ORDERS,
  type InventoryLot,
  type ProductionOrder,
  type DispatchValidationResult,
} from '../services/warehouseApi';
import { toast } from '../services/toast';

interface GuardrailAlertState {
  isOpen: boolean;
  lot: InventoryLot | null;
  targetOrder: ProductionOrder | null;
  validation: DispatchValidationResult | null;
}

interface DispatchDialogState {
  isOpen: boolean;
  lot: InventoryLot | null;
  targetOrderId: string;
  quantity: number;
}

const CLIENT_OPTIONS = ['All', 'Snøhund', 'Brand-X', 'AlpineGear'] as const;

export const WarehouseInventoryView: React.FC = () => {
  const [clientFilter, setClientFilter] = useState<string>('All');
  const [lotSearch, setLotSearch] = useState<string>('');
  const [lots, setLots] = useState<InventoryLot[]>([]);
  const [collisions, setCollisions] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Dispatch interactive dialog
  const [dispatchDialog, setDispatchDialog] = useState<DispatchDialogState>({
    isOpen: false,
    lot: null,
    targetOrderId: 'ORD-401',
    quantity: 50,
  });

  // FR-6.2 Guardrail Alert Modal
  const [guardrailAlert, setGuardrailAlert] = useState<GuardrailAlertState>({
    isOpen: false,
    lot: null,
    targetOrder: null,
    validation: null,
  });

  // Recent audit log for dispatches and blocked attempts
  const [auditLogs, setAuditLogs] = useState<Array<{
    id: string;
    timestamp: string;
    type: 'DISPATCH_SUCCESS' | 'GUARDRAIL_BLOCKED';
    lotTag: string;
    item: string;
    owner: string;
    orderId: string;
    orderClient: string;
    detail: string;
  }>>([
    {
      id: 'audit-0',
      timestamp: '09:15 hari ini',
      type: 'DISPATCH_SUCCESS',
      lotTag: 'LOT-2026-99',
      item: 'Poly-Oxford',
      owner: 'Snøhund',
      orderId: 'ORD-401',
      orderClient: 'Snøhund',
      detail: 'Dispatch 80m dialokasikan untuk cutting line 01',
    },
  ]);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    const res = await listInventoryLots(clientFilter, lotSearch);
    if (res.ok && res.data) {
      setLots(res.data);
    }
    setIsLoading(false);
  }, [clientFilter, lotSearch]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // Handle open dispatch dialog
  const handleOpenDispatch = (lot: InventoryLot) => {
    setDispatchDialog({
      isOpen: true,
      lot,
      targetOrderId: lot.allocatedOrder || DEFAULT_PRODUCTION_ORDERS[0]?.orderId || 'ORD-401',
      quantity: Math.min(lot.balance, 50),
    });
  };

  // Close dispatch dialog
  const handleCloseDispatch = () => {
    setDispatchDialog(prev => ({ ...prev, isOpen: false, lot: null }));
  };

  // Execute Dispatch submission
  const handleConfirmDispatch = async () => {
    if (!dispatchDialog.lot) return;

    const targetOrder = DEFAULT_PRODUCTION_ORDERS.find(
      o => o.orderId === dispatchDialog.targetOrderId,
    );

    if (!targetOrder) {
      toast.error('Order tujuan tidak ditemukan');
      return;
    }

    const res = await executeDispatch({
      lotId: dispatchDialog.lot.id,
      targetOrderId: dispatchDialog.targetOrderId,
      quantity: dispatchDialog.quantity,
    });

    if (!res.ok) {
      if (res.guardrailMismatch) {
        // Trigger FR-6.2 Guardrail Modal!
        setCollisions(c => c + 1);
        handleCloseDispatch();
        setGuardrailAlert({
          isOpen: true,
          lot: dispatchDialog.lot,
          targetOrder,
          validation: res.guardrailMismatch,
        });

        // Record collision audit log
        setAuditLogs(prev => [
          {
            id: `audit-${Date.now()}`,
            timestamp: 'Baru saja',
            type: 'GUARDRAIL_BLOCKED',
            lotTag: dispatchDialog.lot?.lotTag ?? '',
            item: dispatchDialog.lot?.item ?? '',
            owner: dispatchDialog.lot?.owner ?? '',
            orderId: targetOrder.orderId,
            orderClient: targetOrder.client,
            detail: `FR-6.2 Mismatch Rejection: Stock ${dispatchDialog.lot?.owner} diblokir dari Order ${targetOrder.client}`,
          },
          ...prev,
        ]);
        return;
      }

      toast.error(res.error ?? 'Gagal memproses dispatch');
      return;
    }

    // Success dispatch
    toast.success(
      `Dispatch berhasil: ${dispatchDialog.quantity}${dispatchDialog.lot.unit} ${dispatchDialog.lot.item} ke ${targetOrder.orderId} (${targetOrder.client})`,
    );

    setAuditLogs(prev => [
      {
        id: `audit-${Date.now()}`,
        timestamp: 'Baru saja',
        type: 'DISPATCH_SUCCESS',
        lotTag: dispatchDialog.lot?.lotTag ?? '',
        item: dispatchDialog.lot?.item ?? '',
        owner: dispatchDialog.lot?.owner ?? '',
        orderId: targetOrder.orderId,
        orderClient: targetOrder.client,
        detail: `Diterbitkan ${dispatchDialog.quantity}${dispatchDialog.lot?.unit} ke ${targetOrder.orderId}`,
      },
      ...prev,
    ]);

    handleCloseDispatch();
    await loadData();
  };

  // Direct simulation trigger for automated test or single-click verification
  const handleSimulateCrossClientDispatch = (lot: InventoryLot) => {
    // Find an order that belongs to a different client
    const mismatchedOrder = DEFAULT_PRODUCTION_ORDERS.find(o => o.client !== lot.owner) || {
      orderId: 'ORD-402',
      client: 'Brand-X',
      scheme: 'Semi-CMT' as const,
      product: 'Urban Technical Vest',
    };

    setDispatchDialog({
      isOpen: true,
      lot,
      targetOrderId: mismatchedOrder.orderId,
      quantity: 50,
    });
  };

  // Close Guardrail modal
  const handleDismissGuardrail = () => {
    setGuardrailAlert({
      isOpen: false,
      lot: null,
      targetOrder: null,
      validation: null,
    });
  };

  const selectedLotForDialog = dispatchDialog.lot;
  const currentTargetOrder = useMemo(() => {
    return DEFAULT_PRODUCTION_ORDERS.find(o => o.orderId === dispatchDialog.targetOrderId);
  }, [dispatchDialog.targetOrderId]);

  const isCrossClientInDialog = Boolean(
    selectedLotForDialog &&
    currentTargetOrder &&
    selectedLotForDialog.owner !== currentTargetOrder.client,
  );

  return (
    <div className="space-y-6 pb-12 font-sf-pro text-ink" style={{ color: 'var(--c-ink)' }}>
      {/* ── View Header ───────────────────────────────────────────────────────── */}
      <header className="pb-5 border-b" style={{ borderColor: 'var(--c-hair)' }}>
        <p className="font-mono text-[11px] font-semibold uppercase tracking-[.08em] mb-2" style={{ color: 'var(--c-ink-muted)' }}>
          03 — Multi-Client Warehouse Inventory Grid
        </p>
        <h1 className="text-[28px] lg:text-[34px] font-bold tracking-tight" style={{ color: 'var(--c-ink)' }}>
          Multi-Client Warehouse Inventory Grid
        </h1>
        <p className="text-[14px] mt-2" style={{ color: 'var(--c-ink-muted)' }}>
          /app/materials · Ownership is explicit at every issue point.
        </p>
      </header>

      {/* ── Toolbar ───────────────────────────────────────────────────────────── */}
      <div
        className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-[14px] border"
        style={{
          background: 'var(--c-panel)',
          borderColor: 'var(--c-hair)',
        }}
      >
        <div className="flex flex-wrap items-center gap-4">
          {/* Client Filter */}
          <label className="flex items-center gap-2">
            <span className="text-[12px] font-medium" style={{ color: 'var(--c-ink-muted)' }}>
              Filter by Client:
            </span>
            <select
              value={clientFilter}
              onChange={e => setClientFilter(e.target.value)}
              aria-label="Filter by Client"
              className="min-h-[48px] px-3.5 py-2.5 rounded-[12px] text-[13px] font-medium border transition-colors outline-none cursor-pointer"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--c-hair)',
                color: 'var(--c-ink)',
              }}
            >
              {CLIENT_OPTIONS.map(client => (
                <option key={client} value={client}>
                  {client}
                </option>
              ))}
            </select>
          </label>

          {/* Search Lot Tag */}
          <label className="flex items-center gap-2">
            <span className="text-[12px] font-medium" style={{ color: 'var(--c-ink-muted)' }}>
              Search Lot Tag:
            </span>
            <div className="relative flex items-center">
              <input
                type="text"
                value={lotSearch}
                onChange={e => setLotSearch(e.target.value)}
                placeholder="LOT-2026-99"
                aria-label="Search Lot Tag"
                className="min-h-[48px] min-w-[220px] px-3.5 py-2.5 rounded-[12px] text-[13px] border transition-colors outline-none"
                style={{
                  background: 'var(--bg-card)',
                  borderColor: 'var(--c-hair)',
                  color: 'var(--c-ink)',
                }}
              />
              {lotSearch && (
                <button
                  type="button"
                  onClick={() => setLotSearch('')}
                  aria-label="Hapus pencarian"
                  className="absolute right-2 min-h-[48px] min-w-[36px] flex items-center justify-center text-[12px]"
                  style={{ color: 'var(--c-ink-muted)' }}
                >
                  ✕
                </button>
              )}
            </div>
          </label>

          {/* Quick Filter Tag Buttons */}
          <div className="hidden md:flex items-center gap-1.5 ml-2">
            <button
              type="button"
              onClick={() => setLotSearch('LOT-2026-99')}
              className="min-h-[48px] px-3 py-1.5 rounded-[10px] text-[11px] font-mono border transition-colors flex items-center"
              style={{
                background: lotSearch === 'LOT-2026-99' ? 'var(--c-brand-bg)' : 'var(--bg-card)',
                borderColor: lotSearch === 'LOT-2026-99' ? 'var(--c-brand)' : 'var(--c-hair)',
                color: lotSearch === 'LOT-2026-99' ? 'var(--c-brand)' : 'var(--c-ink-muted)',
              }}
            >
              Tag: LOT-2026-99
            </button>
          </div>
        </div>

        {/* Collisions Alert Badge */}
        <div className="flex items-center gap-3">
          <span
            className="font-mono text-[13px] font-semibold px-3.5 py-2 rounded-[10px] border flex items-center gap-2"
            style={{
              background: collisions > 0 ? 'var(--c-bad-bg)' : 'var(--bg-card)',
              borderColor: collisions > 0 ? 'var(--c-bad)' : 'var(--c-hair)',
              color: collisions > 0 ? 'var(--c-bad)' : 'var(--c-ink)',
            }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: collisions > 0 ? 'var(--c-bad)' : 'var(--c-ok)' }}
            />
            Alerts: {collisions} Collisions
          </span>
        </div>
      </div>

      {/* ── Main Inventory Table Panel ────────────────────────────────────────── */}
      <article
        className="rounded-[16px] border overflow-hidden shadow-xs"
        style={{
          background: 'var(--bg-card)',
          borderColor: 'var(--c-hair)',
        }}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse" style={{ fontSize: '13px' }}>
            <thead>
              <tr className="border-b" style={{ borderColor: 'var(--c-hair)' }}>
                <th className="py-3.5 px-4 text-[11px] font-semibold uppercase tracking-[.06em]" style={{ color: 'var(--c-ink-muted)' }}>
                  Item
                </th>
                <th className="py-3.5 px-4 text-[11px] font-semibold uppercase tracking-[.06em]" style={{ color: 'var(--c-ink-muted)' }}>
                  Owner
                </th>
                <th className="py-3.5 px-4 text-[11px] font-semibold uppercase tracking-[.06em]" style={{ color: 'var(--c-ink-muted)' }}>
                  Allocated
                </th>
                <th className="py-3.5 px-4 text-[11px] font-semibold uppercase tracking-[.06em] text-right" style={{ color: 'var(--c-ink-muted)' }}>
                  Balance
                </th>
                <th className="py-3.5 px-4 text-[11px] font-semibold uppercase tracking-[.06em] text-center" style={{ color: 'var(--c-ink-muted)' }}>
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-[13px]" style={{ color: 'var(--c-ink-muted)' }}>
                    Memuat data gudang...
                  </td>
                </tr>
              ) : lots.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-[13px]" style={{ color: 'var(--c-ink-muted)' }}>
                    Tidak ada lot material yang cocok dengan filter atau kata kunci.
                  </td>
                </tr>
              ) : (
                lots.map(lot => {
                  const isSnohund = lot.owner === 'Snøhund';
                  const isBrandX = lot.owner === 'Brand-X';
                  return (
                    <tr
                      key={lot.id}
                      className="border-b last:border-b-0 transition-colors hover:bg-slate-50/50"
                      style={{ borderColor: 'var(--c-hair)' }}
                    >
                      {/* Item column */}
                      <td className="py-4 px-4 font-medium">
                        <div className="flex flex-col">
                          <span className="font-semibold" style={{ color: 'var(--c-ink)' }}>
                            {lot.item}
                          </span>
                          <span className="font-mono text-[11px] mt-0.5" style={{ color: 'var(--c-ink-muted)' }}>
                            {lot.lotTag} · {lot.storageLocation}
                          </span>
                        </div>
                      </td>

                      {/* Owner column */}
                      <td className="py-4 px-4">
                        <span
                          className="inline-flex items-center px-2.5 py-1 rounded-full text-[12px] font-semibold"
                          style={{
                            background: isSnohund
                              ? 'var(--c-brand-bg)'
                              : isBrandX
                              ? 'var(--c-warn-bg)'
                              : 'var(--c-panel-2)',
                            color: isSnohund
                              ? 'var(--c-brand)'
                              : isBrandX
                              ? 'var(--c-warn-2)'
                              : 'var(--c-ink)',
                          }}
                        >
                          {lot.owner}
                        </span>
                      </td>

                      {/* Allocated column */}
                      <td className="py-4 px-4 font-mono font-medium" style={{ color: 'var(--c-ink)' }}>
                        <span className="px-2 py-1 rounded-[6px] bg-slate-100 dark:bg-zinc-800">
                          {lot.allocatedOrder}
                        </span>
                      </td>

                      {/* Balance column */}
                      <td className="py-4 px-4 text-right font-mono font-semibold text-[14px]" style={{ color: 'var(--c-ink)' }}>
                        {lot.balance}{lot.unit}
                      </td>

                      {/* Action column */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          {/* Standard Dispatch Button (>= 48px touch target) */}
                          <button
                            type="button"
                            onClick={() => handleOpenDispatch(lot)}
                            aria-label={`Dispatch ${lot.item}`}
                            className="min-h-[48px] px-5 py-2.5 rounded-[12px] font-semibold text-[13px] transition-all transform active:scale-95 flex items-center justify-center gap-1.5 shadow-xs"
                            style={{
                              background: 'var(--c-brand)',
                              color: '#ffffff',
                              border: 'none',
                            }}
                          >
                            <span>Dispatch</span>
                          </button>

                          {/* Quick Guardrail Test Action (>= 48px touch target) */}
                          <button
                            type="button"
                            onClick={() => handleSimulateCrossClientDispatch(lot)}
                            title="Uji Guardrail FR-6.2 (Simulasi Cross-Client Dispatch)"
                            aria-label={`Uji Guardrail FR-6.2 untuk ${lot.item}`}
                            className="min-h-[48px] px-3 py-2.5 rounded-[12px] font-mono text-[11px] font-semibold border transition-all text-bad hover:bg-red-50 flex items-center justify-center"
                            style={{
                              borderColor: 'var(--c-bad)',
                              color: 'var(--c-bad)',
                              background: 'transparent',
                            }}
                          >
                            Uji FR-6.2
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </article>

      {/* ── FR-6.2 Audit Traceability Stream ──────────────────────────────────── */}
      <div
        className="p-5 rounded-[16px] border space-y-3"
        style={{
          background: 'var(--c-panel)',
          borderColor: 'var(--c-hair)',
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <LucideIcon name="activity" className="w-4 h-4 text-blue-600" />
            <h3 className="text-[14px] font-semibold" style={{ color: 'var(--c-ink)' }}>
              Audit Log Penerbitan Bahan &amp; Guardrail Log (FR-6.2)
            </h3>
          </div>
          <span className="font-mono text-[11px]" style={{ color: 'var(--c-ink-muted)' }}>
            Realtime Stream · Immutable Trace
          </span>
        </div>

        <div className="space-y-2">
          {auditLogs.slice(0, 4).map(log => {
            const isBlocked = log.type === 'GUARDRAIL_BLOCKED';
            return (
              <div
                key={log.id}
                className="flex items-start justify-between p-3 rounded-[10px] border text-[12px]"
                style={{
                  background: isBlocked ? 'var(--c-bad-bg)' : 'var(--bg-card)',
                  borderColor: isBlocked ? 'var(--c-bad)' : 'var(--c-hair)',
                }}
              >
                <div className="flex items-start gap-2.5">
                  <span
                    className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded mt-0.5 shrink-0"
                    style={{
                      background: isBlocked ? 'var(--c-bad)' : 'var(--c-brand)',
                      color: '#ffffff',
                    }}
                  >
                    {isBlocked ? 'FR-6.2 BLOCKED' : 'DISPATCH'}
                  </span>
                  <div>
                    <p className="font-semibold" style={{ color: isBlocked ? 'var(--c-bad)' : 'var(--c-ink)' }}>
                      {log.lotTag} ({log.item}) · Pemilik: {log.owner} ➔ Target: {log.orderId} ({log.orderClient})
                    </p>
                    <p className="text-[11px] mt-0.5" style={{ color: 'var(--c-ink-muted)' }}>
                      {log.detail}
                    </p>
                  </div>
                </div>
                <span className="font-mono text-[11px] shrink-0 ml-3" style={{ color: 'var(--c-ink-muted)' }}>
                  {log.timestamp}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Interactive Dispatch Configuration Modal ──────────────────────────── */}
      {dispatchDialog.isOpen && selectedLotForDialog && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs"
          role="presentation"
        >
          <div
            className="w-full max-w-[500px] p-6 rounded-[20px] shadow-2xl border space-y-5"
            style={{
              background: 'var(--bg-card)',
              borderColor: 'var(--c-hair)',
            }}
            role="dialog"
            aria-modal="true"
            aria-labelledby="dispatch-config-title"
          >
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: 'var(--c-hair)' }}>
              <div>
                <p className="font-mono text-[11px] font-semibold uppercase tracking-wider text-blue-600">
                  Warehouse Material Issue
                </p>
                <h2 id="dispatch-config-title" className="text-[20px] font-bold mt-0.5">
                  Konfirmasi Dispatch Material
                </h2>
              </div>
              <button
                type="button"
                onClick={handleCloseDispatch}
                aria-label="Tutup form dispatch"
                className="min-h-[48px] min-w-[48px] flex items-center justify-center rounded-xl text-[18px] hover:bg-slate-100"
                style={{ color: 'var(--c-ink-muted)' }}
              >
                ✕
              </button>
            </div>

            {/* Lot Summary Card */}
            <div
              className="p-3.5 rounded-[12px] border text-[13px] space-y-1.5"
              style={{ background: 'var(--c-panel)', borderColor: 'var(--c-hair)' }}
            >
              <div className="flex justify-between">
                <span style={{ color: 'var(--c-ink-muted)' }}>Item &amp; Lot:</span>
                <span className="font-semibold">{selectedLotForDialog.item} ({selectedLotForDialog.lotTag})</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--c-ink-muted)' }}>Pemilik Material:</span>
                <span className="font-bold text-blue-600">{selectedLotForDialog.owner}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--c-ink-muted)' }}>Tersedia di Gudang:</span>
                <span className="font-mono font-semibold">{selectedLotForDialog.balance} {selectedLotForDialog.unit}</span>
              </div>
            </div>

            {/* Target Order Selection */}
            <div>
              <label htmlFor="target-order-select" className="block text-[13px] font-semibold mb-1.5">
                Pilih Order Tujuan (Target Order):
              </label>
              <select
                id="target-order-select"
                value={dispatchDialog.targetOrderId}
                onChange={e => setDispatchDialog(prev => ({ ...prev, targetOrderId: e.target.value }))}
                className="w-full min-h-[48px] px-3.5 py-2.5 rounded-[12px] text-[13px] border outline-none cursor-pointer"
                style={{
                  background: 'var(--bg-card)',
                  borderColor: isCrossClientInDialog ? 'var(--c-bad)' : 'var(--c-hair)',
                  color: 'var(--c-ink)',
                }}
              >
                {DEFAULT_PRODUCTION_ORDERS.map(order => {
                  const isMatch = order.client === selectedLotForDialog.owner;
                  return (
                    <option key={order.orderId} value={order.orderId}>
                      {order.orderId} — {order.client} ({order.scheme}) {!isMatch ? '⚠️ [MISMATCH]' : '✓ [MATCH]'}
                    </option>
                  );
                })}
              </select>

              {/* Warning preview if cross-client is selected */}
              {isCrossClientInDialog && (
                <p className="mt-2 text-[12px] font-semibold text-bad flex items-center gap-1.5" style={{ color: 'var(--c-bad)' }}>
                  <span>⚠️ Perhatian:</span>
                  <span>
                    Stock milik <strong>{selectedLotForDialog.owner}</strong> tidak cocok dengan order <strong>{currentTargetOrder?.client}</strong>. Akan ditolak oleh guardrail FR-6.2!
                  </span>
                </p>
              )}
            </div>

            {/* Quantity Input */}
            <div>
              <label htmlFor="dispatch-qty-input" className="block text-[13px] font-semibold mb-1.5">
                Jumlah Dispatch ({selectedLotForDialog.unit}):
              </label>
              <input
                id="dispatch-qty-input"
                type="number"
                min={1}
                max={selectedLotForDialog.balance}
                value={dispatchDialog.quantity}
                onChange={e => setDispatchDialog(prev => ({ ...prev, quantity: Math.max(1, parseInt(e.target.value, 10) || 1) }))}
                className="w-full min-h-[48px] px-3.5 py-2.5 rounded-[12px] text-[14px] font-mono border outline-none"
                style={{
                  background: 'var(--bg-card)',
                  borderColor: 'var(--c-hair)',
                }}
              />
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t" style={{ borderColor: 'var(--c-hair)' }}>
              <button
                type="button"
                onClick={handleCloseDispatch}
                className="min-h-[48px] px-5 py-2.5 rounded-[12px] font-medium text-[13px] border hover:bg-slate-100 transition-colors"
                style={{ borderColor: 'var(--c-hair)', color: 'var(--c-ink)' }}
              >
                Batal
              </button>
              <button
                type="button"
                onClick={handleConfirmDispatch}
                className="min-h-[48px] px-6 py-2.5 rounded-[12px] font-semibold text-[13px] transition-transform active:scale-95 shadow-sm"
                style={{
                  background: isCrossClientInDialog ? 'var(--c-bad)' : 'var(--c-brand)',
                  color: '#ffffff',
                }}
              >
                {isCrossClientInDialog ? 'Uji Rejection Dispatch' : 'Konfirmasi Dispatch'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── CRITICAL GUARDRAIL: FR-6.2 Ownership Guardrail Modal ──────────────── */}
      {guardrailAlert.isOpen && (
        <div
          className="fixed inset-0 z-50 grid place-items-center p-6 bg-black/40 backdrop-blur-xs"
          role="presentation"
        >
          <div
            className="w-full max-w-[460px] p-7 rounded-[18px] border shadow-2xl animate-scaleUp"
            style={{
              background: 'rgba(255, 255, 255, 0.98)',
              borderColor: 'rgba(0, 0, 0, 0.12)',
            }}
            role="dialog"
            aria-modal="true"
            aria-labelledby="dispatch-modal-title"
          >
            {/* Header label matching lukla-ui-mock.html */}
            <p
              className="font-mono text-[11px] font-bold tracking-[.08em] uppercase mb-3"
              style={{ color: 'var(--c-bad)' }}
            >
              FR-6.2 · Ownership guardrail
            </p>

            {/* Exact modal title matching lukla-ui-mock.html */}
            <h2
              id="dispatch-modal-title"
              className="text-[22px] lg:text-[24px] font-bold tracking-tight text-ink"
              style={{ color: 'var(--c-ink)' }}
            >
              Dispatch Ditolak — Ownership Mismatch
            </h2>

            {/* Exact body paragraph matching lukla-ui-mock.html and prompt */}
            <p className="mt-3.5 mb-5 text-[14px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
              Stock milik Client A tidak dapat diterbitkan ke Order Client B. Periksa ownership lot dan order sebelum dispatch dilanjutkan.
            </p>

            {/* Context details badge for audit insight */}
            {guardrailAlert.lot && guardrailAlert.targetOrder && (
              <div
                className="mb-6 p-3 rounded-[12px] border font-mono text-[11px] space-y-1"
                style={{
                  background: 'var(--c-bad-bg)',
                  borderColor: 'var(--c-bad-bg-2)',
                  color: 'var(--c-bad-4)',
                }}
              >
                <div>• Stock Material: {guardrailAlert.lot.item} ({guardrailAlert.lot.lotTag})</div>
                <div>• Pemilik Lot Asal: <strong>{guardrailAlert.lot.owner}</strong></div>
                <div>• Order Tujuan: <strong>{guardrailAlert.targetOrder.orderId}</strong> (Klien: <strong>{guardrailAlert.targetOrder.client}</strong>)</div>
                <div className="pt-1 text-[10px] text-slate-500">• Invarian: Multi-Client Strict Isolation Rule</div>
              </div>
            )}

            {/* Dismiss button matching lukla-ui-mock.html */}
            <button
              type="button"
              onClick={handleDismissGuardrail}
              data-dismiss-modal
              className="w-full min-h-[48px] px-6 py-3 rounded-[12px] font-semibold text-[14px] transition-colors border"
              style={{
                background: 'var(--c-page)',
                color: 'var(--c-ink)',
                borderColor: 'var(--c-hair)',
              }}
            >
              Mengerti
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default WarehouseInventoryView;
