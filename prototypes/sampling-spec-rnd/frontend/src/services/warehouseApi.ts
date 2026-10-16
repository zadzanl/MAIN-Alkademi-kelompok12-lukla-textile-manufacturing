/**
 * Warehouse API service — Multi-Client Inventory & Cross-Client Guardrail (FR-6.2).
 *
 * Contract & Specification:
 * - FR-6.2: Reject material issuance when Material Client != Order Client.
 * - Multi-client warehouse grid matching View-03 of Lukla Operations Engine.
 * - Supports client filtering, lot tag search, and dispatch validation.
 */

export interface InventoryLot {
  id: string;
  item: string;
  lotTag: string;
  owner: string;
  allocatedOrder: string;
  balance: number;
  unit: string;
  materialType: string;
  storageLocation: string;
  status: 'AVAILABLE' | 'ALLOCATED' | 'DEPLETED';
  lastUpdated: string;
}

export interface ProductionOrder {
  orderId: string;
  client: string;
  scheme: 'CMT' | 'Semi-CMT' | 'Full Package';
  product: string;
}

export interface DispatchRequest {
  lotId: string;
  targetOrderId: string;
  quantity: number;
}

export interface DispatchValidationResult {
  allowed: boolean;
  errorCode?: 'FR_6_2_OWNERSHIP_MISMATCH';
  errorMessage?: string;
  sourceClient: string;
  targetClient: string;
  lotTag: string;
  orderId: string;
}

export interface DispatchSuccessResult {
  dispatchId: string;
  lotId: string;
  orderId: string;
  quantity: number;
  remainingBalance: number;
  timestamp: string;
}

export interface WarehouseResult<T> {
  ok: boolean;
  data?: T;
  error?: string;
  guardrailMismatch?: DispatchValidationResult;
}

// ─── Default Reference Data ───────────────────────────────────────────────────

export const DEFAULT_PRODUCTION_ORDERS: ProductionOrder[] = [
  { orderId: 'ORD-401', client: 'Snøhund', scheme: 'CMT', product: 'Arctic Parka v2' },
  { orderId: 'ORD-402', client: 'Brand-X', scheme: 'Semi-CMT', product: 'Urban Technical Vest' },
  { orderId: 'ORD-399', client: 'Snøhund', scheme: 'Full Package', product: 'Alpine Expedition Jacket' },
  { orderId: 'ORD-405', client: 'AlpineGear', scheme: 'CMT', product: 'Summit Windbreaker' },
];

export const INITIAL_INVENTORY_LOTS: InventoryLot[] = [
  {
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
  },
  {
    id: 'lot-02',
    item: 'Thermolite',
    lotTag: 'LOT-2026-102',
    owner: 'Brand-X',
    allocatedOrder: 'ORD-402',
    balance: 184,
    unit: 'm',
    materialType: 'Thermal Insulation',
    storageLocation: 'Rak B-12',
    status: 'ALLOCATED',
    lastUpdated: '2026-10-15T10:15:00+07:00',
  },
  {
    id: 'lot-03',
    item: 'Fleece Polar',
    lotTag: 'LOT-2026-105',
    owner: 'Snøhund',
    allocatedOrder: 'ORD-399',
    balance: 350,
    unit: 'm',
    materialType: 'Lining Fabric',
    storageLocation: 'Rak A-08',
    status: 'ALLOCATED',
    lastUpdated: '2026-10-14T14:20:00+07:00',
  },
  {
    id: 'lot-04',
    item: 'Taslan Microfiber',
    lotTag: 'LOT-2026-108',
    owner: 'Brand-X',
    allocatedOrder: 'ORD-402',
    balance: 215,
    unit: 'm',
    materialType: 'Water-Repellent Fabric',
    storageLocation: 'Rak B-07',
    status: 'ALLOCATED',
    lastUpdated: '2026-10-15T08:45:00+07:00',
  },
  {
    id: 'lot-05',
    item: 'Cordura 500D',
    lotTag: 'LOT-2026-112',
    owner: 'AlpineGear',
    allocatedOrder: 'ORD-405',
    balance: 580,
    unit: 'm',
    materialType: 'Reinforcement Fabric',
    storageLocation: 'Rak C-02',
    status: 'ALLOCATED',
    lastUpdated: '2026-10-13T16:00:00+07:00',
  },
  {
    id: 'lot-06',
    item: 'YKK Waterproof Zipper #5',
    lotTag: 'LOT-2026-118',
    owner: 'Snøhund',
    allocatedOrder: 'ORD-401',
    balance: 1200,
    unit: 'pcs',
    materialType: 'Trim / Hardware',
    storageLocation: 'Kotak H-03',
    status: 'ALLOCATED',
    lastUpdated: '2026-10-15T11:00:00+07:00',
  },
];

