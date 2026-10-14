"""
Sampling & Spec R&D Workflow Service
Orchestrates time study and specification tracking workflows
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from ..models.time_study_recorder import TimeStudyRecorder, TimeSample, StudyStatus
from ..models.spec_version_tracker import SpecVersionTracker, SpecChange, SpecDrift, ChangeType


class SamplingRnDWorkflow:
    """Main workflow orchestrator for sampling and spec R&D"""

    def __init__(self):
        self.active_studies: Dict[str, TimeStudyRecorder] = {}
        self.active_specs: Dict[str, SpecVersionTracker] = {}

    # ==================== TIME STUDY OPERATIONS ====================

    def create_time_study(
        self,
        tenant_id: str,
        process_id: str,
        process_name: str,
        operator_id: str,
        target_sample_size: int = 30,
    ) -> TimeStudyRecorder:
        """Create a new time study"""
        study = TimeStudyRecorder(
            tenant_id=tenant_id,
            process_id=process_id,
            process_name=process_name,
            operator_id=operator_id,
            target_sample_size=target_sample_size,
        )
        self.active_studies[study.study_id] = study
        return study

    def start_time_study(self, study_id: str) -> Tuple[bool, str]:
        """Start a time study"""
        if study_id not in self.active_studies:
            return False, "Study not found"

        study = self.active_studies[study_id]
        if study.start_study():
            return True, f"Study {study_id} started"
        return False, "Cannot start study in current status"

    def add_time_sample(
        self,
        study_id: str,
        cycle_time_ms: float,
        element_name: str,
        observations: Dict[str, Any] = None,
        is_abnormal: bool = False,
        notes: str = "",
    ) -> Tuple[bool, str]:
        """Add a time sample to a study"""
        if study_id not in self.active_studies:
            return False, "Study not found"

        study = self.active_studies[study_id]
        sample = TimeSample(
            cycle_time_ms=cycle_time_ms,
            element_name=element_name,
            observations=observations or {},
            operator_id=study.operator_id,
            machine_id=getattr(study, "machine_id", None),
            is_abnormal=is_abnormal,
            notes=notes,
        )

        if study.add_sample(sample):
            return True, f"Sample added. Progress: {study.total_cycles}/{study.target_sample_size}"
        return False, "Cannot add sample to study in current status"

    def complete_time_study(self, study_id: str) -> Tuple[bool, str]:
        """Complete a time study"""
        if study_id not in self.active_studies:
            return False, "Study not found"

        study = self.active_studies[study_id]
        if study.complete_study():
            result = self._analyze_study(study)
            return True, f"Study completed. {result}"
        return False, f"Cannot complete: need at least 1 sample (current: {len(study.samples)}, status: {study.status.value})"

    def pause_time_study(self, study_id: str) -> Tuple[bool, str]:
        """Pause a time study"""
        if study_id not in self.active_studies:
            return False, "Study not found"

        study = self.active_studies[study_id]
        if study.pause_study():
            return True, f"Study {study_id} paused"
        return False, "Cannot pause study in current status"

    def resume_time_study(self, study_id: str) -> Tuple[bool, str]:
        """Resume a paused time study"""
        if study_id not in self.active_studies:
            return False, "Study not found"

        study = self.active_studies[study_id]
        if study.resume_study():
            return True, f"Study {study_id} resumed"
        return False, "Cannot resume study in current status"

    def get_study_statistics(self, study_id: str) -> Dict[str, Any]:
        """Get statistical analysis of a study"""
        if study_id not in self.active_studies:
            return {}

        study = self.active_studies[study_id]
        if not study.samples:
            return {"status": "no_samples"}

        cycle_times = [s.cycle_time_ms for s in study.samples if not s.is_abnormal]
        normal_count = len(cycle_times)
        abnormal_count = len([s for s in study.samples if s.is_abnormal])

        return {
            "total_samples": len(study.samples),
            "normal_samples": normal_count,
            "abnormal_samples": abnormal_count,
            "mean_cycle_time_ms": study.mean_cycle_time,
            "std_dev": study.std_dev_cycle_time,
            "min_cycle_time_ms": study.min_cycle_time,
            "max_cycle_time_ms": study.max_cycle_time,
            "coeff_of_variation": (
                (study.std_dev_cycle_time / study.mean_cycle_time * 100)
                if study.mean_cycle_time > 0
                else 0
            ),
            "confidence_level": study.confidence_level,
            "allowance_percent": study.allowance_percent,
        }

    def _analyze_study(self, study: TimeStudyRecorder) -> str:
        """Analyze completed study and return summary"""
        stats = self.get_study_statistics(study.study_id)
        summary = (
            f"Mean: {stats['mean_cycle_time_ms']:.2f}ms, "
            f"StdDev: {stats['std_dev']:.2f}ms, "
            f"CV: {stats['coeff_of_variation']:.1f}%"
        )
        return summary

    # ==================== SPECIFICATION OPERATIONS ====================

    def create_spec_version(
        self,
        tenant_id: str,
        spec_id: str,
        spec_name: str,
        created_by: str,
        version_number: str = "1.0.0",
    ) -> SpecVersionTracker:
        """Create a new specification version"""
        spec = SpecVersionTracker(
            tenant_id=tenant_id,
            spec_id=spec_id,
            spec_name=spec_name,
            created_by=created_by,
            version_number=version_number,
        )
        self.active_specs[spec.version_id] = spec
        return spec

    def add_spec_change(
        self,
        version_id: str,
        change_type: ChangeType,
        parameter_name: str,
        old_value: Any,
        new_value: Any,
        changed_by: str,
        reason: str = "",
        impact_assessment: str = "",
    ) -> Tuple[bool, str]:
        """Record a change to a specification"""
        if version_id not in self.active_specs:
            return False, "Spec version not found"

        spec = self.active_specs[version_id]
        change = SpecChange(
            change_type=change_type,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason,
            impact_assessment=impact_assessment,
        )

        if spec.add_change(change):
            return True, f"Change recorded for {parameter_name}"
        return False, "Cannot add change to archived spec"

    def record_drift(
        self,
        version_id: str,
        parameter_name: str,
        specification_limit: float,
        measured_value: float,
        severity: str = "low",
        corrective_action: str = "",
    ) -> Tuple[bool, str]:
        """Record a specification drift"""
        if version_id not in self.active_specs:
            return False, "Spec version not found"

        spec = self.active_specs[version_id]
        deviation_percent = (
            abs(measured_value - specification_limit) / specification_limit * 100
            if specification_limit != 0
            else 0
        )

        drift = SpecDrift(
            parameter_name=parameter_name,
            specification_limit=specification_limit,
            measured_value=measured_value,
            deviation_percent=deviation_percent,
            severity=severity,
            corrective_action=corrective_action,
        )

        if spec.record_drift(drift):
            return True, f"Drift recorded: {deviation_percent:.2f}% deviation"
        return False, "Cannot record drift"

    def resolve_drift(
        self,
        version_id: str,
        drift_id: str,
        corrective_action: str,
    ) -> Tuple[bool, str]:
        """Resolve a recorded drift"""
        if version_id not in self.active_specs:
            return False, "Spec version not found"

        spec = self.active_specs[version_id]
        if spec.resolve_drift(drift_id, corrective_action):
            return True, f"Drift {drift_id} resolved"
        return False, "Drift not found or already resolved"

    def submit_spec_for_review(self, version_id: str, reviewer_id: str) -> Tuple[bool, str]:
        """Submit specification for review"""
        if version_id not in self.active_specs:
            return False, "Spec version not found"

        spec = self.active_specs[version_id]
        if spec.submit_for_review(reviewer_id):
            return True, f"Spec {version_id} submitted for review"
        return False, "Cannot submit spec in current status"

    def approve_spec(self, version_id: str, approver_id: str) -> Tuple[bool, str]:
        """Approve a specification version"""
        if version_id not in self.active_specs:
            return False, "Spec version not found"

        spec = self.active_specs[version_id]
        if spec.approve(approver_id):
            return True, f"Spec {version_id} approved"
        return False, "Cannot approve spec in current status"

    def activate_spec(self, version_id: str) -> Tuple[bool, str]:
        """Activate a specification as the current standard"""
        if version_id not in self.active_specs:
            return False, "Spec version not found"

        spec = self.active_specs[version_id]
        if spec.activate():
            return True, f"Spec {version_id} activated as current standard"
        return False, "Cannot activate spec in current status"

    def get_drift_report(self, version_id: str) -> Dict[str, Any]:
        """Get drift summary report"""
        if version_id not in self.active_specs:
            return {}

        spec = self.active_specs[version_id]
        return spec.get_drift_summary()

    def get_change_history(self, version_id: str, parameter_name: str = None) -> Dict[str, Any]:
        """Get change history for a parameter or entire spec"""
        if version_id not in self.active_specs:
            return {}

        spec = self.active_specs[version_id]
        if parameter_name:
            return {
                "parameter": parameter_name,
                "changes": spec.change_history.get(parameter_name, []),
            }
        return {"all_changes": spec.change_history}

    # ==================== EXPORT & REPORTING ====================

    def export_study_data(self, study_id: str) -> Dict[str, Any]:
        """Export complete study data"""
        if study_id not in self.active_studies:
            return {}

        study = self.active_studies[study_id]
        return study.to_dict()

    def export_spec_data(self, version_id: str) -> Dict[str, Any]:
        """Export complete specification data"""
        if version_id not in self.active_specs:
            return {}

        spec = self.active_specs[version_id]
        return spec.to_dict()

    def get_workflow_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get summary of active workflows for tenant"""
        active_studies = [
            s for s in self.active_studies.values() if s.tenant_id == tenant_id
        ]
        active_specs = [s for s in self.active_specs.values() if s.tenant_id == tenant_id]

        return {
            "active_studies": len([s for s in active_studies if s.status == StudyStatus.IN_PROGRESS]),
            "completed_studies": len([s for s in active_studies if s.status == StudyStatus.COMPLETED]),
            "active_specs": len([s for s in active_specs if s.status.value == "active"]),
            "specs_in_review": len([s for s in active_specs if s.status.value == "review"]),
            "total_drifts": sum(s.total_drifts for s in active_specs),
            "critical_drifts": sum(s.critical_drifts for s in active_specs),
        }
