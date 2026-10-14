/**
 * usePerformance Hook
 * Monitors render performance and provides batch update utilities
 * Optimized for tablet performance (no lag)
 */

import { useEffect, useRef, useCallback } from 'react';

interface PerformanceMetrics {
  renderTime: number;
  fps: number;
  isLagging: boolean;
}

export const usePerformance = () => {
  const renderStartRef = useRef<number>(Date.now());
  const frameCountRef = useRef<number>(0);
  const lastFpsCheckRef = useRef<number>(Date.now());
  const metricsRef = useRef<PerformanceMetrics>({
    renderTime: 0,
    fps: 60,
    isLagging: false,
  });

  // Track render time
  useEffect(() => {
    const renderTime = Date.now() - renderStartRef.current;
    metricsRef.current.renderTime = renderTime;
    
    // Flag as lagging if render takes > 16ms (60fps threshold)
    if (renderTime > 16) {
      metricsRef.current.isLagging = true;
    } else {
      metricsRef.current.isLagging = false;
    }
  });

  // Track FPS
  useEffect(() => {
    let animationFrameId: number;
    
    const countFrame = () => {
      frameCountRef.current++;
      
      const now = Date.now();
      const elapsed = now - lastFpsCheckRef.current;
      
      if (elapsed >= 1000) {
        metricsRef.current.fps = frameCountRef.current;
        frameCountRef.current = 0;
        lastFpsCheckRef.current = now;
      }
      
      animationFrameId = requestAnimationFrame(countFrame);
    };
    
    animationFrameId = requestAnimationFrame(countFrame);
    
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  // Batch updates to reduce re-renders
  const batchUpdate = useCallback((updates: Array<() => void>) => {
    // Use microtask queue for batching
    queueMicrotask(() => {
      updates.forEach((update) => update());
    });
  }, []);

  // Throttle function calls (useful for event handlers)
  const throttle = useCallback(
    <A extends unknown[]>(callback: (...args: A) => void, delay: number = 16) => {
      let lastCall = 0;
      let timeoutId: NodeJS.Timeout | null = null;

      return (...args: A) => {
        const now = Date.now();
        const timeSinceLastCall = now - lastCall;

        if (timeSinceLastCall >= delay) {
          lastCall = now;
          callback(...args);
        } else if (!timeoutId) {
          timeoutId = setTimeout(() => {
            lastCall = Date.now();
            callback(...args);
            timeoutId = null;
          }, delay - timeSinceLastCall);
        }
      };
    },
    []
  );

  // Debounce function calls
  const debounce = useCallback(
    <A extends unknown[]>(callback: (...args: A) => void, delay: number = 300) => {
      let timeoutId: NodeJS.Timeout | null = null;

      return (...args: A) => {
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        timeoutId = setTimeout(() => {
          callback(...args);
          timeoutId = null;
        }, delay);
      };
    },
    []
  );

  // Debounce touch events (16ms for 60fps)
  const debounceTouchEvent = useCallback(
    (callback: (e: TouchEvent) => void) => {
      return debounce(callback, 16);
    },
    [debounce]
  );

  // Request idle callback (low priority work)
  const scheduleIdleTask = useCallback(
    (callback: () => void, timeout: number = 1000) => {
      const w = window as Window & {
        requestIdleCallback?: (cb: () => void, opts?: { timeout: number }) => number;
      };
      if (typeof w.requestIdleCallback === 'function') {
        w.requestIdleCallback(callback, { timeout });
      } else {
        setTimeout(callback, timeout);
      }
    },
    []
  );

  return {
    metrics: metricsRef.current,
    batchUpdate,
    throttle,
    debounce,
    debounceTouchEvent,
    scheduleIdleTask,
  };
};

export default usePerformance;
