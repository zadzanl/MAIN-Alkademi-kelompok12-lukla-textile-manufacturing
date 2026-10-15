/**
 * Modal — slide-up dialog with backdrop blur
 * Animated entry, high-contrast title, close button with hover ring
 */
import React, { useEffect, useRef } from 'react';
import { LucideIcon } from './Sidebar';

interface ModalProps {
  isOpen: boolean;
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  footer?: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, title, children, onClose, footer }) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && isOpen) onClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  // Move focus into the dialog on open and restore it to the trigger on close,
  // so keyboard/screen-reader users are not left behind the backdrop.
  useEffect(() => {
    if (!isOpen) return;
    previouslyFocused.current = document.activeElement as HTMLElement | null;
    const node = dialogRef.current;
    const focusable = node?.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    (focusable ?? node)?.focus();
    return () => previouslyFocused.current?.focus?.();
  }, [isOpen]);

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
        ref={dialogRef} tabIndex={-1}
        role="dialog" aria-modal="true" aria-labelledby="modal-title"
        className="bg-white border border-hair rounded-[20px] w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto shadow-2xl outline-none"
        onClick={e => e.stopPropagation()}
      >
        {/* Title row */}
        <div className="flex justify-between items-center mb-5">
          <h2 id="modal-title" className="text-[17px] font-bold text-ink tracking-tight">
            {title}
          </h2>
          <button
            type="button" aria-label="Tutup"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-panel-2 text-ink-muted flex items-center justify-center
                       hover:bg-bad-bg hover:text-bad-4 transition-all duration-150 active:scale-90"
          >
            <LucideIcon name="x" className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div>{children}</div>

        {/* Footer */}
        {footer && <div className="mt-5 pt-4 border-t border-panel-2">{footer}</div>}
      </div>
    </div>
  );
};

export default Modal;
