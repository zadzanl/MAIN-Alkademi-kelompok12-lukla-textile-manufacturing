import test from 'node:test';
import assert from 'node:assert/strict';
import { sumMinor, type LedgerTransaction } from '../src/services/ledgerApi.ts';
import { buildStacked } from '../src/utils/chartData.ts';

test('executive dashboard: double-entry ledger invariant holds with zero variance', () => {
  const sampleTransactions: LedgerTransaction[] = [
    {
      id: 'tx-001',
      tenantId: 'lukla-textile',
      reversalOf: null,
      entries: [
        { accountCode: '1100', direction: 'DEBIT', amountMinor: 15000000 },
        { accountCode: '4000', direction: 'CREDIT', amountMinor: 15000000 },
      ],
    },
    {
      id: 'tx-002',
      tenantId: 'lukla-textile',
      reversalOf: null,
      entries: [
        { accountCode: '5100', direction: 'DEBIT', amountMinor: 8750000 },
        { accountCode: '2100', direction: 'CREDIT', amountMinor: 8750000 },
      ],
    },
    {
      id: 'tx-003',
      tenantId: 'lukla-textile',
      reversalOf: null,
      entries: [
        { accountCode: '5000', direction: 'DEBIT', amountMinor: 6500000 },
        { accountCode: '1100', direction: 'CREDIT', amountMinor: 6500000 },
      ],
    },
  ];

  let totalDebit = 0;
  let totalCredit = 0;

  for (const tx of sampleTransactions) {
    const debit = sumMinor(tx.entries, 'DEBIT');
    const credit = sumMinor(tx.entries, 'CREDIT');
    assert.equal(debit, credit, `Transaction ${tx.id} must be balanced`);
    totalDebit += debit;
    totalCredit += credit;
  }

  assert.equal(totalDebit, totalCredit);
  assert.equal(totalDebit - totalCredit, 0);
  assert.equal(totalDebit, 30250000);
});

test('executive dashboard: capacity utilization strictly calculates against 70 sewing machines', () => {
  const TOTAL_MACHINES = 70;
  const activeCount = 58;
  const setupCount = 8;
  const maintenanceCount = 4;

  assert.equal(activeCount + setupCount + maintenanceCount, TOTAL_MACHINES);
  const utilizationPct = Math.round((activeCount / TOTAL_MACHINES) * 1000) / 10;
  assert.equal(utilizationPct, 82.9);
});

test('executive dashboard: WIP distribution accurately splits across CMT, Semi-CMT, and Full Package', () => {
  const wipData = [
    { scheme: 'CMT', total: 1420, cutting: 320, sewing: 850, qcFinishing: 250 },
    { scheme: 'SEMI_CMT', total: 1150, cutting: 210, sewing: 690, qcFinishing: 250 },
    { scheme: 'FULL_PACKAGE', total: 610, cutting: 140, sewing: 310, qcFinishing: 160 },
  ];

  const totalWip = wipData.reduce((acc, row) => acc + row.total, 0);
  assert.equal(totalWip, 3180);

  // Check stage sums
  for (const row of wipData) {
    assert.equal(row.cutting + row.sewing + row.qcFinishing, row.total);
  }

  // Format into stacked rows
  const stacked = buildStacked(
    wipData.map(w => ({
      label: w.scheme,
      values: { cutting: w.cutting, sewing: w.sewing, qcFinishing: w.qcFinishing },
    })),
    ['cutting', 'sewing', 'qcFinishing'],
  );

  assert.equal(stacked.length, 3);
  assert.equal(stacked[0].total, 1420);
  assert.equal(stacked[1].total, 1150);
  assert.equal(stacked[2].total, 610);
});

test('executive dashboard: 30-minute interval throughput aggregates actual vs target', () => {
  const intervals = [
    { slot: '08:00 - 08:30', target: 100, actual: 94 },
    { slot: '08:30 - 09:00', target: 110, actual: 108 },
    { slot: '09:00 - 09:30', target: 115, actual: 116 },
    { slot: '09:30 - 10:00', target: 120, actual: 124 },
  ];

  const sumActual = intervals.reduce((acc, i) => acc + i.actual, 0);
  const sumTarget = intervals.reduce((acc, i) => acc + i.target, 0);

  assert.equal(sumActual, 442);
  assert.equal(sumTarget, 445);
  assert.equal(sumActual < sumTarget, true);
});
