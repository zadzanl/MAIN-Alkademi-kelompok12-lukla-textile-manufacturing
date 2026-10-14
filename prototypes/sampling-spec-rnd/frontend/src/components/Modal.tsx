/**
 * Modal Component — Dialog Overlay
 * Matches Garment Backoffice HTML template design
 */

import React, { useEffect } from 'react';
import { LucideIcon } from './Sidebar';

interface ModalProps {
  isOpen: boolean;
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  footer?: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, title, children, onClose, footer }) => {
  // Handle Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop fixed inset-0 bg-[#17171b80] flex items-center justify-center p-4 sm:p-6 z-50"
      onClick={(e) => {
        // Close on backdrop click
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className="surface bg-white border border-[#e6e6e9] rounded-[18px] w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center mb-5">
          <h2
            id="modal-title"
            className="text-[17px] font-semibold tracking-[-0.02em] text-[#1d1d1f]"
          >
            {title}
          </h2>
          <button
            type="button"
            aria-label="Tutup formulir"
            onClick={onClose}
            className="secondary border border-[#d5d5da] bg-white text-[#0066cc] rounded-[10px] p-2 hover:bg-[#f4f8fd] transition-colors"
          >
            <LucideIcon name="x" className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div>{children}</div>

        {/* Footer (optional) */}
        {footer && <div className="mt-4">{footer}</div>}
      </div>
    </div>
  );
};

export default Modal;
