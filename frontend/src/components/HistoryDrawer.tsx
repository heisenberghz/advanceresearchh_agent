"use client";

import React from "react";
import { X, History } from "lucide-react";
import { ResearchRunSummary } from "@/lib/api";

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  runs: ResearchRunSummary[];
  onSelectRun: (id: string) => void;
  currentRunId?: string;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  runs,
  onSelectRun,
  currentRunId,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-md bg-[#FAF9F5] h-full border-l-[3px] border-black shadow-[-6px_0px_0px_#000000] p-5 sm:p-6 flex flex-col z-10 animate-in slide-in-from-right duration-150">
        <div className="flex items-center justify-between pb-4 border-b-2 border-black mb-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-[#FFE600] border-2 border-black flex items-center justify-center shadow-[1.5px_1.5px_0px_#000000]">
              <History className="w-4 h-4 stroke-[2.5]" />
            </div>
            <h2 className="font-mono font-black text-sm uppercase text-black tracking-tight">
              Previous Research ({runs.length})
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded border-2 border-black bg-white hover:bg-slate-100 flex items-center justify-center transition shadow-[2px_2px_0px_#000000]"
          >
            <X className="w-4 h-4 stroke-[3]" />
          </button>
        </div>

        {/* Runs List */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {runs && runs.length > 0 ? (
            runs.map((r) => {
              const isSelected = r.id === currentRunId;
              return (
                <div
                  key={r.id}
                  onClick={() => {
                    onSelectRun(r.id);
                    onClose();
                  }}
                  className={`p-3.5 rounded-lg border-2 border-black cursor-pointer transition-all flex flex-col justify-between ${
                    isSelected
                      ? "bg-[#FEF9C3] shadow-[4px_4px_0px_#000000] translate-x-[-1px] translate-y-[-1px]"
                      : "bg-white hover:bg-[#FEF9C3] shadow-[3px_3px_0px_#000000] hover:shadow-[5px_5px_0px_#000000] hover:translate-x-[-1px] hover:translate-y-[-1px]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-[11px] font-bold text-slate-700">
                      {r.created_at ? new Date(r.created_at).toLocaleDateString() : "Recent"}
                    </span>
                    <span
                      className={`neo-stamp ${
                        r.status === "completed"
                          ? "neo-stamp-green"
                          : r.status === "failed"
                          ? "neo-stamp-red"
                          : "neo-stamp-yellow"
                      }`}
                    >
                      {r.status}
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm font-bold text-black line-clamp-2 mb-2.5">
                    {r.question}
                  </p>

                  <div className="flex items-center justify-between font-mono text-xs font-bold text-slate-600 pt-1 border-t border-slate-200">
                    <span className="text-[11px]">RUN: {r.id.slice(0, 10)}</span>
                    <span className="text-black font-black underline">
                      Open Dossier
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-16 font-mono text-xs font-bold text-slate-500 border-2 border-dashed border-black rounded-lg p-6 bg-white">
              No previous research runs recorded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
