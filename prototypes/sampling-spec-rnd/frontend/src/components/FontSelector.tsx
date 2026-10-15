/**
 * FontSelector
 *
 * Displays a grid of font option cards. Each card previews the font with
 * real sample text rendered in that typeface so the user can compare at a
 * glance before committing.
 *
 * Props:
 *   currentFont  — the active font key (matches FontOption.id)
 *   onChange     — called with the new font key when the user picks one
 */

import React from 'react';

export type FontKey =
  | 'sf-pro'
  | 'inter'
  | 'plus-jakarta'
  | 'dm-sans'
  | 'geist'
  | 'ibm-plex'
  | 'sora';

export interface FontOption {
  id: FontKey;
  name: string;
  /** Actual CSS font-family string used inside the card preview */
  family: string;
  tagline: string;
  /** Short sample string that shows off the typeface's personality */
  sample: string;
  /** Designer / foundry credit */
  by: string;
  recommended?: boolean;
}

export const FONT_OPTIONS: FontOption[] = [
  {
    id: 'sf-pro',
    name: 'SF Pro',
    family: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif",
    tagline: 'System default · Apple HIG',
    sample: 'Aa Bb Cc 0123',
    by: 'Apple',
    recommended: true,
  },
  {
    id: 'inter',
    name: 'Inter',
    family: "'Inter', sans-serif",
    tagline: 'Neutral · Screen-optimised',
    sample: 'Aa Bb Cc 0123',
    by: 'Rasmus Andersson',
    recommended: true,
  },
  {
    id: 'plus-jakarta',
    name: 'Plus Jakarta Sans',
    family: "'Plus Jakarta Sans', sans-serif",
    tagline: 'Modern · Geometric rounded',
    sample: 'Aa Bb Cc 0123',
    by: 'Tokotype',
  },
  {
    id: 'dm-sans',
    name: 'DM Sans',
    family: "'DM Sans', sans-serif",
    tagline: 'Soft · Low optical size',
    sample: 'Aa Bb Cc 0123',
    by: 'Colophon Foundry',
  },
  {
    id: 'geist',
    name: 'Geist',
    family: "'Geist', sans-serif",
    tagline: 'Developer · Precise spacing',
    sample: 'Aa Bb Cc 0123',
    by: 'Vercel',
  },
  {
    id: 'ibm-plex',
    name: 'IBM Plex Sans',
    family: "'IBM Plex Sans', sans-serif",
    tagline: 'Structured · Engineering-grade',
    sample: 'Aa Bb Cc 0123',
    by: 'IBM',
  },
  {
    id: 'sora',
    name: 'Sora',
    family: "'Sora', sans-serif",
    tagline: 'Rounded · Expressive friendly',
    sample: 'Aa Bb Cc 0123',
    by: 'Shun Kambe',
  },
];

interface FontSelectorProps {
  currentFont: FontKey;
  onChange: (font: FontKey) => void;
}

