/**
 * Button Component
 * Apple Design System - stable DOM, no conditional children swap
 */

import React, { memo, forwardRef } from 'react';
import { ButtonProps } from '@/types';

export const Button = memo(
  forwardRef<HTMLButtonElement, ButtonProps>(
    (
      {
        variant = 'primary',
        size = 'md',
        isLoading = false,
        className = '',
        children,
        disabled,
        ...props
      },
      ref
    ) => {
      const baseClasses =
        'inline-flex items-center justify-center font-medium transition-all duration-200 ' +
        'rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 ' +
        'active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ' +
        'whitespace-nowrap shrink-0 relative';

      const sizeClasses: Record<string, string> = {
        sm: 'px-3 py-2 text-sm min-h-9',
        md: 'px-4 py-2.5 text-base min-h-11',
        lg: 'px-6 py-3 text-lg min-h-14',
      };

      const variantClasses: Record<string, string> = {
        primary:
          'bg-accent-blue text-white ' +
          'hover:bg-blue-600 active:bg-blue-700 ' +
          'focus-visible:outline-accent-blue shadow-sm',
        secondary:
          'bg-white text-gray-900 border border-gray-200 ' +
          'hover:bg-gray-50 focus-visible:outline-accent-blue shadow-sm',
        danger:
          'bg-accent-red text-white hover:bg-red-600 active:bg-red-700 ' +
          'focus-visible:outline-accent-red shadow-sm',
        outline:
          'border-2 border-accent-purple text-purple-600 ' +
          'hover:bg-purple-50 focus-visible:outline-accent-purple',
        ghost:
          'text-gray-700 hover:bg-gray-100 active:bg-gray-200 focus-visible:outline-gray-400',
      };

      return (
        <button
          ref={ref}
          className={`${baseClasses} ${sizeClasses[size] ?? sizeClasses.md} ${variantClasses[variant] ?? variantClasses.primary} ${className}`}
          disabled={disabled || isLoading}
          aria-busy={isLoading}
          {...props}
        >
          {/* Spinner overlay — always rendered, just invisible when not loading */}
          <span
            aria-hidden="true"
            className={`absolute inset-0 flex items-center justify-center transition-opacity duration-150 ${isLoading ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
          >
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </span>

          {/* Children always rendered — just invisible when loading */}
          <span className={`transition-opacity duration-150 ${isLoading ? 'opacity-0' : 'opacity-100'}`}>
            {children}
          </span>
        </button>
      );
    }
  )
);

Button.displayName = 'Button';
export default Button;
