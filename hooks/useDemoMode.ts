"use client";

import { useCallback, useState } from "react";

// Small helper so pages can track "is this screen currently showing
// synthetic demo data" without repeating the same two lines of state.
export function useDemoMode() {
  const [demoMode, setDemoMode] = useState(false);
  const markDemo = useCallback((value: boolean) => setDemoMode(value), []);
  return { demoMode, markDemo };
}
