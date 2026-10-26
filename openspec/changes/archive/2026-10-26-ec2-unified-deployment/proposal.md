# Change Proposal: Unified EC2 Cloud Deployment & Amazon Bedrock Integration

> [!IMPORTANT]
> **HANDOFF DIRECTIVE FOR DOWNSTREAM AGENTS / ENGINEERS:**
> This change formalizes the production deployment architecture of the Lukla Operations Engine to an AWS EC2 instance conforming to the Alkademi Hackathon deployment specifications (`Deploy aplikasi ke EC2.pdf`).
> Codebase preparation, Bedrock runtime provider integration, frontend bundling, and deployment scripting are **100% completed and pushed to `origin/master`**.
> Step 5 (physical EC2 instance launch) is intentionally held pending explicit operator authorization.

---

## 1. Why

The Lukla Operations Engine must be deployed to a live AWS EC2 instance provided by the hackathon organizers for mentor evaluation and grading. 

The evaluation environment introduces specific physical and architectural constraints:
1. **Single Open Port (Port 3000 / 80):** Only ports 80 and 3000 are open in the EC2 security group (`sg-0ee4f83cd129e794a`). The platform consists of multiple services (FastAPI core backend, AI Copilot, ERP UI mocks, and the Sampling & Spec R&D React frontend). Without consolidation, running frontend (port 3009) and backend (port 8000) separately would result in an unreachable backend from the public internet.
2. **Strict Hardware Ceilings (1 GB RAM / `t3.micro`):** Building modern Node.js/Vite frontends or compiling heavy dependencies on a 1 GB RAM instance triggers Linux Out-Of-Memory (OOM) process termination (`Killed`).
3. **Role-Based Amazon Bedrock Authentication:** The mentor evaluation specifically tests Bedrock generative AI inference via an attached IAM Role (`MainEC2Role`) in region `us-east-1` (model `us.amazon.nova-micro-v1:0`). Hardcoded AWS access keys or secrets in code/`.env` are explicitly forbidden and disqualify the submission.
4. **Local PostgreSQL 15 Requirement:** The instance requires a local PostgreSQL service (`myappdb` owned by `myappuser`) initialized with the core double-entry and operational schemas.

---

## 2. What Changes

- **Amazon Bedrock Runtime Provider:** Implemented `BedrockLLMProvider` in `backend/app/copilot/provider.py` using `boto3` Bedrock Converse API, targeting `us.amazon.nova-micro-v1:0` in `us-east-1`. Credentials auto-resolve via EC2 IMDSv2 without static credentials in `.env`.
- **Root Entrypoint & Requirements:** Added root `main.py` exposing `app = FastAPI(...)` and root `requirements.txt` to align 1:1 with the standard Alkademi startup command: `uvicorn main:app --host 0.0.0.0 --port 3000`.
- **Unified Single-Port Ingress Architecture:** Mounted all platform capabilities under single ASGI host on port 3000:
  - `GET /`: Clean operational portal landing page returning HTTP 200 for health checks.
  - `GET /copilot`: Interactive React 18 / Tailwind AI Copilot chat interface.
  - `GET /sampling/`: Pre-bundled Sampling & Spec R&D React 18 production app.
  - `GET /ui`: Operations Engine comprehensive ERP dashboard mock.
  - `GET /docs`: Interactive OpenAPI 3.1 Swagger UI documentation.
  - `GET /api/v1/*` & `GET /api/sampling-spec-rnd/*`: Full REST endpoints.
- **Python Namespace Collision Isolation:** Resolved dual `src/` top-level directory conflict between `backend/payroll-costing/src` and `prototypes/sampling-spec-rnd/backend/src` using dynamic module stashing during router registration.
- **Zero-OOM Static Frontend Bundling:** Pre-built the Vite React application locally and tracked production assets in `dist/`, avoiding high-memory compilation on the 1 GB EC2 server.
- **Automated EC2 Provisioning Script (`scripts/deploy_ec2.sh`):** A single idempotent bash script that configures PostgreSQL 15, initializes users, creates `.venv`, runs schema migrations, generates safe production `.env`, launches the background service, and outputs the public URL.
- **Automated Schema Migration Runner (`scripts/init_ec2_db.py`):** Applies all 9 sequential migrations (001 through 013) idempotently against `DATABASE_URL`.

---

## 3. Capabilities

### New Capabilities
- `ec2-unified-deployment`: Single-process multi-app serving architecture on port 3000 with root entrypoint and automated shell deployment.
- `bedrock-converse-provider`: Cloud generative AI provider executing read-only factory tool queries against Amazon Bedrock Nova Micro via EC2 IAM Role credentials.

### Modified Capabilities
- `operational-copilot-gateway`: Extended provider factory to recognize `COPILOT_DEFAULT_PROVIDER=bedrock` alongside `mock`, `ollama`, `openrouter`, and `openai`.

---

## 4. Impact

- **Backend:** Added root entrypoint, Bedrock provider, and static mount handlers. All existing 15 copilot unit tests and 1 newly added Bedrock converse unit test pass without regression.
- **Frontend:** Pre-built `prototypes/sampling-spec-rnd/frontend/dist` with relative API routing (`/api/sampling-spec-rnd` and `/api/auth`) eliminating CORS issues.
- **Database:** Full 9-migration schema coverage runnable via single CLI script.
- **Infrastructure:** Verified Launch Template `main-ec2-template` (`lt-00e4f5effa1c630ad`) in `ap-southeast-1` with user `student_12`. Dry-run succeeded.
