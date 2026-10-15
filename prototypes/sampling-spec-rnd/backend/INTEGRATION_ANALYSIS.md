# Backend Integration Analysis
## SAMPLING & SPEC R&D Module dengan Sistem Lukla Operations Engine

**Dokumen ini menganalisa bagaimana module SAMPLING & SPEC R&D terintegrasi dengan modul lain dalam arsitektur sistem.**

---

## 📊 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│              LUKLA OPERATIONS ENGINE (Event-Driven)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─ FINANCIAL LEDGER ─────┐    ┌─ MULTI-TENANT INVENTORY ────┐    │
│  │ (CDA, Debits, Credits) │    │ (Client_ID, Order_ID Lots)   │    │
│  └────────────┬────────────┘    └────────────┬─────────────────┘    │
│               │                              │                       │
│  ┌────────────▼────────────┐    ┌────────────▼─────────────────┐    │
│  │ MANUFACTURING EXECUTION │    │ SAMPLING & SPEC R&D (THIS)   │    │
│  │ (Events/Tally 30min)    │    │ (Time Study, Versions, Drift)│    │
│  │ - Floor Terminal        │    │ - TimeStudyRecorder          │    │
│  │ - Production Output      │    │ - SpecVersionTracker         │    │
│  └────────────┬────────────┘    │ - R&D Drift Detection        │    │
│               │                 │ - Spec Approval Workflow     │    │
│               │                 └────────────┬─────────────────┘    │
│  ┌────────────▼────────────┐                │                       │
│  │ QUALITY CONTROL & MES   │    ┌───────────▼─────────────────┐    │
│  │ (Pass, Repair, Reject)  │    │ PAYROLL & COSTING           │    │
│  │ - QC Inspection Terminal│    │ - Dynamic Rate Calculation  │    │
│  │ - Defect Taxonomy       │◄───┤ - Bonus Distribution        │    │
│  └─────────────────────────┘    └─────────────────────────────┘    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 SAMPLING & SPEC R&D Integration Points

### 1. **Dengan MANUFACTURING EXECUTION**

**Hubungan**: Spec R&D mendefinisikan standar untuk production, Manufacturing Execution melaksanakannya

**Data Flow**:
```
Spec Version (Approved)
        ↓
TimeStudyRecorder mengukur waktu aktual
        ↓
Manufacturing Execution menggunakan time standard untuk:
  - Set target time per phase
  - Calculate efficiency metrics
  - Flag when actual time exceeds threshold
```

**Integration Points**:
```python
# backend/sampling-spec-rnd/src/models/spec_version_tracker.py
class SpecVersionTracker:
    def get_approved_version(self, product_id):
        """Get approved spec untuk manufacturing"""
        # Return: {version, specification, time_standards}
        pass

    def broadcast_spec_change(self, version_id):
        """Broadcast ke Manufacturing Execution saat ada perubahan"""
        # Trigger: EventQueue atau RabbitMQ
        # Payload: spec_id, version, effective_date
        pass


# backend/sampling-spec-rnd/src/api/spec_version_routes.py
@spec_bp.route("/<version_id>/publish", methods=["POST"])
def publish_spec_to_manufacturing():
    """Publikasikan spec ke Manufacturing module"""
    # 1. Validate spec compliance
    # 2. Get approval status
    # 3. Send event to Manufacturing queue
    # 4. Return: {published, effective_date, module_acknowledgements}
    pass
```

**Contract untuk Manufacturing Team**:
- GET `/api/v1/spec-versions?product_id=X&status=approved`
  - Response: Approved spec dengan time standards
- Subscribe ke event: `spec.version.published`
  - Payload: `{spec_id, version, time_standards, effective_date}`

---

### 2. **Dengan QUALITY CONTROL & MES**

**Hubungan**: Time Study data inform QC defect investigation, Spec Version quality standards

**Data Flow**:
```
TimeStudy → QC Analysis
  ├─ Detect when quality score drops
  ├─ Link to spec version changes
  └─ Trigger R&D drift detection

Defect Data → Spec Revision
  ├─ If defects correlate with spec change
  ├─ Schedule new time study
  └─ Create new spec version
```

**Integration Points**:
```python
# backend/sampling-spec-rnd/src/utils/time_study_patterns.py
def detect_quality_correlation(time_study, defect_data):
    """Detect correlation antara time study changes & quality issues"""
    # Input: time_study (duration, phases)
    #        defect_data (defect_rate, defect_type)
    # Output: correlation score, recommendation
    pass


# backend/sampling-spec-rnd/src/api/time_study_routes.py
@time_study_bp.route("/<ts_id>/correlate-defects", methods=["POST"])
def correlate_with_defects():
    """Check defect correlation untuk specific time study"""
    # 1. Get time study
    # 2. Query QC module untuk defects dalam same period
    # 3. Calculate correlation
    # 4. If strong correlation: flag untuk review
    pass
```

