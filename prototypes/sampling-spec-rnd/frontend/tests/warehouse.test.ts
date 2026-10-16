/**
 * Warehouse & FR-6.2 Cross-Client Ownership Guardrail Unit Tests.
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  listInventoryLots,
  validateDispatchOwnership,
  executeDispatch,
  resetWarehouseStore,
  DEFAULT_PRODUCTION_ORDERS,
  type InventoryLot,
  type ProductionOrder,
} from '../src/services/warehouseApi.ts';

test('inventory lots list filters by client accurately', async () => {
  resetWarehouseStore();
  const allLots = await listInventoryLots('All');
  assert.equal(allLots.ok, true);
  assert.equal(allLots.data?.length, 6);

  const snohundLots = await listInventoryLots('Snøhund');
  assert.equal(snohundLots.ok, true);
  assert.equal(snohundLots.data?.every(l => l.owner === 'Snøhund'), true);
  assert.equal(snohundLots.data?.length, 3);

  const brandXLots = await listInventoryLots('Brand-X');
  assert.equal(brandXLots.ok, true);
  assert.equal(brandXLots.data?.every(l => l.owner === 'Brand-X'), true);
  assert.equal(brandXLots.data?.length, 2);
});

test('inventory lots search matches lot tag case-insensitively', async () => {
  resetWarehouseStore();
  const searchRes = await listInventoryLots('All', 'LOT-2026-99');
  assert.equal(searchRes.ok, true);
  assert.equal(searchRes.data?.length, 1);
  assert.equal(searchRes.data?.[0].lotTag, 'LOT-2026-99');
  assert.equal(searchRes.data?.[0].item, 'Poly-Oxford');
});

test('FR-6.2 guardrail allows matching client dispatch', () => {
  const lot: InventoryLot = {
    id: 'lot-01',
    item: 'Poly-Oxford',
    lotTag: 'LOT-2026-99',
    owner: 'Snøhund',
    allocatedOrder: 'ORD-401',
    balance: 420,
    unit: 'm',
    materialType: 'Outer Shell Fabric',
    storageLocation: 'Rak A-04',
    status: 'ALLOCATED',
    lastUpdated: '2026-10-15T09:30:00+07:00',
  };

  const matchingOrder: ProductionOrder = {
    orderId: 'ORD-401',
    client: 'Snøhund',
    scheme: 'CMT',
    product: 'Arctic Parka v2',
  };

  const validation = validateDispatchOwnership(lot, matchingOrder);
  assert.equal(validation.allowed, true);
  assert.equal(validation.errorCode, undefined);
});

test('FR-6.2 guardrail blocks cross-client dispatch (Client A to Client B order)', () => {
  const lot: InventoryLot = {
    id: 'lot-01',
    item: 'Poly-Oxford',
    lotTag: 'LOT-2026-99',
    owner: 'Snøhund',
    allocatedOrder: 'ORD-401',
    balance: 420,
    unit: 'm',
    materialType: 'Outer Shell Fabric',
    storageLocation: 'Rak A-04',
    status: 'ALLOCATED',
    lastUpdated: '2026-10-15T09:30:00+07:00',
  };

  const mismatchedOrder: ProductionOrder = {
    orderId: 'ORD-402',
    client: 'Brand-X',
    scheme: 'Semi-CMT',
    product: 'Urban Technical Vest',
  };

  const validation = validateDispatchOwnership(lot, mismatchedOrder);
  assert.equal(validation.allowed, false);
  assert.equal(validation.errorCode, 'FR_6_2_OWNERSHIP_MISMATCH');
  assert.match(validation.errorMessage ?? '', /Dispatch Ditolak — Ownership Mismatch/);
  assert.match(validation.errorMessage ?? '', /Stock milik Client A tidak dapat diterbitkan ke Order Client B/);
});

test('executeDispatch rejects cross-client dispatch and preserves stock balance', async () => {
  resetWarehouseStore();
  const res = await executeDispatch({
    lotId: 'lot-01', // Snøhund stock
    targetOrderId: 'ORD-402', // Brand-X order
    quantity: 50,
  });

  assert.equal(res.ok, false);
  assert.equal(res.guardrailMismatch?.errorCode, 'FR_6_2_OWNERSHIP_MISMATCH');
  assert.match(res.error ?? '', /Ownership Mismatch/);

  // Verify stock is untouched
  const lots = await listInventoryLots('All', 'LOT-2026-99');
  assert.equal(lots.data?.[0].balance, 420);
});

test('executeDispatch succeeds for matching client order and decrements balance', async () => {
  resetWarehouseStore();
  const res = await executeDispatch({
    lotId: 'lot-01', // Snøhund stock (420m)
    targetOrderId: 'ORD-401', // Snøhund order
    quantity: 120,
  });

  assert.equal(res.ok, true);
  assert.equal(res.data?.remainingBalance, 300);

  const lots = await listInventoryLots('All', 'LOT-2026-99');
  assert.equal(lots.data?.[0].balance, 300);
});
