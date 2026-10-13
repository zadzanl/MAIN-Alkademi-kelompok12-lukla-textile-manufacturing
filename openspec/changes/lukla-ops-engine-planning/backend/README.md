# Backend Structure Guide
## Lukla Operations Engine - Modular Backend Architecture

**This guide explains the backend folder structure and how modules integrate together.**

---

## 📂 Backend Directory Structure

```
backend/
├── sampling-spec-rnd/              ← SAMPLING & SPEC R&D Module (THIS)
│   ├── src/                        ← Source code
│   │   ├── models/                 ← Data models & classes
│   │   │   ├── time_study_recorder.py
│   │   │   └── spec_version_tracker.py
│   │   ├── services/               ← Business logic & workflows
│   │   │   └── sampling_rd_workflow.py
│   │   ├── utils/                  ← Utility functions & patterns
│   │   │   ├── time_study_patterns.py
│   │   │   └── spec_version_patterns.py
│   │   └── api/                    ← API routes & endpoints
│   │       ├── __init__.py         ← Blueprint registration
│   │       ├── time_study_routes.py
│   │       └── spec_version_routes.py
│   ├── docs/
│   │   └── [module-specific docs]
│   └── tests/                      ← Unit & integration tests
│       └── [test files]
│
├── manufacturing-execution/        ← Other modules (future)
│   └── [similar structure]
│
├── quality-control/               ← Other modules (future)
│   └── [similar structure]
│
├── payroll-costing/               ← Other modules (future)
│   └── [similar structure]
│
├── financial-ledger/              ← Other modules (future)
│   └── [similar structure]
│
├── multi-tenant-inventory/        ← Other modules (future)
│   └── [similar structure]
│
└── shared/                        ← Shared utilities across modules
    ├── middleware/
    ├── decorators/
    ├── validators/
    ├── errors/
    └── utils/
```

---

## 🎯 Module Organization Pattern

Setiap module mengikuti struktur yang sama untuk consistency:

```
module-name/
├── src/
│   ├── models/           Data structures & domain objects
│   ├── services/         Business logic & workflows
│   ├── utils/            Utility functions & patterns
│   ├── api/              REST endpoints
│   └── __init__.py       Module exports
├── docs/                 Module documentation
├── tests/                Unit & integration tests
├── requirements.txt      Dependencies
└── README.md            Module-specific guide
```

### Responsibilities per Folder

