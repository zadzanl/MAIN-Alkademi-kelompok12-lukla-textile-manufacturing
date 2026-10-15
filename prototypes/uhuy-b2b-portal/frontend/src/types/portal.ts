/**
 * portal.ts — Domain types for the UHUY B2B external portal.
 * Mirrors the JSON returned by the external-portal backend (port 8010).
 */

export type OrderStatus = 'confirmed' | 'cutting' | 'sewing' | 'qc' | 'completed';
export type RequestKind = 'order' | 'sample';
export type RequestStatus = 'submitted' | 'review' | 'approved' | 'rejected';
export type MaklonScheme = 'CMT' | 'Semi-CMT' | 'Full Package';

export interface OrderTimelineEntry {
  phase: string;
  status: string;
  at: string;
}

export interface Order {
  order_id: string;
  client_id: string;
  article_name: string;
  quantity: number;
  scheme: string;
  status: string;
  progress: number;
  current_phase: string;
  target_date: string;
  created_at: number;
  timeline: OrderTimelineEntry[];
}

export interface StockLot {
  lot_id: string;
  client_id: string;
  material_code: string;
  material_name: string;
  unit: string;
  quantity_available: number;
  received_at: string;
}

export interface PortalRequest {
  request_id: string;
  client_id: string;
  kind: RequestKind;
  article_name: string;
  quantity: number;
  scheme: string;
  target_date: string;
  notes: string;
  status: string;
  created_at: number;
  updated_at: number;
}

export interface PortalSummary {
  active_orders: number;
  completed_orders: number;
  pending_requests: number;
  consigned_lots: number;
  total_orders: number;
}

export interface ActorContext {
  actorId: string;
  displayName: string;
  email: string;
  role: string;
  status: string;
  clientId: string;
  companyName: string;
}

export interface SessionResult {
  accessToken: string;
  expiresIn: number;
  actor: ActorContext;
}

export interface RegisterPayload {
  company_name: string;
  contact_name: string;
  email: string;
  phone: string;
  password: string;
  consent: boolean;
}

export interface OrderRequestPayload {
  article_name: string;
  quantity: number;
  scheme: string;
  target_date: string;
  notes: string;
}

export interface SampleRequestPayload {
  article_name: string;
  quantity: number;
  scheme: string;
  target_date: string;
  notes: string;
}

export const MAKLON_SCHEMES: MaklonScheme[] = ['CMT', 'Semi-CMT', 'Full Package'];
