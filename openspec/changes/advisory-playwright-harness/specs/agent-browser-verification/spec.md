## ADDED Requirements

### Requirement: Interactive browser tool preference
Agents performing pre-commit verification SHALL prefer an available interactive browser tool for manual browser inspection when the change affects user-visible web behavior.

#### Scenario: Interactive browser tool is available
- **WHEN** the agent can open and inspect a browser page through its environment
- **THEN** it performs the relevant manual smoke interaction and records the tool/environment used

#### Scenario: Interactive browser tool is unavailable
- **WHEN** the agent cannot access an interactive browser tool
- **THEN** it runs the automated Playwright smoke command if the harness is available and records interactive inspection as unavailable

### Requirement: Honest browser evidence
Agents SHALL distinguish interactive browser inspection from automated Playwright execution and SHALL mark browser verification unverified when neither is available.

#### Scenario: Automated fallback is used
- **WHEN** an agent lacks an interactive browser tool but Playwright completes
- **THEN** the report states that automated Playwright evidence was collected and that interactive inspection was not performed

#### Scenario: No browser harness is available
- **WHEN** neither an interactive browser tool nor the automated Playwright harness can run
- **THEN** the report marks browser verification as unverified and does not claim equivalent coverage from an API-only request
