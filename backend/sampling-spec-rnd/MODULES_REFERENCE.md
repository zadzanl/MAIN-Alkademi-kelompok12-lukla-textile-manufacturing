# Sampling & Spec R&D - Modules Reference

Complete module specifications and integration guide for backend components.

## Module Structure

### models/
Data layer - Immutable, versioned, fully audited

#### TimeStudyRecorder
Time study data model with full lifecycle management.

**Key Classes:**
- `TimeSample`: Individual cycle measurement
- `TimeStudyRecorder`: Study container and orchestrator
- `StudyStatus`: Enum (draft, in_progress, paused, completed, archived)

**Key Methods:**
```python
# Study management
start_study() -> bool
pause_study() -> bool
resume_study() -> bool
complete_study() -> bool

# Sample management
add_sample(sample: TimeSample) -> bool

# Statistics
_compute_statistics() -> None  # Auto-calculates mean, std_dev, min, max

# Serialization
to_dict() -> Dict[str, Any]
from_dict(data: Dict) -> TimeStudyRecorder
```

**Data Preservation:**
- Immutable audit trail (samples list)
- Timestamp all operations
- Never modify historical data

#### SpecVersionTracker
Specification version model with drift tracking.

**Key Classes:**
- `SpecChange`: Single modification to spec
- `SpecDrift`: Deviation from spec with severity
- `SpecVersionTracker`: Version container
- `VersionStatus`: Enum (draft, review, approved, active, superseded, archived)
- `ChangeType`: Enum (creation, parameter_update, tolerance_change, etc.)

**Key Methods:**
```python
# Change tracking
add_change(change: SpecChange) -> bool
get_drift_summary() -> Dict[str, Any]

# Drift management
record_drift(drift: SpecDrift) -> bool
resolve_drift(drift_id: str, corrective_action: str) -> bool

# Workflow
submit_for_review(reviewer_id: str) -> bool
approve(approver_id: str) -> bool
activate() -> bool
supersede(new_version_id: str) -> bool

# Analysis
get_drift_summary() -> Dict[str, Any]

# Serialization
to_dict() -> Dict[str, Any]
from_dict(data: Dict) -> SpecVersionTracker
```

### services/
Business logic layer - Orchestration, validation, workflows

#### SamplingRnDWorkflow
Main workflow orchestrator for both time study and spec management.

**Initialization:**
```python
workflow = SamplingRnDWorkflow()
```

**Time Study Operations:**
```python
# Create and manage studies
study = workflow.create_time_study(
    tenant_id: str,
    process_id: str,
    process_name: str,
    operator_id: str,
    target_sample_size: int = 30
) -> TimeStudyRecorder

# Control study
success, msg = workflow.start_time_study(study_id: str) -> Tuple[bool, str]
success, msg = workflow.pause_time_study(study_id: str) -> Tuple[bool, str]
success, msg = workflow.resume_time_study(study_id: str) -> Tuple[bool, str]
success, msg = workflow.complete_time_study(study_id: str) -> Tuple[bool, str]

# Record samples
success, msg = workflow.add_time_sample(
    study_id: str,
    cycle_time_ms: float,
    element_name: str,
    observations: Dict = None,
    is_abnormal: bool = False,
    notes: str = ""
) -> Tuple[bool, str]

# Analysis
stats = workflow.get_study_statistics(study_id: str) -> Dict[str, Any]
data = workflow.export_study_data(study_id: str) -> Dict[str, Any]
```

