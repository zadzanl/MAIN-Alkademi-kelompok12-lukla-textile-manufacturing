/**
 * Card Component
 * Glassmorphism effect with Apple Design System styling
 */

import React, { memo } from 'react';
import { CardProps } from '@/types';

export const Card = memo<CardProps>(
  ({ variant = 'default', className = '', children, ...props }) => {
    const baseClasses = 'rounded-xl transition-all duration-200';

    const variantClasses = {
      default:
        'bg-white/80 backdrop-blur-md border border-white/20 ' +
        'shadow-lg hover:shadow-xl hover:bg-white/90',
      glass:
        'bg-white/60 backdrop-blur-lg border border-white/30 ' +
        'shadow-glass',
      outlined:
        'bg-transparent border-2 border-purple-200 ' +
        'hover:border-purple-400 hover:bg-purple-50/50',
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
