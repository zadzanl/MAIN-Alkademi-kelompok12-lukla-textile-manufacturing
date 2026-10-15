/**
 * types/api.ts — Raw response shapes returned by the sampling backend.
 *
 * Kept separate from the domain models in types/index.ts so a backend contract
 * change surfaces here (and in backend/tests/test_contract.py) instead of
 * leaking into components. The client in services/api.ts maps these to domain
 * models.
 */
import type {
  TimeStudy,
  SpecVersion,
  TimeStudyStats,
  DriftAnalysis,
  WorkflowSummary,
  SampleVersion,
} from './index';

export interface CreateStudyRaw { success: boolean; study_id: string; status: string; message: string }
export interface CreateSpecRaw { success: boolean; version_id: string; status: string; message: string }
export interface StudyDataRaw { success: boolean; data: TimeStudy }
export interface SpecDataRaw { success: boolean; data: SpecVersion }
export interface StatsRaw { success: boolean; statistics: TimeStudyStats }
export interface ListRaw<T> { success: boolean; data: T[]; count: number }
export interface DriftReportRaw { success: boolean; report: unknown }
export interface DriftAnalysisRaw { success: boolean; version_id: string; analysis: DriftAnalysis; risk_score: number }
export interface ChangeHistoryRaw { success: boolean; history: unknown }
export interface WorkflowRaw { success: boolean; summary: WorkflowSummary }
export interface HealthRaw { status: string; module?: string; service?: string }
export interface OkRaw { success: boolean; message: string }
export interface SampleVersionRaw {
  success: boolean;
  version_id: string;
  version_label?: string;
  status?: string;
  parent_version_id?: string;
  order_id?: string;
  component_count?: number;
  material_count?: number;
  estimated_total_cost?: number;
}
export interface SampleVersionDataRaw { success: boolean; data: SampleVersion }
export interface SampleVersionHistoryRaw {
  success: boolean;
  article_id: string;
  versions: SampleVersion[];
  total_versions: number;
}