**Specification Operations:**
```python
# Create versions
spec = workflow.create_spec_version(
    tenant_id: str,
    spec_id: str,
    spec_name: str,
    created_by: str,
    version_number: str = "1.0.0"
) -> SpecVersionTracker

# Record changes
success, msg = workflow.add_spec_change(
    version_id: str,
    change_type: ChangeType,
    parameter_name: str,
    old_value: Any,
    new_value: Any,
    changed_by: str,
    reason: str = "",
    impact_assessment: str = ""
) -> Tuple[bool, str]

# Record drifts
success, msg = workflow.record_drift(
    version_id: str,
    parameter_name: str,
    specification_limit: float,
    measured_value: float,
    severity: str = "low",
    corrective_action: str = ""
) -> Tuple[bool, str]

success, msg = workflow.resolve_drift(
    version_id: str,
    drift_id: str,
    corrective_action: str
) -> Tuple[bool, str]

# Workflow
success, msg = workflow.submit_spec_for_review(version_id, reviewer_id) -> Tuple[bool, str]
success, msg = workflow.approve_spec(version_id, approver_id) -> Tuple[bool, str]
success, msg = workflow.activate_spec(version_id) -> Tuple[bool, str]

# Reporting
report = workflow.get_drift_report(version_id) -> Dict[str, Any]
history = workflow.get_change_history(version_id, parameter_name) -> Dict[str, Any]
data = workflow.export_spec_data(version_id) -> Dict[str, Any]
```

**Tenant Operations:**
```python
summary = workflow.get_workflow_summary(tenant_id: str) -> Dict[str, Any]
# Returns: active_studies, completed_studies, active_specs, specs_in_review, 
#          total_drifts, critical_drifts
```

### utils/
Analysis and pattern detection utilities

#### time_study_patterns.py

**Functions:**

```python
# Main analysis
analyze_time_patterns(cycle_times: List[float]) -> Dict[str, Any]
# Returns: mean, median, std_dev, q1, q3, iqr, cv, min, max, range,
#          trend, distribution, sample_count

# Outlier detection
detect_outliers(
    cycle_times: List[float],
    method: str = "iqr",    # or "zscore"
    threshold: float = 1.5
) -> Dict[str, Any]
# Returns: outliers list, count, indices, percentage

# Standard time calculation
calculate_standard_time(
    mean_cycle_time: float,
    confidence_level: float = 0.95,
    allowance_percent: float = 15.0
) -> Dict[str, float]
# Returns: mean, normal_time, allowance, standard_time
```

**Internal Functions:**
```python
_detect_trend(values: List[float]) -> str
# Returns: "increasing", "decreasing", or "stable"

_classify_distribution(values, mean, stdev) -> str
# Returns: "normal", "left_skewed", or "right_skewed"
```

#### spec_version_patterns.py

**Functions:**

```python
# Change analysis
track_spec_changes(changes: List[Dict]) -> Dict[str, Any]
# Returns: total_changes, by_type, by_parameter, most_changed_parameter,
#          change_frequency_per_day, parameters_affected

# Drift analysis
identify_drift_trends(drifts: List[Dict]) -> Dict[str, Any]
# Returns: total_drifts, severity_distribution, by_parameter,
#          critical_parameters, critical_rate_percent, trend, parameters_with_drift

# Risk assessment
calculate_drift_risk_score(drift_data: Dict) -> float
# Returns: 0-100 risk score

# Recommendations
get_drift_recommendations(drift_data: Dict) -> List[str]
# Returns: actionable recommendations

# Version comparison
compare_spec_versions(version1_data, version2_data) -> Dict[str, Any]
# Returns: changes, modified parameters, impact level
```

### api/
REST API routes - HTTP interface

#### routes.py

**Router Setup:**
```python
router = create_api_router()
# Creates FastAPI APIRouter with all endpoints
# Include in FastAPI app: app.include_router(router)
```

**Time Study Endpoints:**
- `POST /studies/create` - Create new study
- `POST /studies/{study_id}/start` - Start study
- `POST /studies/{study_id}/add-sample` - Add sample
- `POST /studies/{study_id}/complete` - Complete study
- `POST /studies/{study_id}/pause` - Pause study
- `POST /studies/{study_id}/resume` - Resume study
- `GET /studies/{study_id}/stats` - Get statistics
- `GET /studies/{study_id}/data` - Export data

