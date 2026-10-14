# Backend Modules Reference Guide

**Quick reference for all backend modules and their integration points.**

---

## 🗂️ Module Inventory

### 1. SAMPLING & SPEC R&D (ACTIVE)

**Status**: ✅ Ready  
**Location**: `backend/sampling-spec-rnd/`

**Purpose**: 
- Record time studies for production phases
- Track spec versions and prevent R&D drift
- Provide time standards for manufacturing & payroll

**Key Exports**:
- `TimeStudyRecorder` - Record time study data
- `SpecVersionTracker` - Manage spec versions
- API endpoints for Time Studies and Spec Versions
- Utility functions for analysis & pattern detection

**Integration with**:
- Manufacturing Execution (time standards)
- QC & MES (quality analysis)
- Payroll & Costing (rate calculation)
- Finance Ledger (cost variance)
- Inventory (multi-tenant filtering)

**API Base**: `/api/v1/time-studies`, `/api/v1/spec-versions`

**Documentation**:
- API Contracts: `backend/sampling-spec-rnd/API_CONTRACTS.md`
- Integration: `backend/INTEGRATION_ANALYSIS.md`
- Models: `backend/sampling-spec-rnd/src/models/`

---

### 2. MANUFACTURING EXECUTION (FUTURE)

**Status**: 📋 To Be Implemented  
**Location**: `backend/manufacturing-execution/` (template)

**Purpose**:
- Record production output (tally per 30min)
- Track active production lines
- Implement time study standards from Spec R&D
- Emit events for downstream modules

**Will Consume From**:
- Sampling & Spec R&D (time standards)
- Financial Ledger (client/order data)

**Will Provide To**:
- QC & MES (production status)
- Payroll (output data for rate calculation)
- Finance (production cost entries)

**Planned API**: `/api/v1/production-lines`, `/api/v1/output`

**Planned Events**:
- `production.completed` - Line finished a batch
- `output.recorded` - Tally recorded

---

### 3. QUALITY CONTROL & MES (FUTURE)

**Status**: 📋 To Be Implemented  
**Location**: `backend/quality-control/` (template)

**Purpose**:
- Record QC inspection results (Pass/Repair/Reject)
- Track defect taxonomy
- Correlate defects with time studies
- Flag R&D drift

**Will Consume From**:
- Sampling & Spec R&D (spec standards, time study correlation)
- Manufacturing Execution (production status)

**Will Provide To**:
- Payroll (quality factors for bonus)
- Finance (quality variance)
- Sampling R&D (defect correlation for R&D review)

**Planned API**: `/api/v1/qc-inspections`, `/api/v1/defects`

**Planned Events**:
- `qc.inspection.completed` - QC check finished
- `defect.reported` - Defect found

---

### 4. PAYROLL & COSTING (FUTURE)

**Status**: 📋 To Be Implemented  
**Location**: `backend/payroll-costing/` (template)

**Purpose**:
- Calculate dynamic worker pay rates
- Compute efficiency bonus/penalty
- Distribute QC bonus (3-way split)
- Calculate overhead allocation

**Will Consume From**:
- Sampling & Spec R&D (time standards for rate base)
- Manufacturing Execution (output data)
- QC & MES (quality scores for bonus)
- Financial Ledger (cost rates, client data)

**Will Provide To**:
- Finance Ledger (payroll entries, variance analysis)
- Reporting (payroll summaries)

**Planned API**: `/api/v1/payroll-rates`, `/api/v1/worker-calculations`

**Planned Events**:
- `payroll.calculated` - Worker rates calculated
- `bonus.distributed` - QC bonus split

---

### 5. FINANCIAL LEDGER (CORE)

**Status**: ⚠️ Partial (may exist separately)  
**Location**: `backend/financial-ledger/` (if applicable)

**Purpose**:
- Immutable double-entry ledger
- Track all transactions with audit trail
- Record costing & variance entries
- Multi-tenant client isolation

**Critical Rules**:
- ⚠️ NO UPDATE/DELETE on transactions
- Only create new entries or reversal entries
- All entries must balance
- Client_ID filtering on all queries

**Will Consume From**:
- All modules (for transaction data)

**Will Provide To**:
- Reporting (financial statements)
- Compliance (audit trails)

**Planned API**: `/api/v1/journal-entries`, `/api/v1/chart-of-accounts`

---

### 6. MULTI-TENANT INVENTORY (CORE)

**Status**: ⚠️ Partial (may exist separately)  
**Location**: `backend/multi-tenant-inventory/` (if applicable)

**Purpose**:
- Track stock lots per client (anti-contamination)
- Implement RLS (Row-Level Security)
- Prevent cross-client material mixing

**Critical Rules**:
- Client_ID + Lot tracking
- Automatic block if client_id mismatch
- All queries filtered by client_id

**Will Consume From**:
- Financial Ledger (order data)

**Will Provide To**:
- All modules (client & product context)

---

## 🔗 Integration Matrix

