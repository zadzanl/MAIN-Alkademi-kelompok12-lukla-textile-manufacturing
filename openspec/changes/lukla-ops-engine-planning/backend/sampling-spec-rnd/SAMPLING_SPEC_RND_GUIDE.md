# SAMPLING & SPEC R&D Module - Guide

Quick reference guide untuk Vibe Coding modul SAMPLING & SPEC R&D (Time Study, Versions).

## 🎯 Module Overview

Modul ini handle:
- **Time Study Recording**: Capture waktu untuk setiap fase produksi
- **Spec Versioning**: Track perubahan spesifikasi produk dari waktu ke waktu
- **R&D Drift Detection**: Deteksi perubahan tidak terdokumentasi dalam spesifikasi
- **Analysis & Reporting**: Analisa time study data dan generate reports

## 📦 Available Components

### 1. TimeStudyRecorder (Python)
Untuk merekam time study dengan support multiple phases

```python
from components.time_study_recorder import TimeStudyRecorder

# Create recorder
recorder = TimeStudyRecorder(spec_id='spec-123', product_id='prod-001')

# Record phases
recorder.start_timer()
recorder.record_phase('Potong', duration=120, notes='Normal')
recorder.record_phase('Jahit', duration=180, notes='Smooth')

# Get data
phases = recorder.get_phases()
total_time = recorder.get_total_duration()

# Validate & save
if recorder.validate()['is_valid']:
    recorder.save_to_db()
```

**Key Methods**:
- `start_timer()` / `stop_timer()` - Manage timer
- `record_phase(name, duration, notes)` - Record satu fase
- `get_phases()` - Get all recorded phases
- `get_total_duration()` - Total time sum
- `get_average_phase_time(phase_name)` - Average untuk specific phase
- `delete_phase(phase_id)` - Delete satu phase
- `reset()` - Reset recorder
- `validate()` - Validate data
- `to_dict()` - Convert ke dictionary
- `save_to_db()` - Save ke database

### 2. SpecVersionTracker (Python)
Untuk track versi spesifikasi produk

```python
from components.spec_version_tracker import SpecVersionTracker, VersionStatus

# Create tracker
tracker = SpecVersionTracker(product_id='prod-001')

# Create version
version = tracker.create_version(
    version_number='1.0',
    description='Initial spec',
    specification={
        'material': 'Cotton 100%',
        'padding_mm': 5,
        'stitch_size_mm': 2,
    },
    created_by='rd-team'
)

# Update status
tracker.update_version_status(version['id'], VersionStatus.APPROVED)

# Compare versions
comparison = tracker.compare_versions(v1_id, v2_id)

# Save
tracker.save_to_db()
```

**Key Methods**:
- `create_version(...)` - Create versi baru
- `get_versions(status)` - Get versions (optional filter by status)
- `get_version_by_id(id)` - Get specific version
- `update_version_status(id, status, reason)` - Update status
- `add_change_note(id, note, type)` - Add change note
- `get_change_history(id)` - Get history untuk version
- `compare_versions(id1, id2)` - Compare dua versions
- `validate()` - Validate tracker data
- `to_dict()` - Convert ke dictionary
- `save_to_db()` - Save ke database

## 🔨 Available Patterns (Snippets)

### Time Study Patterns
File: `snippets/time_study_patterns.py`

**Available Functions**:
1. `create_time_study_model()` - Standard data model
2. `calculate_average_phase_time(studies, phase_name)` - Average time per phase
3. `calculate_quality_score(actual, expected, tolerance)` - Quality score calculation
4. `compare_spec_versions(v1_studies, v2_studies, phase)` - Compare versions
5. `detect_rnd_drift(historical, current, threshold)` - **R&D Drift Detection**
6. `validate_time_study(study)` - Validate time study
7. `generate_time_study_report(studies, spec_version)` - Generate report
8. `export_time_study_to_csv(studies, spec_version)` - Export to CSV

### Spec Version Patterns
File: `snippets/spec_version_patterns.py`

**Available Functions**:
1. `create_spec_version_model()` - Standard version model
2. `track_spec_change(version, type, fields, actor)` - Track changes
3. `check_spec_compliance(current, approved, tolerance)` - Compliance check
4. `trace_version_lineage(versions, target_id)` - Trace version history
5. `detect_spec_drift(reference, current, critical_fields)` - **Spec Drift Detection**
6. `diff_versions(v1, v2)` - Generate diff antar versions
7. `generate_change_report(version)` - Generate human-readable report
8. `export_version_history_to_csv(versions)` - Export to CSV
9. `approve_spec_version(version, approver, notes)` - Approve version

## 📚 Complete Example Workflow

File: `examples/sampling_rd_workflow.py`

**Class**: `SamplingRnDWorkflow`

