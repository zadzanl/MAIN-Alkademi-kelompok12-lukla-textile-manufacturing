/**
 * StatusBadge — canonical status pill used across tables and lists.
 * Colour variants live in index.css (`.pill-*`, token-backed and dark-aware).
 */
import React from 'react';

const CLS: Record<string, string> = {
  draft:       'pill pill-blue',
  in_progress: 'pill pill-orange',
  paused:      'pill pill-gray',
  completed:   'pill pill-green',
  review:      'pill pill-orange',
  approved:    'pill pill-green',
  active:      'pill pill-green',
  superseded:  'pill pill-gray',
  converted:   'pill pill-gray',
};

const LABEL: Record<string, string> = {
  draft: 'Draft', in_progress: 'Berjalan', paused: 'Pause',
  completed: 'Selesai', review: 'Review', approved: 'Disetujui',
  active: 'Aktif', superseded: 'Digantikan', converted: 'Dikonversi',
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => (
  <span className={CLS[status] ?? 'pill pill-gray'}>{LABEL[status] ?? status}</span>
);

export default StatusBadge;
