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

from datetime import datetime
import math
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ..models.spec_version_tracker import ChangeType
from ..services.sampling_rnd_workflow import SamplingRnDWorkflow
from ..services.ops_store import OpsStore, SnapshotError
from .auth_deps import SessionContext, session_context
from ..utils.spec_version_patterns import calculate_drift_risk_score, identify_drift_trends


def _status_val(s: Any) -> str:
    """Safely extract string value from either a VersionStatus enum or a plain string."""
    return s.value if hasattr(s, "value") else str(s)


def create_api_router(store: OpsStore | None = None) -> APIRouter:
    if store is None:
        raise RuntimeError("create_api_router requires an OpsStore")
    router = APIRouter(prefix="/api/sampling-spec-rnd", tags=["sampling-spec-rnd"])
    protected = APIRouter(dependencies=[Depends(session_context)])
    workflow = SamplingRnDWorkflow()

    def _tenant_scope(context: SessionContext, requested: str | None) -> str:
        if requested is not None and requested != context.tenant_id:
            raise HTTPException(status_code=403, detail="Tenant scope is session-derived")
        return context.tenant_id

    def _client_scope(context: SessionContext):
        return context.effective_scope

    def _bounded_list(body: dict[str, Any], key: str) -> list[Any]:
        value = body.get(key)
        if not isinstance(value, list) or len(value) > 200:
            raise HTTPException(status_code=422, detail=f"{key} must be a bounded list")
        return value

    def _study_owned(study_id: str, context: SessionContext) -> None:
        study = workflow.active_studies.get(study_id)
        if study is not None and study.tenant_id != context.tenant_id:
            raise HTTPException(status_code=404, detail="Study not found")

    def _spec_owned(version_id: str, context: SessionContext) -> None:
        spec = workflow.active_specs.get(version_id)
        if spec is None or spec.tenant_id != context.tenant_id:
            raise HTTPException(status_code=404, detail="Spec not found")

    # ????????????????????????????????????????????????????????????????????
    # HEALTH + WORKFLOW
    # ????????????????????????????????????????????????????????????????????

    @router.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "healthy", "module": "sampling-spec-rnd"}

    @protected.get("/workflow/summary")
    def get_workflow_summary(context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        """Get workflow summary — BUG-FIX #3: guard against raw-string status."""
        # Defensive recalculation using the safe status extractor.
        active_studies_safe = sum(
            1
            for s in workflow.active_studies.values()
            if s.tenant_id == context.tenant_id and _status_val(s.status) == "in_progress"
        )
        completed_studies_safe = sum(
            1
            for s in workflow.active_studies.values()
            if s.tenant_id == context.tenant_id and _status_val(s.status) == "completed"
        )
        active_specs_safe = sum(
            1
            for s in workflow.active_specs.values()
            if s.tenant_id == context.tenant_id and _status_val(s.status) == "active"
        )
        specs_in_review_safe = sum(
            1
            for s in workflow.active_specs.values()
            if s.tenant_id == context.tenant_id and _status_val(s.status) == "review"
        )
        total_drifts_safe = sum(
            getattr(s, "total_drifts", 0)
            for s in workflow.active_specs.values()
            if s.tenant_id == context.tenant_id
        )
        critical_drifts_safe = sum(
            getattr(s, "critical_drifts", 0)
            for s in workflow.active_specs.values()
            if s.tenant_id == context.tenant_id
        )

        tenant_svs = store.list_sample_versions(_client_scope(context))

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

    # ????????????????????????????????????????????????????????????????????
    # TIME STUDY — static first, then parameterised
    # ????????????????????????????????????????????????????????????????????

    @protected.get("/studies/all")
    def get_all_studies(tenant_id: str | None = Query(None), context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        tenant_id = _tenant_scope(context, tenant_id)
        result = [
            workflow.export_study_data(s.study_id)
            for s in workflow.active_studies.values()
            if s.tenant_id == tenant_id
        ]
        return {"success": True, "data": result, "count": len(result)}

    @protected.post("/studies/create")
    def create_study(
        tenant_id: str | None = Query(None),
        process_id: str = Query(...),
        process_name: str = Query(...),
        operator_id: str = Query(...),
        context: SessionContext = Depends(session_context),
        target_sample_size: int = Query(30),
    ) -> dict[str, Any]:
        try:
            study = workflow.create_time_study(
                tenant_id=_tenant_scope(context, tenant_id),
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

    @protected.post("/studies/{study_id}/start")
    def start_study(study_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _study_owned(study_id, context)
        ok, msg = workflow.start_time_study(study_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.post("/studies/{study_id}/pause")
    def pause_study(study_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _study_owned(study_id, context)
        ok, msg = workflow.pause_time_study(study_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.post("/studies/{study_id}/resume")
    def resume_study(study_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _study_owned(study_id, context)
        ok, msg = workflow.resume_time_study(study_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.post("/studies/{study_id}/complete")
    def complete_study(study_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _study_owned(study_id, context)
        ok, msg = workflow.complete_time_study(study_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.post("/studies/{study_id}/add-sample")
    def add_sample(
        study_id: str,
        cycle_time_ms: float = Query(...),
        element_name: str = Query(""),
        is_abnormal: bool = Query(False),
        notes: str = Query(""),
        observations: dict[str, Any] | None = Body(None),
        context: SessionContext = Depends(session_context),
    ) -> dict[str, Any]:
        _study_owned(study_id, context)
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

    @protected.get("/studies/{study_id}/stats")
    def get_study_stats(study_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _study_owned(study_id, context)
        stats = workflow.get_study_statistics(study_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Study not found")
        return {"success": True, "statistics": stats}

    @protected.get("/studies/{study_id}/data")
    def get_study_data(study_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _study_owned(study_id, context)
        data = workflow.export_study_data(study_id)
        if not data:
            raise HTTPException(status_code=404, detail="Study not found")
        return {"success": True, "data": data}

    # ????????????????????????????????????????????????????????????????????
    # SPEC VERSION — static first, then parameterised
    # ????????????????????????????????????????????????????????????????????

    @protected.get("/specs/all")
    def get_all_specs(tenant_id: str | None = Query(None), context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        tenant_id = _tenant_scope(context, tenant_id)
        result = [
            workflow.export_spec_data(s.version_id)
            for s in workflow.active_specs.values()
            if s.tenant_id == tenant_id
        ]
        return {"success": True, "data": result, "count": len(result)}

    @protected.post("/specs/create")
    def create_spec(
        tenant_id: str | None = Query(None),
        spec_id: str = Query(...),
        spec_name: str = Query(...),
        created_by: str | None = Query(None),
        version_number: str = Query("1.0.0"),
        context: SessionContext = Depends(session_context),
    ) -> dict[str, Any]:
        try:
            spec = workflow.create_spec_version(
                tenant_id=_tenant_scope(context, tenant_id),
                spec_id=spec_id,
                spec_name=spec_name,
                created_by=context.user_id,
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

    @protected.post("/specs/{version_id}/record-change")
    def record_spec_change(
        version_id: str,
        change_type: str = Query(...),
        parameter_name: str = Query(...),
        old_value: str = Query(...),
        new_value: str = Query(...),
        changed_by: str | None = Query(None),
        reason: str = Query(""),
        impact_assessment: str = Query(""),
        context: SessionContext = Depends(session_context),
    ) -> dict[str, Any]:
        _spec_owned(version_id, context)
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
            changed_by=context.user_id,
            reason=reason,
            impact_assessment=impact_assessment,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.post("/specs/{version_id}/record-drift")
    def record_drift(
        version_id: str,
        parameter_name: str = Query(...),
        specification_limit: float = Query(...),
        measured_value: float = Query(...),
        severity: str = Query("low"),
        corrective_action: str = Query(""),
        context: SessionContext = Depends(session_context),
    ) -> dict[str, Any]:
        _spec_owned(version_id, context)
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

    @protected.post("/specs/{version_id}/resolve-drift/{drift_id}")
    def resolve_drift(
        version_id: str, drift_id: str, corrective_action: str = Query(...),
        context: SessionContext = Depends(session_context)
    ) -> dict[str, Any]:
        _spec_owned(version_id, context)
        ok, msg = workflow.resolve_drift(version_id, drift_id, corrective_action)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.post("/specs/{version_id}/submit-review")
    def submit_for_review(version_id: str, reviewer_id: str | None = Query(None), context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _spec_owned(version_id, context)
        ok, msg = workflow.submit_spec_for_review(version_id, context.user_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.post("/specs/{version_id}/approve")
    def approve_spec(version_id: str, approver_id: str | None = Query(None), context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _spec_owned(version_id, context)
        ok, msg = workflow.approve_spec(version_id, context.user_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.post("/specs/{version_id}/activate")
    def activate_spec(version_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _spec_owned(version_id, context)
        ok, msg = workflow.activate_spec(version_id)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}

    @protected.get("/specs/{version_id}/drift-report")
    def get_drift_report(version_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        """BUG-FIX #1: always return a valid report dict, never 404 on empty drifts."""
        _spec_owned(version_id, context)
        spec = workflow.active_specs[version_id]
        report = spec.get_drift_summary()
        # Attach full drift list so the frontend can render them
        report["drifts"] = [d.to_dict() for d in spec.drifts]
        return {"success": True, "report": report}

    @protected.get("/specs/{version_id}/drift-analysis")
    def get_drift_analysis(version_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        """BUG-FIX #1: always return valid analysis even if drifts list is empty."""
        _spec_owned(version_id, context)
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

    @protected.get("/specs/{version_id}/change-history")
    def get_change_history(
        version_id: str, parameter_name: str | None = Query(None)
        , context: SessionContext = Depends(session_context)
    ) -> dict[str, Any]:
        _spec_owned(version_id, context)
        history = workflow.get_change_history(version_id, parameter_name)
        return {"success": True, "history": history}

    @protected.get("/specs/{version_id}/data")
    def get_spec_data(version_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        _spec_owned(version_id, context)
        data = workflow.export_spec_data(version_id)
        if not data:
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"success": True, "data": data}

    # ????????????????????????????????????????????????????????????????????
    # SAMPLE VERSIONS — all static routes BEFORE /{version_id}
    # BUG-FIX #2: /article/{article_id}/history registered here, not after.
    # ????????????????????????????????????????????????????????????????????

    @protected.get("/sample-versions/all")
    def list_sample_versions(context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        result = store.list_sample_versions(_client_scope(context))
        return {"success": True, "data": result, "count": len(result)}

    @protected.post("/sample-versions/create")
    def create_sample_version(
        context: SessionContext = Depends(session_context),
        tenant_id: str | None = Query(None),
        article_id: str = Query(...),
        article_name: str = Query(...),
        client_id: str | None = Query(None),
        created_by: str | None = Query(None),
        notes: str = Query(""),
        body: dict[str, Any] | None = Body(None),
    ) -> dict[str, Any]:
        if body is not None and (not isinstance(body, dict) or set(body) - {"components", "materials"}):
            raise HTTPException(status_code=422, detail="Body contains unknown fields")
        if body is not None and any(key in body and not isinstance(body[key], list) for key in ("components", "materials")):
            raise HTTPException(status_code=422, detail="components and materials must be lists")
        tenant_id = _tenant_scope(context, tenant_id)
        scoped_client = context.client_id
        if context.role == "client" and client_id not in (None, scoped_client):
            raise HTTPException(status_code=403, detail="Client scope is session-derived")
        if context.role != "client" and client_id is not None:
            raise HTTPException(status_code=403, detail="Client scope requires a verified session mapping")
        client_id = scoped_client
        created_by = context.user_id
        now = datetime.utcnow().isoformat()
        sv: dict[str, Any] = {
            "tenant_id": tenant_id,
            "article_id": article_id,
            "article_name": article_name,
            "client_id": client_id,
            "version_number": 0,
            "version_label": "",
            "parent_version_id": None,
            "status": "draft",
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
            "approved_by": None,
            "approved_at": None,
            "converted_to_order_id": None,
            "notes": notes,
            "components": body.get("components", []) if body else [],
            "materials": body.get("materials", []) if body else [],
            "revision_log": [
                {
                    "action": "created",
                    "by": created_by,
                    "at": now,
                    "note": notes or "Initial sample version",
                }
            ],
        }
        try:
            sv = store.create_sample_version(sv, _client_scope(context))
        except SnapshotError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "success": True,
            "version_id": sv["version_id"],
            "version_label": sv["version_label"],
            "status": "draft",
        }

    # BUG-FIX #2: article history registered BEFORE /{version_id} routes
    @protected.get("/sample-versions/article/{article_id}/history")
    def get_version_history(article_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        source = store.list_sample_history(_client_scope(context), article_id)
        history = sorted(
            [
                sv
                for sv in source
                if sv["tenant_id"] == context.tenant_id and sv["article_id"] == article_id
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

    @protected.get("/sample-versions/{version_id}")
    def get_sample_version(version_id: str, context: SessionContext = Depends(session_context)) -> dict[str, Any]:
        sample_version = store.get_sample_version(version_id, _client_scope(context))
        if sample_version is None:
            raise HTTPException(status_code=404, detail="Sample version not found")
        return {"success": True, "data": sample_version}

    @protected.post("/sample-versions/{version_id}/new-revision")
    def create_new_revision(
        version_id: str,
        context: SessionContext = Depends(session_context),
        revised_by: str | None = Query(None),
        revision_note: str = Query(...),
        body: dict[str, Any] | None = Body(None),
    ) -> dict[str, Any]:
        parent = store.get_sample_version(version_id, _client_scope(context))
        if parent is None:
            raise HTTPException(status_code=404, detail="Sample version not found")
        body = body or {}
        if set(body) - {"components", "materials"}:
            raise HTTPException(status_code=422, detail="Revision body contains an unknown field")
        revised_by = context.user_id
        now = datetime.utcnow().isoformat()
        new_sv: dict[str, Any] = {
            **parent,
            "version_number": 0,
            "version_label": "",
            "parent_version_id": version_id,
            "status": "draft",
            "created_by": revised_by,
            "created_at": now,
            "updated_at": now,
            "approved_by": None,
            "approved_at": None,
            "converted_to_order_id": None,
            "notes": revision_note,
            "components": body.get("components", parent["components"]),
            "materials": body.get("materials", parent["materials"]),
            "revision_log": [
                *parent["revision_log"],
                {"action": "revised", "by": revised_by, "at": now, "note": revision_note},
            ],
        }
        try:
            new_sv = store.create_sample_revision(version_id, _client_scope(context), new_sv)
        except SnapshotError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if new_sv is None:
            raise HTTPException(status_code=404, detail="Sample version not found")
        return {
            "success": True,
            "version_id": new_sv["version_id"],
            "version_label": new_sv["version_label"],
            "parent_version_id": version_id,
            "status": "draft",
        }

    @protected.post("/sample-versions/{version_id}/submit-approval")
    def submit_sample_for_approval(
        version_id: str, submitted_by: str = Query(...), context: SessionContext = Depends(session_context)
    ) -> dict[str, Any]:
        sv = store.get_sample_version(version_id, _client_scope(context))
        if sv is None:
            raise HTTPException(status_code=404, detail="Sample version not found")
        if sv["status"] != "draft":
            raise HTTPException(
                status_code=400, detail=f"Cannot submit from status: {sv['status']}"
            )
        now = datetime.utcnow().isoformat()
        sv["status"] = "pending_approval"
        sv["updated_at"] = now
        sv["revision_log"].append(
            {"action": "submitted_for_approval", "by": context.user_id, "at": now, "note": ""}
        )
        if store.update_sample_version(version_id, _client_scope(context), sv, expected_etag=int(sv["etag"])) is None:
            raise HTTPException(status_code=409, detail="Sample version changed; retry")
        return {"success": True, "version_id": version_id, "status": "pending_approval"}

    @protected.post("/sample-versions/{version_id}/approve")
    def approve_sample_version(
        version_id: str,
        approved_by: str | None = Query(None),
        approval_note: str = Query(""),
        context: SessionContext = Depends(session_context),
    ) -> dict[str, Any]:
        sv = store.get_sample_version(version_id, _client_scope(context))
        if sv is None:
            raise HTTPException(status_code=404, detail="Sample version not found")
        if sv["status"] != "pending_approval":
            raise HTTPException(
                status_code=400, detail=f"Cannot approve from status: {sv['status']}"
            )
        now = datetime.utcnow().isoformat()
        sv["status"] = "approved"
        sv["approved_by"] = context.user_id
        sv["approved_at"] = now
        sv["updated_at"] = now
        sv["revision_log"].append(
            {"action": "approved", "by": context.user_id, "at": now, "note": approval_note}
        )
        if store.update_sample_version(version_id, _client_scope(context), sv, expected_etag=int(sv["etag"]),
            approval=("sample", context.user_id, approval_note)) is None:
            raise HTTPException(status_code=409, detail="Sample version changed; retry")
        return {"success": True, "version_id": version_id, "status": "approved"}

    @protected.post("/sample-versions/{version_id}/convert-to-order")
    def convert_sample_to_order(
        version_id: str,
        order_id: str = Query(...),
        converted_by: str | None = Query(None),
        context: SessionContext = Depends(session_context),
    ) -> dict[str, Any]:
        sv = store.get_sample_version(version_id, _client_scope(context))
        if sv is None:
            raise HTTPException(status_code=404, detail="Sample version not found")
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
                "by": context.user_id,
                "at": now,
                "note": f"Linked to order {order_id}",
            }
        )
        if store.update_sample_version(version_id, _client_scope(context), sv, expected_etag=int(sv["etag"])) is None:
            raise HTTPException(status_code=409, detail="Sample version changed; retry")
        return {
            "success": True,
            "version_id": version_id,
            "order_id": order_id,
            "status": "converted",
        }

    @protected.put("/sample-versions/{version_id}/components")
    def update_components(
        version_id: str,
        updated_by: str | None = Query(None),
        body: dict[str, Any] = Body(...),
        context: SessionContext = Depends(session_context),
    ) -> dict[str, Any]:
        sv = store.get_sample_version(version_id, _client_scope(context))
        if sv is None:
            raise HTTPException(status_code=404, detail="Sample version not found")
        if sv["status"] != "draft":
            raise HTTPException(
                status_code=400, detail="Components can only be edited on draft versions"
            )
        try:
            store._validate_payload(body)
        except SnapshotError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        now = datetime.utcnow().isoformat()
        sv["components"] = body.get("components", sv["components"])
        sv["updated_at"] = now
        n = len(sv["components"])
        sv["revision_log"].append(
            {
                "action": "components_updated",
                "by": context.user_id,
                "at": now,
                "note": f"{n} components saved",
            }
        )
        if store.update_sample_version(version_id, _client_scope(context), sv, expected_etag=int(sv["etag"])) is None:
            raise HTTPException(status_code=409, detail="Sample version changed; retry")
        return {"success": True, "version_id": version_id, "component_count": n}

    @protected.put("/sample-versions/{version_id}/materials")
    def update_materials(
        version_id: str,
        updated_by: str | None = Query(None),
        body: dict[str, Any] = Body(...),
        context: SessionContext = Depends(session_context),
    ) -> dict[str, Any]:
        sv = store.get_sample_version(version_id, _client_scope(context))
        if sv is None:
            raise HTTPException(status_code=404, detail="Sample version not found")
        if sv["status"] != "draft":
            raise HTTPException(
                status_code=400, detail="Materials can only be edited on draft versions"
            )
        try:
            store._validate_payload(body)
        except SnapshotError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        now = datetime.utcnow().isoformat()
        try:
            mats = _bounded_list(body, "materials")
            store._validate_payload({"materials": mats})
        except SnapshotError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        # auto-compute total_cost
        for m in mats:
            if not isinstance(m, dict):
                raise HTTPException(status_code=422, detail="materials entries must be objects")
            if "total_cost" not in m or m["total_cost"] == 0:
                try:
                    estimated_usage = float(m.get("estimated_usage", 0))
                    unit_cost = float(m.get("unit_cost", 0))
                except (TypeError, ValueError, OverflowError) as exc:
                    raise HTTPException(status_code=422, detail="materials.total_cost must be finite") from exc
                if not math.isfinite(estimated_usage) or not math.isfinite(unit_cost):
                    raise HTTPException(status_code=422, detail="materials.total_cost must be finite")
                computed = estimated_usage * unit_cost
                if not math.isfinite(computed):
                    raise HTTPException(status_code=422, detail="materials.total_cost must be finite")
                m["total_cost"] = computed
        try:
            total = sum(float(m.get("total_cost", 0)) for m in mats)
        except (TypeError, ValueError, OverflowError) as exc:
            raise HTTPException(status_code=422, detail="materials.total_cost must be finite") from exc
        if not math.isfinite(total):
            raise HTTPException(status_code=422, detail="materials.total_cost must be finite")
        sv["materials"] = mats
        sv["updated_at"] = now
        sv["revision_log"].append(
            {
                "action": "materials_updated",
                "by": context.user_id,
                "at": now,
                "note": f"Est. cost: {total:.2f}",
            }
        )
        if store.update_sample_version(version_id, _client_scope(context), sv, expected_etag=int(sv["etag"])) is None:
            raise HTTPException(status_code=409, detail="Sample version changed; retry")
        return {
            "success": True,
            "version_id": version_id,
            "material_count": len(mats),
            "estimated_total_cost": total,
        }

    router.include_router(protected)
    return router