**Specification Endpoints:**
- `POST /specs/create` - Create version
- `POST /specs/{version_id}/record-change` - Record change
- `POST /specs/{version_id}/record-drift` - Record drift
- `POST /specs/{version_id}/resolve-drift/{drift_id}` - Resolve drift
- `POST /specs/{version_id}/submit-review` - Submit review
- `POST /specs/{version_id}/approve` - Approve
- `POST /specs/{version_id}/activate` - Activate
- `GET /specs/{version_id}/drift-report` - Drift report
- `GET /specs/{version_id}/drift-analysis` - Detailed analysis
- `GET /specs/{version_id}/change-history` - Change history
- `GET /specs/{version_id}/data` - Export data

**Workflow Endpoints:**
- `GET /workflow/summary?tenant_id=...` - Tenant summary
- `GET /health` - Health check

## Integration Patterns

### 1. Direct Import Pattern
Use when integrating from another Python module:

```python
from backend.sampling_spec_rnd.src.services import SamplingRnDWorkflow
from backend.sampling_spec_rnd.src.models import TimeStudyRecorder

workflow = SamplingRnDWorkflow()
study = workflow.create_time_study(...)
```

### 2. HTTP API Pattern
Use when integrating from external systems/frontend:

```python
import requests

response = requests.post(
    'http://localhost:8000/api/sampling-spec-rnd/studies/create',
    params={
        'tenant_id': 'default',
        'process_id': 'proc_001',
        'process_name': 'Assembly A',
        'operator_id': 'op_001'
    }
)
```

### 3. Async Workflow Pattern
For batch operations:

```python
from concurrent.futures import ThreadPoolExecutor

def batch_process_samples(study_id, samples):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(workflow.add_time_sample, study_id, s)
            for s in samples
        ]
        results = [f.result() for f in futures]
    return results
```

## Data Flow

### Time Study Flow
```
CREATE → ADD_SAMPLES → ANALYZE → EXPORT
         ↓
      STATISTICS (auto-computed)
         ↓
      PATTERNS (outlier detection, trends)
```

### Specification Flow
```
CREATE → CHANGES → REVIEW → APPROVE → ACTIVATE
         ↓                              ↓
      DRIFTS (monitored)         SUPERSEDE (next version)
         ↓
      RISK_SCORE (trending analysis)
```

## Performance Considerations

- **Workflow.active_studies/active_specs**: In-memory cache (consider DB for scale)
- **Statistics computation**: O(n) on add_sample, cached in model
- **Outlier detection**: O(n log n) sorting
- **Drift risk scoring**: O(d) where d = number of drifts

## Multi-Tenancy

All operations require `tenant_id`:
- Data isolation at workflow level
- No cross-tenant queries
- Tenant-specific summaries

## Error Handling

All workflow operations return `Tuple[bool, str]`:
- `success`: Operation completed successfully
- `message`: Result or error description

API endpoints raise `HTTPException(status_code, detail)` on errors.

## Testing Strategy

```python
# Unit tests for models
def test_time_study_lifecycle():
    study = TimeStudyRecorder(...)
    assert study.start_study()
    assert study.status == StudyStatus.IN_PROGRESS

# Integration tests for workflow
def test_workflow_integration():
    workflow = SamplingRnDWorkflow()
    study = workflow.create_time_study(...)
    workflow.start_time_study(study.study_id)
    # ... add samples, complete

# E2E tests for API
def test_api_create_study(client):
    response = client.post('/api/sampling-spec-rnd/studies/create', ...)
    assert response.status_code == 200
```

## Versioning

Current: **1.0.0**

No breaking changes planned. New features added via:
1. Optional parameters
2. New utility functions
3. New endpoints

## Dependencies

- Python 3.8+
- fastapi
- uvicorn
- python-multipart

## Support

See module docstrings for detailed usage examples.
