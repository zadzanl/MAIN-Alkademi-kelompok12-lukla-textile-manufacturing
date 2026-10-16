/**
 * Ops API client — sewing floor (VIEW-04) and quality (VIEW-05).
 *
 * Contract source of truth:
 *   openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml
 *   GET  /lines                          listLines
 *   POST /lines                          createLine
 *   GET  /operators                      listOperators
 *   POST /operators                      createOperator
 *   GET  /assignments                    listAssignments
 *   PUT  /lines/{lineId}/operators       assignOperator
 *   POST /sewing-tallies                 recordSewingTally
 *   POST /sewing-tallies/{tallyId}/verification  verifySewingTally
 *   GET  /assemblies                     listAssemblies
 *   POST /assemblies                     createAssembly
 *   GET  /production/progress            listProductionProgress
 *   POST /qc-inspections                 inspectUnit
 *
 * KNOWN CEILING (deliberate): same as services/ledgerApi.ts — runs in MOCK
 * mode by default because the live service needs a Bearer JWT + CORS that the
 * backend team is still wiring. Set VITE_LEDGER_MODE=live (shared flag) plus
 * VITE_LEDGER_API_URL / VITE_LEDGER_TOKEN to hit the real service. Shapes stay
 * identical to the contract so switching modes needs no UI change.
 */
import { DATA_MODE as MODE, LEDGER_BASE as LIVE_BASE, LEDGER_TOKEN as LIVE_TOKEN } from './config';

export type AssemblyStatus = 'MENUNGGU_QC' | 'REWORK' | 'QC_PASS' | 'REJECT_SCRAP';
export type QcDisposition = 'PASS' | 'REPAIR' | 'REJECT';
export type QuantityUnit = 'PIECE' | 'METER' | 'KILOGRAM' | 'ROLL';

export interface Quantity { value: string; unit: QuantityUnit; }
export interface Line { id: string; lineCode: string; active: boolean; }
export interface Operator { id: string; displayName: string; employeeCode: string; actorId?: string; active: boolean; }
export interface Assignment {
  id: string;
  lineId: string;
  operatorId: string;
  componentCode: string;
  validFrom: string;
  validThrough: string;
  stationNumber?: number;
}
export interface ProgressItem { orderId: string; componentCode: string; quantity: Quantity; status: AssemblyStatus; }
export interface Assembly { id: string; orderId: string; serialCode: string; componentUnitIds: string[]; status: AssemblyStatus; }
export interface TallyResult { tallyId: string; status: 'RECORDED' | 'VERIFIED'; createdUnitIds: string[]; }
export interface TallyInput {
  orderId: string; cutBatchId: string; lineId: string; componentCode: string;
  operatorId: string; intervalStart: string; intervalEnd: string; pieces: number;
  /** Stable key so retries of the same logical submission are replay-safe. */
  idempotencyKey?: string;
}
export interface Defect { componentUnitId: string; code: string; notes?: string; }
export interface QcRequest { assemblyId: string; disposition: QcDisposition; defects: Defect[]; }
export interface QcInspection extends QcRequest { id: string; }
export interface Page<T> { items: T[]; nextCursor?: string | null; }

export interface OpsResult<T> { ok: boolean; data?: T; error?: string; }

export const isMockOps = MODE === 'mock';

