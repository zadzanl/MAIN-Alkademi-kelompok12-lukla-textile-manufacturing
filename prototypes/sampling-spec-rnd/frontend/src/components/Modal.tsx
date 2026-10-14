/**
 * Modal — slide-up dialog with backdrop blur
 * Animated entry, high-contrast title, close button with hover ring
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
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && isOpen) onClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop fixed inset-0 flex items-center justify-center p-4 z-50"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        role="dialog" aria-modal="true" aria-labelledby="modal-title"
        className="bg-white border border-[#e2e8f0] rounded-[20px] w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Title row */}
        <div className="flex justify-between items-center mb-5">
          <h2 id="modal-title" className="text-[17px] font-bold text-[#0f172a] tracking-tight">
            {title}
          </h2>
          <button
            type="button" aria-label="Tutup"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-[#f1f5f9] text-[#64748b] flex items-center justify-center
                       hover:bg-[#fee2e2] hover:text-[#dc2626] transition-all duration-150 active:scale-90"
          >
            <LucideIcon name="x" className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div>{children}</div>

        {/* Footer */}
        {footer && <div className="mt-5 pt-4 border-t border-[#f1f5f9]">{footer}</div>}
      </div>
    </div>
  );
};

export default Modal;