**Contract untuk QC Team**:
- POST `/api/v1/time-studies/{id}/mark-quality-issue`
  - Payload: `{defect_type, defect_rate, notes}`
  - Triggers review dari R&D
- GET `/api/v1/spec-versions/{id}?include=quality_history`
  - Response: Spec dengan quality issues history

---

### 3. **Dengan PAYROLL & COSTING**

**Hubungan**: Time Study data digunakan untuk menghitung dinamis wage rates

**Data Flow**:
```
Approved TimeStudy Standard
        ↓
Calculate Expected Output per Hour
        ↓
Payroll Rate Calculation
  ├─ Base Rate × Expected Output
  ├─ Efficiency Bonus/Penalty
  └─ Quality Bonus Distribution
```

**Integration Points**:
```python
# backend/sampling-spec-rnd/src/api/time_study_routes.py
@time_study_bp.route("/<ts_id>/to-payroll", methods=["GET"])
def export_for_payroll():
    """Export time study standard untuk payroll calculation"""
    # Return: {
    #   time_standards: {phase: duration, ...},
    #   expected_output: units_per_hour,
    #   quality_factor: multiplier,
    #   effective_date
    # }
    pass


# In Payroll Module
def calculate_worker_rate(spec_version, actual_output):
    """Calculate rate berdasarkan spec time standard"""
    standard_time = spec_version.time_standards["total"]
    efficiency = actual_output / (target_output_from_standard_time)
    base_rate = get_base_rate(spec_version.product_id)
    return base_rate * efficiency * quality_factor
```

**Contract untuk Payroll Team**:
- GET `/api/v1/spec-versions/{id}/time-standards`
  - Response: Time standards untuk wage calculation
- GET `/api/v1/time-studies?product_id=X&status=approved`
  - Response: Approved time studies untuk rate reference
- Event: `time-study.approved`
  - Payload: `{spec_id, time_standards, effective_date}`

---

### 4. **Dengan FINANCIAL LEDGER**

**Hubungan**: Spec changes dapat impact costing dan ledger entries

**Data Flow**:
```
Spec Version Change
        ↓
Cost Impact Analysis
  ├─ Material cost changes
  ├─ Labor cost changes (via Payroll)
  └─ Overhead allocation changes
        ↓
Ledger Entry (via GL)
  ├─ Rate variance accounts
  ├─ Efficiency variance accounts
  └─ Audit trail
```

**Integration Points**:
```python
# backend/sampling-spec-rnd/src/utils/spec_version_patterns.py
def calculate_cost_impact(old_spec, new_spec):
    """Calculate cost impact dari spec change"""
    # Analyze:
    # - Material usage changes
    # - Time/labor changes
    # - Quality/defect implications
    # Return: cost_delta, financial_accounts_affected
    pass


# backend/sampling-spec-rnd/src/api/spec_version_routes.py
@spec_bp.route("/<version_id>/cost-impact", methods=["GET"])
def get_cost_impact():
    """Get financial impact dari spec version"""
    # Return: {
    #   cost_delta: amount,
    #   affected_gl_accounts: [...],
    #   journal_entries: [...],
    #   variance_analysis: {...}
    # }
    pass
```

**Contract untuk Finance Team**:
- GET `/api/v1/spec-versions/{id}/cost-impact`
  - Response: Cost variance analysis
- Subscribe ke: `spec-version.approved`
  - Prepare ledger entries untuk cost allocation changes

---

### 5. **Dengan MULTI-TENANT INVENTORY**

**Hubungan**: Spec version applies to specific client's product variant

**Data Flow**:
```
Multi-Client Inventory (Lot tracking)
        ↓
Spec Version tied to Client_ID + Product
        ↓
TimeStudy measured per Client batch
        ↓
RND Drift detection per Client
```

**Integration Points**:
```python
# backend/sampling-spec-rnd/src/models/spec_version_tracker.py
class SpecVersionTracker:
    def __init__(self, product_id, client_id=None):
        """Support per-client spec variants"""
        self.product_id = product_id
        self.client_id = client_id  # Multi-tenant support
        pass


# backend/sampling-spec-rnd/src/api/spec_version_routes.py
@spec_bp.route("", methods=["GET"])
def list_spec_versions():
    """List dengan multi-tenant filtering"""
    # Query params: product_id, client_id
    # WHERE product_id = X AND (client_id = Y OR client_id IS NULL)
    # Handle: global specs vs client-specific variants
    pass
```

**Multi-Tenant Safety**:
```python
# CRITICAL: Row-Level Security untuk client isolation
# Setiap query HARUS include client_id filter:

# ❌ WRONG:
SELECT * FROM spec_versions WHERE product_id = 'prod-1'

# ✅ CORRECT:
SELECT * FROM spec_versions 
WHERE product_id = 'prod-1' AND client_id = 'client-xyz'
  OR (client_id IS NULL AND product_id = 'prod-1')  # global fallback
```

---

