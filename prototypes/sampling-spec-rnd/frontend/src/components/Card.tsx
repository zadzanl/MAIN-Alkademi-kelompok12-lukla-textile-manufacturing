/**
 * Card Component
 * Glassmorphism effect with Apple Design System styling
 */

import React, { memo } from 'react';
import { CardProps } from '@/types';

export const Card = memo<CardProps>(
  ({ variant = 'default', className = '', children, ...props }) => {
    const baseClasses = 'rounded-2xl transition-all duration-200';

    const variantClasses = {
      default:
        'bg-white backdrop-blur-md border border-gray-100 ' +
        'shadow-sm hover:shadow-md',
      glass:
        'bg-white/85 backdrop-blur-xl border border-white/20 ' +
        'shadow-lg',
      outlined:
        'bg-transparent border border-gray-200 ' +
        'hover:border-gray-300 hover:bg-white/50',
    };

    return (
      <div
        className={`${baseClasses} ${variantClasses[variant]} ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export default Card;
