# Tasks: Unified EC2 Cloud Deployment & Amazon Bedrock Integration

> [!IMPORTANT]
> **DEPLOYMENT ROADMAP & CURRENT STATUS:**
> Phases 1 through 4 are **100% completed, tested, and pushed to `master`**.
> Phase 5 (EC2 instance launch and Session Manager run) is held pending operator instruction.

---

## 1. Codebase Preparation & Architecture Consolidation (Phase 1 - Completed)

- [x] 1.1 **Create Root Entrypoint (`main.py`):** Export `app = FastAPI(...)` importing `backend.app.main.app`, compatible with `uvicorn main:app --host 0.0.0.0 --port 3000`.
- [x] 1.2 **Create Root Dependencies Specification (`requirements.txt`):** Specify minimum production requirements (`fastapi`, `uvicorn[standard]`, `pydantic`, `sqlalchemy`, `psycopg[binary]`, `httpx`, `python-dotenv`, `boto3`, `pyjwt`, `python-multipart`).
- [x] 1.3 **Implement Root Health & Portal Hub (`GET /` & `GET /health`):** Add responsive Tailwind landing page linking to `/copilot`, `/sampling/`, `/ui`, and `/docs`, returning HTTP 200 for health checks.
- [x] 1.4 **Mount Sampling & Spec R&D Static Frontend (`/sampling`):** Mount pre-built Vite assets using `fastapi.staticfiles.StaticFiles(directory=dist, html=True)`.
- [x] 1.5 **Isolate Dual-`src` Namespace Collision:** Implement dynamic module stashing in `backend/app/main.py` so both `payroll-costing` and `sampling-spec-rnd` backend routers load simultaneously without conflict.

## 2. Bedrock Converse Provider & Copilot Integration (Phase 2 - Completed)

- [x] 2.1 **Extend Copilot Settings (`backend/app/copilot/config.py`):** Add `"bedrock"` to `COPILOT_DEFAULT_PROVIDER` literal; add `AWS_REGION` (`us-east-1`) and `BEDROCK_MODEL_ID` (`us.amazon.nova-micro-v1:0`).
- [x] 2.2 **Implement BedrockLLMProvider (`backend/app/copilot/provider.py`):** Create provider using `boto3.client('bedrock-runtime')` Converse API wrapped in `asyncio.to_thread()`.
- [x] 2.3 **Enforce Zero-Credential IMDSv2 Auto-Auth:** Ensure no access keys or secrets are passed to `boto3`; rely entirely on EC2 instance IAM role metadata.
- [x] 2.4 **Map Bedrock Error Payloads to RFC 7807:** Translate `AccessDeniedException` to HTTP 403, model errors to HTTP 400, and provider timeouts to HTTP 504.
- [x] 2.5 **Update Provider Factory:** Ensure `get_llm_provider("bedrock")` returns `BedrockLLMProvider`.

## 3. Automation Scripts & Quality Gates (Phase 3 - Completed)

- [x] 3.1 **Create DB Schema Migration Runner (`scripts/init_ec2_db.py`):** Sequentially execute migrations `001` through `013` idempotently against PostgreSQL `myappdb`.
- [x] 3.2 **Create Single-Command EC2 Deployment Script (`scripts/deploy_ec2.sh`):** Automate PostgreSQL 15 installation, database initialization, virtual environment creation, pip install, `.env` generation, migration execution, and background process spawning.
- [x] 3.3 **Pre-Build Production Frontend Bundle:** Compile `prototypes/sampling-spec-rnd/frontend` into `dist/` with relative API routing (`/api/sampling-spec-rnd` and `/api/auth`) and force-add to git.
- [x] 3.4 **Validate Copilot Test Suite:** Add Bedrock Converse unit test to `backend/tests/test_copilot_api.py`. Confirm 16/16 tests pass (`python -m pytest backend/tests/test_copilot_api.py`).
- [x] 3.5 **Update Workspace Hygiene Validator (`scripts/check_workspace_hygiene.py`):** Whitelist `main.py` and `requirements.txt` in root; confirm zero hygiene violations.

## 4. Git Push & Mainline Alignment (Phase 4 - Completed)

- [x] 4.1 **Stage and Commit Changes:** Commit 28 modified and added files with conventional commit message `feat(ec2): prepare unified deployment with Bedrock provider, root entrypoint, and automated setup`.
- [x] 4.2 **Push to Mainline:** Push directly to `origin/master`. Remote branch updated to commit `d4e56b2`.

## 5. Cloud Provisioning & Live Verification (Phase 5 - On Hold / Ready to Trigger)

- [ ] 5.1 **Launch EC2 Instance:** Run `aws ec2 run-instances --launch-template LaunchTemplateId=lt-00e4f5effa1c630ad --tag-specifications "ResourceType=instance,Tags=[{Key=Owner,Value=student_12}]" --region ap-southeast-1`.
- [ ] 5.2 **Await Instance Health Checks:** Monitor status until state is `Running` and System/Instance status checks reach `2/2 passed`.
- [ ] 5.3 **Execute Deployment in Session Manager:** Connect via AWS Console Session Manager and execute:
  ```bash
  sudo su - ec2-user
  git clone https://github.com/zadzanl/MAIN-Alkademi-kelompok12-lukla-textile-manufacturing.git
  cd MAIN-Alkademi-kelompok12-lukla-textile-manufacturing
  chmod +x scripts/deploy_ec2.sh
  ./scripts/deploy_ec2.sh
  ```
- [ ] 5.4 **Browser & Bedrock Ingestion Verification:** Verify public IP responses on:
  - `http://<IP>:3000/` (200 OK)
  - `http://<IP>:3000/copilot` (Inquire *"Berapa stok kain fleece?"* and verify Bedrock reply)
  - `http://<IP>:3000/sampling/` (Verify Time Study dashboard renders)
- [ ] 5.5 **Submit Deployment Details:** Submit Group Name, EC2 IP, and Port 3000 to `https://forms.gle/v6wZutpAhr8r9v4B7`.
