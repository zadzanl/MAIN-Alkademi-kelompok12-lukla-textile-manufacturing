/**
 * Contract conformance tests for the mock clients whose live HTTP service is not
 * wired yet (ops / ledger / payroll). Each assertion pins the payload shape and
 * enum values the frozen contract promises, so a mock/live drift is caught here
 * instead of in the UI once the real service lands.
 *
 * Source of truth: openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  isMockOps,
  createLine,
  createOperator,
  recordSewingTally,
  listAssemblies,
  listProductionProgress,
  inspectUnit,
  type AssemblyStatus,
} from '../src/services/opsApi.ts';
import {
  isMockLedger,
  getLedgerEntries,
  appendLedgerTransaction,
  reverseLedgerTransaction,
  sumMinor,
  type LedgerEntry,
} from '../src/services/ledgerApi.ts';
import {
  isMockPayroll,
  listPayrollPeriods,
  listFinancialRules,
  calculateWeeklyPayroll,
  getPayrollStatement,
  type PeriodStatus,
  type RuleStatus,
} from '../src/services/payrollApi.ts';

// ─── OPS (VIEW-04 / VIEW-05) ───────────────────────────────────────────────────

test('ops client defaults to mock mode', () => {
  assert.equal(isMockOps, true);
});

test('ops createLine returns the contract Line shape', async () => {
  const res = await createLine('LINE-TEST');
  assert.equal(res.ok, true);
  assert.ok(res.data);
  assert.equal(res.data.lineCode, 'LINE-TEST');
  assert.equal(res.data.active, true);
  assert.equal(typeof res.data.id, 'string');
});

test('ops createOperator returns the contract Operator shape', async () => {
  const res = await createOperator('Test Operator', 'OPR-TEST');
  assert.equal(res.ok, true);
  assert.ok(res.data);
  assert.equal(res.data.displayName, 'Test Operator');
  assert.equal(res.data.employeeCode, 'OPR-TEST');
  assert.equal(res.data.active, true);
});

test('ops recordSewingTally returns RECORDED with one unit per piece', async () => {
  const res = await recordSewingTally({
    orderId: 'order-1',
    cutBatchId: 'batch-1',
    lineId: 'line-1',
    componentCode: 'SLEEVE',
    operatorId: 'op-1',
    intervalStart: '2026-10-13T08:00:00+07:00',
    intervalEnd: '2026-10-13T08:30:00+07:00',
    pieces: 3,
  });
  assert.equal(res.ok, true);
  assert.ok(res.data);
  assert.equal(res.data.status, 'RECORDED');
  assert.equal(res.data.createdUnitIds.length, 3);
  assert.equal(typeof res.data.tallyId, 'string');
});

test('ops listAssemblies returns items with a valid AssemblyStatus', async () => {
  const valid: AssemblyStatus[] = ['MENUNGGU_QC', 'REWORK', 'QC_PASS', 'REJECT_SCRAP'];
  const res = await listAssemblies();
  assert.equal(res.ok, true);
  assert.ok(res.data);
  for (const a of res.data.items) {
    assert.ok(valid.includes(a.status), `unexpected AssemblyStatus: ${a.status}`);
    assert.equal(typeof a.serialCode, 'string');
    assert.ok(Array.isArray(a.componentUnitIds));
  }
});

test('ops listProductionProgress returns the Quantity { value, unit } shape', async () => {
  const res = await listProductionProgress();
  assert.equal(res.ok, true);
  assert.ok(res.data);
  for (const p of res.data.items) {
    assert.equal(typeof p.quantity.value, 'string');
    assert.equal(typeof p.quantity.unit, 'string');
  }
});

test('ops inspectUnit returns the contract QcInspection shape', async () => {
  const queue = await listAssemblies('MENUNGGU_QC');
  assert.ok(queue.data);
  const target = queue.data.items[0];
  assert.ok(target, 'expected a seeded assembly waiting for QC');

  const res = await inspectUnit({ assemblyId: target.id, disposition: 'PASS', defects: [] });
  assert.equal(res.ok, true);
  assert.ok(res.data);
  assert.equal(res.data.assemblyId, target.id);
  assert.equal(res.data.disposition, 'PASS');
  assert.ok(Array.isArray(res.data.defects));
  assert.equal(typeof res.data.id, 'string');
});

// ─── LEDGER ────────────────────────────────────────────────────────────────────

test('ledger client defaults to mock mode', () => {
  assert.equal(isMockLedger, true);
});

test('ledger entries carry the contract LedgerEntry shape', async () => {
  const res = await getLedgerEntries(50);
  assert.equal(res.ok, true);
  assert.ok(res.data);
  for (const tx of res.data.items) {
    assert.equal(typeof tx.id, 'string');
    assert.equal(typeof tx.tenantId, 'string');
    assert.ok(Array.isArray(tx.entries));
    for (const e of tx.entries) {
      assert.equal(typeof e.accountCode, 'string');
      assert.ok(e.direction === 'DEBIT' || e.direction === 'CREDIT');
      assert.equal(typeof e.amountMinor, 'number');
    }
  }
});

test('ledger append rejects an unbalanced transaction (contract invariant)', async () => {
  const entries: LedgerEntry[] = [
    { accountCode: '1100', direction: 'DEBIT', amountMinor: 100 },
    { accountCode: '4000', direction: 'CREDIT', amountMinor: 90 },
  ];
  const res = await appendLedgerTransaction({ transactionType: 'SALE', currency: 'IDR', entries });
  assert.equal(res.ok, false);
  assert.match(res.error ?? '', /balance/i);
});

test('ledger reversal flips directions and links reversalOf', async () => {
  const page = await getLedgerEntries(50);
  assert.ok(page.data);
  const original = page.data.items[0];
  assert.ok(original);

  const res = await reverseLedgerTransaction(original.id, 'contract test reversal');
  assert.equal(res.ok, true);
  assert.ok(res.data);
  assert.equal(res.data.reversalOf, original.id);
  assert.equal(sumMinor(res.data.entries, 'DEBIT'), sumMinor(original.entries, 'CREDIT'));
});

// ─── PAYROLL ───────────────────────────────────────────────────────────────────

test('payroll client defaults to mock mode', () => {
  assert.equal(isMockPayroll, true);
});

test('payroll periods carry the contract Period shape', async () => {
  const res = await listPayrollPeriods();
  assert.equal(res.ok, true);
  assert.ok(res.data);
  for (const p of res.data.items) {
    assert.equal(typeof p.id, 'string');
    assert.equal(p.timezone, 'Asia/Jakarta');
    assert.equal(typeof p.ruleVersion, 'string');
    assert.equal(typeof p.startsOn, 'string');
    assert.equal(typeof p.endsOn, 'string');
  }
});

test('financial rules expose the contract RuleStatus and exactly three recipients', async () => {
  const valid: RuleStatus[] = ['PENDING', 'APPROVED'];
  const res = await listFinancialRules();
  assert.equal(res.ok, true);
  assert.ok(res.data);
  for (const r of res.data.items) {
    assert.ok(valid.includes(r.status), `unexpected RuleStatus: ${r.status}`);
    assert.equal(r.bonusRecipientIds.length, 3);
  }
});

test('payroll statement items carry the Money shape', async () => {
  const periods = await listPayrollPeriods();
  assert.ok(periods.data);
  const period = periods.data.items[0];
  assert.ok(period);

  const calc = await calculateWeeklyPayroll(period.id, { ruleVersion: 'rule-2026-10-01' });
  assert.equal(calc.ok, true);

  const stmt = await getPayrollStatement(period.id);
  assert.equal(stmt.ok, true);
  assert.ok(stmt.data);

  const valid: PeriodStatus[] = ['OPEN', 'CALCULATED', 'PENDING_RULE', 'APPROVED', 'PAID'];
  assert.ok(valid.includes(stmt.data.status), `unexpected PeriodStatus: ${stmt.data.status}`);

  for (const item of stmt.data.items) {
    for (const m of [item.base, item.meal, item.bonus]) {
      assert.equal(typeof m.amountMinor, 'number');
      assert.equal(m.currency, 'IDR');
    }
  }
});
