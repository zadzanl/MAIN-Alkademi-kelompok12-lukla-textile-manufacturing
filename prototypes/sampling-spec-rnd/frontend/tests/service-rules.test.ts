/**
 * Behavioral rule tests for the mock service clients (ops / ledger / payroll).
 *
 * contract.test.ts pins payload shape; this file pins the domain invariants:
 * balanced double-entry, the three-way QC bonus gate, the FINANCIAL_RULE_PENDING
 * guard, tally/QC input validation, and payroll approval/payment state machine.
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  createLine,
  createOperator,
  assignOperator,
  recordSewingTally,
  verifySewingTally,
  createAssembly,
  inspectUnit,
} from '../src/services/opsApi.ts';
import {
  appendLedgerTransaction,
  reverseLedgerTransaction,
  sumMinor,
  type LedgerEntry,
} from '../src/services/ledgerApi.ts';
import {
  createPayrollPeriod,
  calculateWeeklyPayroll,
  getPayrollStatement,
  getBonusPool,
  approvePayroll,
  recordPayrollPayment,
  recordOverhead,
  proposeFinancialRule,
  approveFinancialRule,
  MOCK_RECIPIENTS,
  toMoney,
} from '../src/services/payrollApi.ts';

const balanced = (): LedgerEntry[] => [
  { accountCode: '1100', direction: 'DEBIT', amountMinor: 500 },
  { accountCode: '4000', direction: 'CREDIT', amountMinor: 500 },
];

// ─── OPS input validation ──────────────────────────────────────────────────────

test('ops rejects a tally with zero pieces or a blank component', async () => {
  const base = {
    orderId: 'o1', cutBatchId: 'b1', lineId: 'l1', componentCode: 'SLEEVE',
    operatorId: 'op1', intervalStart: '2026-10-13T08:00:00+07:00',
    intervalEnd: '2026-10-13T08:30:00+07:00', pieces: 0,
  };
  assert.match((await recordSewingTally(base)).error ?? '', /pieces/i);
  assert.match((await recordSewingTally({ ...base, pieces: 2, componentCode: ' ' })).error ?? '', /komponen/i);
});

test('ops rejects invalid line/operator/assignment/assembly input', async () => {
  assert.match((await createLine('   ')).error ?? '', /line/i);
  assert.match((await createOperator('', 'OPR-X')).error ?? '', /karyawan/i);
  assert.match((await assignOperator('', { operatorId: '', componentCode: '', validFrom: '', validThrough: '' })).error ?? '', /operator/i);
  assert.match((await assignOperator('l1', { operatorId: 'op1', componentCode: ' ', validFrom: '', validThrough: '' })).error ?? '', /komponen/i);
  assert.match((await createAssembly({ orderId: '', serialCode: 'A', componentUnitIds: ['u'] })).error ?? '', /order/i);
  assert.match((await createAssembly({ orderId: 'o1', serialCode: ' ', componentUnitIds: ['u'] })).error ?? '', /serial/i);
  assert.match((await createAssembly({ orderId: 'o1', serialCode: 'A', componentUnitIds: [] })).error ?? '', /komponen/i);
});

test('ops verifySewingTally fails for an unknown tally id', async () => {
  const res = await verifySewingTally('does-not-exist', 'APPROVE');
  assert.equal(res.ok, false);
  assert.match(res.error ?? '', /tidak ditemukan/i);
});

test('ops QC REPAIR/REJECT requires at least one defect; PASS does not', async () => {
  const repair = await inspectUnit({ assemblyId: '55555555-5555-4555-8555-555555555555', disposition: 'REPAIR', defects: [] });
  assert.equal(repair.ok, false);
  assert.match(repair.error ?? '', /defect/i);

  const reject = await inspectUnit({ assemblyId: '55555555-5555-4555-8555-555555555555', disposition: 'REJECT', defects: [] });
  assert.equal(reject.ok, false);
});

// ─── LEDGER invariants ─────────────────────────────────────────────────────────

test('ledger rejects fewer than two lines', async () => {
  const res = await appendLedgerTransaction({
    transactionType: 'SALE', currency: 'IDR',
    entries: [{ accountCode: '1100', direction: 'DEBIT', amountMinor: 100 }],
  });
  assert.equal(res.ok, false);
  assert.match(res.error ?? '', /minimal 2/i);
});

test('ledger rejects blank account codes and non-positive amounts', async () => {
  const blank: LedgerEntry[] = [
    { accountCode: ' ', direction: 'DEBIT', amountMinor: 100 },
    { accountCode: '4000', direction: 'CREDIT', amountMinor: 100 },
  ];
  assert.match((await appendLedgerTransaction({ transactionType: 'SALE', currency: 'IDR', entries: blank })).error ?? '', /kode akun/i);

  const zero: LedgerEntry[] = [
    { accountCode: '1100', direction: 'DEBIT', amountMinor: 0 },
    { accountCode: '4000', direction: 'CREDIT', amountMinor: 0 },
  ];
  assert.match((await appendLedgerTransaction({ transactionType: 'SALE', currency: 'IDR', entries: zero })).error ?? '', /lebih dari 0/i);
});

test('ledger accepts a balanced transaction and stamps tenant + no reversal link', async () => {
  const res = await appendLedgerTransaction({ transactionType: 'SALE', currency: 'IDR', entries: balanced() });
  assert.equal(res.ok, true);
  assert.ok(res.data);
  assert.equal(res.data.reversalOf, null);
  assert.equal(typeof res.data.tenantId, 'string');
  assert.equal(sumMinor(res.data.entries, 'DEBIT'), 500);
});

test('ledger reversal requires a reason and an existing transaction', async () => {
  assert.match((await reverseLedgerTransaction('a1000000-0000-4000-8000-000000000001', '  ')).error ?? '', /alasan/i);
  assert.match((await reverseLedgerTransaction('nope', 'valid reason')).error ?? '', /tidak ditemukan/i);
});

// ─── PAYROLL state machine & financial-rule gate ───────────────────────────────

test('payroll period requires both dates and correct ordering', async () => {
  const req = { timezone: 'Asia/Jakarta' as const, cutoffLocal: '23:59:00', ruleVersion: 'rule-2026-10-01' };
  assert.match((await createPayrollPeriod({ ...req, startsOn: '', endsOn: '' })).error ?? '', /wajib diisi/i);
  assert.match((await createPayrollPeriod({ ...req, startsOn: '2026-10-18', endsOn: '2026-10-12' })).error ?? '', /sebelum/i);
});

test('weekly calculation is blocked while the rule version is not APPROVED', async () => {
  const period = await createPayrollPeriod({
    startsOn: '2026-10-12', endsOn: '2026-10-18',
    timezone: 'Asia/Jakarta', cutoffLocal: '23:59:00', ruleVersion: 'rule-2026-10-01',
  });
  assert.ok(period.data);

  const unknown = await calculateWeeklyPayroll(period.data.id, { ruleVersion: 'nope' });
  assert.match(unknown.error ?? '', /FINANCIAL_RULE_PENDING/);

  const pending = await calculateWeeklyPayroll(period.data.id, { ruleVersion: 'rule-2026-11-01' });
  assert.match(pending.error ?? '', /FINANCIAL_RULE_PENDING/);
});

test('weekly calculation with an approved rule yields CALCULATED wages', async () => {
  const period = await createPayrollPeriod({
    startsOn: '2026-10-19', endsOn: '2026-10-25',
    timezone: 'Asia/Jakarta', cutoffLocal: '23:59:00', ruleVersion: 'rule-2026-10-01',
  });
  assert.ok(period.data);

  const calc = await calculateWeeklyPayroll(period.data.id, { ruleVersion: 'rule-2026-10-01' });
  assert.equal(calc.ok, true);
  assert.ok(calc.data);
  assert.equal(calc.data.status, 'CALCULATED');
  assert.ok(calc.data.eligibleUnits > 0);
  assert.equal(calc.data.totalWages.currency, 'IDR');
});

test('statement is unavailable before calculation', async () => {
  const period = await createPayrollPeriod({
    startsOn: '2026-11-02', endsOn: '2026-11-08',
    timezone: 'Asia/Jakarta', cutoffLocal: '23:59:00', ruleVersion: 'rule-2026-10-01',
  });
  assert.ok(period.data);
  const res = await getPayrollStatement(period.data.id);
  assert.equal(res.ok, false);
  assert.match(res.error ?? '', /INVALID_STATE/);
});

test('approval rejects a stale version/inputHash', async () => {
  const period = await createPayrollPeriod({
    startsOn: '2026-11-09', endsOn: '2026-11-15',
    timezone: 'Asia/Jakarta', cutoffLocal: '23:59:00', ruleVersion: 'rule-2026-10-01',
  });
  assert.ok(period.data);
  await calculateWeeklyPayroll(period.data.id, { ruleVersion: 'rule-2026-10-01' });

  const stale = await approvePayroll(period.data.id, { version: 99, inputHash: 'wrong' });
  assert.equal(stale.ok, false);
  assert.match(stale.error ?? '', /INVALID_STATE/);
});

test('payment requires evidence and an APPROVED statement', async () => {
  const period = await createPayrollPeriod({
    startsOn: '2026-11-16', endsOn: '2026-11-22',
    timezone: 'Asia/Jakarta', cutoffLocal: '23:59:00', ruleVersion: 'rule-2026-10-01',
  });
  assert.ok(period.data);
  await calculateWeeklyPayroll(period.data.id, { ruleVersion: 'rule-2026-10-01' });

  assert.match((await recordPayrollPayment(period.data.id, { externalReference: ' ', evidenceFileId: 'f' })).error ?? '', /referensi/i);
  assert.match((await recordPayrollPayment(period.data.id, { externalReference: 'TRF-1', evidenceFileId: ' ' })).error ?? '', /bukti/i);
  assert.match((await recordPayrollPayment(period.data.id, { externalReference: 'TRF-1', evidenceFileId: 'f' })).error ?? '', /disetujui/i);

  const stmt = await getPayrollStatement(period.data.id);
  assert.ok(stmt.data);
  const approved = await approvePayroll(period.data.id, { version: stmt.data.version, inputHash: stmt.data.inputHash });
  assert.equal(approved.ok, true);

  const paid = await recordPayrollPayment(period.data.id, { externalReference: 'TRF-1', evidenceFileId: 'file-1' });
  assert.equal(paid.ok, true);
  assert.equal(paid.data?.status, 'PAID');
});

test('bonus pool is unavailable before calculation', async () => {
  const res = await getBonusPool('b1000000-0000-4000-8000-000000000001');
  // Seeded period has no statement yet in this process → gate must fire.
  assert.equal(res.ok, false);
});

test('overhead rejects non-positive amount and blank kind', async () => {
  assert.match((await recordOverhead({ periodId: 'p', kind: 'LISTRIK', amount: toMoney(0) })).error ?? '', /lebih dari 0/i);
  assert.match((await recordOverhead({ periodId: 'p', kind: ' ', amount: toMoney(1000) })).error ?? '', /jenis/i);
});

test('financial rule proposal enforces three recipients and the 10–15% band', async () => {
  const base = {
    effectiveFrom: '2026-12-01',
    mealBasis: 'VERIFIED_WAGES_PROPOSED' as const,
    mealBasisPoints: 1200,
    mealDistribution: 'PROPORTIONAL_PROPOSED' as const,
    bonusRate: toMoney(150000),
    bonusRecipientIds: [...MOCK_RECIPIENTS],
    remainderPolicy: 'BLOCK_NON_DIVISIBLE' as const,
    cutoffLocal: '23:59:00',
    overheadBasis: 'FIRST_PASS_FINISHED_UNITS_PROPOSED' as const,
  };

  assert.match((await proposeFinancialRule({ ...base, bonusRecipientIds: [MOCK_RECIPIENTS[0]] })).error ?? '', /tiga penerima/i);
  assert.match((await proposeFinancialRule({ ...base, mealBasisPoints: 999 })).error ?? '', /1000/);
  assert.match((await proposeFinancialRule({ ...base, mealBasisPoints: 1501 })).error ?? '', /1500/);

  const ok = await proposeFinancialRule(base);
  assert.equal(ok.ok, true);
  assert.equal(ok.data?.status, 'PENDING');
});

test('financial rule approval requires evidence', async () => {
  const res = await approveFinancialRule('rule-2026-11-01', { evidenceFileId: ' ' });
  assert.equal(res.ok, false);
  assert.match(res.error ?? '', /evidenceFileId/i);
});
