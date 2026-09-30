"use client";

import React, { useEffect, useState } from "react";
import { Sparkles, Plus, Clock, Server, CheckCircle2, AlertCircle } from "lucide-react";
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
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={onNewResearch}>
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/30">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-slate-900 tracking-tight">ResearchOps</span>
              <span className="px-2 py-0.5 text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
                GATEWAYS 2026
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Autonomous Intelligence & Deterministic Verification
            </p>
          </div>
        </div>

        {/* Right Actions & Health Status */}
        <div className="flex items-center gap-3">
          {/* Backend Status Pill */}
          <div
            className={`hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
              health
                ? health.configuration?.is_research_ready
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-amber-50 text-amber-700 border-amber-200"
                : isChecking
                ? "bg-slate-50 text-slate-600 border-slate-200"
                : "bg-rose-50 text-rose-700 border-rose-200"
            }`}
            title={
              health
                ? health.configuration?.is_research_ready
                  ? "All external integrations active (Tavily, OpenRouter, Supabase)"
                  : "Running in deterministic offline mock mode"
                : "Cannot connect to backend server at http://localhost:8000"
            }
          >
            {health ? (
              health.configuration?.is_research_ready ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Live Web Mode</span>
                </>
              ) : (
                <>
                  <Server className="w-3.5 h-3.5 text-amber-600" />
                  <span>Deterministic Offline Mode</span>
                </>
              )
            ) : isChecking ? (
              <>
                <span className="w-2 h-2 rounded-full bg-slate-400 animate-pulse" />
                <span>Checking Backend...</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>Backend Offline</span>
              </>
            )}
          </div>

          {/* History Button */}
          <button
            onClick={onToggleHistory}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              isHistoryOpen
                ? "bg-slate-100 text-slate-900 border-slate-300"
                : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
            }`}
          >
            <Clock className="w-4 h-4 text-slate-500" />
            <span>History</span>
          </button>

          {/* New Research Button */}
          <button
            onClick={onNewResearch}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 active:scale-[0.98] transition shadow-sm shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>New Research</span>
          </button>
        </div>
      </div>
    </header>
  );
};
