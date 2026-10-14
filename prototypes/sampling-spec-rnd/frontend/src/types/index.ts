/**
 * Type definitions for Sampling & Spec R&D
 * Includes: TimeStudy, SpecVersion, SampleVersion, WorkflowSummary
 */
import React from 'react';

// ─────────────────────────────────────────────
// TIME STUDY
// ─────────────────────────────────────────────

export interface TimeSample {
  sample_id: string;
  timestamp: string;
  cycle_time_ms: number;
  element_name: string;
  observations: Record<string, unknown>;
  operator_id: string | null;
  machine_id: string | null;
  is_abnormal: boolean;
  notes: string;
}

export interface TimeStudy {
  study_id: string;
  tenant_id: string;
  process_id: string;
  process_name: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  status: 'draft' | 'in_progress' | 'paused' | 'completed' | 'archived';
  target_sample_size: number;
  samples: TimeSample[];
  confidence_level: number;
  allowance_percent: number;
  operator_id: string;
  department_id: string;
  shift: string;
  product_id: string;
  notes: string;
  total_cycles: number;
  mean_cycle_time: number;
  std_dev_cycle_time: number;
  min_cycle_time: number;
  max_cycle_time: number;
}

export interface TimeStudyStats {
  total_samples: number;
  normal_samples: number;
  abnormal_samples: number;
  mean_cycle_time_ms: number;
  std_dev: number;
  min_cycle_time_ms: number;
  max_cycle_time_ms: number;
  coeff_of_variation: number;
  confidence_level: number;
  allowance_percent: number;
}

// ─────────────────────────────────────────────
// SPEC VERSION
// ─────────────────────────────────────────────

export interface SpecChange {
  change_id: string;
  timestamp: string;
  change_type: string;
  parameter_name: string;
  old_value: string;
  new_value: string;
  changed_by: string;
  reason: string;
  impact_assessment: string;
}

export interface SpecDrift {
  drift_id: string;
  timestamp: string;
  parameter_name: string;
  specification_limit: number;
  measured_value: number;
  deviation_percent: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  corrective_action: string;
  resolved: boolean;
  resolved_at: string | null;
}

export interface SpecVersion {
  version_id: string;
  tenant_id: string;
  spec_id: string;
  spec_name: string;
  version_number: string;
  created_at: string;
  updated_at: string;
  status: 'draft' | 'review' | 'approved' | 'active' | 'superseded' | 'archived';
  parameters: Record<string, unknown>;
  tolerances: Record<string, { min: number; max: number }>;
  materials: string[];
  process_steps: string[];
  changes: SpecChange[];
  drifts: SpecDrift[];
  total_drifts: number;
  critical_drifts: number;
  created_by: string;
  approved_by: string | null;
  approved_at: string | null;
  notes: string;
  parent_version_id: string | null;
  supersedes_version_id: string | null;
}

export interface DriftAnalysis {
  total_drifts: number;
  severity_distribution: Record<string, number>;
  by_parameter: Record<string, { count: number; critical: number }>;
  critical_parameters: string[];
  critical_rate_percent: number;
  trend: 'stable' | 'concerning' | 'worsening' | 'critical';
  parameters_with_drift: number;
}

// ─────────────────────────────────────────────
// SAMPLE VERSION  (new — v1/v2/v3 article versioning per PRD)
// ─────────────────────────────────────────────

/** One sewn component (kerah, lengan, badan depan, badan belakang, etc.) */
export interface GarmentComponent {
  component_id: string;          // local UUID for keying
  part_name: string;             // e.g. "Kerah", "Lengan Kiri"
  description: string;           // technical description / construction notes
  material_type: string;         // e.g. "Cotton Combed 30s"
  estimated_usage_m: number;     // metres of fabric estimated
  unit: string;                  // "m", "pcs", "yard"
  sewing_time_std_ms: number;    // standard time from time study (ms)
  rate_card_idr: number;         // derived rate card (IDR per piece)
  notes: string;
}

/** One material line for BOM (Bill of Materials) estimation */
export interface MaterialEstimation {
  material_code: string;         // e.g. "FAB-CTN-30S"
  material_name: string;         // e.g. "Cotton Combed 30s"
  estimated_usage: number;
  unit: string;                  // "m", "kg", "pcs"
  unit_cost: number;             // IDR per unit
  total_cost: number;            // estimated_usage × unit_cost
  supplier_id: string;
  notes: string;
}

/** Immutable event in the revision log */
export interface RevisionLogEntry {
  action:
    | 'created'
    | 'revised'
    | 'submitted_for_approval'
    | 'approved'
    | 'converted_to_order'
    | 'components_updated'
    | 'materials_updated';
  by: string;
  at: string;   // ISO timestamp
  note: string;
}

/** Full sample version record */
export interface SampleVersion {
  version_id: string;
  tenant_id: string;
  article_id: string;            // stable SKU / article code
  article_name: string;
  client_id: string;             // e.g. "snohund" or external brand ID
  version_number: number;        // 1, 2, 3 …
  version_label: string;         // "v1", "v2", "v3" …
  parent_version_id: string | null;
  status: 'draft' | 'pending_approval' | 'approved' | 'converted';
  created_by: string;
  created_at: string;
  updated_at: string;
  approved_by: string | null;
  approved_at: string | null;
  converted_to_order_id: string | null;
  notes: string;
  components: GarmentComponent[];
  materials: MaterialEstimation[];
  revision_log: RevisionLogEntry[];
}

// ─────────────────────────────────────────────
// WORKFLOW SUMMARY
// ─────────────────────────────────────────────

export interface WorkflowSummary {
  active_studies: number;
  completed_studies: number;
  active_specs: number;
  specs_in_review: number;
  total_drifts: number;
  critical_drifts: number;
  total_sample_versions: number;
  pending_approval: number;
  converted_to_order: number;
}

// ─────────────────────────────────────────────
// SHARED CALLBACKS
// ─────────────────────────────────────────────

/** CSV export handler shared by App and page views. */
export type ExportCSV = (data: unknown[], filename: string) => void;

// ─────────────────────────────────────────────
// COMPONENT PROPS
// ─────────────────────────────────────────────

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  children: React.ReactNode;
}

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'outlined';
  children: React.ReactNode;
}

export interface ModalProps {
  isOpen: boolean;
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  footer?: React.ReactNode;
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  variant?: 'outlined' | 'filled';
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: Array<{ label: string; value: string | number }>;
}
