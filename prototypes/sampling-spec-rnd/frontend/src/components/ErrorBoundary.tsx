/**
 * ErrorBoundary — catches render errors in a view and shows a recoverable
 * fallback instead of a blank page. Placed inside the keyed page wrapper in
 * App, so navigating to another view resets it.
 */

import React from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error('Uncaught view error', error, info.componentStack);
  }

  render(): React.ReactNode {
    if (this.state.error) {
      return (
        <div className="rounded-[18px] border border-[#fecaca] bg-[#fee2e2] px-6 py-10 text-center">
          <h2 className="text-[16px] font-semibold text-[#dc2626]">Terjadi kesalahan saat menampilkan halaman</h2>
          <p className="mt-2 text-[13px] text-[#991b1b]">
            Coba pindah ke menu lain, atau muat ulang aplikasi.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 rounded-[10px] bg-[#dc2626] px-4 py-2 text-[13px] font-semibold text-white"
          >
            Muat Ulang
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