function uuid(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function newIdempotencyKey(): string {
  return uuid().replace(/-/g, '');
}

// ─── Mock store ────────────────────────────────────────────────────────────────
const mockIdempotency = new Map<string, TallyResult>();

const mock = {
  lines: [] as Line[],
  operators: [] as Operator[],
  assignments: [] as Assignment[],
  tallies: new Map<string, TallyResult>(),
  assemblies: [] as Assembly[],
  progress: [] as ProgressItem[],
  inspections: [] as QcInspection[],
};

const SEED_NAMES: { name: string; comp: string }[] = [
  { name: 'Siti', comp: 'SLEEVE' },
  { name: 'Budi', comp: 'COLLAR' },
  { name: 'Rudi S.', comp: 'SLEEVE' },
  { name: 'Mira K.', comp: 'COLLAR' },
  { name: 'Sari P.', comp: 'HEM' },
  { name: 'Dedi A.', comp: 'FRONT_PANEL' },
  { name: 'Hendra G.', comp: 'BACK_PANEL' },
  { name: 'Lina M.', comp: 'POCKET' },
  { name: 'Agus S.', comp: 'ZIPPER' },
  { name: 'Dewi L.', comp: 'CUFF' },
  { name: 'Eko P.', comp: 'PLACKET' },
  { name: 'Wati S.', comp: 'HOOD' },
  { name: 'Bambang T.', comp: 'LINING' },
  { name: 'Rina H.', comp: 'SLEEVE' },
  { name: 'Fajar N.', comp: 'COLLAR' },
  { name: 'Maya A.', comp: 'HEM' },
  { name: 'Tono W.', comp: 'FRONT_PANEL' },
  { name: 'Sri W.', comp: 'BACK_PANEL' },
  { name: 'Joko S.', comp: 'POCKET' },
  { name: 'Novi I.', comp: 'ZIPPER' },
  { name: 'Andi P.', comp: 'CUFF' },
  { name: 'Yuni A.', comp: 'PLACKET' },
  { name: 'Bagas R.', comp: 'HOOD' },
  { name: 'Tari M.', comp: 'LINING' },
  { name: 'Surya K.', comp: 'SLEEVE' },
  { name: 'Putri N.', comp: 'COLLAR' },
  { name: 'Wahyu H.', comp: 'HEM' },
  { name: 'Mega S.', comp: 'FRONT_PANEL' },
  { name: 'Rizky P.', comp: 'BACK_PANEL' },
  { name: 'Dian K.', comp: 'POCKET' },
  { name: 'Arif B.', comp: 'ZIPPER' },
  { name: 'Intan P.', comp: 'CUFF' },
  { name: 'Dimas A.', comp: 'PLACKET' },
  { name: 'Fitri H.', comp: 'HOOD' },
  { name: 'Yusuf M.', comp: 'LINING' },
  { name: 'Anisa R.', comp: 'SLEEVE' },
  { name: 'Ilham F.', comp: 'COLLAR' },
  { name: 'Nurul A.', comp: 'HEM' },
  { name: 'Bayu S.', comp: 'FRONT_PANEL' },
  { name: 'Tri W.', comp: 'BACK_PANEL' },
  { name: 'Ahmad F.', comp: 'POCKET' },
  { name: 'Lestari D.', comp: 'ZIPPER' },
  { name: 'Doni K.', comp: 'CUFF' },
  { name: 'Kartika S.', comp: 'PLACKET' },
  { name: 'Rian P.', comp: 'HOOD' },
  { name: 'Siska M.', comp: 'LINING' },
  { name: 'Farhan A.', comp: 'SLEEVE' },
  { name: 'Ratna D.', comp: 'COLLAR' },
  { name: 'Guruh P.', comp: 'HEM' },
  { name: 'Bella S.', comp: 'FRONT_PANEL' },
  { name: 'Gilang R.', comp: 'BACK_PANEL' },
  { name: 'Tiara K.', comp: 'POCKET' },
  { name: 'Lukman H.', comp: 'ZIPPER' },
  { name: 'Melati P.', comp: 'CUFF' },
  { name: 'Iqbal M.', comp: 'PLACKET' },
  { name: 'Cahya W.', comp: 'HOOD' },
  { name: 'Dani S.', comp: 'LINING' },
  { name: 'Gita R.', comp: 'SLEEVE' },
  { name: 'Haris T.', comp: 'COLLAR' },
  { name: 'Dina M.', comp: 'HEM' },
  { name: 'Reza A.', comp: 'FRONT_PANEL' },
  { name: 'Ayu P.', comp: 'BACK_PANEL' },
  { name: 'Teguh W.', comp: 'POCKET' },
  { name: 'Lia S.', comp: 'ZIPPER' },
  { name: 'Zul F.', comp: 'CUFF' },
  { name: 'Nita R.', comp: 'PLACKET' },
  { name: 'Adit P.', comp: 'HOOD' },
  { name: 'Vina M.', comp: 'LINING' },
  { name: 'Yoga S.', comp: 'SLEEVE' },
  { name: 'Restu K.', comp: 'HEM' },
];

export function seedSeventyStations(targetLineId?: string): Assignment[] {
  const lineId = targetLineId ?? (mock.lines[0]?.id ?? '11111111-1111-4111-8111-111111111111');
  const now = new Date();
  const validFrom = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 7, 0, 0).toISOString();
  const validThrough = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 17, 0, 0).toISOString();

  // Remove existing assignments for this line to prevent duplicates
  mock.assignments = mock.assignments.filter(a => a.lineId !== lineId);

  const created: Assignment[] = [];
  SEED_NAMES.forEach((entry, idx) => {
    const stationNumber = idx + 1;
    const empCode = `OPR-${String(stationNumber).padStart(3, '0')}`;
    let op = mock.operators.find(o => o.employeeCode === empCode);
    if (!op) {
      op = {
        id: stationNumber === 1 ? '44444444-4444-4444-8444-444444444444' : (stationNumber === 2 ? '44444444-4444-4444-8444-444444444445' : uuid()),
        displayName: entry.name,
        employeeCode: empCode,
        active: true,
      };
      mock.operators.push(op);
    }
    const asgn: Assignment = {
      id: uuid(),
      lineId,
      operatorId: op.id,
      componentCode: entry.comp,
      validFrom,
      validThrough,
      stationNumber,
    };
    created.push(asgn);
  });

  mock.assignments = [...mock.assignments, ...created];
  return created;
}

