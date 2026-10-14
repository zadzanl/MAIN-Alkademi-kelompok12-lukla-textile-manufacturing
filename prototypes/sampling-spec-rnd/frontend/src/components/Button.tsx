/**
 * Button Component
 * Apple Design System - rounded corners, clear contrast, touch-friendly
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
        'whitespace-nowrap shrink-0 touch-target';

      const sizeClasses = {
        sm: 'px-3 py-2 text-sm min-h-9 min-w-9',
        md: 'px-4 py-2.5 text-base min-h-12 min-w-12',
        lg: 'px-6 py-3 text-lg min-h-14 min-w-14',
      };

      const variantClasses = {
        primary:
          'bg-gradient-to-r from-purple-500 to-purple-600 text-white ' +
          'hover:from-purple-600 hover:to-purple-700 ' +
          'focus-visible:outline-purple-500 shadow-md',
        secondary:
          'bg-white/70 backdrop-blur-md text-gray-900 border border-white/20 ' +
          'hover:bg-white/80 ' +
          'focus-visible:outline-purple-500 shadow-md',
        danger:
          'bg-red-500 text-white hover:bg-red-600 ' +
          'focus-visible:outline-red-500 shadow-md',
        outline:
          'border-2 border-purple-500 text-purple-600 ' +
          'hover:bg-purple-50 ' +
          'focus-visible:outline-purple-500',
      };

      return (
        <button
          ref={ref}
          className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
          disabled={disabled || isLoading}
          {...props}
        >
          {isLoading ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Loading...
            </>
          ) : (
            children
          )}
        </button>
      );
    }
  )
);

Button.displayName = 'Button';

export default Button;
