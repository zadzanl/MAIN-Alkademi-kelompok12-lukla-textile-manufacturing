/**
 * MockModeBanner — single source for the "mock data" notice shown at the top of
 * every view whose live HTTP service is not wired yet (ops / ledger / payroll).
 *
 * The service clients already swap to the real service when VITE_LEDGER_MODE=live
 * (see services/config.ts), so this banner is purely informational.
 */

import React from 'react';

interface MockModeBannerProps {
  /** Sentence after the "Mode mock aktif —" prefix, ending with a period. */
  detail: string;
  /** Sentence after the env-var hint. Defaults to "untuk service asli." */
  hint?: string;
}

const MockModeBanner: React.FC<MockModeBannerProps> = ({ detail, hint = 'untuk service asli.' }) => (
  <div className="rounded-[14px] border border-[#d5d5da] bg-[#f4f8fd] px-4 py-3 text-[12.5px] text-[#334155]">
    Mode mock aktif — {detail} Set <code className="font-mono">VITE_LEDGER_MODE=live</code> {hint}
  </div>
);

export default MockModeBanner;
