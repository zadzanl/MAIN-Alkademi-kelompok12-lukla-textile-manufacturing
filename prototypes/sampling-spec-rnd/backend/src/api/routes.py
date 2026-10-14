"""
API Routes for Sampling & Spec R&D Module
FastAPI router — Time Study, Spec Version, Sample Versioning, Workflow

IMPORTANT: Static routes (e.g. /studies/all, /studies/create) MUST be
registered BEFORE parameterised routes (/studies/{study_id}/...) so that
FastAPI does not swallow them as path-parameter values.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from ..models.time_study_recorder import TimeStudyRecorder, StudyStatus
from ..models.spec_version_tracker import SpecVersionTracker, ChangeType
from ..services.sampling_rnd_workflow import SamplingRnDWorkflow
from ..utils.time_study_patterns import analyze_time_patterns, detect_outliers
from ..utils.spec_version_patterns import identify_drift_trends, calculate_drift_risk_score


def create_api_router() -> APIRouter:
    """Create and configure the API router"""
    router = APIRouter(prefix="/api/sampling-spec-rnd", tags=["sampling-spec-rnd"])
    workflow = SamplingRnDWorkflow()

    # In-memory store for sample versions (new feature)
    # Structure: { version_id: SampleVersionRecord }
    sample_versions: Dict[str, Dict[str, Any]] = {}

    # ================================================================
    # HEALTH + WORKFLOW  (no path params — always first)
    # ================================================================

    @router.get("/health")
    def health_check() -> Dict[str, str]:
        """Health check endpoint"""
        return {"status": "healthy", "module": "sampling-spec-rnd"}

    @router.get("/workflow/summary")
    def get_workflow_summary(tenant_id: str = Query(...)) -> Dict[str, Any]:
        """Get workflow summary for tenant"""
        summary = workflow.get_workflow_summary(tenant_id)

        # Augment with sample-version counts
        tenant_svs = [sv for sv in sample_versions.values() if sv["tenant_id"] == tenant_id]
        summary["total_sample_versions"] = len(tenant_svs)
        summary["pending_approval"] = len([sv for sv in tenant_svs if sv["status"] == "pending_approval"])
        summary["converted_to_order"] = len([sv for sv in tenant_svs if sv["status"] == "converted"])

        return {"success": True, "summary": summary}

    # ================================================================
    # TIME STUDY — static routes first
    # ================================================================

    @router.get("/studies/all")
    def get_all_studies(tenant_id: str = Query(...)) -> Dict[str, Any]:
        """List all time studies for a tenant"""
        result = []
        for study in workflow.active_studies.values():
            if study.tenant_id == tenant_id:
                result.append(workflow.export_study_data(study.study_id))
        return {"success": True, "data": result, "count": len(result)}

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

    # ----------------------------------------------------------------
    # TIME STUDY — parameterised routes
    # ----------------------------------------------------------------

    @router.post("/studies/{study_id}/start")
    def start_study(study_id: str) -> Dict[str, Any]:
        success, message = workflow.start_time_study(study_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/studies/{study_id}/pause")
    def pause_study(study_id: str) -> Dict[str, Any]:
        success, message = workflow.pause_time_study(study_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/studies/{study_id}/resume")
    def resume_study(study_id: str) -> Dict[str, Any]:
        success, message = workflow.resume_time_study(study_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/studies/{study_id}/complete")
    def complete_study(study_id: str) -> Dict[str, Any]:
        success, message = workflow.complete_time_study(study_id)
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
        return {"success": True, "message": message, "study_id": study_id}

    @router.get("/studies/{study_id}/stats")
    def get_study_stats(study_id: str) -> Dict[str, Any]:
        stats = workflow.get_study_statistics(study_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Study not found")
        return {"success": True, "statistics": stats}

    @router.get("/studies/{study_id}/data")
    def get_study_data(study_id: str) -> Dict[str, Any]:
        data = workflow.export_study_data(study_id)
        if not data:
            raise HTTPException(status_code=404, detail="Study not found")
        return {"success": True, "data": data}

    # ================================================================
    # SPEC VERSION — static routes first
    # ================================================================

    @router.get("/specs/all")
    def get_all_specs(tenant_id: str = Query(...)) -> Dict[str, Any]:
        """List all spec versions for a tenant"""
        result = []
        for spec in workflow.active_specs.values():
            if spec.tenant_id == tenant_id:
                result.append(workflow.export_spec_data(spec.version_id))
        return {"success": True, "data": result, "count": len(result)}

    @router.post("/specs/create")
    def create_spec(
        tenant_id: str = Query(...),
        spec_id: str = Query(...),
        spec_name: str = Query(...),
        created_by: str = Query(...),
        version_number: str = Query("1.0.0"),
    ) -> Dict[str, Any]:
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

    # ----------------------------------------------------------------
    # SPEC VERSION — parameterised routes
    # ----------------------------------------------------------------

    @router.post("/specs/{version_id}/record-change")
    def record_spec_change(
        version_id: str,
        change_type: str = Query(...),
        parameter_name: str = Query(...),
        old_value: str = Query(...),
        new_value: str = Query(...),
        changed_by: str = Query(...),
        reason: str = Query(""),
        impact_assessment: str = Query(""),
    ) -> Dict[str, Any]:
        try:
            change_type_enum = ChangeType[change_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid change type: {change_type}. Valid: {[e.name for e in ChangeType]}",
            )

        def parse_value(v: str) -> Any:
            try:
                return int(v)
            except ValueError:
                try:
                    return float(v)
                except ValueError:
                    return v

        success, message = workflow.add_spec_change(
            version_id=version_id,
            change_type=change_type_enum,
            parameter_name=parameter_name,
            old_value=parse_value(old_value),
            new_value=parse_value(new_value),
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
    def resolve_drift(version_id: str, drift_id: str, corrective_action: str = Query(...)) -> Dict[str, Any]:
        success, message = workflow.resolve_drift(version_id, drift_id, corrective_action)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/specs/{version_id}/submit-review")
    def submit_for_review(version_id: str, reviewer_id: str = Query(...)) -> Dict[str, Any]:
        success, message = workflow.submit_spec_for_review(version_id, reviewer_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/specs/{version_id}/approve")
    def approve_spec(version_id: str, approver_id: str = Query(...)) -> Dict[str, Any]:
        success, message = workflow.approve_spec(version_id, approver_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.post("/specs/{version_id}/activate")
    def activate_spec(version_id: str) -> Dict[str, Any]:
        success, message = workflow.activate_spec(version_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    @router.get("/specs/{version_id}/drift-report")
    def get_drift_report(version_id: str) -> Dict[str, Any]:
        report = workflow.get_drift_report(version_id)
        if not report:
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"success": True, "report": report}

    @router.get("/specs/{version_id}/drift-analysis")
    def get_drift_analysis(version_id: str) -> Dict[str, Any]:
        data = workflow.export_spec_data(version_id)
        if not data:
            raise HTTPException(status_code=404, detail="Spec not found")
        drifts = data.get("drifts", [])
        drift_analysis = identify_drift_trends(drifts)
        risk_score = calculate_drift_risk_score(drift_analysis)
        return {"success": True, "version_id": version_id, "analysis": drift_analysis, "risk_score": round(risk_score, 1)}

    @router.get("/specs/{version_id}/change-history")
    def get_change_history(version_id: str, parameter_name: Optional[str] = Query(None)) -> Dict[str, Any]:
        history = workflow.get_change_history(version_id, parameter_name)
        if history is None:
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"success": True, "history": history}

    @router.get("/specs/{version_id}/data")
    def get_spec_data(version_id: str) -> Dict[str, Any]:
        data = workflow.export_spec_data(version_id)
        if not data:
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"success": True, "data": data}

    # ================================================================
    # SAMPLE VERSION (New Feature — Version History per Article/SKU)
    # ================================================================

    @router.get("/sample-versions/all")
    def list_sample_versions(tenant_id: str = Query(...)) -> Dict[str, Any]:
        """List all sample versions for a tenant"""
        result = [sv for sv in sample_versions.values() if sv["tenant_id"] == tenant_id]
        result.sort(key=lambda x: x["created_at"], reverse=True)
        return {"success": True, "data": result, "count": len(result)}

    @router.post("/sample-versions/create")
    def create_sample_version(
        tenant_id: str = Query(...),
        article_id: str = Query(...),
        article_name: str = Query(...),
        client_id: str = Query(...),
        created_by: str = Query(...),
        notes: str = Query(""),
        body: Optional[Dict[str, Any]] = Body(None),
    ) -> Dict[str, Any]:
        """
        Create initial sample version (v1) for an article.
        Body (optional JSON): { components: [...], materials: [...] }
        """
        now = datetime.utcnow().isoformat()

        # Find existing versions for this article to determine version number
        existing = [
            sv for sv in sample_versions.values()
            if sv["tenant_id"] == tenant_id and sv["article_id"] == article_id
        ]
        version_num = len(existing) + 1
        version_label = f"v{version_num}"

        parent_id = None
        if existing:
            # Link to latest version
            existing_sorted = sorted(existing, key=lambda x: x["version_number"])
            parent_id = existing_sorted[-1]["version_id"]

        sv_id = str(uuid.uuid4())
        sv = {
            "version_id": sv_id,
            "tenant_id": tenant_id,
            "article_id": article_id,
            "article_name": article_name,
            "client_id": client_id,
            "version_number": version_num,
            "version_label": version_label,
            "parent_version_id": parent_id,
            "status": "draft",          # draft → pending_approval → approved → converted
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
            "approved_by": None,
            "approved_at": None,
            "converted_to_order_id": None,
            "notes": notes,
            # Component specifications per garment part
            "components": (body or {}).get("components", []),
            # Material estimation list
            "materials": (body or {}).get("materials", []),
            # Revision notes history (immutable append-only)
            "revision_log": [
                {"action": "created", "by": created_by, "at": now, "note": notes or f"Initial {version_label}"}
            ],
        }
        sample_versions[sv_id] = sv
        return {"success": True, "version_id": sv_id, "version_label": version_label, "status": "draft"}

    @router.post("/sample-versions/{version_id}/new-revision")
    def create_new_revision(
        version_id: str,
        revised_by: str = Query(...),
        revision_note: str = Query(...),
        body: Optional[Dict[str, Any]] = Body(None),
    ) -> Dict[str, Any]:
        """
        Branch a new revision from an existing version (v1 → v2 → v3…).
        Carry forward components + materials unless overridden in body.
        """
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")

        parent = sample_versions[version_id]
        now = datetime.utcnow().isoformat()

        existing = [
            sv for sv in sample_versions.values()
            if sv["tenant_id"] == parent["tenant_id"] and sv["article_id"] == parent["article_id"]
        ]
        new_version_num = len(existing) + 1
        new_label = f"v{new_version_num}"

        new_sv_id = str(uuid.uuid4())
        new_sv = {
            **parent,
            "version_id": new_sv_id,
            "version_number": new_version_num,
            "version_label": new_label,
            "parent_version_id": version_id,
            "status": "draft",
            "created_by": revised_by,
            "created_at": now,
            "updated_at": now,
            "approved_by": None,
            "approved_at": None,
            "converted_to_order_id": None,
            "notes": revision_note,
            # Merge overrides from body
            "components": (body or {}).get("components", parent["components"]),
            "materials": (body or {}).get("materials", parent["materials"]),
            "revision_log": [
                *parent["revision_log"],
                {"action": "revised", "by": revised_by, "at": now, "note": revision_note},
            ],
        }
        sample_versions[new_sv_id] = new_sv
        return {
            "success": True,
            "version_id": new_sv_id,
            "version_label": new_label,
            "parent_version_id": version_id,
            "status": "draft",
        }

    @router.post("/sample-versions/{version_id}/submit-approval")
    def submit_sample_for_approval(
        version_id: str,
        submitted_by: str = Query(...),
    ) -> Dict[str, Any]:
        """Submit a sample version for approval"""
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] != "draft":
            raise HTTPException(status_code=400, detail=f"Cannot submit from status: {sv['status']}")
        now = datetime.utcnow().isoformat()
        sv["status"] = "pending_approval"
        sv["updated_at"] = now
        sv["revision_log"].append({"action": "submitted_for_approval", "by": submitted_by, "at": now, "note": ""})
        return {"success": True, "version_id": version_id, "status": "pending_approval"}

    @router.post("/sample-versions/{version_id}/approve")
    def approve_sample_version(
        version_id: str,
        approved_by: str = Query(...),
        approval_note: str = Query(""),
    ) -> Dict[str, Any]:
        """Approve a sample version"""
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] != "pending_approval":
            raise HTTPException(status_code=400, detail=f"Cannot approve from status: {sv['status']}")
        now = datetime.utcnow().isoformat()
        sv["status"] = "approved"
        sv["approved_by"] = approved_by
        sv["approved_at"] = now
        sv["updated_at"] = now
        sv["revision_log"].append({"action": "approved", "by": approved_by, "at": now, "note": approval_note})
        return {"success": True, "version_id": version_id, "status": "approved"}

    @router.post("/sample-versions/{version_id}/convert-to-order")
    def convert_sample_to_order(
        version_id: str,
        order_id: str = Query(...),
        converted_by: str = Query(...),
    ) -> Dict[str, Any]:
        """
        Mark an approved sample version as converted to Mass Order.
        Registers the downstream order_id for traceability.
        """
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] != "approved":
            raise HTTPException(status_code=400, detail="Only approved versions can be converted to order")
        now = datetime.utcnow().isoformat()
        sv["status"] = "converted"
        sv["converted_to_order_id"] = order_id
        sv["updated_at"] = now
        sv["revision_log"].append({
            "action": "converted_to_order",
            "by": converted_by,
            "at": now,
            "note": f"Linked to order {order_id}",
        })
        return {"success": True, "version_id": version_id, "order_id": order_id, "status": "converted"}

    @router.put("/sample-versions/{version_id}/components")
    def update_components(
        version_id: str,
        updated_by: str = Query(...),
        body: Dict[str, Any] = Body(...),
    ) -> Dict[str, Any]:
        """
        Replace component list for a draft sample version.
        body: { components: [ { part_name, description, material_type, estimated_usage_m, unit, notes } ] }
        """
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] not in ("draft",):
            raise HTTPException(status_code=400, detail="Components can only be edited on draft versions")
        now = datetime.utcnow().isoformat()
        sv["components"] = body.get("components", sv["components"])
        sv["updated_at"] = now
        sv["revision_log"].append({"action": "components_updated", "by": updated_by, "at": now, "note": f"{len(sv['components'])} components saved"})
        return {"success": True, "version_id": version_id, "component_count": len(sv["components"])}

    @router.put("/sample-versions/{version_id}/materials")
    def update_materials(
        version_id: str,
        updated_by: str = Query(...),
        body: Dict[str, Any] = Body(...),
    ) -> Dict[str, Any]:
        """
        Replace material estimation list for a draft sample version.
        body: { materials: [ { material_code, material_name, estimated_usage, unit, unit_cost, total_cost } ] }
        """
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] not in ("draft",):
            raise HTTPException(status_code=400, detail="Materials can only be edited on draft versions")
        now = datetime.utcnow().isoformat()
        sv["materials"] = body.get("materials", sv["materials"])
        sv["updated_at"] = now
        total_cost = sum(float(m.get("total_cost", 0)) for m in sv["materials"])
        sv["revision_log"].append({"action": "materials_updated", "by": updated_by, "at": now, "note": f"Est. cost: {total_cost:.2f}"})
        return {"success": True, "version_id": version_id, "material_count": len(sv["materials"]), "estimated_total_cost": total_cost}

    @router.get("/sample-versions/{version_id}")
    def get_sample_version(version_id: str) -> Dict[str, Any]:
        """Get a single sample version with full detail"""
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        return {"success": True, "data": sample_versions[version_id]}

    @router.get("/sample-versions/article/{article_id}/history")
    def get_version_history(article_id: str, tenant_id: str = Query(...)) -> Dict[str, Any]:
        """Get full version history for an article (v1 → v2 → v3…)"""
        history = [
            sv for sv in sample_versions.values()
            if sv["tenant_id"] == tenant_id and sv["article_id"] == article_id
        ]
        history.sort(key=lambda x: x["version_number"])
        return {"success": True, "article_id": article_id, "versions": history, "total_versions": len(history)}

    return router
