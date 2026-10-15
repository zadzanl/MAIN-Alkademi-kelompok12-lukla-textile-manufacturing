/**
 * PortalBadge — the visual marker for the EXTERNAL portal (UHUY B2B).
 *
 * Rendered in the sidebar brand, the page header, and the login hero so this
 * build can never be confused with the internal factory dashboard. Styling is
 * token-backed (`.portal-badge` in index.css) and dark-mode aware.
 */
import React from 'react';

interface PortalBadgeProps {
  variant?: 'outline' | 'solid';
  className?: string;
}

const PortalBadge: React.FC<PortalBadgeProps> = ({ variant = 'outline', className = '' }) => (
  <span
    className={`portal-badge ${variant === 'solid' ? 'portal-badge--solid' : ''} ${className}`.trim()}
    title="Portal eksternal — akses data dibatasi hanya untuk klien Anda"
  >
    <span className="portal-badge__dot" aria-hidden="true" />
    PORTAL EKSTERNAL
  </span>
);

export default PortalBadge;
