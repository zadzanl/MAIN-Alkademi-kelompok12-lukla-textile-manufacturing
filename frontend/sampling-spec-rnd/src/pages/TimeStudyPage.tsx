/**
 * Time Study Page
 * Main interface for recording time studies
 * Integrated with Backend API
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { usePerformance } from '@/hooks/usePerformance';
import { Card, Button, Input, SamplingCard } from '@/components';
import { TimeStudy } from '@/types';
import { api } from '@/services/api';

const TimeStudyPage: React.FC = () => {
  const [studies, setStudies] = useState<TimeStudy[]>([]);
  const [selectedStudy, setSelectedStudy] = useState<TimeStudy | null>(null);
  const [cycleTime, setCycleTime] = useState('');
  const [elementName, setElementName] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [backendError, setBackendError] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);

  const { throttle, debounce } = usePerformance();

  // Check backend connection on mount
  useEffect(() => {
    const checkConnection = async () => {
      const health = await api.checkHealth();
      setIsConnected(health.success);
      if (!health.success) {
        console.warn('Backend not available, using local storage only');
      }
    };
    checkConnection();
  }, []);

  // Create new study
  const handleCreateStudy = useCallback(
    throttle(async () => {
      if (!elementName.trim()) return;

      setIsProcessing(true);
      setBackendError('');
      try {
        if (isConnected) {
          // Call backend API
          const response = await api.createStudy({
            tenant_id: 'default',
            process_id: 'proc_001',
            process_name: elementName,
            operator_id: 'op_001',
            target_sample_size: 30,
          });

          if (!response.success) {
            throw new Error(response.error || 'Failed to create study');
          }

          // Fetch full study data from backend
          const studyData = await api.getStudyData(response.data?.study_id || '');
          if (studyData.success && studyData.data) {
            const newStudy = studyData.data as TimeStudy;
            setStudies((prev) => [newStudy, ...prev]);
            setSelectedStudy(newStudy);
          }
        } else {
          // Fallback: local storage only
          const newStudy: TimeStudy = {
            study_id: `study_${Date.now()}`,
            tenant_id: 'default',
            process_id: 'proc_001',
            process_name: elementName,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            started_at: null,
            completed_at: null,
            status: 'draft',
            target_sample_size: 30,
            samples: [],
            confidence_level: 0.95,
            allowance_percent: 15,
            operator_id: 'op_001',
            department_id: 'dept_001',
            shift: 'A',
            product_id: 'prod_001',
            notes: '',
            total_cycles: 0,
            mean_cycle_time: 0,
            std_dev_cycle_time: 0,
            min_cycle_time: 0,
            max_cycle_time: 0,
          };

          setStudies((prev) => [newStudy, ...prev]);
          setSelectedStudy(newStudy);
        }
        setElementName('');
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        setBackendError(message);
        console.error('Failed to create study:', error);
      } finally {
        setIsProcessing(false);
      }
    }, 300),
    [isConnected]
  );

  // Add sample to study
  const handleAddSample = useCallback(
    debounce(async () => {
      if (!selectedStudy || !cycleTime.trim()) return;
      if (selectedStudy.status !== 'in_progress') return;

      try {
        if (isConnected) {
          // Call backend API
          const response = await api.addSample({
            study_id: selectedStudy.study_id,
            cycle_time_ms: parseFloat(cycleTime),
            element_name: 'manual_entry',
          });

          if (!response.success) {
            throw new Error(response.error || 'Failed to add sample');
          }

          // Fetch updated study data
          const updatedData = await api.getStudyData(selectedStudy.study_id);
          if (updatedData.success && updatedData.data) {
            setSelectedStudy(updatedData.data as TimeStudy);
            setStudies((prev) =>
              prev.map((s) =>
                s.study_id === selectedStudy.study_id ? (updatedData.data as TimeStudy) : s
              )
            );
          }
        } else {
          // Fallback: local calculation
          const updatedStudy = {
            ...selectedStudy,
            total_cycles: selectedStudy.total_cycles + 1,
            mean_cycle_time: parseFloat(
              (
                (selectedStudy.mean_cycle_time * selectedStudy.total_cycles +
                  parseFloat(cycleTime)) /
                (selectedStudy.total_cycles + 1)
              ).toFixed(2)
            ),
          };

          setSelectedStudy(updatedStudy);
          setStudies((prev) =>
            prev.map((s) => (s.study_id === updatedStudy.study_id ? updatedStudy : s))
          );
        }
        setCycleTime('');
      } catch (error) {
        console.error('Failed to add sample:', error);
      }
    }, 100),
    [selectedStudy, isConnected]
  );

  const activeStudies = useMemo(
    () => studies.filter((s) => s.status === 'in_progress' || s.status === 'paused'),
    [studies]
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header with Connection Status */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Time Study Recording
              </h1>
              <p className="text-gray-600">
                Record manufacturing process cycles with precision
              </p>
            </div>
            <div className="text-right">
              <div
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  isConnected
                    ? 'bg-green-100 text-green-800'
                    : 'bg-orange-100 text-orange-800'
                }`}
              >
                {isConnected ? '🟢 Backend Connected' : '🟡 Local Storage Mode'}
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {backendError && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 rounded-lg text-red-800">
            ⚠️ {backendError}
          </div>
        )}

        {/* Create New Study */}
        <Card variant="glass" className="p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Create New Study
          </h2>
          <div className="flex gap-4">
            <Input
              placeholder="Process Name (e.g., Assembly Line A)"
              value={elementName}
              onChange={(e) => setElementName(e.target.value)}
              className="flex-1"
            />
            <Button
              variant="primary"
              onClick={handleCreateStudy}
              isLoading={isProcessing}
            >
              Create Study
            </Button>
          </div>
        </Card>

        {/* Active Studies */}
        {activeStudies.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Active Studies ({activeStudies.length})
            </h2>
            <div className="space-y-4">
              {activeStudies.map((study) => (
                <SamplingCard
                  key={study.study_id}
                  study={study}
                  onStart={() => {
                    const updated = { ...study, status: 'in_progress' as const };
                    setSelectedStudy(updated);
                    setStudies((prev) =>
                      prev.map((s) => (s.study_id === study.study_id ? updated : s))
                    );
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Sample Input */}
        {selectedStudy && selectedStudy.status === 'in_progress' && (
          <Card variant="glass" className="p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Add Sample
            </h2>
            <div className="flex gap-4">
              <Input
                type="number"
                placeholder="Cycle Time (ms)"
                value={cycleTime}
                onChange={(e) => setCycleTime(e.target.value)}
                className="flex-1"
              />
              <Button
                variant="primary"
                onClick={handleAddSample}
                isLoading={isProcessing}
              >
                Add Sample
              </Button>
            </div>
          </Card>
        )}

        {/* All Studies List */}
        {studies.length > 0 && (
          <Card variant="default" className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              All Studies ({studies.length})
            </h2>
            <div className="space-y-3">
              {studies.map((study) => (
                <div
                  key={study.study_id}
                  className="flex items-center justify-between p-4 bg-white/50 rounded-lg cursor-pointer hover:bg-white/80 transition-all"
                  onClick={() => setSelectedStudy(study)}
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {study.process_name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {study.total_cycles} / {study.target_sample_size} samples
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      {
                        draft: 'bg-gray-100 text-gray-800',
                        in_progress: 'bg-blue-100 text-blue-800',
                        paused: 'bg-orange-100 text-orange-800',
                        completed: 'bg-green-100 text-green-800',
                        archived: 'bg-gray-100 text-gray-800',
                      }[study.status]
                    }`}
                  >
                    {study.status.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default TimeStudyPage;
