"use client";

import React, { useEffect, useState } from "react";
import { Plus, History, AlertCircle } from "lucide-react";
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
    <header className="sticky top-0 z-40 bg-white border-b-[3px] border-black shadow-[0_3px_0px_#000000]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-15 flex items-center justify-between">
        {/* Brand / Logo */}
        <div
          className="flex items-center gap-3 cursor-pointer select-none group"
          onClick={onNewResearch}
        >
          <div className="w-8 h-8 rounded-lg bg-[#FFE600] border-2 border-black shadow-[2px_2px_0px_#000000] flex items-center justify-center text-black font-mono font-black text-sm tracking-tighter group-hover:bg-[#FFD700] transition">
            RO
          </div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-base text-black tracking-tight uppercase">
              ResearchOps
            </span>
            <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded bg-black text-white hidden sm:inline">
              AGENT v1.0
            </span>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2.5">
          {/* Status Indicator */}
          <div className="hidden sm:flex items-center">
            {health ? (
              health.configuration?.is_research_ready ? (
                <span className="neo-stamp neo-stamp-green">
                  <span className="w-2 h-2 rounded-full bg-black inline-block animate-pulse" />
                  Live Web Grounding
                </span>
              ) : (
                <span className="neo-stamp neo-stamp-yellow">
                  <span className="w-2 h-2 rounded-full bg-black inline-block" />
                  Deterministic Mock
                </span>
              )
            ) : isChecking ? (
              <span className="neo-stamp neo-stamp-white">
                <span className="w-2 h-2 rounded-full bg-slate-400 inline-block animate-ping" />
                Checking API
              </span>
            ) : (
              <span className="neo-stamp neo-stamp-red">
                <AlertCircle className="w-3 h-3 text-black inline-block mr-0.5" />
                Offline
              </span>
            )}
          </div>

          {/* History Drawer Trigger */}
          <button
            onClick={onToggleHistory}
            className={`neo-btn-secondary text-xs sm:text-xs py-1.5 px-3 ${
              isHistoryOpen ? "bg-[#FEF9C3]" : ""
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>History</span>
          </button>

          {/* New Research Button */}
          <button
            onClick={onNewResearch}
            className="neo-btn-primary text-xs sm:text-xs py-1.5 px-3.5"
          >
            <Plus className="w-4 h-4 stroke-[3]" />
            <span>New run</span>
          </button>
        </div>
      </div>
    </header>
  );
};
