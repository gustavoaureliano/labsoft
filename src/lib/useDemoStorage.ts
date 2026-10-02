"use client";

import { startTransition, useCallback, useEffect, useRef, useState } from "react";

export function readDemoStorage<T>(key: string, fallback: T): T {
  try {
    const stored = window.localStorage.getItem(key);
    return stored ? JSON.parse(stored) as T : fallback;
  } catch {
    return fallback;
  }
}

export function writeDemoStorage<T>(key: string, value: T) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function useDemoStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState(initialValue);
  const [ready, setReady] = useState(false);
  const initialValueRef = useRef(initialValue);

  useEffect(() => {
    startTransition(() => {
      setValue(readDemoStorage(key, initialValueRef.current));
      setReady(true);
    });
  }, [key]);

  const save = useCallback((nextValue: T) => {
    setValue(nextValue);
    return writeDemoStorage(key, nextValue);
  }, [key]);

  return [value, save, ready] as const;
}