| Folder | Purpose | Examples |
|--------|---------|----------|
| **models/** | Data structures, domain logic | `TimeStudyRecorder`, `SpecVersionTracker` |
| **services/** | Business workflows, complex logic | `SamplingRnDWorkflow` complete flow |
| **utils/** | Helper functions, algorithms | Calculation, validation, pattern functions |
| **api/** | REST endpoints, request handlers | Route definitions, response formatting |

---

## 🔗 How Modules Connect

### 1. **Same Module Integration**

```python
# Within sampling-spec-rnd module
from backend.sampling_spec_rnd.src.models import TimeStudyRecorder
from backend.sampling_spec_rnd.src.services import SamplingRnDWorkflow
from backend.sampling_spec_rnd.src.utils import calculate_quality_score

# Use in API endpoint
@app.route('/api/v1/time-studies', methods=['POST'])
def create_time_study():
    recorder = TimeStudyRecorder(spec_id=...)
    # ... use recorder
    result = recorder.to_dict()
    return jsonify(result)
```

### 2. **Cross-Module Integration**

```python
# From manufacturing-execution module
from backend.sampling_spec_rnd.src.models import SpecVersionTracker

def get_time_standards(product_id):
    tracker = SpecVersionTracker(product_id)
    approved_version = tracker.get_versions(status='approved')[0]
    return approved_version.specification['time_standards']
```

### 3. **Via API Contracts**

```python
# Manufacturing module calls via HTTP
import requests

def fetch_approved_spec(product_id):
    response = requests.get(
        f'{BACKEND_URL}/api/v1/spec-versions',
        params={'product_id': product_id, 'status': 'approved'}
    )
    return response.json()['data'][0]

# More loosely coupled, easier to scale separately
```

### 4. **Via Event System** (Async)

```python
# Spec version approved event
from backend.shared.events import EventBus

def publish_spec_approved(version_id):
    event = {
        'type': 'spec.version.approved',
        'data': {
            'spec_id': version_id,
            'time_standards': {...},
            'effective_date': '2026-10-20'
        }
    }
    EventBus.publish(event)

# Manufacturing module subscribes
EventBus.subscribe('spec.version.approved', handle_spec_approved)

def handle_spec_approved(event):
    # Update manufacturing parameters
    update_time_targets(event['data'])
```

---

## 🏗️ Integration Patterns

### Pattern 1: Direct Import (Tightly Coupled)
```python
# ✅ Use within same module or closely related
from backend.sampling_spec_rnd.src.models import TimeStudyRecorder

# ❌ Avoid across distant modules (use API instead)
from backend.payroll_costing.src.models import PayrollCalculator
```

### Pattern 2: HTTP API (Loosely Coupled)
```python
# ✅ Use across modules that might scale independently
response = requests.get('/api/v1/spec-versions/{id}')

# Best for: external modules, scheduled services, third-party integrations
```

### Pattern 3: Event System (Decoupled & Scalable)
```python
# ✅ Use for broadcast events, async workflows
EventBus.publish('spec.version.published', data)
EventBus.subscribe('payroll.calculation.needed', handle_payroll)

# Best for: multi-module coordination, real-time updates, scalability
```

### Pattern 4: Database Shared Tables (Shared Data)
```python
# ✅ Use for truly shared entities (users, clients, products)
from backend.shared.models import Client, Product

# ❌ Avoid module-specific data (use API layer)
# WRONG: from backend.sampling_spec_rnd.src.models import TimeStudyRecorder
#        access_directly(TimeStudyRecorder) in another module
```

---

## 📋 Dependency Management

### Import Hierarchy (Recommended)

```
API Layer (routes)
    ↓
Service Layer (workflows, business logic)
    ↓
Model Layer (data structures)
    ↓
Utils Layer (pure functions)
    ↓
Shared Utilities (middleware, validators)
```

### Avoid Circular Dependencies

```python
# ❌ BAD: Circular import
# models.py imports from services.py
# services.py imports from models.py
from backend.sampling_spec_rnd.src.services import some_service  # ← CIRCULAR!

# ✅ GOOD: One-way dependency
# services.py imports from models.py (NOT vice versa)
# models.py only imports from utils.py
```

---

## 🚀 Adding a New Module

When adding another module (e.g., `manufacturing-execution`):

### Step 1: Create Structure
```bash
mkdir -p backend/manufacturing-execution/src/{models,services,utils,api}
touch backend/manufacturing-execution/src/__init__.py
touch backend/manufacturing-execution/README.md
```

### Step 2: Define Data Models
```python
# backend/manufacturing-execution/src/models/production_line.py
class ProductionLine:
    def __init__(self, line_id, product_id, spec_version_id):
        self.line_id = line_id
        self.product_id = product_id
        self.spec_version_id = spec_version_id
```

### Step 3: Define Services
```python
# backend/manufacturing-execution/src/services/execution_service.py
from backend.sampling_spec_rnd.src.models import SpecVersionTracker

class ExecutionService:
    def set_line_targets(self, line_id, product_id):
        # Get spec from sampling-spec-rnd
        tracker = SpecVersionTracker(product_id)
        spec = tracker.get_version(...)
        # Use spec to set production targets
```

### Step 4: Define API
```python
# backend/manufacturing-execution/src/api/production_routes.py
from flask import Blueprint
from backend.manufacturing_execution.src.services import ExecutionService

prod_bp = Blueprint('production', __name__, url_prefix='/api/v1/production')

@prod_bp.route('/lines/<line_id>/targets', methods=['GET'])
def get_line_targets(line_id):
    service = ExecutionService()
    targets = service.get_line_targets(line_id)
    return jsonify(targets)
```

### Step 5: Register in Main App
```python
# main.py or app.py
from backend.sampling_spec_rnd.src.api import register_blueprints as register_sampling
from backend.manufacturing_execution.src.api import register_blueprints as register_manufacturing

app = Flask(__name__)
register_sampling(app)
register_manufacturing(app)
```

---

## 🔐 Security & Multi-Tenancy

### Critical Rules

1. **ALWAYS filter by client_id**
```python
# ❌ WRONG - leaks data across clients
spec = SpecVersionTracker.query.filter_by(product_id=pid).first()

# ✅ CORRECT - enforces isolation
spec = SpecVersionTracker.query.filter_by(
    product_id=pid, 
    client_id=current_user.client_id
).first()
```

2. **Use middleware for automatic enforcement**
```python
# backend/shared/middleware/tenant_middleware.py
@app.before_request
def enforce_tenant_isolation():
    request.client_id = get_authenticated_client_id()
    # All queries auto-filtered
```

3. **Document integrations with tenant awareness**
```python
# API contract must specify multi-tenant behavior
GET /api/v1/spec-versions
Response: Only spec versions for authenticated client_id
```

---

## 📊 Module Dependencies Graph

```
┌─────────────────────────────────────────┐
│         SHARED UTILITIES                │
│  (middleware, validators, errors, etc)  │
└──────────────────────┬──────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────┐  ┌──────────────┐  ┌─────────┐
│SAMPLING& │  │MANUFACTURING │  │ QUALITY │
│SPEC R&D  │  │ EXECUTION    │  │   QC    │
│(THIS)    │  │              │  │         │
└──────────┘  └──────────────┘  └─────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐  ┌────────┐  ┌──────────┐
│PAYROLL &     │  │FINANCE │  │INVENTORY │
│COSTING       │  │LEDGER  │  │ (MULTI-  │
│              │  │        │  │ TENANT)  │
└──────────────┘  └────────┘  └──────────┘
```

**Direction of arrows = can import from**

---

## 🧪 Testing Strategy

### Unit Tests (Per Module)
```python
# backend/sampling-spec-rnd/tests/test_models.py
def test_time_study_recorder():
    recorder = TimeStudyRecorder('spec-123', 'prod-001')
    recorder.record_phase('Jahit', 180)
    assert recorder.get_total_duration() == 180

def test_spec_version_tracker():
    tracker = SpecVersionTracker('prod-001')
    version = tracker.create_version('1.0', 'Initial spec', {...})
    assert version['status'] == 'draft'
```

### Integration Tests (Cross-Module)
```python
# backend/tests/test_sampling_to_payroll_integration.py
def test_spec_approved_updates_payroll_rates():
    # 1. Create spec in sampling module
    spec = create_approved_spec(...)
    
    # 2. Call payroll API
    rates = get_payroll_rates(spec['id'])
    
    # 3. Verify rates updated
    assert rates['base_rate'] > 0
```

### API Tests (End-to-End)
```python
# backend/tests/test_api_e2e.py
def test_create_time_study_via_api():
    client = app.test_client()
    response = client.post(
        '/api/v1/time-studies',
        json={...}
    )
    assert response.status_code == 201
```

---

## 📚 Documentation Structure

```
backend/
├── README.md                    ← THIS FILE (overall backend)
├── INTEGRATION_ANALYSIS.md      ← How modules integrate
│
├── sampling-spec-rnd/
│   ├── README.md               ← Module-specific guide
│   ├── docs/
│   │   ├── API.md              ← API documentation
│   │   ├── DATA_MODELS.md      ← Data structure docs
│   │   └── INTEGRATION.md      ← How to integrate THIS module
│   └── ...
│
├── manufacturing-execution/
│   ├── README.md
│   ├── docs/
│   │   └── ...
│   └── ...
```

---

## 🚀 Getting Started

### For Sampling & Spec R&D Development
1. Read: `backend/sampling-spec-rnd/README.md`
2. Review: `backend/sampling-spec-rnd/src/models/`
3. Study: `backend/INTEGRATION_ANALYSIS.md` for integration points
4. Code: Start with models → services → api

### For Adding New Modules
1. Read: `backend/README.md` (this file) - "Adding a New Module"
2. Copy structure from sampling-spec-rnd
3. Follow dependency patterns
4. Register in main app
5. Document integration points

### For Integration Work
1. Read: `backend/INTEGRATION_ANALYSIS.md` (comprehensive)
2. Identify integration pattern (direct import, API, events)
3. Implement with proper multi-tenant handling
4. Add integration tests
5. Document data contracts

---

## ✅ Quality Checklist

Before committing code:

- [ ] Module follows standard structure
- [ ] No circular imports
- [ ] Multi-tenant filters on all DB queries
- [ ] API endpoints documented
- [ ] Error handling implemented
- [ ] Unit tests written
- [ ] Integration points identified
- [ ] Documentation updated
- [ ] Code follows naming conventions
- [ ] No hardcoded values (use config)

---

## 📞 Support & Questions

For questions about:
- **Module structure**: See "Module Organization Pattern" above
- **Integration**: See `backend/INTEGRATION_ANALYSIS.md`
- **Specific module**: See module's own README.md
- **API contracts**: See `src/api/` files in each module

---

**Document Version**: 1.0  
**Last Updated**: 2026-10-13  
**Status**: ✅ Ready for Team Development
