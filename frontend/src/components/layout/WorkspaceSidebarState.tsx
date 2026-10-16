"use client";

import { createContext, startTransition, useContext, useEffect, useState, type ReactNode } from "react";

const storageKey = "aprovaai_sidebar_collapsed";

type SidebarState = {
  collapsed: boolean;
  animate: boolean;
  toggle: () => void;
};

const SidebarContext = createContext<SidebarState | null>(null);

export function WorkspaceSidebarProvider({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    let saved = false;
    try { saved = window.localStorage.getItem(storageKey) === "true"; } catch { /* Storage may be unavailable. */ }
    startTransition(() => setCollapsed(saved));
  }, []);

  function toggle() {
    const next = !collapsed;
    setAnimate(true);
    setCollapsed(next);
    try { window.localStorage.setItem(storageKey, String(next)); } catch { /* Keep the current page usable. */ }
  }

  return <SidebarContext.Provider value={{ collapsed, animate, toggle }}>{children}</SidebarContext.Provider>;
}

export function useWorkspaceSidebar() {
  const state = useContext(SidebarContext);
  if (!state) throw new Error("WorkspaceSidebarProvider is missing");
  return state;
}
