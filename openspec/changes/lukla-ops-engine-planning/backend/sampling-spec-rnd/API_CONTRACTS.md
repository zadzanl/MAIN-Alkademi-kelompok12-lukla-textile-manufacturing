# API Contracts - SAMPLING & SPEC R&D Module

**This document defines the API contracts that other modules should use when integrating with Sampling & Spec R&D.**

---

## 📋 Table of Contents

1. [Time Study Endpoints](#time-study-endpoints)
2. [Spec Version Endpoints](#spec-version-endpoints)
3. [Event Subscriptions](#event-subscriptions)
4. [Error Codes](#error-codes)
5. [Integration Examples](#integration-examples)

---

## 🕐 Time Study Endpoints

### 1. Create Time Study

**Endpoint**: `POST /api/v1/time-studies`

**Request**:
```json
{
  "spec_id": "spec-prod-001-v1.0",
  "product_id": "prod-001",
  "operator": "operator-123",
  "phases": [
    {
      "name": "Potong",
      "duration": 120,
      "notes": "Normal pace"
    },
    {
      "name": "Jahit",
      "duration": 180,
      "notes": "Smooth execution"
    }
  ]
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": "ts-20261013-001",
    "spec_id": "spec-prod-001-v1.0",
    "product_id": "prod-001",
    "operator": "operator-123",
    "total_duration": 300,
    "phases": [...],
    "status": "completed",
    "created_at": "2026-10-13T10:00:00Z"
  }
}
```

**Used By**: 
- Manufacturing Execution (capture actual production times)
- QC & MES (for quality correlation)

---

### 2. List Time Studies

**Endpoint**: `GET /api/v1/time-studies`

**Query Parameters**:
```
?spec_id=spec-123
&product_id=prod-001
&status=completed
&limit=50
&offset=0
```

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    { time study 1 },
    { time study 2 }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

**Used By**: 
- Manufacturing Execution (reference for time standards)
- Payroll (for rate calculation)
- Finance (for costing analysis)

---

### 3. Get Time Study Detail

**Endpoint**: `GET /api/v1/time-studies/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": "ts-20261013-001",
    "spec_id": "spec-prod-001-v1.0",
    "phases": [...],
    "total_duration": 300,
    "created_at": "2026-10-13T10:00:00Z"
  }
}
```

---

### 4. Analyze Time Study

**Endpoint**: `POST /api/v1/time-studies/{id}/analyze`

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "time_study_id": "ts-20261013-001",
    "phase_analysis": [
      {
        "phase_name": "Jahit",
        "average": 180,
        "min": 170,
        "max": 190,
        "std_dev": 8.5
      }
    ],
    "quality_score": 95,
    "analyzed_at": "2026-10-13T10:05:00Z"
  }
}
```

**Used By**: 
- QC & MES (quality correlation analysis)
- Finance (efficiency variance calculation)

---

### 5. Correlate with Defects

**Endpoint**: `POST /api/v1/time-studies/{id}/correlate-defects`

**Request**:
```json
{
  "defect_type": "stitch_quality",
  "defect_rate": 0.05,
  "notes": "Quality dropped this period"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "correlation_score": 0.87,
    "has_strong_correlation": true,
    "recommendation": "Review spec changes from this period",
    "recommended_action": "trigger_rnd_review"
  }
}
```

**Used By**: 
- QC & MES (flag quality issues)
- R&D team (trigger investigation)

---

## 📋 Spec Version Endpoints

### 1. Create Spec Version

**Endpoint**: `POST /api/v1/spec-versions`

**Request**:
```json
{
  "product_id": "prod-001",
  "version_number": "1.0",
  "description": "Initial specification with 5mm padding",
  "specification": {
    "material": "Cotton 100%",
    "padding_mm": 5,
    "stitch_size_mm": 2,
    "quality_standard": "ISO 9001",
    "time_standards": {
      "potong": 120,
      "jahit": 180,
      "qc": 60,
      "total": 360
    }
  },
  "created_by": "rd-team",
  "changes": "Initial version from R&D"
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": "spec-prod-001-v1.0",
    "product_id": "prod-001",
    "version_number": "1.0",
    "status": "draft",
    "created_at": "2026-10-13T10:00:00Z",
    "change_history": [...]
  }
}
```

**Used By**: 
- R&D team (create specifications)
- Manufacturing (get standards)

---

### 2. List Spec Versions

**Endpoint**: `GET /api/v1/spec-versions`

**Query Parameters**:
```
?product_id=prod-001
&status=approved
&limit=50
```

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "spec-prod-001-v1.0",
      "product_id": "prod-001",
      "version_number": "1.0",
      "status": "approved",
      "created_at": "2026-10-13T10:00:00Z"
    }
  ],
  "total": 1
}
```

**Used By**: 
- Manufacturing Execution
- QC & MES
- Payroll & Costing

---

### 3. Get Spec Version Detail

**Endpoint**: `GET /api/v1/spec-versions/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": "spec-prod-001-v1.0",
    "specification": {
      "material": "Cotton 100%",
      "padding_mm": 5,
      "time_standards": {...}
    },
    "status": "approved",
    "change_history": [...]
  }
}
```

**Used By**: 
- All modules needing spec details

---

### 4. Update Spec Status

**Endpoint**: `PATCH /api/v1/spec-versions/{id}/status`

**Request**:
```json
{
  "status": "approved",
  "approver": "qc-manager",
  "reason": "Time study shows 10% improvement"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": "spec-prod-001-v1.0",
    "status": "approved",
    "updated_at": "2026-10-13T11:00:00Z"
  }
}
```

**Publishes Event**: `spec.version.approved` (see Events section)

---

### 5. Compare Versions

**Endpoint**: `POST /api/v1/spec-versions/{id}/compare`

**Request**:
```json
{
  "compare_with_id": "spec-prod-001-v1.1"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "version1": "1.0",
    "version2": "1.1",
    "differences": [
      {
        "field": "padding_mm",
        "from": 5,
        "to": 4
      }
    ],
    "total_changes": 1
  }
}
```

---

### 6. Check R&D Drift

**Endpoint**: `POST /api/v1/spec-versions/{id}/drift-check`

**Request**:
```json
{
  "baseline_version_id": "spec-prod-001-v1.0",
  "critical_fields": ["material", "padding_mm", "stitch_size_mm"]
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "has_critical_drift": false,
    "drift_count": 0,
    "drifts": [],
    "warnings": [],
    "checked_at": "2026-10-13T11:00:00Z"
  }
}
```

**Used By**: 
- QC & MES (detect quality issues)
- Manufacturing (flag spec violations)

---

## 📡 Event Subscriptions

### Event: `spec.version.published`

**When**: Spec version is approved and published

**Schema**:
```json
{
  "type": "spec.version.published",
  "data": {
    "spec_id": "spec-prod-001-v1.0",
    "product_id": "prod-001",
    "version_number": "1.0",
    "time_standards": {
      "potong": 120,
      "jahit": 180,
      "qc": 60
    },
    "specification": {...},
    "effective_date": "2026-10-20",
    "published_by": "qc-manager"
  },
  "timestamp": "2026-10-13T11:00:00Z"
}
```

**Subscribers**:
- Manufacturing Execution (update production targets)
- Payroll & Costing (update rate calculations)
- Finance Ledger (prepare cost entries)

---

### Event: `time-study.recorded`

**When**: Time study is recorded and saved

**Schema**:
```json
{
  "type": "time-study.recorded",
  "data": {
    "time_study_id": "ts-20261013-001",
    "spec_id": "spec-prod-001-v1.0",
    "product_id": "prod-001",
    "total_duration": 300,
    "operator": "operator-123",
    "phases": [...],
    "recorded_at": "2026-10-13T10:00:00Z"
  },
  "timestamp": "2026-10-13T10:05:00Z"
}
```

**Subscribers**:
- QC & MES (for quality analysis)
- Analytics (for trend analysis)

---

### Event: `rnd-drift.detected`

**When**: R&D drift is detected during analysis

**Schema**:
```json
{
  "type": "rnd-drift.detected",
  "data": {
    "spec_id": "spec-prod-001-v1.1",
    "baseline_spec_id": "spec-prod-001-v1.0",
    "drift_percent": 18.5,
    "critical_fields": ["padding_mm"],
    "severity": "high",
    "recommendation": "immediate_review_required"
  },
  "timestamp": "2026-10-13T11:00:00Z"
}
```

**Subscribers**:
- R&D team (alert for investigation)
- QC & MES (flag production for review)
- Manufacturing Execution (pause or monitor line)

---

## ❌ Error Codes

### Standard HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 201 | Created | POST /time-studies success |
| 200 | OK | GET request successful |
| 400 | Bad Request | Missing required field |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | No access to this client's data |
| 404 | Not Found | Time study ID doesn't exist |
| 409 | Conflict | Cannot approve already approved version |
| 500 | Server Error | Database error |

### Error Response Format

```json
{
  "success": false,
  "error": "Descriptive error message",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "spec_id",
    "reason": "must be non-empty"
  }
}
```

### Specific Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| VALIDATION_ERROR | 400 | Input validation failed |
| NOT_FOUND | 404 | Resource doesn't exist |
| ALREADY_APPROVED | 409 | Cannot modify approved version |
| PERMISSION_DENIED | 403 | User doesn't have access |
| TENANT_MISMATCH | 403 | Resource belongs to different client |
| DRIFT_DETECTED | 422 | R&D drift prevents operation |
| INTERNAL_ERROR | 500 | Server error |

---

## 🔌 Integration Examples

### Example 1: Manufacturing Execution Module

```python
# manufacturing-execution/src/services/production_service.py

import requests

class ProductionService:
    def __init__(self, api_base_url):
        self.api_base = api_base_url
    
    def get_time_standards(self, product_id):
        """Get approved spec with time standards"""
        response = requests.get(
            f'{self.api_base}/api/v1/spec-versions',
            params={
                'product_id': product_id,
                'status': 'approved'
            }
        )
        if response.status_code == 200:
            specs = response.json()['data']
            return specs[0]['specification']['time_standards']
        return None
    
    def set_line_targets(self, line_id, product_id):
        """Set production line targets based on spec"""
        time_standards = self.get_time_standards(product_id)
        # Update line targets
        self.db.update_line_targets(
            line_id=line_id,
            target_total_time=time_standards['total'],
            phases=time_standards
        )
```

---

### Example 2: Payroll Module

```python
# payroll-costing/src/services/rate_service.py

import requests

class RateService:
    def calculate_worker_rate(self, worker_id, product_id, actual_output):
        """Calculate pay rate based on spec time standard"""
        # Get spec
        response = requests.get(
            f'{api_base}/api/v1/spec-versions',
            params={'product_id': product_id, 'status': 'approved'}
        )
        spec = response.json()['data'][0]
        
        # Calculate efficiency
        standard_time = spec['specification']['time_standards']['total']
        expected_output = 3600 / standard_time  # units per hour
        efficiency = actual_output / expected_output
        
        # Calculate rate
        base_rate = self.get_base_rate(product_id)
        worker_rate = base_rate * efficiency
        
        return worker_rate
```

---

### Example 3: Event Subscription

```python
# manufacturing-execution/src/services/event_handler.py

from backend.shared.events import EventBus

class EventHandler:
    def __init__(self):
        # Subscribe to spec published event
        EventBus.subscribe(
            'spec.version.published',
            self.handle_spec_published
        )
    
    def handle_spec_published(self, event):
        """Handle when new spec is published"""
        spec_data = event['data']
        
        # Update all production lines for this product
        self.update_product_parameters(
            product_id=spec_data['product_id'],
            time_standards=spec_data['time_standards'],
            effective_date=spec_data['effective_date']
        )
        
        # Notify operators
        self.send_notification(
            message=f"New spec {spec_data['version_number']} is now active"
        )
```

---

## 📚 Related Documentation

- **Module README**: `backend/sampling-spec-rnd/README.md`
- **Integration Guide**: `backend/INTEGRATION_ANALYSIS.md`
- **Backend README**: `backend/README.md`
- **Data Models**: `backend/sampling-spec-rnd/src/models/`
- **Source Code**: `backend/sampling-spec-rnd/src/api/`

---

**Document Version**: 1.0  
**Last Updated**: 2026-10-13  
**Status**: ✅ Ready for Integration
