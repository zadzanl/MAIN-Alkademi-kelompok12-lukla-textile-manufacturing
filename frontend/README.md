# Lukla Frontend & E2E Test Harness

This package hosts the frontend workspace and browser verification harness for the Lukla Operations Engine.

## Test Harness (Independent Mock UI Verification)

The initial E2E test suite targets standalone UI interactions in `prototypes/design-mocks/lukla-ui-mock.html` completely independently of unfinished backend services.

### Test Coverage
- `UI-PROTO-VIEW03-MISMATCH-MODAL` (Closing Scenario 1 / FR-6.2): Verifies the cross-client material issuance rejection modal and dismissal controls.
- `UI-PROTO-VIEW04-TALLY-STEPPER` (View 04 / FR-7.3): Verifies 30-minute production interval tally stepper increments, decrements, and lower-bound enforcement.

### Running Tests

From `frontend/`:
```bash
# Run Playwright tests
node ../node_modules/@playwright/test/cli.js test

# Normalize evidence bundle into results.json and manifest.json
python ../tools/collect_evidence.py
```

### Evidence Artifacts
All test results are normalized into `frontend/artifacts/evidence/` according to `openspec/changes/lukla-ops-engine-planning/16-test-harness-and-agent-verification.md` §4:
- `results.xml`: JUnit-compatible test result XML.
- `results.json`: Normalized evidence bundle with contract SHA256 and test statuses.
- `manifest.json`: Verification manifest with file hashes and tooling metadata.
