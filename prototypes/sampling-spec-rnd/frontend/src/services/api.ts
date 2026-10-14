/**
 * API Service — Sampling & Spec R&D
 * Covers all 24 backend endpoints, normalizes responses.
 * Base URL from VITE_API_URL env or defaults to proxy path.
 */

import type {
  TimeStudy,
  TimeStudyStats,
  SpecVersion,
  DriftAnalysis,
  WorkflowSummary,
} from '@/types';

const BASE = import.meta.env.VITE_API_URL || '/api/sampling-spec-rnd';

// ─── Generic response shape ───────────────────────────────────────────────────
export interface ApiResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function qs(params: Record<string, string | number | boolean | undefined>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') p.append(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : '';
}

async function post<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${BASE}${path}${params ? qs(params) : ''}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const raw = await res.json();
    if (!res.ok) return { success: false, error: raw.detail ?? `HTTP ${res.status}` };
    return { success: raw.success ?? true, data: raw as T, message: raw.message };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

async function get<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${BASE}${path}${params ? qs(params) : ''}`);
    const raw = await res.json();
    if (!res.ok) return { success: false, error: raw.detail ?? `HTTP ${res.status}` };
    return { success: raw.success ?? true, data: raw as T };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

// ─── Raw response shapes from backend ────────────────────────────────────────
interface CreateStudyRaw  { success: boolean; study_id: string; status: string; message: string }
interface CreateSpecRaw   { success: boolean; version_id: string; status: string; message: string }
interface StudyDataRaw    { success: boolean; data: TimeStudy }
interface SpecDataRaw     { success: boolean; data: SpecVersion }
interface StatsRaw        { success: boolean; statistics: TimeStudyStats }
interface DriftReportRaw  { success: boolean; report: unknown }
interface DriftAnalysisRaw{ success: boolean; version_id: string; analysis: DriftAnalysis; risk_score: number }
interface ChangeHistoryRaw{ success: boolean; history: unknown }
interface WorkflowRaw     { success: boolean; summary: WorkflowSummary }
interface HealthRaw       { status: string; module: string }
interface OkRaw           { success: boolean; message: string }

// ═══════════════════════════════════════════════════════════════════════════════
// TIME STUDY
// ═══════════════════════════════════════════════════════════════════════════════

/** POST /studies/create → { study_id, status } */
export async function createStudy(p: {
  tenant_id: string;
  process_id: string;
  process_name: string;
  operator_id: string;
  target_sample_size?: number;
}): Promise<ApiResult<{ study_id: string; status: string }>> {
  const res = await post<CreateStudyRaw>('/studies/create', p as any);
  if (!res.success || !res.data) return res as ApiResult<{ study_id: string; status: string }>;
  return { success: true, data: { study_id: res.data.study_id, status: res.data.status }, message: res.data.message };
}

/** POST /studies/{id}/start */
export async function startStudy(studyId: string): Promise<ApiResult<null>> {
  return post<OkRaw>(`/studies/${studyId}/start`) as unknown as Promise<ApiResult<null>>;
}

/** POST /studies/{id}/pause */
export async function pauseStudy(studyId: string): Promise<ApiResult<null>> {
  return post<OkRaw>(`/studies/${studyId}/pause`) as unknown as Promise<ApiResult<null>>;
}

/** POST /studies/{id}/resume */
export async function resumeStudy(studyId: string): Promise<ApiResult<null>> {
  return post<OkRaw>(`/studies/${studyId}/resume`) as unknown as Promise<ApiResult<null>>;
}

/** POST /studies/{id}/complete */
export async function completeStudy(studyId: string): Promise<ApiResult<null>> {
  return post<OkRaw>(`/studies/${studyId}/complete`) as unknown as Promise<ApiResult<null>>;
}

/** POST /studies/{id}/add-sample */
export async function addSample(p: {
  study_id: string;
  cycle_time_ms: number;
  element_name?: string;
  is_abnormal?: boolean;
  notes?: string;
}): Promise<ApiResult<null>> {
  const { study_id, ...rest } = p;
  return post<OkRaw>(`/studies/${study_id}/add-sample`, rest as any) as unknown as Promise<ApiResult<null>>;
}

/** GET /studies/{id}/data → TimeStudy */
export async function getStudyData(studyId: string): Promise<ApiResult<TimeStudy>> {
  const res = await get<StudyDataRaw>(`/studies/${studyId}/data`);
  if (!res.success || !res.data) return res as unknown as ApiResult<TimeStudy>;
  return { success: true, data: res.data.data };
}

/** GET /studies/{id}/stats → TimeStudyStats */
export async function getStudyStats(studyId: string): Promise<ApiResult<TimeStudyStats>> {
  const res = await get<StatsRaw>(`/studies/${studyId}/stats`);
  if (!res.success || !res.data) return res as unknown as ApiResult<TimeStudyStats>;
  return { success: true, data: res.data.statistics };
}

// ═══════════════════════════════════════════════════════════════════════════════
// SPEC VERSION
// ═══════════════════════════════════════════════════════════════════════════════

/** POST /specs/create → { version_id, status } */
export async function createSpec(p: {
  tenant_id: string;
  spec_id: string;
  spec_name: string;
  created_by: string;
  version_number?: string;
}): Promise<ApiResult<{ version_id: string; status: string }>> {
  const res = await post<CreateSpecRaw>('/specs/create', p as any);
  if (!res.success || !res.data) return res as ApiResult<{ version_id: string; status: string }>;
  return { success: true, data: { version_id: res.data.version_id, status: res.data.status }, message: res.data.message };
}

/** POST /specs/{id}/record-change */
export async function recordSpecChange(p: {
  version_id: string;
  change_type: string;
  parameter_name: string;
  old_value: string;
  new_value: string;
  changed_by: string;
  reason?: string;
  impact_assessment?: string;
}): Promise<ApiResult<null>> {
  const { version_id, ...rest } = p;
  return post<OkRaw>(`/specs/${version_id}/record-change`, rest as any) as unknown as Promise<ApiResult<null>>;
}

/** POST /specs/{id}/record-drift */
export async function recordDrift(p: {
  version_id: string;
  parameter_name: string;
  specification_limit: number;
  measured_value: number;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  corrective_action?: string;
}): Promise<ApiResult<null>> {
  const { version_id, ...rest } = p;
  return post<OkRaw>(`/specs/${version_id}/record-drift`, rest as any) as unknown as Promise<ApiResult<null>>;
}

/** POST /specs/{id}/resolve-drift/{drift_id} */
export async function resolveDrift(versionId: string, driftId: string, corrective_action: string): Promise<ApiResult<null>> {
  return post<OkRaw>(`/specs/${versionId}/resolve-drift/${driftId}`, { corrective_action }) as unknown as Promise<ApiResult<null>>;
}

/** POST /specs/{id}/submit-review */
export async function submitSpecReview(versionId: string, reviewer_id: string): Promise<ApiResult<null>> {
  return post<OkRaw>(`/specs/${versionId}/submit-review`, { reviewer_id }) as unknown as Promise<ApiResult<null>>;
}

/** POST /specs/{id}/approve */
export async function approveSpec(versionId: string, approver_id: string): Promise<ApiResult<null>> {
  return post<OkRaw>(`/specs/${versionId}/approve`, { approver_id }) as unknown as Promise<ApiResult<null>>;
}

/** POST /specs/{id}/activate */
export async function activateSpec(versionId: string): Promise<ApiResult<null>> {
  return post<OkRaw>(`/specs/${versionId}/activate`) as unknown as Promise<ApiResult<null>>;
}

/** GET /specs/{id}/data → SpecVersion */
export async function getSpecData(versionId: string): Promise<ApiResult<SpecVersion>> {
  const res = await get<SpecDataRaw>(`/specs/${versionId}/data`);
  if (!res.success || !res.data) return res as unknown as ApiResult<SpecVersion>;
  return { success: true, data: res.data.data };
}

/** GET /specs/{id}/drift-report */
export async function getDriftReport(versionId: string): Promise<ApiResult<unknown>> {
  const res = await get<DriftReportRaw>(`/specs/${versionId}/drift-report`);
  if (!res.success || !res.data) return res;
  return { success: true, data: res.data.report };
}

/** GET /specs/{id}/drift-analysis → DriftAnalysis + risk_score */
export async function getDriftAnalysis(versionId: string): Promise<ApiResult<{ analysis: DriftAnalysis; risk_score: number }>> {
  const res = await get<DriftAnalysisRaw>(`/specs/${versionId}/drift-analysis`);
  if (!res.success || !res.data) return res as unknown as ApiResult<{ analysis: DriftAnalysis; risk_score: number }>;
  return { success: true, data: { analysis: res.data.analysis, risk_score: res.data.risk_score } };
}

/** GET /specs/{id}/change-history */
export async function getChangeHistory(versionId: string, parameter_name?: string): Promise<ApiResult<unknown>> {
  const res = await get<ChangeHistoryRaw>(`/specs/${versionId}/change-history`, parameter_name ? { parameter_name } : undefined);
  if (!res.success || !res.data) return res;
  return { success: true, data: res.data.history };
}

// ═══════════════════════════════════════════════════════════════════════════════
// WORKFLOW
// ═══════════════════════════════════════════════════════════════════════════════

/** GET /workflow/summary */
export async function getWorkflowSummary(tenant_id: string): Promise<ApiResult<WorkflowSummary>> {
  const res = await get<WorkflowRaw>('/workflow/summary', { tenant_id });
  if (!res.success || !res.data) return res as unknown as ApiResult<WorkflowSummary>;
  return { success: true, data: res.data.summary };
}

// ═══════════════════════════════════════════════════════════════════════════════
// HEALTH
// ═══════════════════════════════════════════════════════════════════════════════

/** GET /health */
export async function checkHealth(): Promise<ApiResult<{ status: string; module: string }>> {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 5000);
    const res = await fetch(`${BASE}/health`, { signal: ctrl.signal });
    clearTimeout(timer);
    if (!res.ok) return { success: false, error: `HTTP ${res.status}` };
    const raw: HealthRaw = await res.json();
    return { success: raw.status === 'healthy', data: raw };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

// ─── Legacy class-style export for backward compat ───────────────────────────
export const api = {
  checkHealth,
  createStudy,
  startStudy,
  pauseStudy,
  resumeStudy,
  completeStudy,
  addSample,
  getStudyData,
  getStudyStats,
  createSpec,
  recordSpecChange,
  recordDrift,
  resolveDrift,
  submitSpecReview,
  approveSpec,
  activateSpec,
  getSpecData,
  getDriftReport,
  getDriftAnalysis,
  getChangeHistory,
  getWorkflowSummary,
};

export default api;
