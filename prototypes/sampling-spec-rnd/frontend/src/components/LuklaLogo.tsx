/**
 * LuklaLogo — the LUKLA mountain mark plus optional wordmark, used in the
 * portal header and footer. The gradient id is instance-unique (React useId)
 * so multiple logos can coexist on one page without SVG id collisions.
 */
import React, { useId } from 'react';

interface LuklaLogoProps {
  size?: number;
  showWordmark?: boolean;
  wordmarkColor?: string;
  className?: string;
}

const LuklaLogo: React.FC<LuklaLogoProps> = ({
  size = 30,
  showWordmark = true,
  wordmarkColor = 'var(--c-ink)',
  className = '',
}) => {
  const gradientId = useId();

  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`.trim()}>
      <svg
        width={size}
        height={(size * 26) / 40}
        viewBox="0 0 40 26"
        role="img"
        aria-label="Lukla"
        focusable="false"
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#4f83b3" />
            <stop offset="1" stopColor="#1d3857" />
          </linearGradient>
        </defs>
        <path d="M27 2 40 26H14Z" fill={`url(#${gradientId})`} />
        <path d="M13 7 26 26H0Z" fill="#2f5d8a" />
        <path d="M13 7l3.5 5.5H9.5Z" fill="#8fb4d1" />
      </svg>
      {showWordmark && (
        <span
          className="font-semibold tracking-[.16em]"
          style={{ color: wordmarkColor, fontSize: Math.round(size * 0.6) }}
        >
          LUKLA
        </span>
      )}
    </span>
  );
};

export default LuklaLogo;
