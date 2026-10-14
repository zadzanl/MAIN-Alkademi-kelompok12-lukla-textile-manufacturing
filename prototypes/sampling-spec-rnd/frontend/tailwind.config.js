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
    'bg-[#e8f2ff]', 'text-[#0066cc]',
    'bg-[#fff4e6]', 'text-[#ff9500]',
    'bg-[#ffebee]', 'text-[#ff3b30]',
    'bg-[#ff3b30]', 'text-white',
    // status badge colours
    'bg-[#e8f5e9]', 'text-[#34c759]',
    'bg-[#f0f0f2]', 'text-[#626269]',
    // border-left accent on study cards
    'border-l-[#34c759]', 'border-l-[#ff9500]', 'border-l-[#0071e3]',
    // trend text colours
    'text-[#34c759]',
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
        // Apple System Colors
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
          blue: '#007AFF',    // Apple blue
          green: '#34C759',   // Apple green
          orange: '#FF9500',  // Apple orange
          red: '#FF3B30',     // Apple red
          purple: '#AF52DE',  // Apple purple
        },
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
      shadows: {
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        base: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
        glass: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
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
