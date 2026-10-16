# Design: Unified EC2 Cloud Deployment & Amazon Bedrock Integration

> [!NOTE]
> This design documents the structural decisions, ingress routing, memory boundaries, and cloud security contracts governing the single-port EC2 deployment of Lukla Operations Engine.

---

## 1. System Topology & Ingress Architecture

Because AWS Security Group `sg-0ee4f83cd129e794a` strictly restricts inbound traffic to TCP ports 80 and 3000, all platform sub-services are unified into a single ASGI process hosted on port 3000:

```mermaid
flowchart TD
    subgraph Internet["Public Ingress (0.0.0.0/0)"]
        Browser["User Browser / Evaluator"]
        CLI["curl / Terminal Testing"]
    end

    subgraph EC2["AWS EC2 t3.micro (Amazon Linux 2023 · ap-southeast-1)"]
        SG["Security Group sg-0ee4f83cd129e794a (Port 3000 TCP)"]
        
        subgraph FastAPI["Unified ASGI Host (uvicorn main:app :3000)"]
            RootPortal["GET / (Operations Portal Hub)"]
            CopilotUI["GET /copilot (React 18 AI Chat Widget)"]
            SamplingUI["GET /sampling/* (Static Vite React Dist)"]
            DashboardUI["GET /ui (Enterprise ERP HTML Mock)"]
            DocsUI["GET /docs (OpenAPI 3.1 Swagger)"]
            
            CoreAPI["/api/v1/* (Ledger, Stock, Payroll, Telegram)"]
            SamplingAPI["/api/sampling-spec-rnd/* (Time Study, Specs)"]
            AuthAPI["/api/auth/* (Portal User Auth)"]
            
            CopilotEngine["Lukla Intelligence / Copilot Core"]
        end

        subgraph Storage["Local Services"]
            PG[("PostgreSQL 15 (127.0.0.1:5432 / myappdb)")]
            Swap["2 GiB Swapfile (/swapfile)"]
        end
        
        subgraph IMDS["Instance Metadata (IMDSv2)"]
            RoleCreds["MainEC2Role (Temporary STS Credentials)"]
        end
    end

    subgraph AWSCloud["AWS Region us-east-1"]
        Bedrock["Amazon Bedrock Runtime (us.amazon.nova-micro-v1:0)"]
    end

    Browser -->|HTTP :3000| SG
    CLI -->|HTTP :3000| SG
    SG --> FastAPI
    
    FastAPI -->|Loopback TCP 5432| PG
    FastAPI -->|IMDSv2 Token Request| RoleCreds
    CopilotEngine -->|HTTPS boto3 Converse API (us-east-1)| Bedrock
    RoleCreds -.->|Auto-authenticated STS Token| Bedrock
```

---

## 2. Ingress & Routing Table

The unified routing table in `backend/app/main.py` is structured as follows:

| Path Prefix | Handler / Component | Protocol / Type | Authentication / Access |
|---|---|---|---|
| `GET /` | `get_root_portal` | HTML (Tailwind CDN) | Public · Landing page returning 200 OK |
| `GET /health` | `health_check` | JSON `{"status":"OK"}` | Public · Liveness probe |
| `GET /copilot` | `get_copilot_page` | HTML + CDN React 18 | Public UI · Issues calls to `/api/v1/copilot/chat` |
| `GET /sampling/*` | `StaticFiles(directory=dist)` | Static SPA assets | Public static bundle (Vite React 18) |
| `GET /ui` | `get_dashboard_ui` | Standalone HTML Mock | Public UI · Mock ERP dashboard |
| `GET /docs` | Swagger UI | OpenAPI 3.1 Documentation | Interactive developer contract |
| `/api/v1/*` | `api_router` | REST (JSON / Problem) | Bearer JWT / Role-based authorization |
| `/api/sampling-spec-rnd/*` | `create_sampling_router()` | REST (33 endpoints) | In-memory + future PG storage |
| `/api/auth/*` | `create_auth_router()` | REST (11 endpoints) | Session tokens for portal users |

---

## 3. Amazon Bedrock Converse Integration Mechanics

