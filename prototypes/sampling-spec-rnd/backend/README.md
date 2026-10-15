# Sampling & Spec R&D Backend

Enterprise-grade backend service for time study recording and specification version tracking with full audit trails and multi-tenant support.

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn python-multipart
```

### Running the Server

```bash
# Development
uvicorn backend.sampling-spec-rnd.src.api.routes:app --reload --port 8000

# Production
uvicorn backend.sampling-spec-rnd.src.api.routes:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## Portal Authentication (Prototype)

Internal-user auth for the PT Luka portal: registration with Admin IT verification, password login
by employee ID / NIK / email / phone, password change, and OTP-based recovery.

- **Storage**: in-memory (`src/services/auth_store.py`); resets on restart. Passwords use stdlib
  `hashlib.scrypt`; NIK/KTP is stored only as a SHA-256 lookup hash + masked last-4.
- **No new dependencies**: email uses stdlib `smtplib`; tokens/OTPs use `secrets`.
- **Email**: with no `SMTP_HOST`, the OTP is written to the backend log (`dev-log` mode).

Endpoints (prefix `/api/auth`):

```
POST /register            ajukan akun (status pending)
POST /login               identifier + password → access token + actor
POST /logout              cabut sesi (Bearer)
GET  /me                  konteks aktor (Bearer)
POST /change-password     ganti password (Bearer)
POST /forgot-password     kirim OTP (respons generik)
POST /reset-password      setel ulang password dengan OTP
GET  /admin/registrations daftar pengajuan pending (admin)
POST /admin/registrations/{id}/approve|reject (admin)
GET  /health              status modul + mode email
```

Default Admin IT seed (override via `.env`): `admin@luka.local` / `Admin#12345`.

**"Did it work?" check** — with the server running:

```bash
curl http://localhost:8009/api/auth/health
# → {"status":"healthy","module":"portal-auth","email_mode":"dev-log"}
```

Run the auth tests: `pytest tests/test_auth.py -q`.

## Project Structure

```
backend/sampling-spec-rnd/
├── src/
│   ├── models/              # Data models
│   │   ├── time_study_recorder.py
│   │   └── spec_version_tracker.py
│   ├── services/            # Business logic
│   │   └── sampling_rnd_workflow.py
│   ├── utils/               # Utilities
│   │   ├── time_study_patterns.py
│   │   └── spec_version_patterns.py
│   └── api/                 # API routes
│       └── routes.py
├── __init__.py
├── README.md
├── MODULES_REFERENCE.md
└── INTEGRATION_ANALYSIS.md
```

## API Endpoints

### Time Study Endpoints

#### Create Study
```
POST /api/sampling-spec-rnd/studies/create
Query Parameters:
  - tenant_id (string)
  - process_id (string)
  - process_name (string)
  - operator_id (string)
  - target_sample_size (int, default: 30)
```

#### Start Study
```
POST /api/sampling-spec-rnd/studies/{study_id}/start
```

#### Add Sample
```
POST /api/sampling-spec-rnd/studies/{study_id}/add-sample
Query Parameters:
  - cycle_time_ms (float)
  - element_name (string)
  - is_abnormal (bool, default: false)
  - notes (string)
Body (optional):
  - observations (JSON object)
```

#### Complete Study
```
POST /api/sampling-spec-rnd/studies/{study_id}/complete
```

#### Pause/Resume Study
```
POST /api/sampling-spec-rnd/studies/{study_id}/pause
POST /api/sampling-spec-rnd/studies/{study_id}/resume
```

#### Get Statistics
```
GET /api/sampling-spec-rnd/studies/{study_id}/stats
```

#### Export Study Data
```
GET /api/sampling-spec-rnd/studies/{study_id}/data
```

### Specification Endpoints

#### Create Version
```
POST /api/sampling-spec-rnd/specs/create
Query Parameters:
  - tenant_id (string)
  - spec_id (string)
  - spec_name (string)
  - created_by (string)
  - version_number (string, default: "1.0.0")
```

#### Record Change
```
POST /api/sampling-spec-rnd/specs/{version_id}/record-change
Query Parameters:
  - change_type (string)
  - parameter_name (string)
  - changed_by (string)
  - reason (string, optional)
  - impact_assessment (string, optional)
Body:
  - old_value
  - new_value
```

#### Record Drift
```
POST /api/sampling-spec-rnd/specs/{version_id}/record-drift
Query Parameters:
  - parameter_name (string)
  - specification_limit (float)
  - measured_value (float)
  - severity (string: low|medium|high|critical)
  - corrective_action (string, optional)
```

#### Resolve Drift
```
POST /api/sampling-spec-rnd/specs/{version_id}/resolve-drift/{drift_id}
Query Parameters:
  - corrective_action (string)
```

#### Workflow Endpoints
```
POST /api/sampling-spec-rnd/specs/{version_id}/submit-review
POST /api/sampling-spec-rnd/specs/{version_id}/approve
POST /api/sampling-spec-rnd/specs/{version_id}/activate
```

#### Get Reports
```
GET /api/sampling-spec-rnd/specs/{version_id}/drift-report
GET /api/sampling-spec-rnd/specs/{version_id}/drift-analysis
GET /api/sampling-spec-rnd/specs/{version_id}/change-history
GET /api/sampling-spec-rnd/specs/{version_id}/data
```

### Workflow Endpoints

```
GET /api/sampling-spec-rnd/workflow/summary?tenant_id=...
GET /api/sampling-spec-rnd/health
```

## Data Models

### TimeStudyRecorder
- `study_id`: Unique identifier
- `status`: draft → in_progress → paused → completed → archived
- `samples`: List of TimeSample objects
- `statistics`: Automatically computed (mean, std_dev, min, max)

### SpecVersionTracker
- `version_id`: Unique identifier
- `status`: draft → review → approved → active → superseded
- `changes`: Audit trail of all modifications
- `drifts`: Specification drift records with severity levels

## Key Features

✅ **Time Study Recording**
- Capture cycle times with outlier detection
- Statistical analysis (mean, standard deviation, CV)
- Abnormal cycle flagging
- Confidence level tracking

✅ **Specification Tracking**
- Complete version history with change audit trail
- Specification drift detection and severity classification
- Corrective action tracking
- Approval workflow (draft → review → approved → active)

✅ **Analysis & Reporting**
- Pattern detection in time data
- Drift trend analysis with risk scoring
- Parameter-level change history
- Performance recommendations

✅ **Multi-Tenant Support**
- Complete tenant isolation
- Separate data storage per tenant
- Tenant-specific workflow summaries

✅ **Data Integrity**
- Immutable audit trails
- Timestamped records
- Change history preservation
- Drift resolution tracking

## Integration Points

- **Manufacturing Execution System**: Study results feed into scheduling
- **QC/MES**: Spec versions control inspection criteria
- **Payroll**: Time study data supports payment calculations
- **Finance**: Spec changes impact costing
- **Inventory**: Process specs affect material flow

## Performance Considerations

- Batch operations for multiple samples
- Lazy loading of statistical summaries
- Indexed queries on tenant_id and status
- Caching of computed statistics
- Connection pooling for database

## Security

- Tenant isolation enforced at service level
- No cross-tenant data access
- Audit logs for all modifications
- Change tracking with user IDs
- Approval workflows for critical changes

## Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Production Deployment

See `INTEGRATION_ANALYSIS.md` for production integration patterns and `MODULES_REFERENCE.md` for architectural guidance.

## Support

For integration questions, see:
- `INTEGRATION_ANALYSIS.md` - System integration patterns
- `MODULES_REFERENCE.md` - Module specifications
- Individual model/service docstrings for API details
