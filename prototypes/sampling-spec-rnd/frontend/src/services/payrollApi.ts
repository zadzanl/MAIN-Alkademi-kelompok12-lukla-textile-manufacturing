/**
 * Payroll & Costing API client — Lukla Operations Engine (MOD-05, VIEW-06).
 *
 * Contract source of truth:
 *   openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml
 *   backend/payroll-costing/API_CONTRACTS.md
 *   POST /payroll-periods                         createPayrollPeriod
 *   GET  /payroll-periods                         listPayrollPeriods
 *   POST /payroll/weekly/{periodId}               calculateWeeklyPayroll   (409 FINANCIAL_RULE_PENDING)
 *   GET  /payroll/weekly/{periodId}/statement     getPayrollStatement
 *   GET  /payroll/weekly/{periodId}/bonus-pool    getBonusPool
 *   POST /payroll/weekly/{periodId}/approval      approvePayroll
 *   POST /payroll/weekly/{periodId}/payment       recordPayrollPayment
 *   POST /overhead                                recordOverhead
 *   POST /overhead/{periodId}/allocation          calculateOverhead
 *   GET  /financial-rules                         listFinancialRules
 *   POST /financial-rules                         proposeFinancialRule
 *   POST /financial-rules/{ruleId}/approval       approveFinancialRule
 *
 * KNOWN CEILING (deliberate): the payroll HTTP layer is not implemented yet in
 * backend/payroll-costing (see that module's README). This client therefore runs
 * in MOCK mode by default, but every request/response shape is kept identical to
 * the frozen contract so that flipping to the real service needs no UI change.
 * Reuses the shared finance flag: set VITE_LEDGER_MODE=live plus
 * VITE_LEDGER_API_URL / VITE_LEDGER_TOKEN to hit the real service.
 */
import { DATA_MODE as MODE, LEDGER_BASE as LIVE_BASE, LEDGER_TOKEN as LIVE_TOKEN } from './config';

export type Currency = 'IDR' | 'USD';
export interface Money { amountMinor: number; currency: Currency; }

export type PeriodStatus = 'OPEN' | 'CALCULATED' | 'PENDING_RULE' | 'APPROVED' | 'PAID';
export type RuleStatus = 'PENDING' | 'APPROVED';

export interface PeriodRequest {
  startsOn: string;          // date
  endsOn: string;            // date
  timezone: 'Asia/Jakarta';
  cutoffLocal: string;       // HH:MM:00
  ruleVersion: string;
}
export interface Period extends PeriodRequest { id: string; }

export interface PayrollResult {
  periodId: string;
  status: 'CALCULATED' | 'NO_OUTPUT' | 'PENDING_RULE';
  eligibleUnits: number;
  totalWages: Money;
}
export interface BonusRecipient { recipientId: string; amount: Money; }
export interface BonusPool {
  periodId: string;
  pool: Money;
  recipients: BonusRecipient[];
  status: string;
}
export interface PayrollItem {
  recipientId: string;
  base: Money;
  meal: Money;
  bonus: Money;
}
export interface PayrollStatement {
  periodId: string;
  version: number;
  inputHash: string;
  status: PeriodStatus;
  items: PayrollItem[];
  reserve: Money;
}
export interface PayrollApproval { version: number; inputHash: string; }
export interface PaymentEvidence { externalReference: string; evidenceFileId: string; }

export interface OverheadRequest { periodId: string; kind: string; amount: Money; }
export interface OverheadEvent extends OverheadRequest { id: string; }
export interface OverheadAllocation {
  periodId: string;
  status: 'ALLOCATED' | 'NO_OUTPUT';
  amountPerUnit?: Money;
}

export interface FinancialRuleFields {
  effectiveFrom: string;
  mealBasis: 'VERIFIED_WAGES_PROPOSED';
  mealBasisPoints: number;                 // 1000..1500 (10%..15%)
  mealDistribution: 'PROPORTIONAL_PROPOSED' | 'EQUAL_ACTIVE_PROPOSED';
  bonusRate: Money;
  bonusRecipientIds: string[];             // exactly three
  remainderPolicy: 'BLOCK_NON_DIVISIBLE' | 'RESERVE_PROPOSED';
  cutoffLocal: string;
  overheadBasis: 'FIRST_PASS_FINISHED_UNITS_PROPOSED';
}
export type FinancialRuleRequest = FinancialRuleFields;
export interface FinancialRule extends FinancialRuleFields { id: string; status: RuleStatus; }
export interface FinancialRuleApproval {
  evidenceFileId: string;
  approvalReference?: string;
  note?: string;
}
export interface RuleRequest { ruleVersion: string; }