// ─── In-memory store ─────────────────────────────────────────────────────────

let inventoryStore: InventoryLot[] = [...INITIAL_INVENTORY_LOTS];
let collisionCount = 0;

export function getCollisionCount(): number {
  return collisionCount;
}

export function resetWarehouseStore(): void {
  inventoryStore = [...INITIAL_INVENTORY_LOTS];
  collisionCount = 0;
}

// ─── Core FR-6.2 Guardrail Logic ─────────────────────────────────────────────

/**
 * Validates cross-client ownership prior to dispatch.
 * FR-6.2: Rejects issuance if material owner does not match destination order client.
 */
export function validateDispatchOwnership(
  lot: InventoryLot,
  targetOrder: ProductionOrder,
): DispatchValidationResult {
  if (lot.owner !== targetOrder.client) {
    collisionCount++;
    return {
      allowed: false,
      errorCode: 'FR_6_2_OWNERSHIP_MISMATCH',
      errorMessage: `Dispatch Ditolak — Ownership Mismatch. Stock milik Client A tidak dapat diterbitkan ke Order Client B. Periksa ownership lot dan order sebelum dispatch dilanjutkan.`,
      sourceClient: lot.owner,
      targetClient: targetOrder.client,
      lotTag: lot.lotTag,
      orderId: targetOrder.orderId,
    };
  }

  return {
    allowed: true,
    sourceClient: lot.owner,
    targetClient: targetOrder.client,
    lotTag: lot.lotTag,
    orderId: targetOrder.orderId,
  };
}

// ─── Service Methods ──────────────────────────────────────────────────────────

export async function listInventoryLots(clientFilter?: string, lotTagQuery?: string): Promise<WarehouseResult<InventoryLot[]>> {
  let filtered = [...inventoryStore];

  if (clientFilter && clientFilter !== 'All') {
    filtered = filtered.filter(lot => lot.owner.toLowerCase() === clientFilter.toLowerCase());
  }

  if (lotTagQuery && lotTagQuery.trim()) {
    const q = lotTagQuery.trim().toLowerCase();
    filtered = filtered.filter(lot =>
      lot.lotTag.toLowerCase().includes(q) ||
      lot.item.toLowerCase().includes(q) ||
      lot.allocatedOrder.toLowerCase().includes(q),
    );
  }

  return { ok: true, data: filtered };
}

export async function executeDispatch(req: DispatchRequest): Promise<WarehouseResult<DispatchSuccessResult>> {
  const lot = inventoryStore.find(l => l.id === req.lotId);
  if (!lot) {
    return { ok: false, error: 'Lot inventory tidak ditemukan.' };
  }

  const order = DEFAULT_PRODUCTION_ORDERS.find(o => o.orderId === req.targetOrderId);
  if (!order) {
    return { ok: false, error: 'Target order tidak valid.' };
  }

  if (req.quantity <= 0) {
    return { ok: false, error: 'Jumlah dispatch harus lebih dari 0.' };
  }

  if (req.quantity > lot.balance) {
    return { ok: false, error: `Jumlah dispatch melebihi sisa stok (${lot.balance} ${lot.unit}).` };
  }

  // Enforce FR-6.2 Guardrail
  const validation = validateDispatchOwnership(lot, order);
  if (!validation.allowed) {
    return {
      ok: false,
      error: validation.errorMessage,
      guardrailMismatch: validation,
    };
  }

  // Successful dispatch
  lot.balance -= req.quantity;
  if (lot.balance === 0) {
    lot.status = 'DEPLETED';
  }
  lot.lastUpdated = new Date().toISOString();

  const successData: DispatchSuccessResult = {
    dispatchId: `DSP-${Date.now().toString().slice(-6)}`,
    lotId: lot.id,
    orderId: order.orderId,
    quantity: req.quantity,
    remainingBalance: lot.balance,
    timestamp: lot.lastUpdated,
  };

  return { ok: true, data: successData };
}
