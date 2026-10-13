/**
 * Apple Design System Tokens
 * Rounded corners, clear contrast, glassmorphism
 */

export const designTokens = {
  // Colors
  colors: {
    primary: '#8b5cf6',
    primaryLight: '#a78bfa',
    primaryDark: '#6d28d9',
    
    accent: {
      blue: '#3b82f6',
      green: '#10b981',
      orange: '#f97316',
      red: '#ef4444',
    },
    
    neutral: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
    
    glass: {
      light: 'rgba(255, 255, 255, 0.9)',
      medium: 'rgba(255, 255, 255, 0.7)',
      dark: 'rgba(17, 24, 39, 0.8)',
    },
    
    status: {
      success: '#10b981',
      warning: '#f97316',
      error: '#ef4444',
      info: '#3b82f6',
    },
  },

  // Spacing
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    '2xl': '32px',
    '3xl': '48px',
  },

  // Border Radius (Apple Design - rounded corners)
  borderRadius: {
    xs: '4px',
    sm: '6px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '20px',
    '3xl': '24px',
    full: '9999px',
  },

  // Font sizing
  fontSize: {
    xs: '12px',
    sm: '14px',
    base: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
  },

  // Line height
  lineHeight: {
    tight: '1.2',
    normal: '1.5',
    relaxed: '1.75',
    loose: '2',
  },

  // Font weights
  fontWeight: {
    thin: 100,
    extralight: 200,
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
    black: 900,
  },

  // Shadows - Glassmorphism effect
  shadows: {
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    glass: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  },

  // Backdrop blur
  backdropBlur: {
    xs: '2px',
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '24px',
  },

  // Z-index scale
  zIndex: {
    dropdown: 1000,
    sticky: 1100,
    fixed: 1200,
    modal: 1300,
    popover: 1400,
    tooltip: 1500,
  },

  // Touch targets (Factory tablet with gloves)
  touchTarget: {
    min: '48px',
    default: '56px',
    large: '64px',
  },

  // Transitions
  transition: {
    fast: '0.15s ease-out',
    normal: '0.2s ease-out',
    slow: '0.3s ease-out',
    slower: '0.5s ease-out',
  },

  // Performance optimization
  performance: {
    renderThrottle: 16, // 60fps
    debounce: 100,
    touchDebounce: 16,
  },
} as const;

// Helper functions
export const getGlassmorphismStyle = (intensity: 'sm' | 'md' | 'lg' = 'md') => {
  const blurMap = {
    sm: '4px',
    md: '8px',
    lg: '12px',
  };

  return {
    background: 'rgba(255, 255, 255, 0.7)',
    backdropFilter: `blur(${blurMap[intensity]})`,
    WebkitBackdropFilter: `blur(${blurMap[intensity]})`,
    border: '1px solid rgba(255, 255, 255, 0.2)',
  };
};

export const getClearContrastStyle = (text: 'primary' | 'secondary' | 'muted' = 'primary') => {
  const colorMap = {
    primary: '#1f2937',
    secondary: '#374151',
    muted: '#6b7280',
  };

  return {
    color: colorMap[text],
  };
};

export const getTouchTargetStyle = (size: 'default' | 'large' = 'default') => {
  const sizeMap = {
    default: '48px',
    large: '56px',
  };

  return {
    minHeight: sizeMap[size],
    minWidth: sizeMap[size],
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };
};

export default designTokens;
