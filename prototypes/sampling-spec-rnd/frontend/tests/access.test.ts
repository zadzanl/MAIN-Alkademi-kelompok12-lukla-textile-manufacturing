/**
 * Contract tests for services/access.ts — the frontend authorization boundary.
 *
 * Pins exact canonical role membership, the view matrix, and landing views so
 * alias-valued sessions cannot silently regain access (DEF-002).
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ASSIGNABLE_ROLES,
  CANONICAL_ROLES,
  allowedViewsForRole,
  isKnownRole,
  landingViewForRole,
  navKeyForRole,
  roleLabel,
} from '../src/services/access.ts';

const sorted = (values: Iterable<string>) => [...values].sort();

test('CANONICAL_ROLES is exactly the nine session roles', () => {
  assert.deepEqual(
    [...CANONICAL_ROLES],
    ['admin', 'Owner', 'Sample', 'Warehouse', 'Mandor', 'Tailor', 'QCInspector', 'FinancePayroll', 'client'],
  );
});

test('ASSIGNABLE_ROLES is exactly the eight non-client roles', () => {
  assert.deepEqual(
    [...ASSIGNABLE_ROLES],
    ['admin', 'Owner', 'Sample', 'Warehouse', 'Mandor', 'Tailor', 'QCInspector', 'FinancePayroll'],
  );
});

test('isKnownRole accepts every canonical role', () => {
  for (const role of CANONICAL_ROLES) {
    assert.equal(isKnownRole(role), true, `${role} must be a known role`);
  }
});

test('isKnownRole rejects roleless values', () => {
  assert.equal(isKnownRole(undefined), false);
  assert.equal(isKnownRole(null), false);
  assert.equal(isKnownRole(''), false);
});

test('isKnownRole rejects aliases and legacy values', () => {
  const aliases = [
    'qc',
    'qc_inspector',
    'finance',
    'finance_payroll',
    'owner',
    'sample',
    'tim_sample',
    'warehouse',
    'gudang',
    'mandor',
    'kepala_produksi',
    'tailor',
    'penjahit',
    'rnd_operator',
    'employee',
  ];
  for (const alias of aliases) {
    assert.equal(isKnownRole(alias), false, `${alias} must NOT be a known role`);
  }
});

test('allowedViewsForRole returns the exact matrix per canonical role', () => {
  assert.equal(allowedViewsForRole('admin'), 'all');

  const expected: Record<string, string[]> = {
    client: ['sample-versions', 'production', 'warehouse'],
    QCInspector: ['quality', 'production', 'spec-list'],
    FinancePayroll: ['payroll', 'reports', 'ledger', 'overview'],
    Owner: ['overview', 'reports', 'ledger', 'payroll', 'warehouse', 'spec-versions'],
    Sample: [
      'sample-versions',
      'stopwatch',
      'active-studies',
      'time-studies',
      'study-list',
      'spec-versions',
      'spec-list',
      'drift-analysis',
    ],
    Warehouse: ['warehouse'],
    Mandor: ['production', 'spec-list', 'active-studies'],
    Tailor: ['production'],
  };

  for (const [role, views] of Object.entries(expected)) {
    const actual = allowedViewsForRole(role);
    assert.notEqual(actual, 'all', `${role} must not have all views`);
    assert.deepEqual(
      sorted(actual as ReadonlySet<string>),
      sorted([...views, 'settings', 'copilot']),
      `${role} view set mismatch`,
    );
  }
});

test('every known role can reach settings and copilot (shared views)', () => {
  for (const role of CANONICAL_ROLES) {
    const actual = allowedViewsForRole(role);
    if (actual === 'all') continue;
    assert.equal(actual.has('settings'), true, `${role} must reach settings`);
    assert.equal(actual.has('copilot'), true, `${role} must reach copilot`);
  }
});

test('allowedViewsForRole limits roleless and unknown roles to settings and copilot', () => {
  for (const role of [undefined, null, '', 'rnd_operator', 'qc']) {
    const actual = allowedViewsForRole(role);
    assert.notEqual(actual, 'all');
    assert.deepEqual(sorted(actual as ReadonlySet<string>), ['copilot', 'settings']);
  }
});

test('landingViewForRole returns the exact landing view per canonical role', () => {
  const expected: Record<string, string> = {
    admin: 'overview',
    client: 'sample-versions',
    QCInspector: 'quality',
    FinancePayroll: 'payroll',
    Owner: 'overview',
    Sample: 'sample-versions',
    Warehouse: 'warehouse',
    Mandor: 'production',
    Tailor: 'production',
  };
  for (const [role, view] of Object.entries(expected)) {
    assert.equal(landingViewForRole(role), view, `${role} landing mismatch`);
  }
});

test('landingViewForRole sends roleless and unknown roles to settings', () => {
  for (const role of [undefined, null, '', 'rnd_operator', 'owner']) {
    assert.equal(landingViewForRole(role), 'settings');
  }
});

test('navKeyForRole maps canonical roles and returns null for roleless', () => {
  assert.equal(navKeyForRole('admin'), 'admin');
  assert.equal(navKeyForRole('client'), 'client');
  assert.equal(navKeyForRole('QCInspector'), 'qc');
  assert.equal(navKeyForRole('FinancePayroll'), 'finance');
  assert.equal(navKeyForRole('Owner'), 'owner');
  assert.equal(navKeyForRole('Sample'), 'sample');
  assert.equal(navKeyForRole('Warehouse'), 'warehouse');
  assert.equal(navKeyForRole('Mandor'), 'mandor');
  assert.equal(navKeyForRole('Tailor'), 'tailor');
  assert.equal(navKeyForRole(undefined), null);
  assert.equal(navKeyForRole('qc'), null);
});

test('roleLabel returns human labels and echoes unknown roles', () => {
  assert.equal(roleLabel('QCInspector'), 'QC Inspector');
  assert.equal(roleLabel('FinancePayroll'), 'Finance & Payroll');
  assert.equal(roleLabel('admin'), 'Admin IT');
  assert.equal(roleLabel('mystery'), 'mystery');
});
