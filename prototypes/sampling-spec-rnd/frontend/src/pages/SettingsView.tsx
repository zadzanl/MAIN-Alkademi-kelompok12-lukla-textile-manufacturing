/**
 * SettingsView — appearance (theme + font) and system info.
 */
import React from 'react';
import FontSelector, { FontKey } from '../components/FontSelector';
import { LucideIcon } from '../components/Sidebar';
import ChangePasswordCard from '../components/ChangePasswordCard';
import { SAMPLING_BASE, DATA_MODE } from '../services/config';
import { toast } from '../services/toast';
import { TENANT_ID } from '../services/identity';

interface SettingsViewProps {
  isDark: boolean;
  onToggleDark: () => void;
  font: FontKey;
  onFontChange: (font: FontKey) => void;
  onCheckHealth: () => Promise<boolean>;
  onLoggedOut: () => void;
}

const SettingsView: React.FC<SettingsViewProps> = ({
  isDark, onToggleDark, font, onFontChange, onCheckHealth, onLoggedOut,
}) => (
  <div className="space-y-6 max-w-3xl">

    {/* ── Dark mode toggle ───────────────────────────────────────── */}
    <div
      className="border rounded-[18px] p-6"
      style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3
            className="text-[15px] font-semibold mb-1"
            style={{ color: 'var(--c-ink)' }}
          >
            Tampilan
          </h3>
          <p className="text-[13px]" style={{ color: 'var(--c-ink-muted)' }}>
            {isDark ? 'Mode Gelap aktif — klik untuk beralih ke Mode Terang' : 'Mode Terang aktif — klik untuk beralih ke Mode Gelap'}
          </p>
        </div>
        {/* Toggle switch */}
        <button
          type="button"
          role="switch"
          aria-checked={isDark}
          aria-label="Toggle dark mode"
          onClick={onToggleDark}
          className="relative inline-flex items-center rounded-full transition-colors focus-visible:outline-none shrink-0"
          style={{ width: 52, height: 30, background: isDark ? 'var(--c-brand)' : 'var(--c-hair-4)' }}
        >
          <span
            className="inline-block rounded-full bg-white shadow-sm"
            style={{
              width: 22, height: 22,
              transform: isDark ? 'translateX(26px)' : 'translateX(4px)',
              transition: 'transform 200ms cubic-bezier(.34,1.56,.64,1)',
            }}
          />
        </button>
      </div>
    </div>

    {/* ── Font selector ─────────────────────────────────────────── */}
    <div
      className="border rounded-[18px] p-6"
      style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}
    >
      <FontSelector currentFont={font} onChange={onFontChange} />
    </div>

    {/* ── Security (change password) ────────────────────────────── */}
    <ChangePasswordCard onLoggedOut={onLoggedOut} />

    {/* ── System info ───────────────────────────────────────────── */}
    <div
      className="border rounded-[18px] p-6"
      style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}
    >
      <h3
        className="text-[15px] font-semibold mb-4"
        style={{ color: 'var(--c-ink)' }}
      >
        Informasi Sistem
      </h3>
      <div className="space-y-0">
        {[
          { label: 'Tenant ID',   value: TENANT_ID },
          { label: 'Backend URL', value: SAMPLING_BASE },
          { label: 'Mode Data',   value: DATA_MODE === 'mock' ? 'Mock (in-memory)' : 'Live' },
          { label: 'Frontend',    value: 'http://localhost:3009' },
          { label: 'Versi Modul', value: 'Sprint 1 · v1.0.0' },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="flex justify-between py-3 border-b last:border-0"
            style={{ borderColor: 'var(--c-panel-2)' }}
          >
            <span className="text-sm" style={{ color: 'var(--c-ink-muted)' }}>{label}</span>
            <code className="text-sm font-medium" style={{ color: 'var(--c-ink)' }}>{value}</code>
          </div>
        ))}
      </div>
      <div className="mt-5">
        <button
          onClick={async () => {
            const ok = await onCheckHealth();
            if (ok) toast.success('Backend terhubung dan sehat.');
            else toast.error('Backend tidak dapat dijangkau. Periksa port 8009.');
          }}
          className="btn-secondary inline-flex items-center gap-2">
          <LucideIcon name="activity" className="w-4 h-4" /> Test Koneksi Backend
        </button>
      </div>
    </div>

  </div>
);

export default SettingsView;