```python
from examples.sampling_rd_workflow import SamplingRnDWorkflow

# Initialize
workflow = SamplingRnDWorkflow(product_id='shirt-001')

# Step 1: Create initial spec
spec_v1 = workflow.create_initial_spec(
    version_number='1.0',
    description='Initial spec',
    specification={'material': 'Cotton', 'padding': 5}
)

# Step 2: Record time studies
workflow.record_time_study_session(
    spec_version_id=spec_v1['id'],
    operator_name='Operator-1',
    phases_data=[
        {'name': 'Potong', 'duration': 120},
        {'name': 'Jahit', 'duration': 180},
    ]
)

# Step 3: Analyze
analysis = workflow.analyze_time_studies(spec_v1['id'])

# Step 4: Create improved spec
spec_v1_1 = workflow.create_improved_spec(
    previous_version_id=spec_v1['id'],
    new_version_number='1.1',
    changes={'padding': 4},
    change_reason='Reduce padding'
)

# Step 5: Record time studies untuk v1.1
workflow.record_time_study_session(...)

# Step 6: Check drift
drift = workflow.check_for_rnd_drift(spec_v1['id'], spec_v1_1['id'])

# Step 7: Approve
workflow.approve_spec(spec_v1_1['id'], approver='QC-Manager')

# Step 8: Summary
summary = workflow.generate_workflow_summary()
```

**Key Methods**:
- `create_initial_spec(...)` - Phase 1: Create initial
- `record_time_study_session(...)` - Phase 2: Record time studies
- `analyze_time_studies(...)` - Phase 3: Analyze data
- `create_improved_spec(...)` - Phase 4: Iterate spec
- `check_for_rnd_drift(...)` - Phase 5: Detect drift
- `approve_spec(...)` - Phase 6: Approve version
- `generate_workflow_summary()` - Phase 7: Generate docs

## 🚀 Common Vibe Coding Scenarios

### Scenario 1: Quick Time Study Recording
```python
from components.time_study_recorder import TimeStudyRecorder

recorder = TimeStudyRecorder('spec-123', 'prod-001')
recorder.record_phase('Potong', 120)
recorder.record_phase('Jahit', 180)
recorder.record_phase('QC', 60)

# Get average untuk Jahit phase
avg = recorder.get_average_phase_time('Jahit')
```

### Scenario 2: Compare Two Spec Versions
```python
from snippets.time_study_patterns import compare_spec_versions

result = compare_spec_versions(
    v1_studies,
    v2_studies,
    phase_name='Jahit'
)

print(f"V1 avg: {result['version1_avg_time']}s")
print(f"V2 avg: {result['version2_avg_time']}s")
print(f"Improvement: {result['improvement_percentage']}%")
```

### Scenario 3: Detect R&D Drift
```python
from snippets.spec_version_patterns import detect_spec_drift

drift_result = detect_spec_drift(
    reference_spec={'material': 'Cotton', 'padding': 5},
    current_spec={'material': 'Cotton', 'padding': 4},
    critical_fields={'material'}
)

if drift_result['has_critical_drift']:
    print("WARNING: Critical field changed!")
```

### Scenario 4: Generate Report
```python
from snippets.time_study_patterns import generate_time_study_report
from snippets.spec_version_patterns import generate_change_report

# Time study report
ts_report = generate_time_study_report(time_studies, spec_version='1.0')

# Spec change report
change_report = generate_change_report(version)
print(change_report)
```

## 📋 Naming Conventions

Ikuti naming standards di `conventions/NAMING_CONVENTIONS.md`

**Python Classes**:
```python
class TimeStudyRecorder:  # PascalCase
    def record_phase(self):  # snake_case untuk methods
```

**Variables**:
```python
spec_id = "spec-123"  # snake_case
total_duration = 300  # descriptive names
phase_records = []  # plural untuk collections
```

**Constants**:
```python
DEFAULT_TOLERANCE = 10.0  # UPPER_SNAKE_CASE
MAX_PHASES_PER_STUDY = 50
```

**Database/API**:
```python
# Tables (snake_case, plural)
time_studies
spec_versions
operator_logs

# Columns (snake_case)
spec_id, product_id, created_at, created_by

# API Endpoints
GET /api/v1/time-studies
POST /api/v1/time-studies
GET /api/v1/time-studies/:id
PUT /api/v1/time-studies/:id
```

## 🔍 Tips untuk Vibe Coding

### ✅ DO:
- Cek INVENTORY.md dulu sebelum bikin dari scratch
- Gunakan `TimeStudyRecorder` dan `SpecVersionTracker` sebagai starting point
- Copy patterns dari `snippets/` dan modify sesuai kebutuhan
- Reference `sampling_rd_workflow.py` untuk full workflow
- Add documentation & comments
- Update INVENTORY.md saat tambah components baru

### ❌ DON'T:
- Bikin duplicate functionality
- Use inconsistent naming
- Forget to validate data
- Skip error handling
- Hardcode values - gunakan constants

## 📞 Quick Reference Links

| Item | Path |
|------|------|
| Python Components | `components/time_study_recorder.py` |
| | `components/spec_version_tracker.py` |
| Python Patterns | `snippets/time_study_patterns.py` |
| | `snippets/spec_version_patterns.py` |
| Full Workflow | `examples/sampling_rd_workflow.py` |
| All Items | `INVENTORY.md` |
| Naming Standards | `conventions/NAMING_CONVENTIONS.md` |

## 🎓 Learning Path

1. **Understand the Module**: Baca PRD untuk SAMPLING & SPEC R&D
2. **Review Components**: Lihat `time_study_recorder.py` dan `spec_version_tracker.py`
3. **Learn Patterns**: Explore functions di `time_study_patterns.py`
4. **Study Example**: Baca `sampling_rd_workflow.py` untuk full context
5. **Start Coding**: Copy component, modify, integrate
6. **Share Results**: Save improved code ke OpenCode, update INVENTORY

---

**Module Version**: 1.0  
**Last Updated**: 2026-10-13  
**Status**: Ready for Vibe Coding ✅
