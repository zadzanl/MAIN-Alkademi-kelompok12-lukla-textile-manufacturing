"""
Time Study Recorder Model
Records time studies for manufacturing processes with sampling data
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StudyStatus(Enum):
    """Status of a time study"""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class TimeSample:
    """Individual time sample within a study"""

    sample_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cycle_time_ms: float = 0.0
    element_name: str = ""
    observations: dict[str, Any] = field(default_factory=dict)
    operator_id: str | None = None
    machine_id: str | None = None
    is_abnormal: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/API"""
        return {
            "sample_id": self.sample_id,
            "timestamp": self.timestamp.isoformat(),
            "cycle_time_ms": self.cycle_time_ms,
            "element_name": self.element_name,
            "observations": self.observations,
            "operator_id": self.operator_id,
            "machine_id": self.machine_id,
            "is_abnormal": self.is_abnormal,
            "notes": self.notes,
        }


@dataclass
class TimeStudyRecorder:
    """Main time study recording model"""

    study_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    process_id: str = ""
    process_name: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: StudyStatus = StudyStatus.DRAFT

    # Study parameters
    target_sample_size: int = 30
    samples: list[TimeSample] = field(default_factory=list)
    confidence_level: float = 0.95
    allowance_percent: float = 15.0

    # Metadata
    operator_id: str = ""
    department_id: str = ""
    shift: str = ""
    product_id: str = ""
    notes: str = ""

    # Computed statistics
    total_cycles: int = 0
    mean_cycle_time: float = 0.0
    std_dev_cycle_time: float = 0.0
    min_cycle_time: float = 0.0
    max_cycle_time: float = 0.0

    def add_sample(self, sample: TimeSample) -> bool:
        """Add a time sample to the study"""
        if self.status not in [StudyStatus.IN_PROGRESS]:
            return False

        self.samples.append(sample)
        self.total_cycles = len(self.samples)
        self.updated_at = datetime.utcnow()
        self._compute_statistics()
        return True

    def _compute_statistics(self) -> None:
        """Compute statistical measures"""
        if not self.samples:
            return

        cycle_times = [s.cycle_time_ms for s in self.samples if not s.is_abnormal]
        if not cycle_times:
            return

        import statistics

        self.mean_cycle_time = statistics.mean(cycle_times)
        self.std_dev_cycle_time = statistics.stdev(cycle_times) if len(cycle_times) > 1 else 0.0
        self.min_cycle_time = min(cycle_times)
        self.max_cycle_time = max(cycle_times)

    def start_study(self) -> bool:
        """Start the time study"""
        if self.status != StudyStatus.DRAFT:
            return False

        self.status = StudyStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True

    def pause_study(self) -> bool:
        """Pause the time study"""
        if self.status != StudyStatus.IN_PROGRESS:
            return False

        self.status = StudyStatus.PAUSED
        self.updated_at = datetime.utcnow()
        return True

    def resume_study(self) -> bool:
        """Resume a paused study"""
        if self.status != StudyStatus.PAUSED:
            return False

        self.status = StudyStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
        return True

    def complete_study(self) -> bool:
        """Mark study as completed"""
        if self.status not in [StudyStatus.IN_PROGRESS, StudyStatus.PAUSED]:
            return False

        if len(self.samples) < 1:  # min 1 sample, 30 is recommendation
            return False

        self.status = StudyStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/API"""
        return {
            "study_id": self.study_id,
            "tenant_id": self.tenant_id,
            "process_id": self.process_id,
            "process_name": self.process_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "target_sample_size": self.target_sample_size,
            "samples": [s.to_dict() for s in self.samples],
            "confidence_level": self.confidence_level,
            "allowance_percent": self.allowance_percent,
            "operator_id": self.operator_id,
            "department_id": self.department_id,
            "shift": self.shift,
            "product_id": self.product_id,
            "notes": self.notes,
            "total_cycles": self.total_cycles,
            "mean_cycle_time": self.mean_cycle_time,
            "std_dev_cycle_time": self.std_dev_cycle_time,
            "min_cycle_time": self.min_cycle_time,
            "max_cycle_time": self.max_cycle_time,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimeStudyRecorder":
        """Create instance from dictionary"""
        instance = cls(
            study_id=data.get("study_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", ""),
            process_id=data.get("process_id", ""),
            process_name=data.get("process_name", ""),
            status=StudyStatus(data.get("status", "draft")),
            target_sample_size=data.get("target_sample_size", 30),
            confidence_level=data.get("confidence_level", 0.95),
            allowance_percent=data.get("allowance_percent", 15.0),
            operator_id=data.get("operator_id", ""),
            department_id=data.get("department_id", ""),
            shift=data.get("shift", ""),
            product_id=data.get("product_id", ""),
            notes=data.get("notes", ""),
        )
        return instance
