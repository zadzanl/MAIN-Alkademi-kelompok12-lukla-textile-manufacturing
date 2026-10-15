/**
 * API Service — Sampling & Spec R&D.
 *
 * Single client for all 33 sampling endpoints. Built on services/http.ts so
 * every call shares one base URL, timeout, and error shape. Returns the same
 * `ApiResult<T>` envelope the pages already rely on.
 */

import type {
  TimeStudy,
  TimeStudyStats,
  SpecVersion,
  DriftAnalysis,
  WorkflowSummary,
  SampleVersion,
  GarmentComponent,
  MaterialEstimation,
} from '@/types';
import { http, errorMessage } from './http';
import type {
  CreateStudyRaw,
  CreateSpecRaw,
  StudyDataRaw,
  SpecDataRaw,
  StatsRaw,
  ListRaw,
  DriftReportRaw,
  DriftAnalysisRaw,
  ChangeHistoryRaw,
  WorkflowRaw,
  HealthRaw,
  OkRaw,
  SampleVersionRaw,
  SampleVersionDataRaw,
  SampleVersionHistoryRaw,
} from '@/types/api';

// ─── Generic response shape ───────────────────────────────────────────────────
export interface ApiResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
async function get<T>(path: string, params?: Record<string, unknown>): Promise<ApiResult<T>> {
  try {
    const raw = await http.get<T>(path, { params });
    return { success: (raw as { success?: boolean })?.success ?? true, data: raw };
  } catch (error) {
    return { success: false, error: errorMessage(error) };
  }
}

async function post<T>(path: string, params?: Record<string, unknown>): Promise<ApiResult<T>> {
  try {
    const raw = await http.post<T>(path, { params });
    return {
      success: (raw as { success?: boolean })?.success ?? true,
      data: raw,
      message: (raw as { message?: string })?.message,
    };
  } catch (error) {
    return { success: false, error: errorMessage(error) };
  }
}

