/**
 * Main App Component
 * Sampling & Spec R&D Module with Apple Design System
 */

import React, { Suspense } from 'react';
import TimeStudyPage from '@/pages/TimeStudyPage';
import '@/styles/globals.css';

const App: React.FC = () => {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      }
    >
      <TimeStudyPage />
    </Suspense>
  );
};

export default App;
