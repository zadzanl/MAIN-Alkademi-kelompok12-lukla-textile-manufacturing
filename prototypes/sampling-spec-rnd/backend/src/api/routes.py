"""
API Routes for Sampling & Spec R&D Module

STATIC routes MUST be registered BEFORE parameterised routes.

Bug-fix log (this revision):
  #1 — get_drift_report / get_drift_summary now always returns a valid dict,
        never an empty dict, so 404 false-positive is eliminated.
  #2 — /sample-versions/all, /sample-versions/create, and
        /sample-versions/article/{article_id}/history are now registered
        BEFORE /sample-versions/{version_id}/...  to avoid path-param swallow.
  #3 — get_workflow_summary now guards against specs whose .status might be
        a raw string instead of a VersionStatus enum (defensive .value call).
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from ..models.spec_version_tracker import ChangeType
from ..services.sampling_rnd_workflow import SamplingRnDWorkflow
from ..services.seed import save_state, seed_sampling_rnd
from ..utils.spec_version_patterns import calculate_drift_risk_score, identify_drift_trends


def _status_val(s: Any) -> str:
    """Safely extract string value from either a VersionStatus enum or a plain string."""
    return s.value if hasattr(s, "value") else str(s)


def create_api_router(seed: bool = True) -> APIRouter:
    router = APIRouter(prefix="/api/sampling-spec-rnd", tags=["sampling-spec-rnd"])
    workflow = SamplingRnDWorkflow()
    sample_versions: dict[str, dict[str, Any]] = {}

    if seed:
        seed_sampling_rnd(workflow, sample_versions)

    # ════════════════════════════════════════════════════════════════════
    # HEALTH + WORKFLOW
    # ════════════════════════════════════════════════════════════════════

    @router.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "healthy", "module": "sampling-spec-rnd"}

    @router.get("/workflow/summary")
    def get_workflow_summary(tenant_id: str = Query(...)) -> dict[str, Any]:
        """Get workflow summary — BUG-FIX #3: guard against raw-string status."""
        # Defensive recalculation using the safe status extractor.
        active_studies_safe = sum(
            1
            for s in workflow.active_studies.values()
            if s.tenant_id == tenant_id and _status_val(s.status) == "in_progress"
        )
        completed_studies_safe = sum(
            1
            for s in workflow.active_studies.values()
            if s.tenant_id == tenant_id and _status_val(s.status) == "completed"
        )
        active_specs_safe = sum(
            1
            for s in workflow.active_specs.values()
            if s.tenant_id == tenant_id and _status_val(s.status) == "active"
        )
        specs_in_review_safe = sum(
            1
            for s in workflow.active_specs.values()
            if s.tenant_id == tenant_id and _status_val(s.status) == "review"
        )
        total_drifts_safe = sum(
            getattr(s, "total_drifts", 0)
            for s in workflow.active_specs.values()
            if s.tenant_id == tenant_id
        )
        critical_drifts_safe = sum(
            getattr(s, "critical_drifts", 0)
            for s in workflow.active_specs.values()
            if s.tenant_id == tenant_id
        )

        tenant_svs = [sv for sv in sample_versions.values() if sv["tenant_id"] == tenant_id]

        summary = {
            "active_studies": active_studies_safe,
            "completed_studies": completed_studies_safe,
            "active_specs": active_specs_safe,
            "specs_in_review": specs_in_review_safe,
            "total_drifts": total_drifts_safe,
            "critical_drifts": critical_drifts_safe,
            "total_sample_versions": len(tenant_svs),
            "pending_approval": sum(1 for sv in tenant_svs if sv["status"] == "pending_approval"),
            "converted_to_order": sum(1 for sv in tenant_svs if sv["status"] == "converted"),
        }
        return {"success": True, "summary": summary}

    # ════════════════════════════════════════════════════════════════════
    # TIME STUDY — static first, then parameterised
    # ════════════════════════════════════════════════════════════════════

    @router.get("/studies/all")
    def get_all_studies(tenant_id: str = Query(...)) -> dict[str, Any]:
        result = [
            workflow.export_study_data(s.study_id)
            for s in workflow.active_studies.values()
            if s.tenant_id == tenant_id
        ]
        return {"success": True, "data": result, "count": len(result)}

    @router.post("/studies/create")
    def create_study(
        tenant_id: str = Query(...),
        process_id: str = Query(...),
        process_name: str = Query(...),
        operator_id: str = Query(...),
        target_sample_size: int = Query(30),
    ) -> dict[str, Any]:
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
            raise HTTPException(status_code=400, detail=str(e)) from e

    # --- parameterised ---

    @router.post("/studies/{study_id}/start")
    def start_study(study_id: str) -> dict[str, Any]:
        ok, msg = workflow.start_time_study(study_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/studies/{study_id}/pause")
    def pause_study(study_id: str) -> dict[str, Any]:
        ok, msg = workflow.pause_time_study(study_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/studies/{study_id}/resume")
    def resume_study(study_id: str) -> dict[str, Any]:
        ok, msg = workflow.resume_time_study(study_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/studies/{study_id}/complete")
    def complete_study(study_id: str) -> dict[str, Any]:
        ok, msg = workflow.complete_time_study(study_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/studies/{study_id}/add-sample")
    def add_sample(
        study_id: str,
        cycle_time_ms: float = Query(...),
        element_name: str = Query(""),
        is_abnormal: bool = Query(False),
        notes: str = Query(""),
        observations: dict[str, Any] | None = Body(None),
    ) -> dict[str, Any]:
        ok, msg = workflow.add_time_sample(
            study_id=study_id,
            cycle_time_ms=cycle_time_ms,
            element_name=element_name,
            observations=observations or {},
            is_abnormal=is_abnormal,
            notes=notes,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg, "study_id": study_id}

    @router.get("/studies/{study_id}/stats")
    def get_study_stats(study_id: str) -> dict[str, Any]:
        stats = workflow.get_study_statistics(study_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Study not found")
        return {"success": True, "statistics": stats}

    @router.get("/studies/{study_id}/data")
    def get_study_data(study_id: str) -> dict[str, Any]:
        data = workflow.export_study_data(study_id)
        if not data:
            raise HTTPException(status_code=404, detail="Study not found")
        return {"success": True, "data": data}

    # ════════════════════════════════════════════════════════════════════
    # SPEC VERSION — static first, then parameterised
    # ════════════════════════════════════════════════════════════════════

    @router.get("/specs/all")
    def get_all_specs(tenant_id: str = Query(...)) -> dict[str, Any]:
        result = [
            workflow.export_spec_data(s.version_id)
            for s in workflow.active_specs.values()
            if s.tenant_id == tenant_id
        ]
        return {"success": True, "data": result, "count": len(result)}

    @router.post("/specs/create")
    def create_spec(
        tenant_id: str = Query(...),
        spec_id: str = Query(...),
        spec_name: str = Query(...),
        created_by: str = Query(...),
        version_number: str = Query("1.0.0"),
    ) -> dict[str, Any]:
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
                "status": _status_val(spec.status),
                "message": f"Spec version created: {spec.version_id}",
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    # --- parameterised ---

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
    ) -> dict[str, Any]:
        try:
            ct = ChangeType[change_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid change_type. Valid: {[e.name for e in ChangeType]}",
            ) from None

        def _parse(v: str) -> Any:
            try:
                return int(v)
            except ValueError:
                try:
                    return float(v)
                except ValueError:
                    return v

        ok, msg = workflow.add_spec_change(
            version_id=version_id,
            change_type=ct,
            parameter_name=parameter_name,
            old_value=_parse(old_value),
            new_value=_parse(new_value),
            changed_by=changed_by,
            reason=reason,
            impact_assessment=impact_assessment,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/specs/{version_id}/record-drift")
    def record_drift(
        version_id: str,
        parameter_name: str = Query(...),
        specification_limit: float = Query(...),
        measured_value: float = Query(...),
        severity: str = Query("low"),
        corrective_action: str = Query(""),
    ) -> dict[str, Any]:
        ok, msg = workflow.record_drift(
            version_id=version_id,
            parameter_name=parameter_name,
            specification_limit=specification_limit,
            measured_value=measured_value,
            severity=severity,
            corrective_action=corrective_action,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/specs/{version_id}/resolve-drift/{drift_id}")
    def resolve_drift(
        version_id: str, drift_id: str, corrective_action: str = Query(...)
    ) -> dict[str, Any]:
        ok, msg = workflow.resolve_drift(version_id, drift_id, corrective_action)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/specs/{version_id}/submit-review")
    def submit_for_review(version_id: str, reviewer_id: str = Query(...)) -> dict[str, Any]:
        ok, msg = workflow.submit_spec_for_review(version_id, reviewer_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/specs/{version_id}/approve")
    def approve_spec(version_id: str, approver_id: str = Query(...)) -> dict[str, Any]:
        ok, msg = workflow.approve_spec(version_id, approver_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.post("/specs/{version_id}/activate")
    def activate_spec(version_id: str) -> dict[str, Any]:
        ok, msg = workflow.activate_spec(version_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @router.get("/specs/{version_id}/drift-report")
    def get_drift_report(version_id: str) -> dict[str, Any]:
        """BUG-FIX #1: always return a valid report dict, never 404 on empty drifts."""
        if version_id not in workflow.active_specs:
            raise HTTPException(status_code=404, detail="Spec not found")
        spec = workflow.active_specs[version_id]
        report = spec.get_drift_summary()
        # Attach full drift list so the frontend can render them
        report["drifts"] = [d.to_dict() for d in spec.drifts]
        return {"success": True, "report": report}

    @router.get("/specs/{version_id}/drift-analysis")
    def get_drift_analysis(version_id: str) -> dict[str, Any]:
        """BUG-FIX #1: always return valid analysis even if drifts list is empty."""
        if version_id not in workflow.active_specs:
            raise HTTPException(status_code=404, detail="Spec not found")
        spec = workflow.active_specs[version_id]
        drifts = [d.to_dict() for d in spec.drifts]
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
        version_id: str, parameter_name: str | None = Query(None)
    ) -> dict[str, Any]:
        if version_id not in workflow.active_specs:
            raise HTTPException(status_code=404, detail="Spec not found")
        history = workflow.get_change_history(version_id, parameter_name)
        return {"success": True, "history": history}

    @router.get("/specs/{version_id}/data")
    def get_spec_data(version_id: str) -> dict[str, Any]:
        data = workflow.export_spec_data(version_id)
        if not data:
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"success": True, "data": data}

    # ════════════════════════════════════════════════════════════════════
    # SAMPLE VERSIONS — all static routes BEFORE /{version_id}
    # BUG-FIX #2: /article/{article_id}/history registered here, not after.
    # ════════════════════════════════════════════════════════════════════

    @router.get("/sample-versions/all")
    def list_sample_versions(tenant_id: str = Query(...)) -> dict[str, Any]:
        result = sorted(
            [sv for sv in sample_versions.values() if sv["tenant_id"] == tenant_id],
            key=lambda x: x["created_at"],
            reverse=True,
        )
        return {"success": True, "data": result, "count": len(result)}

    @router.post("/sample-versions/create")
    def create_sample_version(
        tenant_id: str = Query(...),
        article_id: str = Query(...),
        article_name: str = Query(...),
        client_id: str = Query(...),
        created_by: str = Query(...),
        notes: str = Query(""),
        body: dict[str, Any] | None = Body(None),
    ) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()
        existing = [
            sv
            for sv in sample_versions.values()
            if sv["tenant_id"] == tenant_id and sv["article_id"] == article_id
        ]
        version_num = len(existing) + 1
        version_label = f"v{version_num}"
        parent_id = None
        if existing:
            parent_id = sorted(existing, key=lambda x: x["version_number"])[-1]["version_id"]

        sv_id = str(uuid.uuid4())
        sv: dict[str, Any] = {
            "version_id": sv_id,
            "tenant_id": tenant_id,
            "article_id": article_id,
            "article_name": article_name,
            "client_id": client_id,
            "version_number": version_num,
            "version_label": version_label,
            "parent_version_id": parent_id,
            "status": "draft",
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
            "approved_by": None,
            "approved_at": None,
            "converted_to_order_id": None,
            "notes": notes,
            "components": (body or {}).get("components", []),
            "materials": (body or {}).get("materials", []),
            "revision_log": [
                {
                    "action": "created",
                    "by": created_by,
                    "at": now,
                    "note": notes or f"Initial {version_label}",
                }
            ],
        }
        sample_versions[sv_id] = sv
        return {
            "success": True,
            "version_id": sv_id,
            "version_label": version_label,
            "status": "draft",
        }

    # BUG-FIX #2: article history registered BEFORE /{version_id} routes
    @router.get("/sample-versions/article/{article_id}/history")
    def get_version_history(article_id: str, tenant_id: str = Query(...)) -> dict[str, Any]:
        history = sorted(
            [
                sv
                for sv in sample_versions.values()
                if sv["tenant_id"] == tenant_id and sv["article_id"] == article_id
            ],
            key=lambda x: x["version_number"],
        )
        return {
            "success": True,
            "article_id": article_id,
            "versions": history,
            "total_versions": len(history),
        }

    # --- parameterised sample-version routes ---

    @router.get("/sample-versions/{version_id}")
    def get_sample_version(version_id: str) -> dict[str, Any]:
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        return {"success": True, "data": sample_versions[version_id]}

    @router.post("/sample-versions/{version_id}/new-revision")
    def create_new_revision(
        version_id: str,
        revised_by: str = Query(...),
        revision_note: str = Query(...),
        body: dict[str, Any] | None = Body(None),
    ) -> dict[str, Any]:
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        parent = sample_versions[version_id]
        now = datetime.utcnow().isoformat()
        existing = [
            sv
            for sv in sample_versions.values()
            if sv["tenant_id"] == parent["tenant_id"] and sv["article_id"] == parent["article_id"]
        ]
        new_num = len(existing) + 1
        new_label = f"v{new_num}"
        new_id = str(uuid.uuid4())
        new_sv: dict[str, Any] = {
            **parent,
            "version_id": new_id,
            "version_number": new_num,
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
            "components": (body or {}).get("components", parent["components"]),
            "materials": (body or {}).get("materials", parent["materials"]),
            "revision_log": [
                *parent["revision_log"],
                {"action": "revised", "by": revised_by, "at": now, "note": revision_note},
            ],
        }
        sample_versions[new_id] = new_sv
        return {
            "success": True,
            "version_id": new_id,
            "version_label": new_label,
            "parent_version_id": version_id,
            "status": "draft",
        }

    @router.post("/sample-versions/{version_id}/submit-approval")
    def submit_sample_for_approval(
        version_id: str, submitted_by: str = Query(...)
    ) -> dict[str, Any]:
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] != "draft":
            raise HTTPException(
                status_code=400, detail=f"Cannot submit from status: {sv['status']}"
            )
        now = datetime.utcnow().isoformat()
        sv["status"] = "pending_approval"
        sv["updated_at"] = now
        sv["revision_log"].append(
            {"action": "submitted_for_approval", "by": submitted_by, "at": now, "note": ""}
        )
        return {"success": True, "version_id": version_id, "status": "pending_approval"}

    @router.post("/sample-versions/{version_id}/approve")
    def approve_sample_version(
        version_id: str,
        approved_by: str = Query(...),
        approval_note: str = Query(""),
    ) -> dict[str, Any]:
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] != "pending_approval":
            raise HTTPException(
                status_code=400, detail=f"Cannot approve from status: {sv['status']}"
            )
        now = datetime.utcnow().isoformat()
        sv["status"] = "approved"
        sv["approved_by"] = approved_by
        sv["approved_at"] = now
        sv["updated_at"] = now
        sv["revision_log"].append(
            {"action": "approved", "by": approved_by, "at": now, "note": approval_note}
        )
        return {"success": True, "version_id": version_id, "status": "approved"}

    @router.post("/sample-versions/{version_id}/convert-to-order")
    def convert_sample_to_order(
        version_id: str,
        order_id: str = Query(...),
        converted_by: str = Query(...),
    ) -> dict[str, Any]:
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] != "approved":
            raise HTTPException(
                status_code=400, detail="Only approved versions can be converted to order"
            )
        now = datetime.utcnow().isoformat()
        sv["status"] = "converted"
        sv["converted_to_order_id"] = order_id
        sv["updated_at"] = now
        sv["revision_log"].append(
            {
                "action": "converted_to_order",
                "by": converted_by,
                "at": now,
                "note": f"Linked to order {order_id}",
            }
        )
        return {
            "success": True,
            "version_id": version_id,
            "order_id": order_id,
            "status": "converted",
        }

    @router.put("/sample-versions/{version_id}/components")
    def update_components(
        version_id: str,
        updated_by: str = Query(...),
        body: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] != "draft":
            raise HTTPException(
                status_code=400, detail="Components can only be edited on draft versions"
            )
        now = datetime.utcnow().isoformat()
        sv["components"] = body.get("components", sv["components"])
        sv["updated_at"] = now
        n = len(sv["components"])
        sv["revision_log"].append(
            {
                "action": "components_updated",
                "by": updated_by,
                "at": now,
                "note": f"{n} components saved",
            }
        )
        return {"success": True, "version_id": version_id, "component_count": n}

    @router.put("/sample-versions/{version_id}/materials")
    def update_materials(
        version_id: str,
        updated_by: str = Query(...),
        body: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        if version_id not in sample_versions:
            raise HTTPException(status_code=404, detail="Sample version not found")
        sv = sample_versions[version_id]
        if sv["status"] != "draft":
            raise HTTPException(
                status_code=400, detail="Materials can only be edited on draft versions"
            )
        now = datetime.utcnow().isoformat()
        mats = body.get("materials", sv["materials"])
        # auto-compute total_cost
        for m in mats:
            if "total_cost" not in m or m["total_cost"] == 0:
                m["total_cost"] = float(m.get("estimated_usage", 0)) * float(m.get("unit_cost", 0))
        sv["materials"] = mats
        sv["updated_at"] = now
        total = sum(float(m.get("total_cost", 0)) for m in mats)
        sv["revision_log"].append(
            {
                "action": "materials_updated",
                "by": updated_by,
                "at": now,
                "note": f"Est. cost: {total:.2f}",
            }
        )
        return {
            "success": True,
            "version_id": version_id,
            "material_count": len(mats),
            "estimated_total_cost": total,
        }

    return router
