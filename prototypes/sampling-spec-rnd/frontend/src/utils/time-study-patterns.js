/**
 * @name: Time Study Patterns
 * @description: Common patterns untuk Time Study recording dan calculation
 */

// ============================================
// PATTERN 1: Time Study Data Model
// ============================================
/**
 * Standard structure untuk time study record
 */
const timeStudyModel = {
  id: 'ts-20261013-001',
  specId: 'spec-001',
  productId: 'prod-001',
  operator: 'operator-id-123',
  date: '2026-10-13',
  phases: [
    {
      id: 'phase-1',
      name: 'Potong Kain',
      duration: 120, // seconds
      startTime: '10:00:00',
      endTime: '10:02:00',
      notes: 'Sempurna, tidak ada reject',
    },
    {
      id: 'phase-2',
      name: 'Jahit',
      duration: 180,
      startTime: '10:02:00',
      endTime: '10:05:00',
      notes: 'Jahitan rapi, sesuai standar',
    },
  ],
  totalTime: 300, // seconds
  qualityScore: 95, // QC rating
  status: 'completed',
  createdAt: '2026-10-13T10:05:00Z',
  updatedAt: '2026-10-13T10:05:00Z',
};

// ============================================
// PATTERN 2: Calculate Average Time Per Phase
// ============================================
/**
 * Hitung rata-rata waktu per fase dari multiple time studies
 * @param {array} timeStudies - Array of time study records
 * @param {string} phaseName - Nama fase yang dicari
 * @returns {object} Average time dan statistics
 */
function calculateAveragePhaseTime(timeStudies, phaseName) {
  const phaseRecords = timeStudies
    .flatMap(ts => ts.phases)
    .filter(phase => phase.name === phaseName);

  if (phaseRecords.length === 0) {
    return { average: 0, count: 0, min: 0, max: 0 };
  }

  const durations = phaseRecords.map(p => p.duration);
  const total = durations.reduce((sum, d) => sum + d, 0);
  const average = total / durations.length;
  const min = Math.min(...durations);
  const max = Math.max(...durations);

  return {
    average: Math.round(average),
    count: phaseRecords.length,
    min,
    max,
    standardDeviation: calculateStdDev(durations, average),
  };
}

// ============================================
// PATTERN 3: Standard Deviation Calculation
// ============================================
function calculateStdDev(values, average) {
  const squareDiffs = values.map(value => Math.pow(value - average, 2));
  const avgSquareDiff = squareDiffs.reduce((sum, d) => sum + d, 0) / values.length;
  return Math.sqrt(avgSquareDiff);
}

// ============================================
// PATTERN 4: Quality Score Based on Time Variance
// ============================================
/**
 * Hitung quality score berdasarkan variance dari expected time
 * @param {number} actualTime - Waktu aktual (seconds)
 * @param {number} expectedTime - Expected time (seconds)
 * @param {number} tolerance - Tolerance percentage (default 10%)
 * @returns {number} Quality score 0-100
 */
function calculateQualityScore(actualTime, expectedTime, tolerance = 10) {
  const deviation = Math.abs(actualTime - expectedTime) / expectedTime;
  const toleranceDecimal = tolerance / 100;

  if (deviation <= toleranceDecimal) {
    return 100;
  }

  if (deviation > toleranceDecimal * 2) {
    return 50;
  }

  return 100 - (deviation / (toleranceDecimal * 2)) * 50;
}

// ============================================
// PATTERN 5: Version Comparison
// ============================================
/**
 * Compare time study results antar versi spesifikasi
 */
function compareSpecVersions(version1TimeStudies, version2TimeStudies) {
  const avg1 = calculateAveragePhaseTime(version1TimeStudies, 'Jahit').average;
  const avg2 = calculateAveragePhaseTime(version2TimeStudies, 'Jahit').average;

  const improvement = ((avg1 - avg2) / avg1) * 100;

  return {
    version1AvgTime: avg1,
    version2AvgTime: avg2,
    improvementPercentage: improvement,
    isFaster: improvement > 0,
  };
}

// ============================================
// PATTERN 6: Detect R&D Drift
// ============================================
/**
 * Deteksi jika ada perubahan signifikan dalam time study dari versi sebelumnya
 * @param {array} historicalTimeStudies - Historical time studies
 * @param {array} currentTimeStudies - Current time studies
 * @param {number} threshold - Threshold percentage untuk flag (default 15%)
 * @returns {object} Drift analysis
 */
function detectRnDDrift(historicalTimeStudies, currentTimeStudies, threshold = 15) {
  const driftAnalysis = {};

  // Cek semua phases
  const allPhases = new Set(
    historicalTimeStudies
      .concat(currentTimeStudies)
      .flatMap(ts => ts.phases.map(p => p.name))
  );

  allPhases.forEach(phaseName => {
    const histAvg = calculateAveragePhaseTime(historicalTimeStudies, phaseName).average;
    const currAvg = calculateAveragePhaseTime(currentTimeStudies, phaseName).average;

    if (histAvg > 0) {
      const driftPercent = Math.abs(histAvg - currAvg) / histAvg * 100;
      driftAnalysis[phaseName] = {
        historicalAverage: histAvg,
        currentAverage: currAvg,
        driftPercent: driftPercent.toFixed(2),
        hasDrift: driftPercent > threshold,
        direction: currAvg > histAvg ? 'slower' : 'faster',
      };
    }
  });

  return {
    driftDetected: Object.values(driftAnalysis).some(d => d.hasDrift),
    analysis: driftAnalysis,
    threshold,
  };
}

// ============================================
// PATTERN 7: Time Study Validation
// ============================================
/**
 * Validate time study data sebelum save
 */
function validateTimeStudy(timeStudy) {
  const errors = [];

  if (!timeStudy.specId) errors.push('specId is required');
  if (!timeStudy.phases || timeStudy.phases.length === 0) {
    errors.push('At least one phase is required');
  }

  // Check phase validity
  timeStudy.phases?.forEach((phase, idx) => {
    if (!phase.name) errors.push(`Phase ${idx}: name is required`);
    if (phase.duration <= 0) errors.push(`Phase ${idx}: duration must be > 0`);
  });

  return {
    isValid: errors.length === 0,
    errors,
  };
}

// ============================================
// PATTERN 8: Export Time Study Report
// ============================================
/**
 * Generate time study report untuk export
 */
function generateTimeStudyReport(timeStudies, specVersion) {
  const totalRecordings = timeStudies.length;
  const totalPhases = timeStudies.reduce((sum, ts) => sum + ts.phases.length, 0);
  const averageTotalTime = 
    timeStudies.reduce((sum, ts) => sum + ts.totalTime, 0) / totalRecordings;

  return {
    reportDate: new Date().toISOString(),
    specVersion,
    summary: {
      totalRecordings,
      totalPhases,
      averageTotalTime: Math.round(averageTotalTime),
    },
    phaseAnalysis: Array.from(new Set(timeStudies.flatMap(ts => ts.phases.map(p => p.name)))).map(phaseName => ({
      phaseName,
      ...calculateAveragePhaseTime(timeStudies, phaseName),
    })),
    rawData: timeStudies,
  };
}

// ============================================
// EXPORT FUNCTIONS
// ============================================
module.exports = {
  calculateAveragePhaseTime,
  calculateStdDev,
  calculateQualityScore,
  compareSpecVersions,
  detectRnDDrift,
  validateTimeStudy,
  generateTimeStudyReport,
  timeStudyModel,
};
