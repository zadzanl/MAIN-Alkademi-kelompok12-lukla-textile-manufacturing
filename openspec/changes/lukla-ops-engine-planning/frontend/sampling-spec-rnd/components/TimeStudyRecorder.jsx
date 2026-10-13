/**
 * @name: TimeStudyRecorder
 * @description: Component untuk merekam Time Study dengan stopwatch digital
 * @params: {string} specId - ID spesifikasi produk
 * @params: {function} onTimeRecorded - callback saat time study tersimpan
 * @returns: JSX component
 * @example:
 *   <TimeStudyRecorder specId="spec-123" onTimeRecorded={handleSave} />
 */

import React, { useState, useEffect } from 'react';

const TimeStudyRecorder = ({ specId, onTimeRecorded }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [recordings, setRecordings] = useState([]);
  const [currentPhase, setCurrentPhase] = useState('');

  // Stopwatch logic
  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        setSeconds(s => s + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  // Format seconds to MM:SS
  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  // Start/pause stopwatch
  const handleToggleTimer = () => {
    setIsRunning(!isRunning);
  };

  // Record current phase time
  const handleRecordPhase = () => {
    if (!currentPhase.trim()) {
      alert('Masukkan nama fase terlebih dahulu');
      return;
    }

    const newRecording = {
      id: Date.now(),
      phase: currentPhase,
      duration: seconds,
      timestamp: new Date().toISOString(),
    };

    setRecordings([...recordings, newRecording]);
    setSeconds(0);
    setCurrentPhase('');
  };

  // Save all recordings
  const handleSaveRecordings = async () => {
    if (recordings.length === 0) {
      alert('Tidak ada time study yang direkam');
      return;
    }

    try {
      const timeStudyData = {
        specId,
        totalTime: recordings.reduce((sum, r) => sum + r.duration, 0),
        phases: recordings,
        createdAt: new Date().toISOString(),
      };

      // Call parent callback
      onTimeRecorded?.(timeStudyData);

      // Reset
      setRecordings([]);
      alert('Time Study berhasil tersimpan!');
    } catch (error) {
      console.error('Error saving time study:', error);
      alert('Gagal menyimpan time study');
    }
  };

  // Delete recording
  const handleDeleteRecording = (id) => {
    setRecordings(recordings.filter(r => r.id !== id));
  };

  return (
    <div className="time-study-recorder">
      <div className="recorder-header">
        <h2>Time Study Recorder</h2>
        <p className="spec-id">Spec ID: {specId}</p>
      </div>

      {/* Stopwatch Display */}
      <div className="stopwatch-display">
        <div className="time-display">{formatTime(seconds)}</div>
        <button 
          className="btn-primary" 
          onClick={handleToggleTimer}
        >
          {isRunning ? 'Pause' : 'Start'}
        </button>
      </div>

      {/* Phase Input */}
      <div className="phase-input">
        <input
          type="text"
          placeholder="Nama fase kerja (e.g., Potong, Jahit, QC)"
          value={currentPhase}
          onChange={(e) => setCurrentPhase(e.target.value)}
          className="input-field"
        />
        <button 
          className="btn-secondary" 
          onClick={handleRecordPhase}
          disabled={isRunning}
        >
          Record Phase
        </button>
      </div>

      {/* Recording List */}
      <div className="recordings-list">
        <h3>Recorded Phases</h3>
        {recordings.length === 0 ? (
          <p className="empty-state">Belum ada fase yang direkam</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Fase</th>
                <th>Durasi</th>
                <th>Waktu Rekam</th>
                <th>Aksi</th>
              </tr>
            </thead>
            <tbody>
              {recordings.map((recording) => (
                <tr key={recording.id}>
                  <td>{recording.phase}</td>
                  <td>{formatTime(recording.duration)}</td>
                  <td>{new Date(recording.timestamp).toLocaleTimeString('id-ID')}</td>
                  <td>
                    <button 
                      className="btn-delete"
                      onClick={() => handleDeleteRecording(recording.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Total Time */}
      {recordings.length > 0 && (
        <div className="total-time">
          <strong>Total Time: {formatTime(recordings.reduce((sum, r) => sum + r.duration, 0))}</strong>
        </div>
      )}

      {/* Save Button */}
      {recordings.length > 0 && (
        <button 
          className="btn-save" 
          onClick={handleSaveRecordings}
        >
          Save Time Study
        </button>
      )}
    </div>
  );
};

export default TimeStudyRecorder;