| From \ To | MFG EX | QC | Payroll | Finance | Inventory |
|-----------|--------|----|-----------|---------| ----------|
| **Sampling R&D** | Time Std | TS Data | Time Std | Impact | Multi-T |
| **MFG EX** | - | Prod Status | Output | Costs | Stock |
| **QC** | - | - | Quality | Variance | Defects |
| **Payroll** | - | - | - | Entries | - |
| **Finance** | GL Data | GL Data | GL Data | - | GL Data |
| **Inventory** | Lots | Lots | - | GL Data | - |

- **Time Std**: Time standards from approved spec
- **TS Data**: Time study data for correlation
- **Prod Status**: Current production line status
- **Quality**: Quality scores for bonus calculation
- **Output**: Units produced for rate calc
- **Costs**: Cost entries from production
- **Variance**: Variance analysis from quality/time
- **Entries**: Journal entries to ledger
- **GL Data**: Chart of accounts, balancing entries
- **Multi-T**: Client isolation, filtering
- **Lots**: Stock lot tracking per client
- **Defects**: Defect data

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│         FINANCIAL LEDGER (Core - Double Entry)          │
│     (Immutable, Multi-tenant, RLS Protected)             │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│INVENTORY     │ │ SAMPLING &   │ │   (Future)   │
│Multi-Tenant  │ │ SPEC R&D     │ │  Costing     │
│(RLS, Lots)   │ │ (THIS)       │ │              │
└──────────────┘ └──────────┬───┘ └──────────────┘
        │                   │
        │         ┌─────────┼─────────┐
        │         │         │         │
        ▼         ▼         ▼         ▼
    ┌────────────────────────────────────┐
    │   MANUFACTURING EXECUTION          │
    │   (Production Lines, Tally)        │
    └────────────┬───────────────────────┘
                 │
         ┌───────┼───────┐
         │       │       │
         ▼       ▼       ▼
    ┌─────────────────────────────┐
    │   QC & MES                  │
    │   (Inspection, Defects)     │
    └────────┬────────────────────┘
             │
         ┌───┴───┐
         │       │
         ▼       ▼
    ┌──────────────────────┐
    │  PAYROLL & COSTING   │
    │ (Rate Calc, Bonus)   │
    └─────────────────────┘
```

---

## 🔐 Security & Multi-Tenancy

### Critical Rules (ALWAYS enforce)

1. **Client_ID Filtering**
```python
# WRONG
SELECT * FROM specs WHERE product_id = X

# RIGHT - filter by client_id first
SELECT * FROM specs 
WHERE client_id = auth_client_id 
  AND product_id = X
```

2. **Immutable Ledger**
```python
# WRONG
UPDATE ledger_entry SET amount = new_amount

# RIGHT - create reversal entry
INSERT ledger_entry (amount = -old_amount)
INSERT ledger_entry (amount = new_amount)
```

3. **Event Publishing**
- Always include client_id in event data
- Subscribers must filter by client_id
- Events use message queue for async safety

---

## 📋 Module Development Checklist

For each new module, ensure:

### Structure
- [ ] Follow `backend/module-name/src/{models,services,utils,api}` structure
- [ ] Create `README.md` and `API_CONTRACTS.md`
- [ ] Document integration points

### Security
- [ ] Multi-tenant filtering on all queries
- [ ] Row-level security (RLS) implemented
- [ ] Authentication/authorization middleware
- [ ] Input validation on all endpoints

### Integration
- [ ] Define data contracts (request/response)
- [ ] Define event schemas
- [ ] Document error codes
- [ ] Document timeout & retry policies
- [ ] Add integration tests

### Quality
- [ ] Unit tests for business logic
- [ ] Integration tests with dependent modules
- [ ] Error handling & logging
- [ ] API documentation
- [ ] Code follows naming conventions

---

## 🚀 Getting Started as New Module

1. **Copy template structure**
   ```bash
   mkdir -p backend/new-module/src/{models,services,utils,api}
   cp backend/sampling-spec-rnd/README.md backend/new-module/
   ```

2. **Define models** → `src/models/your_model.py`
   
3. **Implement services** → `src/services/your_service.py`
   
4. **Create API routes** → `src/api/your_routes.py`

5. **Document API contracts** → `API_CONTRACTS.md`

6. **Register in main app**
   ```python
   from backend.new_module.src.api import register_blueprints
   register_blueprints(app)
   ```

7. **Write tests** → `tests/`

8. **Add to MODULES_REFERENCE.md** (this file)

---

## 📞 Integration Support

**For questions about**:
- **Module structure**: See `backend/README.md`
- **Cross-module integration**: See `backend/INTEGRATION_ANALYSIS.md`
- **API contracts**: See `backend/[module]/API_CONTRACTS.md`
- **Code patterns**: See `backend/[module]/src/`

---

**Document Version**: 1.0  
**Last Updated**: 2026-10-13  
**Status**: ✅ Reference Ready
