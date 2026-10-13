/**
 * SamplingCard Component
 * Displays time study with glassmorphism and Apple Design
 */

import React, { memo, useMemo } from 'react';
import { TimeStudy } from '@/types';
import Card from './Card';
import Button from './Button';

interface SamplingCardProps {
  study: TimeStudy;
  onStart?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onComplete?: () => void;
}

export const SamplingCard = memo<SamplingCardProps>(
  ({ study, onStart, onPause, onResume, onComplete }) => {
    const progressPercent = useMemo(
      () => (study.total_cycles / study.target_sample_size) * 100,
      [study.total_cycles, study.target_sample_size]
    );

    const statusColor = {
      draft: 'bg-gray-100 text-gray-800',
      in_progress: 'bg-blue-100 text-blue-800',
      paused: 'bg-orange-100 text-orange-800',
      completed: 'bg-green-100 text-green-800',
      archived: 'bg-gray-100 text-gray-800',
    };

    return (
      <Card variant="glass" className="p-6 mb-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {study.process_name}
            </h3>
            <p className="text-sm text-gray-600">{study.study_id}</p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              statusColor[study.status as keyof typeof statusColor]
            }`}
          >
            {study.status.replace('_', ' ')}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Samples Collected
            </span>
            <span className="text-sm text-purple-600 font-semibold">
              {study.total_cycles} / {study.target_sample_size}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-purple-500 to-purple-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${Math.min(progressPercent, 100)}%` }}
            />
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white/40 backdrop-blur-md rounded-lg p-3 border border-white/20">
            <p className="text-xs text-gray-600 mb-1">Mean Time</p>
            <p className="text-lg font-bold text-gray-900">
              {study.mean_cycle_time.toFixed(2)}ms
            </p>
          </div>
          <div className="bg-white/40 backdrop-blur-md rounded-lg p-3 border border-white/20">
            <p className="text-xs text-gray-600 mb-1">Std Dev</p>
            <p className="text-lg font-bold text-gray-900">
              {study.std_dev_cycle_time.toFixed(2)}ms
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          {study.status === 'draft' && (
            <Button
              variant="primary"
              size="md"
              onClick={onStart}
              className="flex-1"
            >
              Start Study
            </Button>
          )}
          {study.status === 'in_progress' && (
            <>
              <Button
                variant="secondary"
                size="md"
                onClick={onPause}
                className="flex-1"
              >
                Pause
              </Button>
              <Button
                variant="primary"
                size="md"
                onClick={onComplete}
                className="flex-1"
              >
                Complete
              </Button>
            </>
          )}
          {study.status === 'paused' && (
            <>
              <Button
                variant="primary"
                size="md"
                onClick={onResume}
                className="flex-1"
              >
                Resume
              </Button>
              <Button
                variant="secondary"
                size="md"
                onClick={onComplete}
                className="flex-1"
              >
                Complete
              </Button>
            </>
          )}
        </div>
      </Card>
    );
  }
);

SamplingCard.displayName = 'SamplingCard';

export default SamplingCard;
