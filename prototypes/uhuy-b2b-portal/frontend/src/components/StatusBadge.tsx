/**
 * StatusBadge — canonical status pill used across tables and lists.
 * Colour variants live in index.css (`.pill-*`, token-backed and dark-aware).
 * Covers both order-lifecycle and portal-request statuses.
 */
import React from 'react';

const CLS: Record<string, string> = {
  // order lifecycle
  confirmed:   'pill pill-blue',
  cutting:     'pill pill-orange',
  sewing:      'pill pill-orange',
  qc:          'pill pill-orange',
  completed:   'pill pill-green',
  // portal requests
  submitted:   'pill pill-orange',
  review:      'pill pill-orange',
  approved:    'pill pill-green',
  rejected:    'pill pill-red',
  // account / generic
  pending:     'pill pill-orange',
  active:      'pill pill-green',
  done:        'pill pill-green',
  draft:       'pill pill-blue',
  in_progress: 'pill pill-orange',
  paused:      'pill pill-gray',
  superseded:  'pill pill-gray',
  converted:   'pill pill-gray',
};

const LABEL: Record<string, string> = {
  confirmed: 'Dikonfirmasi',
  cutting: 'Cutting',
  sewing: 'Produksi Jahit',
  qc: 'Inspeksi QC',
  completed: 'Selesai',
  submitted: 'Diajukan',
  review: 'Ditinjau',
  approved: 'Disetujui',
  rejected: 'Ditolak',
  pending: 'Menunggu',
  active: 'Aktif',
  done: 'Selesai',
  draft: 'Draft',
  in_progress: 'Berjalan',
  paused: 'Pause',
  superseded: 'Digantikan',
  converted: 'Dikonversi',
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => (
  <span className={CLS[status] ?? 'pill pill-gray'}>{LABEL[status] ?? status}</span>
);

export default StatusBadge;