async function put<T>(path: string, params?: Record<string, unknown>, body?: unknown): Promise<ApiResult<T>> {
  try {
    const raw = await http.put<T>(path, { params, body });
    return { success: (raw as { success?: boolean })?.success ?? true, data: raw };
  } catch (error) {
    return { success: false, error: errorMessage(error) };
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TIME STUDY
// ═══════════════════════════════════════════════════════════════════════════════

/** GET /studies/all → TimeStudy[] */
export async function listStudies(tenant_id: string): Promise<ApiResult<TimeStudy[]>> {
  const res = await get<ListRaw<TimeStudy>>('/studies/all', { tenant_id });
  if (!res.success || !res.data) return res as unknown as ApiResult<TimeStudy[]>;
  return { success: true, data: res.data.data ?? [] };
}

/** POST /studies/create → { study_id, status } */
export async function createStudy(p: {
  tenant_id: string;
  process_id: string;
  process_name: string;
  operator_id: string;
  target_sample_size?: number;
}): Promise<ApiResult<{ study_id: string; status: string }>> {
  const res = await post<CreateStudyRaw>('/studies/create', p);
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
  return post<OkRaw>(`/studies/${study_id}/add-sample`, { ...rest }) as unknown as Promise<ApiResult<null>>;
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

/** GET /specs/all → SpecVersion[] */
export async function listSpecs(tenant_id: string): Promise<ApiResult<SpecVersion[]>> {
  const res = await get<ListRaw<SpecVersion>>('/specs/all', { tenant_id });
  if (!res.success || !res.data) return res as unknown as ApiResult<SpecVersion[]>;
  return { success: true, data: res.data.data ?? [] };
}

/** POST /specs/create → { version_id, status } */
export async function createSpec(p: {
  tenant_id: string;
  spec_id: string;
  spec_name: string;
  created_by: string;
  version_number?: string;
}): Promise<ApiResult<{ version_id: string; status: string }>> {
  const res = await post<CreateSpecRaw>('/specs/create', p);
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
  return post<OkRaw>(`/specs/${version_id}/record-change`, { ...rest }) as unknown as Promise<ApiResult<null>>;
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
  return post<OkRaw>(`/specs/${version_id}/record-drift`, { ...rest }) as unknown as Promise<ApiResult<null>>;
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
// SAMPLE VERSIONS
// ═══════════════════════════════════════════════════════════════════════════════

/** GET /sample-versions/all → SampleVersion[] */
export async function listSampleVersions(tenant_id: string): Promise<ApiResult<SampleVersion[]>> {
  const res = await get<ListRaw<SampleVersion>>('/sample-versions/all', { tenant_id });
  if (!res.success || !res.data) return res as unknown as ApiResult<SampleVersion[]>;
  return { success: true, data: res.data.data ?? [] };
}

/** GET /sample-versions/{id} → SampleVersion */
export async function getSampleVersion(versionId: string): Promise<ApiResult<SampleVersion>> {
  const res = await get<SampleVersionDataRaw>(`/sample-versions/${versionId}`);
  if (!res.success || !res.data) return res as unknown as ApiResult<SampleVersion>;
  return { success: true, data: res.data.data };
}

/** GET /sample-versions/article/{article_id}/history → SampleVersion[] */
export async function getSampleVersionHistory(articleId: string, tenant_id: string): Promise<ApiResult<SampleVersion[]>> {
  const res = await get<SampleVersionHistoryRaw>(`/sample-versions/article/${articleId}/history`, { tenant_id });
  if (!res.success || !res.data) return res as unknown as ApiResult<SampleVersion[]>;
  return { success: true, data: res.data.versions ?? [] };
}

/** POST /sample-versions/create */
export async function createSampleVersion(p: {
  tenant_id: string;
  article_id: string;
  article_name: string;
  client_id: string;
  created_by: string;
  notes?: string;
}): Promise<ApiResult<{ version_id: string; version_label: string }>> {
  const res = await post<SampleVersionRaw>('/sample-versions/create', p);
  if (!res.success || !res.data) return res as unknown as ApiResult<{ version_id: string; version_label: string }>;
  return { success: true, data: { version_id: res.data.version_id, version_label: res.data.version_label ?? '' } };
}

/** POST /sample-versions/{id}/new-revision */
export async function createSampleVersionRevision(versionId: string, revised_by: string, revision_note: string): Promise<ApiResult<SampleVersionRaw>> {
  return post<SampleVersionRaw>(`/sample-versions/${versionId}/new-revision`, { revised_by, revision_note });
}

/** POST /sample-versions/{id}/submit-approval */
export async function submitSampleVersionApproval(versionId: string, submitted_by: string): Promise<ApiResult<SampleVersionRaw>> {
  return post<SampleVersionRaw>(`/sample-versions/${versionId}/submit-approval`, { submitted_by });
}

/** POST /sample-versions/{id}/approve */
export async function approveSampleVersion(versionId: string, approved_by: string, approval_note = ''): Promise<ApiResult<SampleVersionRaw>> {
  return post<SampleVersionRaw>(`/sample-versions/${versionId}/approve`, { approved_by, approval_note });
}

/** POST /sample-versions/{id}/convert-to-order */
export async function convertSampleVersionToOrder(versionId: string, order_id: string, converted_by: string): Promise<ApiResult<SampleVersionRaw>> {
  return post<SampleVersionRaw>(`/sample-versions/${versionId}/convert-to-order`, { order_id, converted_by });
}

/** PUT /sample-versions/{id}/components */
export async function updateSampleVersionComponents(versionId: string, updated_by: string, components: GarmentComponent[]): Promise<ApiResult<SampleVersionRaw>> {
  return put<SampleVersionRaw>(`/sample-versions/${versionId}/components`, { updated_by }, { components });
}

/** PUT /sample-versions/{id}/materials */
export async function updateSampleVersionMaterials(versionId: string, updated_by: string, materials: MaterialEstimation[]): Promise<ApiResult<SampleVersionRaw>> {
  return put<SampleVersionRaw>(`/sample-versions/${versionId}/materials`, { updated_by }, { materials });
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
export async function checkHealth(): Promise<ApiResult<HealthRaw>> {
  try {
    const raw = await http.get<HealthRaw>('/health', { timeoutMs: 5000 });
    return { success: raw.status === 'healthy', data: raw };
  } catch (error) {
    return { success: false, error: errorMessage(error) };
  }
}

// ─── Legacy class-style export for backward compat ───────────────────────────
export const api = {
  checkHealth,
  listStudies,
  createStudy,
  startStudy,
  pauseStudy,
  resumeStudy,
  completeStudy,
  addSample,
  getStudyData,
  getStudyStats,
  listSpecs,
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
  listSampleVersions,
  getSampleVersion,
  getSampleVersionHistory,
  createSampleVersion,
  createSampleVersionRevision,
  submitSampleVersionApproval,
  approveSampleVersion,
  convertSampleVersionToOrder,
  updateSampleVersionComponents,
  updateSampleVersionMaterials,
  getWorkflowSummary,
};

export default api;
