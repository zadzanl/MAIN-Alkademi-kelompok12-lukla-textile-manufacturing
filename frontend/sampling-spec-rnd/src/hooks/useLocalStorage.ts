/**
 * useLocalStorage Hook
 * IndexedDB-based offline caching for time study and spec data
 * Fallback to localStorage for small data
 */

import { useState, useCallback, useEffect } from 'react';

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  useIndexedDB?: boolean; // Use IndexedDB for large datasets
}

let dbPromise: Promise<IDBDatabase> | null = null;

const getDB = async (): Promise<IDBDatabase> => {
  if (dbPromise) return dbPromise;

  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open('SamplingSpecRnD', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains('cache')) {
        db.createObjectStore('cache', { keyPath: 'key' });
      }
    };
  });

  return dbPromise;
};

export const useLocalStorage = <T>(
  key: string,
  initialValue: T,
  options: CacheOptions = {}
): [T, (value: T | ((val: T) => T)) => void, () => void] => {
  const { ttl = null, useIndexedDB = true } = options;
  const [storedValue, setStoredValue] = useState<T>(initialValue);
  const [isLoaded, setIsLoaded] = useState(false);

  // Initialize from storage on mount
  useEffect(() => {
    const loadValue = async () => {
      try {
        // Try IndexedDB first
        if (useIndexedDB) {
          const db = await getDB();
          const transaction = db.transaction('cache', 'readonly');
          const store = transaction.objectStore('cache');
          const request = store.get(key);

          request.onsuccess = () => {
            const result = request.result;
            if (result) {
              // Check TTL
              if (ttl && Date.now() - result.timestamp > ttl) {
                // TTL expired, use initial value
                setStoredValue(initialValue);
              } else {
                setStoredValue(result.value);
              }
            } else {
              setStoredValue(initialValue);
            }
            setIsLoaded(true);
          };

          request.onerror = () => {
            // Fallback to localStorage
            const item = localStorage.getItem(key);
            if (item) {
              try {
                const parsed = JSON.parse(item);
                if (ttl && Date.now() - parsed.timestamp > ttl) {
                  setStoredValue(initialValue);
                } else {
                  setStoredValue(parsed.value);
                }
              } catch {
                setStoredValue(initialValue);
              }
            }
            setIsLoaded(true);
          };
        } else {
          // Use localStorage only
          const item = localStorage.getItem(key);
          if (item) {
            try {
              const parsed = JSON.parse(item);
              if (ttl && Date.now() - parsed.timestamp > ttl) {
                setStoredValue(initialValue);
              } else {
                setStoredValue(parsed.value);
              }
            } catch {
              setStoredValue(initialValue);
            }
          }
          setIsLoaded(true);
        }
      } catch (error) {
        console.error('Failed to load from storage:', error);
        setStoredValue(initialValue);
        setIsLoaded(true);
      }
    };

    loadValue();
  }, [key, initialValue, ttl, useIndexedDB]);

  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);

        const dataToStore = {
          key,
          value: valueToStore,
          timestamp: Date.now(),
        };

        // Try to store in IndexedDB
        if (useIndexedDB) {
          getDB()
            .then((db) => {
              const transaction = db.transaction('cache', 'readwrite');
              const store = transaction.objectStore('cache');
              store.put(dataToStore);
            })
            .catch(() => {
              // Fallback to localStorage
              localStorage.setItem(key, JSON.stringify(dataToStore));
            });
        } else {
          localStorage.setItem(key, JSON.stringify(dataToStore));
        }
      } catch (error) {
        console.error('Failed to save to storage:', error);
      }
    },
    [key, storedValue, useIndexedDB]
  );

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);

      if (useIndexedDB) {
        getDB()
          .then((db) => {
            const transaction = db.transaction('cache', 'readwrite');
            const store = transaction.objectStore('cache');
            store.delete(key);
          })
          .catch(() => {
            localStorage.removeItem(key);
          });
      } else {
        localStorage.removeItem(key);
      }
    } catch (error) {
      console.error('Failed to remove from storage:', error);
    }
  }, [key, initialValue, useIndexedDB]);

  // Return loading state as well
  if (!isLoaded) {
    return [initialValue, setValue, removeValue];
  }

  return [storedValue, setValue, removeValue];
};

export default useLocalStorage;
