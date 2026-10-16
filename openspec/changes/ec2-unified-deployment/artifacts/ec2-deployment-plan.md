# Engineering Plan: Unified EC2 Cloud Deployment

## ASK and NEED

- **ASK:** Deploy the Lukla platform to an AWS EC2 instance strictly conforming to `Deploy aplikasi ke EC2.pdf`, using AWS CLI where helpful, but hold on launching the instance until told to do so.
- **NEED:** Provide a production-grade, single-port deployment on port 3000 that allows evaluators to interactively test Amazon Bedrock AI queries, browse the Sampling & Spec R&D prototype, view the enterprise ERP mock, inspect OpenAPI contracts, and submit verified deployment parameters to the Alkademi reporting form—while guaranteeing that 1 GB RAM constraints on `t3.micro` never crash the server.

---

## Technical Anchors & Evidence

- **FastAPI Core Application:** Mounted in [backend/app/main.py](file:///c:/Projects/hackathon-MAIN-alkademi/backend/app/main.py#L18-L23), exposing OpenAPI schema, security middleware, and `/copilot` HTML renderer.
- **LLM Provider Factory:** Located in [backend/app/copilot/provider.py](file:///c:/Projects/hackathon-MAIN-alkademi/backend/app/copilot/provider.py#L378-L388), creating providers (`MockLLMProvider`, `OpenAILLMProvider`, `OllamaLLMProvider`, `OpenRouterLLMProvider`, `BedrockLLMProvider`).
- **AWS Launch Template:** `main-ec2-template` (`lt-00e4f5effa1c630ad`) in region `ap-southeast-1` with attached role `MainEC2Role` and Security Group `sg-0ee4f83cd129e794a` [code: `aws ec2 describe-launch-templates`].
- **AWS Bedrock Endpoint:** Bedrock models allocated for student testing reside in AWS region `us-east-1` with model ID `us.amazon.nova-micro-v1:0` [doc: `Deploy aplikasi ke EC2.pdf` page 7, 13].
- **Pre-existing Frontend Prototype:** Vite React application located in `prototypes/sampling-spec-rnd/frontend/` [code: `package.json`].
- **Database Migrations:** 9 sequential migrations located in `backend/migrations/` (`001_identities.sql` .. `013_telegram_copilot_bindings.sql`).

---

## Target Files

### Existing Files Modified
1. `c:\Projects\hackathon-MAIN-alkademi\backend\app\copilot\config.py` — add `"bedrock"` to `COPILOT_DEFAULT_PROVIDER` literal and add `AWS_REGION` and `BEDROCK_MODEL_ID` configuration fields.
2. `c:\Projects\hackathon-MAIN-alkademi\backend\app\copilot\provider.py` — implement `BedrockLLMProvider` using `boto3` Bedrock Converse API with IAM role credentials; register in `get_llm_provider`.
3. `c:\Projects\hackathon-MAIN-alkademi\backend\app\main.py` — mount root portal landing page (`GET /`), health check (`GET /health`), Sampling & Spec R&D static frontend (`/sampling`), and isolated prototype backend routers.
4. `c:\Projects\hackathon-MAIN-alkademi\backend\tests\test_copilot_api.py` — add test case `test_bedrock_provider_initialization_and_mock` verifying Bedrock provider instantiation and message converse parsing.
5. `c:\Projects\hackathon-MAIN-alkademi\scripts\check_workspace_hygiene.py` — whitelist `main.py` and `requirements.txt` in root allow-list.

### New Files Created
1. `c:\Projects\hackathon-MAIN-alkademi\main.py` — root application entry point exporting `app = FastAPI(...)` for `uvicorn main:app --host 0.0.0.0 --port 3000`.
2. `c:\Projects\hackathon-MAIN-alkademi\requirements.txt` — root production dependency manifest.
3. `c:\Projects\hackathon-MAIN-alkademi\scripts\init_ec2_db.py` — automated PostgreSQL migration runner executing migrations 001–013 idempotently.
4. `c:\Projects\hackathon-MAIN-alkademi\scripts\deploy_ec2.sh` — single-command shell deployment script for AWS Session Manager.
5. `c:\Projects\hackathon-MAIN-alkademi\prototypes\sampling-spec-rnd\frontend\.env.production` — relative API configuration for Vite frontend build.
6. `c:\Projects\hackathon-MAIN-alkademi\prototypes\sampling-spec-rnd\frontend\dist\` — pre-compiled static frontend production assets.

---

## Signatures and Schemas

### 1. BedrockLLMProvider Signature
```python
class BedrockLLMProvider(BaseLLMProvider):
    def __init__(self, settings: Optional[CopilotSettings] = None):
        self.settings: CopilotSettings
        self.region_name: str # Defaults to "us-east-1"
        self.model_id: str    # Defaults to "us.amazon.nova-micro-v1:0"
        self._client: Optional[boto3.client]

    async def chat_turn(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        ...
```

### 2. Ingress Endpoints
- `GET /` -> `HTMLResponse`: Renders responsive operations portal (status 200 OK).
- `GET /health` -> `JSONResponse`: Returns `{"status": "OK", "service": "lukla-operations-engine"}`.
- `GET /copilot` -> `HTMLResponse`: Renders interactive React Copilot widget.
- `GET /sampling/*` -> `StaticFiles`: Mounts pre-bundled Sampling & Spec R&D frontend.
- `POST /api/v1/copilot/chat` -> `JSONResponse`: Executes LLM turn (supported provider: `bedrock`).

---

## Edge Cases and Mitigations

1. **Memory Exhaustion (1 GB RAM OOM):**
   - *Risk:* `npm run build` or heavy Python wheels kill the compiler during setup.
   - *Mitigation:* Frontend is pre-built locally on workstation and committed as static HTML/CSS/JS in `dist/`. The deployment script uses existing 2 GB swap configured in Launch Template user-data.
2. **Bedrock Cross-Region Latency & IAM Permissions:**
   - *Risk:* EC2 is in `ap-southeast-1` while Bedrock is provisioned in `us-east-1`. Calling the default local region results in `ResourceNotFoundException`.
   - *Mitigation:* `BedrockLLMProvider` explicitly targets `region_name="us-east-1"`. If IAM permissions are lacking, errors surface as RFC 7807 `HTTP 403 FORBIDDEN` detailing the missing IAM role policy.
3. **Dual-`src` Namespace Collision:**
   - *Risk:* Importing `sampling-spec-rnd` routers fails because `sys.modules['src']` is claimed by `payroll-costing`.
   - *Mitigation:* `main.py` uses dynamic module stashing during router registration to load both routers cleanly into memory.
4. **PostgreSQL Privilege Isolation:**
   - *Risk:* Non-superuser `myappuser` cannot run `CREATE ROLE lukla_app`.
   - *Mitigation:* `init_ec2_db.py` wraps DDL executions in structured try-except blocks, recording notes for existing roles while continuing table creation.

---

## Verification & Validation Commands

```powershell
# 1. Run Copilot unit tests including Bedrock converse provider mock
python -m pytest backend/tests/test_copilot_api.py

# 2. Verify workspace hygiene and root file isolation
python scripts/check_workspace_hygiene.py

# 3. Test root entrypoint and router mounting
python -c "import main; print('Total routes:', len(main.app.routes))"

# 4. Dry-run AWS EC2 instance launch
aws ec2 run-instances `
  --launch-template LaunchTemplateId=lt-00e4f5effa1c630ad `
  --tag-specifications "ResourceType=instance,Tags=[{Key=Owner,Value=student_12}]" `
  --region ap-southeast-1 `
  --dry-run
```

---

## Post-Planning Handoff Brief

> **STOP CONDITION FOR IMPLEMENTATION AGENT:**
> Phases 1 through 4 are already implemented and pushed to `master`.
> Do NOT launch the EC2 instance (Step 5) until explicit operator confirmation is received.
> If anything differs from this brief, return:
> `BLOCKED: <what differs> | <evidence> | <question>`
> Do not choose for the user and do not widen scope.
