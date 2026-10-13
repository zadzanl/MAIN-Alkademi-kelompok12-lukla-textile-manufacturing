/**
 * Input Component
 * Apple Design System with clear contrast and tablet-friendly touch targets
 */

import React, { memo, forwardRef } from 'react';
import { InputProps } from '@/types';

export const Input = memo(
  forwardRef<HTMLInputElement, InputProps>(
    (
      {
        label,
        error,
        helperText,
        variant = 'outlined',
        className = '',
        ...props
      },
      ref
    ) => {
      const baseClasses =
        'w-full px-4 py-3 rounded-lg font-base text-base ' +
        'transition-all duration-200 focus-visible:outline-2 ' +
        'focus-visible:outline-offset-0 focus-visible:outline-purple-500 ' +
        'disabled:bg-gray-100 disabled:cursor-not-allowed ' +
        'min-h-12';

      const variantClasses = {
        outlined:
          'border-2 border-gray-200 bg-white text-gray-900 ' +
          'hover:border-gray-300 ' +
          'focus-visible:border-purple-500 ' +
          (error ? 'border-red-500' : ''),
        filled:
          'bg-gray-100 border-0 text-gray-900 ' +
          'focus-visible:bg-white ' +
          (error ? 'bg-red-50' : ''),
      };

      return (
        <div className="w-full">
          {label && (
            <label className="block text-sm font-medium text-gray-900 mb-2">
              {label}
            </label>
          )}
          <input
            ref={ref}
            className={`${baseClasses} ${variantClasses[variant]} ${className}`}
            {...props}
          />
          {error && (
            <p className="mt-1 text-sm text-red-500 font-medium">{error}</p>
          )}
          {helperText && !error && (
            <p className="mt-1 text-sm text-gray-500">{helperText}</p>
          )}
        </div>
      );
    }
  )
);

Input.displayName = 'Input';

export default Input;
