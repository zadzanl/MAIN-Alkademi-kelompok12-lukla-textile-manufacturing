"""
Specification Version Tracker Model
Tracks version history and spec drift for manufacturing specifications
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid


class VersionStatus(Enum):
    """Status of a specification version"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ChangeType(Enum):
    """Type of change made to specification"""
    CREATION = "creation"
    PARAMETER_UPDATE = "parameter_update"
    TOLERANCE_CHANGE = "tolerance_change"
    MATERIAL_CHANGE = "material_change"
    PROCESS_CHANGE = "process_change"
    OTHER = "other"


@dataclass
class SpecChange:
    """Individual change to a specification"""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    change_type: ChangeType = ChangeType.OTHER
    parameter_name: str = ""
    old_value: Any = None
    new_value: Any = None
    changed_by: str = ""
    reason: str = ""
    impact_assessment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "change_id": self.change_id,
            "timestamp": self.timestamp.isoformat(),
            "change_type": self.change_type.value,
            "parameter_name": self.parameter_name,
            "old_value": str(self.old_value),
            "new_value": str(self.new_value),
            "changed_by": self.changed_by,
            "reason": self.reason,
            "impact_assessment": self.impact_assessment,
        }


@dataclass
class SpecDrift:
    """Specification drift record"""
    drift_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    parameter_name: str = ""
    specification_limit: float = 0.0
    measured_value: float = 0.0
    deviation_percent: float = 0.0
    severity: str = "low"  # low, medium, high, critical
    corrective_action: str = ""
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "drift_id": self.drift_id,
            "timestamp": self.timestamp.isoformat(),
            "parameter_name": self.parameter_name,
            "specification_limit": self.specification_limit,
            "measured_value": self.measured_value,
            "deviation_percent": self.deviation_percent,
            "severity": self.severity,
            "corrective_action": self.corrective_action,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class SpecVersionTracker:
    """Main specification version tracking model"""
    version_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    spec_id: str = ""
    spec_name: str = ""
    version_number: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: VersionStatus = VersionStatus.DRAFT
    
    # Specification data
    parameters: Dict[str, Any] = field(default_factory=dict)
    tolerances: Dict[str, Dict[str, float]] = field(default_factory=dict)
    materials: List[str] = field(default_factory=list)
    process_steps: List[str] = field(default_factory=list)
    
    # Change tracking
    changes: List[SpecChange] = field(default_factory=list)
    change_history: Dict[str, List[Any]] = field(default_factory=dict)
    
    # Drift tracking
    drifts: List[SpecDrift] = field(default_factory=list)
    total_drifts: int = 0
    critical_drifts: int = 0
    
    # Metadata
    created_by: str = ""
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: str = ""
    
    # Relationships
    parent_version_id: Optional[str] = None
    supersedes_version_id: Optional[str] = None

    def add_change(self, change: SpecChange) -> bool:
        """Record a change to the specification"""
        if self.status == VersionStatus.ARCHIVED:
            return False
        
        self.changes.append(change)
        
        # Track change history by parameter
        if change.parameter_name not in self.change_history:
            self.change_history[change.parameter_name] = []
        self.change_history[change.parameter_name].append(change.to_dict())
        
        self.updated_at = datetime.utcnow()
        return True

    def record_drift(self, drift: SpecDrift) -> bool:
        """Record a specification drift"""
        self.drifts.append(drift)
        self.total_drifts += 1
        
        if drift.severity == "critical":
            self.critical_drifts += 1
        
        self.updated_at = datetime.utcnow()
        return True

    def resolve_drift(self, drift_id: str, corrective_action: str) -> bool:
        """Mark a drift as resolved"""
        for drift in self.drifts:
            if drift.drift_id == drift_id:
                drift.resolved = True
                drift.resolved_at = datetime.utcnow()
                drift.corrective_action = corrective_action
                self.updated_at = datetime.utcnow()
                return True
        return False

    def submit_for_review(self, reviewer_id: str) -> bool:
        """Submit version for review"""
        if self.status != VersionStatus.DRAFT:
            return False
        
        self.status = VersionStatus.REVIEW
        self.updated_at = datetime.utcnow()
        return True

    def approve(self, approver_id: str) -> bool:
        """Approve the specification version"""
        if self.status not in [VersionStatus.REVIEW]:
            return False
        
        self.status = VersionStatus.APPROVED
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True

    def activate(self) -> bool:
        """Activate this version as the current specification"""
        if self.status != VersionStatus.APPROVED:
            return False
        
        self.status = VersionStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        return True

    def supersede(self, new_version_id: str) -> bool:
        """Mark this version as superseded"""
        if self.status != VersionStatus.ACTIVE:
            return False
        
        self.status = VersionStatus.SUPERSEDED
        self.supersedes_version_id = new_version_id
        self.updated_at = datetime.utcnow()
        return True

    def get_drift_summary(self) -> Dict[str, Any]:
        """Get summary of drifts"""
        return {
            "total_drifts": self.total_drifts,
            "critical_drifts": self.critical_drifts,
            "resolved_drifts": len([d for d in self.drifts if d.resolved]),
            "pending_drifts": len([d for d in self.drifts if not d.resolved]),
            "severity_distribution": self._get_severity_distribution(),
        }

    def _get_severity_distribution(self) -> Dict[str, int]:
        """Calculate severity distribution of drifts"""
        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for drift in self.drifts:
            if drift.severity in distribution:
                distribution[drift.severity] += 1
        return distribution

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API"""
        return {
            "version_id": self.version_id,
            "tenant_id": self.tenant_id,
            "spec_id": self.spec_id,
            "spec_name": self.spec_name,
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "parameters": self.parameters,
            "tolerances": self.tolerances,
            "materials": self.materials,
            "process_steps": self.process_steps,
            "changes": [c.to_dict() for c in self.changes],
            "drifts": [d.to_dict() for d in self.drifts],
            "total_drifts": self.total_drifts,
            "critical_drifts": self.critical_drifts,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "notes": self.notes,
            "parent_version_id": self.parent_version_id,
            "supersedes_version_id": self.supersedes_version_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpecVersionTracker":
        """Create instance from dictionary"""
        instance = cls(
            version_id=data.get("version_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", ""),
            spec_id=data.get("spec_id", ""),
            spec_name=data.get("spec_name", ""),
            version_number=data.get("version_number", "1.0.0"),
            status=VersionStatus(data.get("status", "draft")),
            parameters=data.get("parameters", {}),
            tolerances=data.get("tolerances", {}),
            materials=data.get("materials", []),
            process_steps=data.get("process_steps", []),
            created_by=data.get("created_by", ""),
            notes=data.get("notes", ""),
        )
        return instance