export interface Page<T> { items: T[]; }
export interface PayrollResultEnvelope<T> { ok: boolean; data?: T; error?: string; }

const CURRENCY: Currency = 'IDR';

export const isMockPayroll = MODE === 'mock';

// ─── Helpers ──────────────────────────────────────────────────────────────────
function uuid(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function idempotencyKey(): string {
  return uuid().replace(/-/g, '');
}

const money = (amountMinor: number, currency: Currency = CURRENCY): Money => ({ amountMinor, currency });

function hash(input: string): string {
  let h = 0;
  for (let i = 0; i < input.length; i++) h = (Math.imul(31, h) + input.charCodeAt(i)) | 0;
  return `h${(h >>> 0).toString(16).padStart(8, '0')}`;
}

// ─── Mock store ────────────────────────────────────────────────────────────────
const RECIPIENTS = [
  'aaaaaaaa-0000-4000-8000-000000000001',
  'aaaaaaaa-0000-4000-8000-000000000002',
  'aaaaaaaa-0000-4000-8000-000000000003',
];

const mock = {
  periods: [] as Period[],
  statements: new Map<string, PayrollStatement>(),
  bonusPools: new Map<string, BonusPool>(),
  overheads: [] as OverheadEvent[],
  rules: [] as FinancialRule[],
};

function seed() {
  mock.periods = [{
    id: 'b1000000-0000-4000-8000-000000000001',
    startsOn: '2026-10-05',
    endsOn: '2026-10-11',
    timezone: 'Asia/Jakarta',
    cutoffLocal: '23:59:00',
    ruleVersion: 'rule-2026-10-01',
  }];

  mock.rules = [
    {
      id: 'rule-2026-10-01',
      status: 'APPROVED',
      effectiveFrom: '2026-10-01',
      mealBasis: 'VERIFIED_WAGES_PROPOSED',
      mealBasisPoints: 1200,
      mealDistribution: 'PROPORTIONAL_PROPOSED',
      bonusRate: money(150000),
      bonusRecipientIds: [...RECIPIENTS],
      remainderPolicy: 'BLOCK_NON_DIVISIBLE',
      cutoffLocal: '23:59:00',
      overheadBasis: 'FIRST_PASS_FINISHED_UNITS_PROPOSED',
    },
    {
      id: 'rule-2026-11-01',
      status: 'PENDING',
      effectiveFrom: '2026-11-01',
      mealBasis: 'VERIFIED_WAGES_PROPOSED',
      mealBasisPoints: 1500,
      mealDistribution: 'EQUAL_ACTIVE_PROPOSED',
      bonusRate: money(200000),
      bonusRecipientIds: [...RECIPIENTS],
      remainderPolicy: 'RESERVE_PROPOSED',
      cutoffLocal: '23:59:00',
      overheadBasis: 'FIRST_PASS_FINISHED_UNITS_PROPOSED',
    },
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

async function liveGet<T>(path: string): Promise<PayrollResultEnvelope<T>> {
  try {
    const res = await fetch(`${LIVE_BASE}${path}`, { headers: authHeaders() });
    if (!res.ok) return { ok: false, error: await readProblem(res) };
    return { ok: true, data: (await res.json()) as T };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

async function livePost<T>(path: string, body: unknown): Promise<PayrollResultEnvelope<T>> {
  try {
    const res = await fetch(`${LIVE_BASE}${path}`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Idempotency-Key': idempotencyKey() },
      body: JSON.stringify(body),
    });
    if (!res.ok) return { ok: false, error: await readProblem(res) };
    return { ok: true, data: (await res.json()) as T };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

// ─── Periods ──────────────────────────────────────────────────────────────────
export async function listPayrollPeriods(): Promise<PayrollResultEnvelope<Page<Period>>> {
  if (MODE === 'live') return liveGet<Page<Period>>('/payroll-periods');
  return { ok: true, data: { items: [...mock.periods] } };
}

export async function createPayrollPeriod(req: PeriodRequest): Promise<PayrollResultEnvelope<Period>> {
  if (!req.startsOn || !req.endsOn) return { ok: false, error: 'Tanggal mulai dan selesai wajib diisi.' };
  if (req.endsOn < req.startsOn) return { ok: false, error: 'Tanggal selesai tidak boleh sebelum tanggal mulai.' };
  if (MODE === 'live') return livePost<Period>('/payroll-periods', req);
  const period: Period = { id: uuid(), ...req };
  mock.periods = [period, ...mock.periods];
  return { ok: true, data: period };
}

// ─── Weekly calculation & statement ────────────────────────────────────────────
export async function calculateWeeklyPayroll(
  periodId: string, req: RuleRequest,
): Promise<PayrollResultEnvelope<PayrollResult>> {
  if (MODE === 'live') return livePost<PayrollResult>(`/payroll/weekly/${periodId}`, req);

  const period = mock.periods.find(p => p.id === periodId);
  if (!period) return { ok: false, error: 'INVALID_STATE: periode tidak ditemukan.' };
  const rule = mock.rules.find(r => r.id === req.ruleVersion);
  if (!rule) return { ok: false, error: `FINANCIAL_RULE_PENDING: versi aturan ${req.ruleVersion} tidak ditemukan.` };
  if (rule.status !== 'APPROVED') {
    return { ok: false, error: `FINANCIAL_RULE_PENDING: aturan ${req.ruleVersion} belum disetujui.` };
  }

  const eligibleUnits = 128;
  const basePerUnit = 250000;                                   // IDR 2.500 / unit (minor)
  const baseTotal = eligibleUnits * basePerUnit;
  const mealTotal = Math.round((baseTotal * rule.mealBasisPoints) / 10000);
  const bonusPoolTotal = rule.bonusRate.amountMinor * eligibleUnits;

  // Split totals across the three recipients; first recipient absorbs the remainder.
  const split = (total: number): number[] => {
    const per = Math.floor(total / RECIPIENTS.length);
    const first = total - per * (RECIPIENTS.length - 1);
    return [first, per, per];
  };
  const bases = split(baseTotal);
  const meals = split(mealTotal);
  const bonuses = split(bonusPoolTotal);

  const statement: PayrollStatement = {
    periodId,
    version: 1,
    inputHash: hash(`${periodId}:${rule.id}:${eligibleUnits}:${baseTotal}`),
    status: 'CALCULATED',
    items: RECIPIENTS.map((recipientId, i) => ({
      recipientId,
      base: money(bases[i]),
      meal: money(meals[i]),
      bonus: money(bonuses[i]),
    })),
    reserve: money(0),
  };
  mock.statements.set(periodId, statement);
  mock.bonusPools.set(periodId, {
    periodId,
    pool: money(bonusPoolTotal),
    recipients: RECIPIENTS.map((recipientId, i) => ({ recipientId, amount: money(bonuses[i]) })),
    status: 'OPEN',
  });

  return {
    ok: true,
    data: {
      periodId,
      status: 'CALCULATED',
      eligibleUnits,
      totalWages: money(baseTotal + mealTotal),
    },
  };
}

export async function getPayrollStatement(periodId: string): Promise<PayrollResultEnvelope<PayrollStatement>> {
  if (MODE === 'live') return liveGet<PayrollStatement>(`/payroll/weekly/${periodId}/statement`);
  const stmt = mock.statements.get(periodId);
  if (!stmt) return { ok: false, error: 'INVALID_STATE: statement belum dihitung untuk periode ini.' };
  return { ok: true, data: stmt };
}

export async function getBonusPool(periodId: string): Promise<PayrollResultEnvelope<BonusPool>> {
  if (MODE === 'live') return liveGet<BonusPool>(`/payroll/weekly/${periodId}/bonus-pool`);
  const pool = mock.bonusPools.get(periodId);
  if (!pool) return { ok: false, error: 'FINANCIAL_RULE_PENDING: bonus pool belum tersedia untuk periode ini.' };
  const rule = mock.rules.find(r => r.id === mock.periods.find(p => p.id === periodId)?.ruleVersion);
  if (rule?.remainderPolicy === 'BLOCK_NON_DIVISIBLE' && pool.pool.amountMinor % RECIPIENTS.length !== 0) {
    return { ok: false, error: 'FINANCIAL_RULE_PENDING: pool tidak habis dibagi tiga (BLOCK_NON_DIVISIBLE).' };
  }
  return { ok: true, data: pool };
}

export async function approvePayroll(
  periodId: string, req: PayrollApproval,
): Promise<PayrollResultEnvelope<PayrollStatement>> {
  if (MODE === 'live') return livePost<PayrollStatement>(`/payroll/weekly/${periodId}/approval`, req);
  const stmt = mock.statements.get(periodId);
  if (!stmt) return { ok: false, error: 'INVALID_STATE: statement belum dihitung.' };
  if (stmt.version !== req.version || stmt.inputHash !== req.inputHash) {
    return { ok: false, error: 'INVALID_STATE: versi/inputHash tidak cocok dengan statement terakhir.' };
  }
  stmt.status = 'APPROVED';
  return { ok: true, data: stmt };
}

export async function recordPayrollPayment(
  periodId: string, req: PaymentEvidence,
): Promise<PayrollResultEnvelope<PayrollStatement>> {
  if (!req.externalReference.trim()) return { ok: false, error: 'Referensi pembayaran eksternal wajib diisi.' };
  if (!req.evidenceFileId.trim()) return { ok: false, error: 'Bukti pembayaran (evidenceFileId) wajib diisi.' };
  if (MODE === 'live') return livePost<PayrollStatement>(`/payroll/weekly/${periodId}/payment`, req);
  const stmt = mock.statements.get(periodId);
  if (!stmt) return { ok: false, error: 'INVALID_STATE: statement belum dihitung.' };
  if (stmt.status !== 'APPROVED') return { ok: false, error: 'INVALID_STATE: hanya run yang disetujui dapat dibayar.' };
  stmt.status = 'PAID';
  return { ok: true, data: stmt };
}

// ─── Overhead ─────────────────────────────────────────────────────────────────
export async function recordOverhead(req: OverheadRequest): Promise<PayrollResultEnvelope<OverheadEvent>> {
  if (req.amount.amountMinor <= 0) return { ok: false, error: 'Nominal overhead harus lebih dari 0.' };
  if (!req.kind.trim()) return { ok: false, error: 'Jenis overhead wajib diisi.' };
  if (MODE === 'live') return livePost<OverheadEvent>('/overhead', req);
  const event: OverheadEvent = { id: uuid(), ...req };
  mock.overheads = [event, ...mock.overheads];
  return { ok: true, data: event };
}

export async function calculateOverhead(
  periodId: string, req: RuleRequest,
): Promise<PayrollResultEnvelope<OverheadAllocation>> {
  if (MODE === 'live') return livePost<OverheadAllocation>(`/overhead/${periodId}/allocation`, req);
  const rule = mock.rules.find(r => r.id === req.ruleVersion);
  if (!rule || rule.status !== 'APPROVED') {
    return { ok: false, error: `FINANCIAL_RULE_PENDING: aturan ${req.ruleVersion} belum disetujui.` };
  }
  const stmt = mock.statements.get(periodId);
  if (!stmt || stmt.items.length === 0) {
    return { ok: true, data: { periodId, status: 'NO_OUTPUT' } };
  }
  const totalOverhead = mock.overheads
    .filter(o => o.periodId === periodId)
    .reduce((sum, o) => sum + o.amount.amountMinor, 0);
  if (totalOverhead <= 0) return { ok: true, data: { periodId, status: 'NO_OUTPUT' } };
  return {
    ok: true,
    data: { periodId, status: 'ALLOCATED', amountPerUnit: money(Math.round(totalOverhead / 128)) },
  };
}

// ─── Financial rules ──────────────────────────────────────────────────────────
export async function listFinancialRules(): Promise<PayrollResultEnvelope<Page<FinancialRule>>> {
  if (MODE === 'live') return liveGet<Page<FinancialRule>>('/financial-rules');
  return { ok: true, data: { items: [...mock.rules] } };
}

export async function proposeFinancialRule(
  req: FinancialRuleRequest,
): Promise<PayrollResultEnvelope<FinancialRule>> {
  if (req.bonusRecipientIds.length !== 3) {
    return { ok: false, error: 'Aturan bonus wajib menunjuk tepat tiga penerima.' };
  }
  if (req.mealBasisPoints < 1000 || req.mealBasisPoints > 1500) {
    return { ok: false, error: 'mealBasisPoints harus antara 1000 dan 1500 (10%–15%).' };
  }
  if (MODE === 'live') return livePost<FinancialRule>('/financial-rules', req);
  const rule: FinancialRule = { id: `rule-${req.effectiveFrom}`, status: 'PENDING', ...req };
  mock.rules = [rule, ...mock.rules];
  return { ok: true, data: rule };
}

export async function approveFinancialRule(
  ruleId: string, req: FinancialRuleApproval,
): Promise<PayrollResultEnvelope<FinancialRule>> {
  if (!req.evidenceFileId.trim()) return { ok: false, error: 'evidenceFileId wajib diisi untuk approval.' };
  if (MODE === 'live') return livePost<FinancialRule>(`/financial-rules/${ruleId}/approval`, req);
  const rule = mock.rules.find(r => r.id === ruleId);
  if (!rule) return { ok: false, error: 'Aturan tidak ditemukan.' };
  rule.status = 'APPROVED';
  return { ok: true, data: rule };
}

export { RECIPIENTS as MOCK_RECIPIENTS, money as toMoney };
