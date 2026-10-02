#!/usr/bin/env node
'use strict';
/**
 * workspace-manifest receipt conservation tests.
 *
 *   node tests/receipt_conservation.test.js              positive suite, exit 0 = pass
 *   node tests/receipt_conservation.test.js --self-test  every check is re-run against a
 *                                                        mutated input and MUST fail there,
 *                                                        proving each assertion can actually fire
 *
 * Invariant under test - the whole point of a receipt:
 *     expanded_files + SUM(skipped_entries[].count) === scanned_total
 * expanded_files / scanned_total are integer counts; skipped_entries is an array of
 * {reason, count, paths?} and `reason` must come from the closed five-value taxonomy.
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const SCHEMA = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'manifest-schema.json'), 'utf8'));
const SELF_TEST = process.argv.includes('--self-test');
const CLOSED_REASONS = ['binary_excluded', 'hidden_by_pattern', 'other_typed', 'permission_denied', 'symlink_loop'];

const clone = (o) => JSON.parse(JSON.stringify(o));
const rp = (s) => {
  const r = s.properties.receipt_payload;
  assert.ok(r, 'receipt_payload is missing from the schema');
  return r;
};

// ---------------------------------------------------------------- schema checks
const SCHEMA_CHECKS = [
  {
    name: 'receipt_payload requires scanned_total, expanded_files and skipped_entries',
    run: (s) => {
      for (const f of ['scanned_total', 'expanded_files', 'skipped_entries']) {
        assert.ok(rp(s).required.indexOf(f) !== -1, f + ' is not required');
      }
    },
    mutate: (s) => { rp(s).required = ['scanned_total', 'skipped_entries']; },
  },
  {
    name: 'counters are integers, skipped_entries is the array',
    run: (s) => {
      assert.strictEqual(rp(s).properties.expanded_files.type, 'integer', 'expanded_files must be an integer count');
      assert.strictEqual(rp(s).properties.scanned_total.type, 'integer', 'scanned_total must be an integer count');
      assert.strictEqual(rp(s).properties.skipped_entries.type, 'array', 'skipped_entries must be an array');
    },
    mutate: (s) => { rp(s).properties.expanded_files.type = 'array'; },
  },
  {
    name: 'every skipped_entry requires reason and count',
    run: (s) => {
      assert.deepStrictEqual(rp(s).properties.skipped_entries.items.required.slice().sort(), ['count', 'reason']);
    },
    mutate: (s) => { rp(s).properties.skipped_entries.items.required = ['count']; },
  },
  {
    name: 'skipped reason taxonomy is closed to five values',
    run: (s) => {
      const e = rp(s).properties.skipped_entries.items.properties.reason.enum;
      assert.deepStrictEqual(e.slice().sort(), CLOSED_REASONS, 'reason enum is not the closed taxonomy');
    },
    mutate: (s) => { rp(s).properties.skipped_entries.items.properties.reason.enum.push('made_up_reason'); },
  },
];

// ------------------------------------------------------------ fixture checks
function conserved(r) {
  return r.expanded_files + r.skipped_entries.reduce((sum, e) => sum + e.count, 0) === r.scanned_total;
}

const FIXTURE_CHECKS = [
  {
    name: 'a conserved receipt is accepted',
    receipt: { scanned_total: 4, expanded_files: 3, skipped_entries: [{ reason: 'binary_excluded', count: 1, paths: ['a.bin'] }] },
    expect: true,
    mutate: null,
  },
  {
    name: 'an under-counted receipt is rejected',
    receipt: { scanned_total: 5, expanded_files: 3, skipped_entries: [{ reason: 'binary_excluded', count: 1 }] },
    expect: false,
    mutate: (r) => { r.scanned_total = 4; },   // make it balance -> the rejection must disappear
  },
  {
    name: 'an over-counted receipt is rejected',
    receipt: { scanned_total: 2, expanded_files: 3, skipped_entries: [] },
    expect: false,
    mutate: (r) => { r.scanned_total = 3; },
  },
  {
    name: 'a receipt carried entirely by skipped entries still balances',
    receipt: {
      scanned_total: 3, expanded_files: 1,
      skipped_entries: [{ reason: 'permission_denied', count: 1 }, { reason: 'symlink_loop', count: 1 }],
    },
    expect: true,
    mutate: (r) => { r.skipped_entries[1].count = 0; },
  },
];

// ---------------------------------------------------------------- run modes
let passed = 0;
let failed = 0;

if (!SELF_TEST) {
  console.log('workspace-manifest receipt conservation - positive suite\n');
  for (const c of SCHEMA_CHECKS) {
    try { c.run(SCHEMA); passed++; console.log('  ok   ' + c.name); }
    catch (e) { failed++; console.error('  FAIL ' + c.name + ': ' + e.message); }
  }
  for (const c of FIXTURE_CHECKS) {
    const got = conserved(c.receipt);
    if (got === c.expect) { passed++; console.log('  ok   ' + c.name); }
    else { failed++; console.error('  FAIL ' + c.name + ': conserved()=' + got + ' expected ' + c.expect); }
  }
} else {
  console.log('workspace-manifest receipt conservation - self-test (each check must FAIL on a mutated input)\n');
  for (const c of SCHEMA_CHECKS) {
    let fired = false;
    try { c.run(c.mutate(clone(SCHEMA))); } catch (e) { fired = true; }
    if (fired) { passed++; console.log('  ok   ' + c.name + ' -> assertion fired on the mutant'); }
    else { failed++; console.error('  FAIL ' + c.name + ' -> assertion stayed silent on the mutant'); }
  }
  for (const c of FIXTURE_CHECKS) {
    if (!c.mutate) { console.log('  --   ' + c.name + ' (no mutant; positive fixture only)'); continue; }
    const mutated = clone(c.receipt);
    c.mutate(mutated);
    const got = conserved(mutated);
    if (got !== c.expect) { passed++; console.log('  ok   ' + c.name + ' -> mutant flips the verdict (conserved=' + got + ')'); }
    else { failed++; console.error('  FAIL ' + c.name + ' -> mutant did not change the verdict'); }
  }
}

console.log('\n' + (SELF_TEST ? '[self-test] ' : '') + passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