## 🏗️ Integration Architecture

### Data Flow Diagram
```
┌──────────────────────────────────────┐
│  SAMPLING & SPEC R&D MODULE          │
│  ├─ Spec Versions (approved/draft)   │
│  ├─ Time Studies (recorded/analyzed) │
│  └─ R&D Drift Detection              │
└──────────────┬───────────────────────┘
               │
    ┌──────────┼──────────┬─────────────┬──────────────┐
    │          │          │             │              │
    ▼          ▼          ▼             ▼              ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐ ┌────────────┐
│Mfg.Ex  │ │QC/MES  │ │Payroll │ │ Finance │ │ Inventory  │
│Module  │ │ Module │ │ Module │ │ Module  │ │  Module    │
└────────┘ └────────┘ └────────┘ └─────────┘ └────────────┘
```

### Data Exchange Patterns

**1. Synchronous (Request-Response)**
```
Frontend → API
  ↓
Backend Controller (routes.py)
  ↓
Service Layer (models.py / services.py)
  ↓
External Module API Call
  ↓
Response
```

**2. Asynchronous (Event-Driven)**
```
Spec Version Approved
  ↓
Event: spec.version.published
  ↓
Message Queue (RabbitMQ / Kafka)
  ↓
Manufacturing Module consumes
  ↓
Updates internal cache/DB
```

**3. Batch Processing**
```
Time Studies for Period X
  ↓
Generate Payroll Data
  ↓
Export to Finance Module
  ↓
Ledger entries created
```

---

## 🔐 Security & Isolation

### Multi-Tenant Isolation (CRITICAL)
```python
# Every query MUST enforce client_id

# ✅ GOOD Pattern:
def get_time_studies(client_id, product_id, filters):
    return TimeStudy.query.filter(
        TimeStudy.client_id == client_id,  # ALWAYS first
        TimeStudy.product_id == product_id,
        TimeStudy.spec_id == filters.get("spec_id"),
    )


# ✅ BETTER: Use middleware
@app.before_request
def enforce_client_isolation():
    request.client_id = get_authenticated_client_id()
    # All queries auto-filtered
```

### Immutable Ledger Compliance
```python
# SAMPLING & SPEC R&D must NEVER update existing records
# Only create new versions or reversed entries

# ✅ CORRECT:
def update_spec(version_id, changes):
    # Create new version, mark old as deprecated
    old = get_version(version_id)
    new = create_new_version(based_on=old, changes=changes, change_reason="Spec correction")
    old.status = "deprecated"
    return new


# ❌ WRONG:
def update_spec(version_id, changes):
    spec = get_version(version_id)
    spec.update(changes)  # DON'T do this!
```

---

## 📋 Integration Checklist

### Pre-Integration Review
- [ ] All API endpoints have auth/authorization
- [ ] Multi-tenant filters on all queries
- [ ] Error handling returns appropriate HTTP status
- [ ] Request/response formats documented
- [ ] Event schemas documented for subscribers
- [ ] Rate limiting configured
- [ ] Logging includes request_id for tracing

### For Each Module Integration
- [ ] Define data contracts (request/response)
- [ ] Define event schemas
- [ ] Define error codes & recovery procedures
- [ ] Document timeout & retry policies
- [ ] Test with mock data
- [ ] Load test integration points
- [ ] Document rollback procedures

### Deployment
- [ ] Feature flags untuk new integrations
- [ ] Gradual rollout (canary, staged)
- [ ] Monitor integration health metrics
- [ ] Document incident response
- [ ] Plan rollback if issues
- [ ] Verify data consistency post-deployment

---

## 🚀 Integration Readiness

| Integration | Status | Ready | Notes |
|------------|--------|-------|-------|
| Manufacturing Execution | API defined | ✅ | Needs: spec publish event |
| QC & MES | API defined | ✅ | Needs: quality correlation logic |
| Payroll & Costing | API defined | ✅ | Needs: rate calculation algorithm |
| Finance Ledger | API defined | ⚠️ | Needs: GL account mapping |
| Multi-Tenant Inventory | API defined | ✅ | Needs: client_id enforcement |
| Event Publishing | Planned | ❌ | Needs: message queue setup |
| API Authentication | Planned | ❌ | Needs: auth middleware |
| Rate Limiting | Planned | ❌ | Needs: throttle middleware |

---

## 📚 Related Documentation

- **Module Structure**: `STRUCTURE.md` di folder ini
- **API Endpoints**: `backend/sampling-spec-rnd/src/api/`
- **Data Models**: `backend/sampling-spec-rnd/src/models/`
- **Utility Functions**: `backend/sampling-spec-rnd/src/utils/`
- **System PRD**: `artifacts/lukla_PRD_V.1.0.md`
- **Database Structure**: `artifacts/backend_database_structure.md`

---

**Document Version**: 1.0  
**Last Updated**: 2026-10-13  
**Status**: ✅ Ready for Integration Review
