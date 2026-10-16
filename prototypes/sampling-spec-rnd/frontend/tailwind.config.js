/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  // Bug-fix #9: safelist runtime-constructed classes so Tailwind never purges them.
  // These come from SEV_COLOR map in DriftAnalysisView and STATUS_STYLE maps.
  safelist: [
    // severity pill backgrounds / text used via variable lookup
    'bg-brand-bg', 'text-brand',
    'bg-warn-bg', 'text-warn',
    'bg-bad-bg', 'text-bad',
    'bg-bad', 'text-white',
    // status badge colours
    'bg-ok-bg', 'text-ok',
    'bg-panel-2', 'text-ink-muted',
    // border-left accent on study cards
    'border-l-ok', 'border-l-warn', 'border-l-brand',
    // trend text colours
    'text-ok',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Display"',
          '"SF Pro Text"',
          '"Segoe UI"',
          '"Helvetica Neue"',
          'sans-serif',
        ],
      },
      colors: {
        // Legacy palette retained for existing page utilities; shared chrome
        // uses the CSS-variable semantic layer below.
        apple: {
          gray6: '#F2F2F7',      // System Gray 6 (background)
          gray5: '#E5E5EA',      // System Gray 5
          gray4: '#D1D1D6',      // System Gray 4
          gray3: '#C7C7CC',      // System Gray 3
          gray2: '#AEAEB2',      // System Gray 2
          gray: '#8E8E93',       // System Gray
          label: '#000000',      // Label (dark text)
          secondary: '#3C3C43',  // Secondary label
          tertiary: '#3C3C4399', // Tertiary label
        },
        primary: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        },
        glass: {
          50: 'rgba(255, 255, 255, 0.9)',
          100: 'rgba(255, 255, 255, 0.8)',
          200: 'rgba(255, 255, 255, 0.7)',
        },
        accent: {
          blue: '#315F86',
          green: '#287A4B',
          orange: '#9A6418',
          red: '#A33A35',
          purple: '#66627A',
        },
        // ── Semantic token layer (CSS-variable backed, dark-aware) ──────────
        // Light values are defined in index.css :root, dark values in .dark.
        // Near-duplicate tokens were consolidated (see Fase 2b).
        ink: 'var(--c-ink)',
        'ink-2': 'var(--c-ink-2)',
        'ink-muted': 'var(--c-ink-muted)',
        'ink-faint': 'var(--c-ink-faint)',
        brand: 'var(--c-brand)',
        'brand-soft': 'var(--c-brand-soft)',
        'brand-bg': 'var(--c-brand-bg)',
        'brand-bg-5': 'var(--c-brand-bg-5)',
        ok: 'var(--c-ok)',
        'ok-2': 'var(--c-ok-2)',
        'ok-bg': 'var(--c-ok-bg)',
        warn: 'var(--c-warn)',
        'warn-2': 'var(--c-warn-2)',
        'warn-bg': 'var(--c-warn-bg)',
        'warn-bg-2': 'var(--c-warn-bg-2)',
        bad: 'var(--c-bad)',
        'bad-4': 'var(--c-bad-4)',
        'bad-bg': 'var(--c-bad-bg)',
        'bad-bg-2': 'var(--c-bad-bg-2)',
        page: 'var(--c-page)',
        panel: 'var(--c-panel)',
        'panel-2': 'var(--c-panel-2)',
        'panel-6': 'var(--c-panel-6)',
        hair: 'var(--c-hair)',
        'hair-2': 'var(--c-hair-2)',
        'hair-4': 'var(--c-hair-4)',
      },
      spacing: {
        '3xs': '0.25rem',
        '2xs': '0.5rem',
        xs: '0.75rem',
        sm: '1rem',
        md: '1.5rem',
        lg: '2rem',
        xl: '3rem',
        '2xl': '4rem',
        '3xl': '6rem',
      },
      borderRadius: {
        none: '0',
        xs: '4px',
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        '2xl': '20px',
        '3xl': '24px',
        full: '9999px',
      },
      fontSize: {
        xs: ['12px', { lineHeight: '16px' }],
        sm: ['14px', { lineHeight: '20px' }],
        base: ['16px', { lineHeight: '24px' }],
        lg: ['18px', { lineHeight: '28px' }],
        xl: ['20px', { lineHeight: '28px' }],
        '2xl': ['24px', { lineHeight: '32px' }],
        '3xl': ['30px', { lineHeight: '36px' }],
      },
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
      animation: {
        fadeIn: 'fadeIn 0.2s ease-in-out',
        slideUp: 'slideUp 0.3s ease-out',
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      zIndex: {
        0: '0',
        10: '10',
        20: '20',
        30: '30',
        40: '40',
        50: '50',
        auto: 'auto',
      },
      minHeight: {
        '12': '48px',
      },
      minWidth: {
        '12': '48px',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
