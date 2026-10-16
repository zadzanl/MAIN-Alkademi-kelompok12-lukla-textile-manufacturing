# Retrospective: Unified EC2 Cloud Deployment & Amazon Bedrock Integration

> **Change ID:** `ec2-unified-deployment`  
> **Author:** Solutions Architecture Pairing Agent  
> **Date:** October 16, 2026  
> **Status:** Code Implemented & Pushed (Mainline Commit `d4e56b2`); Cloud Provisioning Held on Standby

---

## 1. Executive Summary

The objective of this initiative was to prepare the Lukla Operations Engine repository for production cloud deployment to an AWS EC2 instance conforming strictly to the Alkademi Hackathon evaluation guide (`Deploy aplikasi ke EC2.pdf`). 

The primary challenge was architectural consolidation: the repository contained distinct services (FastAPI core backend, Vite React sampling prototype, standalone payroll engine, and zero-build HTML copilot widgets) developed across multiple sprints, while the deployment environment allowed only a single open port (port 3000) and operated under tight hardware ceilings (1 GB RAM `t3.micro`).

All preparation, provider integration, frontend pre-bundling, database migration scripting, and automated deployment tooling were completed, tested, and pushed directly to `origin/master`. Physical server provisioning (Step 5) was paused per explicit maintainer directive.

---

## 2. Root Cause Analysis: Critical Obstacles Overcome

### 2.1 The Single-Port Constraint (Port 3000 / 80)
- **The Problem:** The Alkademi EC2 template security group (`sg-0ee4f83cd129e794a`) only opens ports 80 and 3000 to the public internet (`0.0.0.0/0`). In local development, the Sampling & Spec R&D frontend runs on port 3009, its backend runs on port 8009, and the core ERP backend runs on port 8000. If deployed as separate services, the frontend would be unable to connect to the backend because port 8000/8009 is blocked by the AWS firewall.
- **Root Cause:** Decentralized microservice prototyping during early hackathon sprints without a centralized reverse-proxy or unified ingress configuration.
- **Solution:** Unified all platform services into a single ASGI FastAPI application hosted on port 3000. Pre-bundled the React SPA into static assets mounted at `/sampling/`, mounted the core API at `/api/v1/`, mounted sampling endpoints at `/api/sampling-spec-rnd/`, and created an operations portal at `/` that immediately returns HTTP 200 for health checks.

### 2.2 The 1 GB RAM Out-Of-Memory (OOM) Trap
- **The Problem:** Slide 9 and 13 of the hackathon guide explicitly caution that running `npm run build` or Docker builds on 1 GB RAM triggers process crashes (`Killed`).
- **Root Cause:** Node.js TypeScript compilers (`tsc && vite build`) require peak memory allocations of 600 MB–1.2 GB, exceeding physical RAM and causing the Linux kernel to invoke `oom-killer`.
- **Solution:** 
  1. Built the React frontend locally on the development workstation with production environment variables (`VITE_API_URL=/api/sampling-spec-rnd`).
  2. Force-tracked the pre-built `prototypes/sampling-spec-rnd/frontend/dist/` in git.
  3. Ensured the EC2 setup script relies on the 2 GB swapfile provisioned in the template's user-data. The EC2 server never runs Node.js or `npm build`.

### 2.3 The Dual-`src` Python Package Namespace Collision
- **The Problem:** When attempting to import the Sampling & Spec R&D router (`from src.api.routes import create_api_router`) within `backend/app/main.py`, Python raised:
  `ModuleNotFoundError: No module named 'src.api.routes'`.
- **Root Cause:** Both `backend/payroll-costing` and `prototypes/sampling-spec-rnd/backend` used an unnamespaced top-level `src/` directory. Because `backend/app/api/v1/payroll.py` imported from `payroll-costing` first, Python cached `<module 'src' from 'backend/payroll-costing/src/__init__.py'>` in `sys.modules['src']`. Subsequent imports of `src.api.routes` looked inside `payroll-costing/src`, where no `api` module exists.
- **Solution:** Implemented dynamic module stashing in `backend/app/main.py`:
  ```python
  _stashed_src = {k: sys.modules.pop(k) for k in list(sys.modules.keys()) if k == "src" or k.startswith("src.")}
  _old_path = list(sys.path)
  sys.path.insert(0, _sampling_backend_dir)
  try:
      from src.api.routes import create_api_router as create_sampling_router
      from src.api.auth_routes import create_auth_router
      app.include_router(create_sampling_router())
      app.include_router(create_auth_router())
  finally:
      sys.path[:] = _old_path
      sys.modules.update(_stashed_src)
  ```
  Both sub-engines now coexist in memory without requiring invasive refactoring of their internal relative imports.

