import test from 'node:test';
import assert from 'node:assert/strict';
import { buildPareto, buildStacked, buildWaterfall } from '../src/utils/chartData.ts';

test('buildPareto ranks descending and computes cumulative share', () => {
  const points = buildPareto([
    { label: 'Broken Stitch', value: 5 },
    { label: 'Puckering', value: 3 },
    { label: 'Uneven Seam', value: 2 },
  ]);
  assert.equal(points.length, 3);
  assert.deepEqual(points.map(p => p.label), ['Broken Stitch', 'Puckering', 'Uneven Seam']);
  assert.equal(points[0].sharePct, 50);
  assert.equal(points[0].cumulativePct, 50);
  assert.equal(points[1].cumulativePct, 80);
  assert.equal(points[2].cumulativePct, 100);
});

test('buildPareto drops non-positive categories and handles empty/zero input', () => {
  assert.deepEqual(buildPareto([]), []);
  assert.deepEqual(buildPareto([{ label: 'A', value: 0 }]), []);
  const points = buildPareto([
    { label: 'A', value: 4 },
    { label: 'B', value: -2 },
    { label: 'C', value: 0 },
  ]);
  assert.deepEqual(points.map(p => p.label), ['A']);
  assert.equal(points[0].cumulativePct, 100);
});

test('buildPareto is stable on ties (label order) and survives bad input', () => {
  const tied = buildPareto([
    { label: 'Zeta', value: 1 },
    { label: 'Alpha', value: 1 },
  ]);
  assert.deepEqual(tied.map(p => p.label), ['Alpha', 'Zeta']);
  // @ts-expect-error deliberate malformed input for the defensive guard
  assert.deepEqual(buildPareto(null), []);
});

test('buildStacked sums known keys and zero-fills missing ones', () => {
  const rows = buildStacked(
    [
      { label: 'SLEEVE', values: { QC_PASS: 10, REWORK: 2 } },
      { label: 'COLLAR', values: { QC_PASS: 5 } },
    ],
    ['QC_PASS', 'REWORK', 'REJECT_SCRAP'],
  );
  assert.equal(rows.length, 2);
  assert.equal(rows[0].total, 12);
  assert.equal(rows[0].segments.REJECT_SCRAP, 0);
  assert.equal(rows[1].total, 5);
});

test('buildStacked ignores unknown keys and non-finite values', () => {
  const rows = buildStacked(
    [{ label: 'X', values: { QC_PASS: Number.NaN, GHOST: 9 } }],
    ['QC_PASS'],
  );
  assert.equal(rows[0].segments.QC_PASS, 0);
  assert.equal(rows[0].total, 0);
  assert.equal('GHOST' in rows[0].segments, false);
});

test('buildWaterfall chains deltas and anchors totals at zero', () => {
  const bars = buildWaterfall([
    { label: 'Base', delta: 320000 },
    { label: 'Meal', delta: 38400 },
    { label: 'Bonus', delta: 19200000 },
    { label: 'Total', delta: 19558400, kind: 'total' },
  ]);
  assert.equal(bars[0].start, 0);
  assert.equal(bars[0].end, 320000);
  assert.equal(bars[1].start, 320000);
  assert.equal(bars[1].end, 358400);
  assert.equal(bars[2].end, 19558400);
  assert.equal(bars[3].kind, 'total');
  assert.equal(bars[3].start, 0);
  assert.equal(bars[3].end, 19558400);
});

test('buildWaterfall handles negative deltas and empty input', () => {
  const bars = buildWaterfall([
    { label: 'A', delta: 100 },
    { label: 'Refund', delta: -40 },
  ]);
  assert.equal(bars[1].start, 100);
  assert.equal(bars[1].end, 60);
  assert.deepEqual(buildWaterfall([]), []);
});
