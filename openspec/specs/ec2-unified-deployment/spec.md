# ec2-unified-deployment Specification

## Purpose
TBD - created by archiving change ec2-unified-deployment. Update Purpose after archive.
## Requirements
### Requirement: Single-Port Unified Ingress on Port 3000
The system SHALL host all user interfaces, interactive API documentation, and REST endpoints on a single ASGI process binding to `0.0.0.0:3000`, conforming to the AWS Security Group constraint permitting only ports 80 and 3000.

#### Scenario: Evaluator accesses root URL for health and portal discovery
- **GIVEN** the unified FastAPI server running on `0.0.0.0:3000`
- **WHEN** an evaluator or script performs `GET /` or `curl -I http://localhost:3000`
- **THEN** the system returns HTTP 200 OK
- **AND** the response body contains an interactive HTML operations portal linking to `/copilot`, `/sampling/`, `/ui`, and `/docs`

#### Scenario: Browser navigates to Sampling & Spec R&D without separate Node process
- **GIVEN** the pre-bundled frontend assets located in `prototypes/sampling-spec-rnd/frontend/dist`
- **WHEN** a user navigates to `http://<IP>:3000/sampling/` in their web browser
- **THEN** FastAPI serves `index.html` and associated CSS/JS bundles with status HTTP 200
- **AND** client-side API requests route to relative endpoints `/api/sampling-spec-rnd/*` and `/api/auth/*` on the same host and port without CORS preflight failures

#### Scenario: Dual-`src` namespace isolation between payroll and sampling engines
- **GIVEN** `backend/app/api/v1/payroll.py` has loaded modules under `sys.modules['src']` from `backend/payroll-costing/src`
- **WHEN** `backend/app/main.py` imports routes from `prototypes/sampling-spec-rnd/backend/src`
- **THEN** the application temporarily stashes existing `src.*` modules from `sys.modules`
- **AND** imports `create_api_router` and `create_auth_router` from the sampling directory
- **AND** restores the stashed payroll modules to `sys.modules`
- **AND** both payroll calculation models and sampling routes function concurrently in memory