### 2.4 Cross-Region AWS Bedrock Routing
- **The Problem:** The EC2 Launch Template (`main-ec2-template`) is provisioned in `ap-southeast-1` (Singapore), but the hackathon mentor instructions specify calling Bedrock in `us-east-1` (N. Virginia) using model ID `us.amazon.nova-micro-v1:0`. A naive boto3 client without region override defaults to the instance's local region (`ap-southeast-1`), where student model access is not provisioned.
- **Solution:** Explicitly configured `AWS_REGION=us-east-1` in `CopilotSettings` and initialized the boto3 Bedrock Runtime client with `region_name="us-east-1"`. Credentials automatically inherit from the instance IAM role via IMDSv2, satisfying the "no secret keys in code or `.env`" requirement.

---

## 3. Decisions & Tradeoffs Register

| Decision | Selected Option | Rejected Alternative | Rationale |
|---|---|---|---|
| **Frontend Serving Strategy** | Serve pre-built SPA via FastAPI `StaticFiles` on port 3000 | Run Vite dev server on port 3009 with Nginx reverse proxy | Nginx adds an extra process, configuration drift, and manual setup; FastAPI static files requires zero extra processes. |
| **Frontend Build Location** | Build on workstation, commit `dist/` | Build on EC2 during deployment | 1 GB RAM instance crashes during `npm run build`; workstation build is fast (6.9s) and 100% reliable. |
| **Bedrock API Interface** | Boto3 Bedrock Runtime `converse` API | Legacy `invoke_model` API | `converse` natively handles multi-turn conversation formatting, system prompts, tool schemas, and structured error payloads across Nova and Claude models. |
| **Database Migrations** | Standalone Python runner (`scripts/init_ec2_db.py`) | Alembic migrations framework | Repo uses sequential raw SQL migrations (001–013); a minimal Python script has zero extra dependencies and matches existing team patterns. |

---

## 4. Verification & Audit Trail

| Verification Item | Command / Test | Result |
|---|---|---|
| **Copilot & Bedrock Unit Tests** | `python -m pytest backend/tests/test_copilot_api.py` | ✅ 16 passed in 2.19s |
| **Workspace Hygiene Check** | `python scripts/check_workspace_hygiene.py` | ✅ Passed (0 violations) |
| **Root Entrypoint Import** | `python -c "import main; print(len(main.app.routes))"` | ✅ 15 core routes + 44 prototype routes mounted |
| **AWS CLI Identity** | `aws sts get-caller-identity` | ✅ Authenticated as `student_12` (Account 820242904049) |
| **EC2 Launch Template Audit** | `aws ec2 describe-launch-templates --region ap-southeast-1` | ✅ Found `main-ec2-template` (`lt-00e4f5effa1c630ad`) |
| **EC2 RunInstances Dry-Run** | `aws ec2 run-instances ... --dry-run` | ✅ Request succeeded (DryRunOperation verified) |
| **Git Mainline Sync** | `git push origin master` | ✅ Mainline updated to commit `d4e56b2` |
| **Live EC2 Launch (Step 5)** | Physical instance launch | ⏸️ **HELD** pending maintainer instruction |

---

## 5. Upgrade Path & Next Steps

When the operator authorizes physical cloud deployment:
1. Trigger Step 5 via the provided AWS CLI run-instance command.
2. Connect to the instance terminal via AWS Console Session Manager.
3. Execute `./scripts/deploy_ec2.sh`.
4. Capture the public IPv4 and submit it to `https://forms.gle/v6wZutpAhr8r9v4B7`.
