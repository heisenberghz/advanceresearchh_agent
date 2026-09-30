"use client";

import React, { useEffect, useState } from "react";
import { Plus, History, Check, AlertCircle, Shield } from "lucide-react";
import { checkBackendHealth, SystemHealth } from "@/lib/api";

interface HeaderProps {
  onNewResearch: () => void;
  onToggleHistory: () => void;
  isHistoryOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onNewResearch,
  onToggleHistory,
  isHistoryOpen,
}) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchHealth = async () => {
      const data = await checkBackendHealth();
      if (mounted) {
        setHealth(data);
        setIsChecking(false);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Brand / Logo */}
        <div
          className="flex items-center gap-2.5 cursor-pointer select-none group"
          onClick={onNewResearch}
        >
          <div className="w-7 h-7 rounded-md bg-slate-900 flex items-center justify-center text-white font-mono font-bold text-xs tracking-tighter shadow-xs group-hover:bg-slate-800 transition">
            RO
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-slate-900 tracking-tight">
              ResearchOps
            </span>
            <span className="text-slate-300 hidden sm:inline">/</span>
            <span className="text-xs text-slate-500 hidden sm:inline font-mono">
              Primary Source Verification
            </span>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2">
          {/* Status Indicator */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono border border-slate-200/70 bg-slate-50/80 text-slate-600">
            {health ? (
              health.configuration?.is_research_ready ? (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Live Web Grounding</span>
                </>
              ) : (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  <span>Deterministic Mock Mode</span>
                </>
              )
            ) : isChecking ? (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse" />
                <span>Checking API</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3 h-3 text-rose-500" />
                <span className="text-rose-700">Offline</span>
              </>
            )}
          </div>

          {/* History Drawer Trigger */}
          <button
            onClick={onToggleHistory}
            className={`btn-command-secondary text-xs px-3 py-1.5 ${
              isHistoryOpen ? "bg-slate-100 border-slate-300 text-slate-900" : ""
            }`}
          >
            <History className="w-3.5 h-3.5 text-slate-500" />
            <span>History</span>
          </button>

          {/* New Research Button */}
          <button
            onClick={onNewResearch}
            className="btn-command-primary text-xs px-3 py-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New run</span>
          </button>
        </div>
      </div>
    </header>
  );
};
