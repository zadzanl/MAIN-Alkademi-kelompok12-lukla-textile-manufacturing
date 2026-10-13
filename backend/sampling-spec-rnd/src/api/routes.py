"""
API Routes for Sampling & Spec R&D Module
FastAPI router for time study and specification endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Import models and services
from ..models.time_study_recorder import TimeStudyRecorder, StudyStatus
from ..models.spec_version_tracker import SpecVersionTracker, ChangeType
from ..services.sampling_rnd_workflow import SamplingRnDWorkflow
from ..utils.time_study_patterns import analyze_time_patterns, detect_outliers
from ..utils.spec_version_patterns import identify_drift_trends, calculate_drift_risk_score


def create_api_router() -> APIRouter:
    """Create and configure the API router"""
    router = APIRouter(prefix="/api/sampling-spec-rnd", tags=["sampling-spec-rnd"])
    workflow = SamplingRnDWorkflow()

    # ==================== TIME STUDY ENDPOINTS ====================

    @router.post("/studies/create")
    def create_study(
        tenant_id: str = Query(...),
        process_id: str = Query(...),
        process_name: str = Query(...),
        operator_id: str = Query(...),
        target_sample_size: int = Query(30),
    ) -> Dict[str, Any]:
        """Create a new time study"""
        try:
            study = workflow.create_time_study(
                tenant_id=tenant_id,
                process_id=process_id,
                process_name=process_name,
                operator_id=operator_id,
                target_sample_size=target_sample_size,
            )
            return {
                "success": True,
                "study_id": study.study_id,
                "status": study.status.value,
                "message": f"Study created: {study.study_id}",
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/studies/{study_id}/start")
    def start_study(study_id: str) -> Dict[str, Any]:
        """Start a time study"""
        success, message = workflow.start_time_study(study_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/studies/{study_id}/add-sample")
    def add_sample(
        study_id: str,
        cycle_time_ms: float = Query(...),
        element_name: str = Query(""),
        is_abnormal: bool = Query(False),
        notes: str = Query(""),
        observations: Optional[Dict[str, Any]] = Body(None),
    ) -> Dict[str, Any]:
        """Add a time sample to a study"""
        success, message = workflow.add_time_sample(
            study_id=study_id,
            cycle_time_ms=cycle_time_ms,
            element_name=element_name,
            observations=observations or {},
            is_abnormal=is_abnormal,
            notes=notes,
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {
            "success": True,
            "message": message,
            "study_id": study_id,
        }

    @router.post("/studies/{study_id}/complete")
    def complete_study(study_id: str) -> Dict[str, Any]:
        """Complete a time study"""
        success, message = workflow.complete_time_study(study_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/studies/{study_id}/pause")
    def pause_study(study_id: str) -> Dict[str, Any]:
        """Pause a time study"""
        success, message = workflow.pause_time_study(study_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/studies/{study_id}/resume")
    def resume_study(study_id: str) -> Dict[str, Any]:
        """Resume a time study"""
        success, message = workflow.resume_time_study(study_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.get("/studies/{study_id}/stats")
    def get_study_stats(study_id: str) -> Dict[str, Any]:
        """Get statistical analysis of a study"""
        stats = workflow.get_study_statistics(study_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Study not found")
        return {"success": True, "statistics": stats}

    @router.get("/studies/{study_id}/data")
    def get_study_data(study_id: str) -> Dict[str, Any]:
        """Export complete study data"""
        data = workflow.export_study_data(study_id)
        if not data:
            raise HTTPException(status_code=404, detail="Study not found")
        return {"success": True, "data": data}

    # ==================== SPECIFICATION ENDPOINTS ====================

    @router.post("/specs/create")
    def create_spec(
        tenant_id: str = Query(...),
        spec_id: str = Query(...),
        spec_name: str = Query(...),
        created_by: str = Query(...),
        version_number: str = Query("1.0.0"),
    ) -> Dict[str, Any]:
        """Create a new specification version"""
        try:
            spec = workflow.create_spec_version(
                tenant_id=tenant_id,
                spec_id=spec_id,
                spec_name=spec_name,
                created_by=created_by,
                version_number=version_number,
            )
            return {
                "success": True,
                "version_id": spec.version_id,
                "status": spec.status.value,
                "message": f"Spec version created: {spec.version_id}",
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/specs/{version_id}/record-change")
    def record_spec_change(
        version_id: str,
        change_type: str = Query(...),
        parameter_name: str = Query(...),
        old_value: Any = Body(...),
        new_value: Any = Body(...),
        changed_by: str = Query(...),
        reason: str = Query(""),
        impact_assessment: str = Query(""),
    ) -> Dict[str, Any]:
        """Record a change to a specification"""
        try:
            change_type_enum = ChangeType[change_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid change type: {change_type}")

        success, message = workflow.add_spec_change(
            version_id=version_id,
            change_type=change_type_enum,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason,
            impact_assessment=impact_assessment,
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/specs/{version_id}/record-drift")
    def record_drift(
        version_id: str,
        parameter_name: str = Query(...),
        specification_limit: float = Query(...),
        measured_value: float = Query(...),
        severity: str = Query("low"),
        corrective_action: str = Query(""),
    ) -> Dict[str, Any]:
        """Record a specification drift"""
        success, message = workflow.record_drift(
            version_id=version_id,
            parameter_name=parameter_name,
            specification_limit=specification_limit,
            measured_value=measured_value,
            severity=severity,
            corrective_action=corrective_action,
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/specs/{version_id}/resolve-drift/{drift_id}")
    def resolve_drift(
        version_id: str,
        drift_id: str,
        corrective_action: str = Query(...),
    ) -> Dict[str, Any]:
        """Resolve a recorded drift"""
        success, message = workflow.resolve_drift(
            version_id=version_id,
            drift_id=drift_id,
            corrective_action=corrective_action,
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/specs/{version_id}/submit-review")
    def submit_for_review(
        version_id: str,
        reviewer_id: str = Query(...),
    ) -> Dict[str, Any]:
        """Submit spec for review"""
        success, message = workflow.submit_spec_for_review(version_id, reviewer_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/specs/{version_id}/approve")
    def approve_spec(
        version_id: str,
        approver_id: str = Query(...),
    ) -> Dict[str, Any]:
        """Approve a specification version"""
        success, message = workflow.approve_spec(version_id, approver_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/specs/{version_id}/activate")
    def activate_spec(version_id: str) -> Dict[str, Any]:
        """Activate a specification"""
        success, message = workflow.activate_spec(version_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.get("/specs/{version_id}/drift-report")
    def get_drift_report(version_id: str) -> Dict[str, Any]:
        """Get drift summary report"""
        report = workflow.get_drift_report(version_id)
        if not report:
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"success": True, "report": report}

    @router.get("/specs/{version_id}/drift-analysis")
    def get_drift_analysis(version_id: str) -> Dict[str, Any]:
        """Get detailed drift analysis with trends and recommendations"""
        data = workflow.export_spec_data(version_id)
        if not data:
            raise HTTPException(status_code=404, detail="Spec not found")
        
        drifts = data.get("drifts", [])
        drift_analysis = identify_drift_trends(drifts)
        risk_score = calculate_drift_risk_score(drift_analysis)
        
        return {
            "success": True,
            "version_id": version_id,
            "analysis": drift_analysis,
            "risk_score": round(risk_score, 1),
        }

    @router.get("/specs/{version_id}/change-history")
    def get_change_history(
        version_id: str,
        parameter_name: Optional[str] = Query(None),
    ) -> Dict[str, Any]:
        """Get change history"""
        history = workflow.get_change_history(version_id, parameter_name)
        if not history:
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"success": True, "history": history}

    @router.get("/specs/{version_id}/data")
    def get_spec_data(version_id: str) -> Dict[str, Any]:
        """Export complete specification data"""
        data = workflow.export_spec_data(version_id)
        if not data:
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"success": True, "data": data}

    # ==================== WORKFLOW ENDPOINTS ====================

    @router.get("/workflow/summary")
    def get_workflow_summary(tenant_id: str = Query(...)) -> Dict[str, Any]:
        """Get workflow summary for tenant"""
        summary = workflow.get_workflow_summary(tenant_id)
        return {"success": True, "summary": summary}

    @router.get("/health")
    def health_check() -> Dict[str, str]:
        """Health check endpoint"""
        return {"status": "healthy", "module": "sampling-spec-rnd"}

    return router