### Credential Resolution Contract
Per Hackathon constraints (Slide 7), no AWS keys or secrets exist in the codebase or `.env`. Authentication operates through AWS standard default credential provider chain:
1. `boto3` queries local EC2 IMDSv2 (`http://169.254.169.254/latest/api/token`).
2. Fetches short-lived STS credentials for attached IAM Role `MainEC2Role`.
3. Boto3 signs outbound requests with AWS Signature Version 4.

### Cross-Region Routing
While the EC2 instance resides in AWS Region `ap-southeast-1` (Singapore), Bedrock models allocated for student testing are provisioned in `us-east-1` (N. Virginia). The provider explicitly overrides the AWS client region:
```python
boto3.client("bedrock-runtime", region_name=self.region_name) # region_name="us-east-1"
```

### Converse API Implementation
The provider leverages AWS's modern `converse` API:
```python
response = await asyncio.to_thread(
    client.converse,
    modelId=self.model_id, # "us.amazon.nova-micro-v1:0"
    messages=bedrock_messages,
    system=[{"text": sys_prompt}],
    inferenceConfig={"temperature": 0.1, "maxTokens": 2048},
    toolConfig={"tools": bedrock_tools, "toolChoice": {"auto": {}}} # When tools available
)
```
- **Async Execution:** Synchronous `boto3` client invocations are wrapped in `asyncio.to_thread()` to prevent blocking the FastAPI async event loop.
- **RFC 7807 Problem Mapping:** Bedrock exceptions (`AccessDeniedException`, `ValidationException`, `ResourceNotFoundException`) are mapped to structured RFC 7807 JSON problems (`HTTP 403 FORBIDDEN`, `HTTP 400 VALIDATION_ERROR`, `HTTP 502 BAD_GATEWAY`).

---

## 4. Dual-Namespace Python Module Stashing

Both `backend/payroll-costing` and `prototypes/sampling-spec-rnd/backend` originally used an unnamespaced `src/` directory. When `payroll.py` was imported, `sys.modules['src']` was populated by payroll-costing. Any subsequent import `from src.api.routes ...` attempted to load routes from `payroll-costing/src/api/routes`, which failed with `ModuleNotFoundError`.

### Resolution Pattern
In `backend/app/main.py`, router registration uses a dynamic scoped stashing block:
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
This enables both sub-modules to coexist in the same Python process without modifying their internal import statements.

---

## 5. Memory Management & OOM Mitigation on 1 GB RAM

The hackathon template provides a `t3.micro` instance with 1 GiB physical RAM. Running Node.js compiler toolchains (`tsc && vite build`) or running multiple concurrent Docker containers on 1 GiB RAM triggers the Linux OOM Killer:
- **Defense 1 (2 GiB Swap Allocation):** Configured in template user-data:
  ```bash
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  ```
- **Defense 2 (Local Pre-Bundling):** The React frontend is built on the development workstation and committed as static production assets in `prototypes/sampling-spec-rnd/frontend/dist/`. The EC2 server never executes `npm install` or `npm run build`.

---

## 6. Database Lifecycle & Migrations

PostgreSQL 15 runs locally on loopback `127.0.0.1:5432`. It is isolated by the EC2 Security Group (port 5432 is not exposed externally).

### Migration Pipeline
[`scripts/init_ec2_db.py`](file:///c:/Projects/hackathon-MAIN-alkademi/scripts/init_ec2_db.py) applies the full schema sequence idempotently and seeds the default factory tenant/actor/accounts:
1. `001_identities.sql`: Tenants, actors, audit events, idempotency records, and `lukla_app` role.
2. `006_payroll_rate_cards.sql`: Operation codes, piece rates, rate cards (`btree_gist` pre-enabled by superuser).
3. `007_payroll_qc_inputs.sql`: Garment assemblies, component allocations, QC inspections, and defect logs.
4. `008_double_entry_ledger.sql`: Accounts, journal entries, balanced postings.
5. `009_payroll_core.sql`: Payroll periods, statements, line items.
6. `011_job_idempotency.sql`: Processing locks and job replay guards.
7. `012_payroll_routines_rls.sql`: Stored functions, RLS policies, tenant isolation.
8. `013_telegram_copilot_bindings.sql`: Telegram chat bindings and enrollments.