const FontSelector: React.FC<FontSelectorProps> = ({ currentFont, onChange }) => {
  return (
    <section aria-labelledby="font-selector-heading">
      {/* ── Section header ─────────────────────────────────────────────────── */}
      <div className="mb-5">
        <h3
          id="font-selector-heading"
          className="text-[15px] font-semibold text-ink mb-1"
        >
          Gaya Font Antarmuka
        </h3>
        <p className="text-[13px] text-ink-muted">
          Pilih tipografi yang paling nyaman untuk Anda. Perubahan langsung
          diterapkan ke seluruh antarmuka.
        </p>
      </div>

      {/* ── Font option grid ───────────────────────────────────────────────── */}
      <div
        className="grid gap-3"
        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}
        role="radiogroup"
        aria-labelledby="font-selector-heading"
      >
        {FONT_OPTIONS.map((font) => {
          const isActive = currentFont === font.id;
          return (
            <button
              key={font.id}
              role="radio"
              aria-checked={isActive}
              onClick={() => onChange(font.id)}
              title={`Pilih ${font.name}`}
              style={{ fontFamily: 'inherit', textAlign: 'left' }}
              className={[
                'relative rounded-[14px] p-4 border-2 text-left',
                'transition-all duration-150',
                isActive
                  ? 'border-brand bg-brand-bg shadow-[0_0_0_4px_rgba(0,113,227,0.12)]'
                  : 'border-hair bg-white hover:border-brand/40 hover:bg-panel hover:shadow-sm',
              ].join(' ')}
            >
              {/* Recommended badge */}
              {font.recommended && (
                <span
                  className="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full"
                  style={{
                    background: isActive ? '#0071e3' : '#e2e8f0',
                    color: isActive ? '#fff' : '#64748b',
                  }}
                >
                  Rekomendasi
                </span>
              )}

              {/* Font preview — rendered IN the candidate typeface */}
              <div
                className="mb-3 leading-none"
                style={{ fontFamily: font.family }}
              >
                <span
                  className="block font-bold"
                  style={{
                    fontSize: '26px',
                    color: isActive ? '#0071e3' : '#0f172a',
                    letterSpacing: '-0.02em',
                  }}
                >
                  {font.sample}
                </span>
                <span
                  className="block mt-1 font-medium"
                  style={{
                    fontSize: '11px',
                    color: isActive ? '#0071e3' : '#64748b',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  {font.name}
                </span>
              </div>

              {/* Meta */}
              <p
                className="text-[11px] leading-snug"
                style={{ color: isActive ? '#1d4ed8' : '#475569' }}
              >
                {font.tagline}
              </p>
              <p
                className="text-[10px] mt-1"
                style={{ color: isActive ? '#3b82f6' : '#94a3b8' }}
              >
                by {font.by}
              </p>

              {/* Active checkmark */}
              {isActive && (
                <span
                  className="absolute bottom-3 right-3 w-5 h-5 rounded-full flex items-center justify-center"
                  style={{ background: '#0071e3' }}
                  aria-hidden="true"
                >
                  {/* Simple SVG checkmark */}
                  <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                    <path
                      d="M1 4l2.5 2.5L9 1"
                      stroke="white"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Live preview strip ─────────────────────────────────────────────── */}
      <LivePreview fontKey={currentFont} />
    </section>
  );
};

/* ── Live Preview ────────────────────────────────────────────────────────────── */

const PREVIEW_TEXT: Record<FontKey, { heading: string; body: string }> = {
  'sf-pro': {
    heading: 'Sampling & Spec R&D',
    body: 'Studi waktu membantu Anda memahami ritme produksi secara akurat.',
  },
  inter: {
    heading: 'Sampling & Spec R&D',
    body: 'Analisis data produksi dengan presisi tinggi dan efisiensi penuh.',
  },
  'plus-jakarta': {
    heading: 'Sampling & Spec R&D',
    body: 'Kelola setiap versi spec dan pantau drift dalam satu dasbor terpadu.',
  },
  'dm-sans': {
    heading: 'Sampling & Spec R&D',
    body: 'Tampilan yang ramah dan nyaman untuk sesi kerja panjang di lantai produksi.',
  },
  geist: {
    heading: 'Sampling & Spec R&D',
    body: 'Presisi teknikal dalam setiap piksel — untuk tim rekayasa yang serius.',
  },
  'ibm-plex': {
    heading: 'Sampling & Spec R&D',
    body: 'Terstruktur, terbaca, dan andal. Dirancang untuk lingkungan industri.',
  },
  sora: {
    heading: 'Sampling & Spec R&D',
    body: 'Antarmuka yang hangat dan ekspresif mendukung kolaborasi tim yang lebih baik.',
  },
};

const LivePreview: React.FC<{ fontKey: FontKey }> = ({ fontKey }) => {
  const opt = FONT_OPTIONS.find((f) => f.id === fontKey)!;
  const preview = PREVIEW_TEXT[fontKey];

  return (
    <div
      className="mt-5 rounded-[14px] border border-hair bg-white p-5 overflow-hidden"
      aria-label="Pratinjau font aktif"
    >
      <p className="text-[11px] font-bold uppercase tracking-widest text-ink-faint mb-3">
        Pratinjau — {opt.name}
      </p>
      <div style={{ fontFamily: opt.family }}>
        {/* Heading scale */}
        <p
          className="font-bold leading-tight mb-1"
          style={{ fontSize: '22px', color: '#0f172a', letterSpacing: '-0.025em' }}
        >
          {preview.heading}
        </p>
        {/* Body scale */}
        <p
          className="leading-relaxed"
          style={{ fontSize: '14px', color: '#334155' }}
        >
          {preview.body}
        </p>
        {/* UI micro-copy samples */}
        <div className="flex flex-wrap gap-2 mt-3">
          {['Draft', 'Berjalan', 'Selesai', 'Disetujui'].map((label) => (
            <span
              key={label}
              className="inline-flex items-center px-3 py-1 rounded-full text-[11px] font-semibold"
              style={{
                background: '#eff6ff',
                color: '#1d4ed8',
                border: '1px solid #bfdbfe',
                fontFamily: opt.family,
              }}
            >
              {label}
            </span>
          ))}
          <span
            className="inline-flex items-center px-3 py-1 rounded-full text-[11px] font-semibold"
            style={{
              background: '#0071e3',
              color: '#fff',
              fontFamily: opt.family,
            }}
          >
            Buat Studi Baru
          </span>
        </div>
      </div>
    </div>
  );
};

export default FontSelector;
