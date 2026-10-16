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
        <div className="rounded-[18px] border border-bad-bg-2 bg-bad-bg px-6 py-8 text-center">
          <h2 className="text-[17px] font-semibold text-bad-4">Terjadi kesalahan saat menampilkan halaman</h2>
          <p className="mt-2 text-[15px] text-bad-4">
            Coba pindah ke menu lain, atau muat ulang aplikasi.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 rounded-[10px] bg-bad-4 px-4 py-2 text-[15px] font-semibold text-white"
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
