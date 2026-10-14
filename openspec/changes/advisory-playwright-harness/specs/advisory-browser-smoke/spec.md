## ADDED Requirements

### Requirement: Advisory browser smoke
The prototype SHALL provide one read-only Playwright Chromium smoke test that loads the frontend through the configured frontend service and verifies the backend connection state through the rendered UI.

#### Scenario: Dashboard reaches a healthy backend
- **WHEN** the frontend and backend services are started using the harness configuration
- **THEN** the test loads the dashboard, finds the main application heading, and observes the `Connected` status

#### Scenario: Smoke test does not mutate application state
- **WHEN** the smoke test completes successfully or fails
- **THEN** it has performed no workflow creation, start, sample, completion, or other write operation

#### Scenario: Existing application defect prevents rendering
- **WHEN** an existing missing import or runtime defect prevents the dashboard from loading
- **THEN** the smoke SHALL fail with a nonzero test exit and available diagnostics without skipping assertions, mocking the application, repairing the feature, or claiming successful E2E verification

### Requirement: Advisory CI execution
The browser smoke job SHALL run on relevant prototype changes, preserve failure diagnostics, and SHALL NOT block a pull request when the smoke fails.

#### Scenario: Browser smoke fails in CI
- **WHEN** the Playwright test exits unsuccessfully
- **THEN** the job remains non-blocking, the failure is visible in the workflow result, and available Playwright reports, screenshots, or traces are uploaded

#### Scenario: Browser smoke passes in CI
- **WHEN** the configured Chromium smoke exits successfully
- **THEN** the job reports success without changing or replacing existing quality jobs