function seed() {
  const lineA: Line = { id: '11111111-1111-4111-8111-111111111111', lineCode: 'LINE-A', active: true };
  const lineB: Line = { id: '11111111-1111-4111-8111-111111111112', lineCode: 'LINE-B', active: true };
  mock.lines = [lineA, lineB];

  // Seed up to 70 sewing stations for LINE-A
  seedSeventyStations(lineA.id);

  mock.assemblies = [
    { id: '55555555-5555-4555-8555-555555555555', orderId: 'ORD-401', serialCode: 'SN-401-0891', componentUnitIds: [uuid(), uuid()], status: 'MENUNGGU_QC' },
    { id: '55555555-5555-4555-8555-555555555556', orderId: 'ORD-401', serialCode: 'SN-401-0892', componentUnitIds: [uuid(), uuid()], status: 'MENUNGGU_QC' },
    { id: '55555555-5555-4555-8555-555555555557', orderId: 'ORD-401', serialCode: 'SN-401-0893', componentUnitIds: [uuid(), uuid()], status: 'MENUNGGU_QC' },
    { id: '55555555-5555-4555-8555-555555555558', orderId: 'ORD-402', serialCode: 'SN-402-0104', componentUnitIds: [uuid(), uuid()], status: 'MENUNGGU_QC' },
  ];
  mock.progress = [
    { orderId: '33333333-3333-4333-8333-333333333333', componentCode: 'SLEEVE', quantity: { value: '18', unit: 'PIECE' }, status: 'MENUNGGU_QC' },
  ];
  mock.inspections = [
    { id: uuid(), assemblyId: uuid(), disposition: 'REPAIR', defects: [{ componentUnitId: uuid(), code: 'Broken Stitch' }, { componentUnitId: uuid(), code: 'Puckering' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REPAIR', defects: [{ componentUnitId: uuid(), code: 'Broken Stitch' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REJECT', defects: [{ componentUnitId: uuid(), code: 'Broken Stitch' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REPAIR', defects: [{ componentUnitId: uuid(), code: 'Broken Stitch' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REPAIR', defects: [{ componentUnitId: uuid(), code: 'Broken Stitch' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REPAIR', defects: [{ componentUnitId: uuid(), code: 'Puckering' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REPAIR', defects: [{ componentUnitId: uuid(), code: 'Puckering' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REJECT', defects: [{ componentUnitId: uuid(), code: 'Puckering' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REPAIR', defects: [{ componentUnitId: uuid(), code: 'Uneven Seam' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REPAIR', defects: [{ componentUnitId: uuid(), code: 'Uneven Seam' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REJECT', defects: [{ componentUnitId: uuid(), code: 'Open Seam' }] },
    { id: uuid(), assemblyId: uuid(), disposition: 'REJECT', defects: [{ componentUnitId: uuid(), code: 'Needle Hole' }] },
  ];
}
seed();

// ─── Live transport ────────────────────────────────────────────────────────────
function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (LIVE_TOKEN) headers.Authorization = `Bearer ${LIVE_TOKEN}`;
  return headers;
}

async function readProblem(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (body && typeof body === 'object') {
      const { code, detail } = body as { code?: unknown; detail?: unknown };
      if (typeof detail === 'string') return typeof code === 'string' ? `${code}: ${detail}` : detail;
    }
  } catch {
    /* not JSON */
  }
  return `HTTP ${res.status}`;
}

async function liveGet<T>(path: string, params?: Record<string, string>): Promise<OpsResult<T>> {
  try {
    const qs = params ? `?${new URLSearchParams(params).toString()}` : '';
    const res = await fetch(`${LIVE_BASE}${path}${qs}`, { headers: authHeaders() });
    if (!res.ok) return { ok: false, error: await readProblem(res) };
    return { ok: true, data: (await res.json()) as T };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

async function liveWrite<T>(method: 'POST' | 'PUT', path: string, body: unknown, idempotencyKey?: string): Promise<OpsResult<T>> {
  try {
    const res = await fetch(`${LIVE_BASE}${path}`, {
      method,
      headers: { ...authHeaders(), 'Idempotency-Key': idempotencyKey ?? newIdempotencyKey() },
      body: JSON.stringify(body),
    });
    if (!res.ok) return { ok: false, error: await readProblem(res) };
    return { ok: true, data: (await res.json()) as T };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

// ─── VIEW-04: lines & operators ─────────────────────────────────────────────────
export async function listLines(): Promise<OpsResult<Page<Line>>> {
  if (MODE === 'live') return liveGet<Page<Line>>('/lines');
  return { ok: true, data: { items: mock.lines } };
}

export async function createLine(lineCode: string): Promise<OpsResult<Line>> {
  if (!lineCode.trim()) return { ok: false, error: 'Kode line wajib diisi.' };
  if (MODE === 'live') return liveWrite<Line>('POST', '/lines', { lineCode });
  const line: Line = { id: uuid(), lineCode: lineCode.trim(), active: true };
  mock.lines = [...mock.lines, line];
  return { ok: true, data: line };
}

export async function listOperators(): Promise<OpsResult<Page<Operator>>> {
  if (MODE === 'live') return liveGet<Page<Operator>>('/operators');
  return { ok: true, data: { items: mock.operators } };
}

export async function createOperator(displayName: string, employeeCode: string): Promise<OpsResult<Operator>> {
  if (!displayName.trim() || !employeeCode.trim()) return { ok: false, error: 'Nama dan kode karyawan wajib diisi.' };
  if (MODE === 'live') return liveWrite<Operator>('POST', '/operators', { displayName, employeeCode });
  const operator: Operator = { id: uuid(), displayName: displayName.trim(), employeeCode: employeeCode.trim(), active: true };
  mock.operators = [...mock.operators, operator];
  return { ok: true, data: operator };
}

// ─── VIEW-04: assignments ───────────────────────────────────────────────────────
export async function listAssignments(): Promise<OpsResult<Page<Assignment>>> {
  if (MODE === 'live') return liveGet<Page<Assignment>>('/assignments');
  return { ok: true, data: { items: mock.assignments } };
}

export async function assignOperator(lineId: string, req: {
  operatorId: string; componentCode: string; validFrom: string; validThrough: string;
  stationNumber?: number;
}): Promise<OpsResult<Assignment>> {
  if (!lineId || !req.operatorId) return { ok: false, error: 'Line dan operator wajib dipilih.' };
  if (!req.componentCode.trim()) return { ok: false, error: 'Kode komponen wajib diisi.' };
  if (MODE === 'live') return liveWrite<Assignment>('PUT', `/lines/${lineId}/operators`, req);
  const assignment: Assignment = { id: uuid(), lineId, ...req, componentCode: req.componentCode.trim() };
  mock.assignments = [...mock.assignments, assignment];
  return { ok: true, data: assignment };
}

// ─── VIEW-04: 30-minute tally ───────────────────────────────────────────────────
export async function recordSewingTally(input: TallyInput): Promise<OpsResult<TallyResult>> {
  if (!input.pieces || input.pieces < 1) return { ok: false, error: 'Jumlah pieces harus lebih dari 0.' };
  if (!input.componentCode.trim()) return { ok: false, error: 'Kode komponen wajib diisi.' };
  if (MODE === 'live') return liveWrite<TallyResult>('POST', '/sewing-tallies', input, input.idempotencyKey);

  // Replay-safety: return existing recorded result if same idempotency key is submitted
  if (input.idempotencyKey && mockIdempotency.has(input.idempotencyKey)) {
    return { ok: true, data: mockIdempotency.get(input.idempotencyKey)! };
  }

  const result: TallyResult = {
    tallyId: uuid(),
    status: 'RECORDED',
    createdUnitIds: Array.from({ length: input.pieces }, () => uuid()),
  };
  mock.tallies.set(result.tallyId, result);
  if (input.idempotencyKey) {
    mockIdempotency.set(input.idempotencyKey, result);
  }

  const existing = mock.progress.find(p => p.orderId === input.orderId && p.componentCode === input.componentCode);
  if (existing) {
    existing.quantity = { value: String(Number(existing.quantity.value) + input.pieces), unit: 'PIECE' };
  } else {
    mock.progress = [...mock.progress, {
      orderId: input.orderId, componentCode: input.componentCode,
      quantity: { value: String(input.pieces), unit: 'PIECE' }, status: 'MENUNGGU_QC',
    }];
  }
  return { ok: true, data: result };
}

export async function verifySewingTally(
  tallyId: string, decision: 'APPROVE' | 'REJECT', reason?: string,
): Promise<OpsResult<TallyResult>> {
  if (MODE === 'live') return liveWrite<TallyResult>('POST', `/sewing-tallies/${tallyId}/verification`, { decision, reason });
  const stored = mock.tallies.get(tallyId);
  if (!stored) return { ok: false, error: 'Tally tidak ditemukan.' };
  const verified: TallyResult = { ...stored, status: 'VERIFIED' };
  mock.tallies.set(tallyId, verified);
  return { ok: true, data: verified };
}

// ─── VIEW-04/05: assemblies ─────────────────────────────────────────────────────
export async function listAssemblies(status?: AssemblyStatus): Promise<OpsResult<Page<Assembly>>> {
  if (MODE === 'live') return liveGet<Page<Assembly>>('/assemblies', status ? { status } : undefined);
  const items = status ? mock.assemblies.filter(a => a.status === status) : mock.assemblies;
  return { ok: true, data: { items } };
}

export async function createAssembly(req: {
  orderId: string; serialCode: string; componentUnitIds: string[];
}): Promise<OpsResult<Assembly>> {
  if (!req.orderId) return { ok: false, error: 'Order wajib dipilih.' };
  if (!req.serialCode.trim()) return { ok: false, error: 'Serial code wajib diisi.' };
  if (req.componentUnitIds.length === 0) return { ok: false, error: 'Minimal satu unit komponen diperlukan.' };
  if (MODE === 'live') return liveWrite<Assembly>('POST', '/assemblies', req);
  const assembly: Assembly = { id: uuid(), ...req, serialCode: req.serialCode.trim(), status: 'MENUNGGU_QC' };
  mock.assemblies = [...mock.assemblies, assembly];
  return { ok: true, data: assembly };
}

export async function listProductionProgress(): Promise<OpsResult<Page<ProgressItem>>> {
  if (MODE === 'live') return liveGet<Page<ProgressItem>>('/production/progress');
  return { ok: true, data: { items: mock.progress } };
}

// ─── VIEW-05: QC inspection ─────────────────────────────────────────────────────
export async function inspectUnit(req: QcRequest): Promise<OpsResult<QcInspection>> {
  if (req.disposition !== 'PASS' && req.defects.length === 0) {
    return { ok: false, error: 'Disposisi REPAIR/REJECT wajib menyertakan minimal satu defect.' };
  }
  if (MODE === 'live') return liveWrite<QcInspection>('POST', '/qc-inspections', req);

  const assembly = mock.assemblies.find(a => a.id === req.assemblyId);
  if (!assembly) return { ok: false, error: 'Assembly tidak ditemukan.' };
  assembly.status =
    req.disposition === 'PASS' ? 'QC_PASS' : req.disposition === 'REPAIR' ? 'REWORK' : 'REJECT_SCRAP';
  const inspection: QcInspection = { id: uuid(), ...req };
  mock.inspections = [...mock.inspections, inspection];
  return { ok: true, data: inspection };
}

/** Mock-only helper so the UI can show the QC queue without a contract list op. */
export function listMockInspections(): QcInspection[] {
  return mock.inspections;
}
