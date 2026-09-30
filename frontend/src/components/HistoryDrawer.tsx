"use client";

import React from "react";
import { X, Clock, ArrowRight } from "lucide-react";
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
        className="fixed inset-0 bg-slate-900/30 backdrop-blur-2xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-md bg-white h-full shadow-2xl border-l border-slate-200 p-6 flex flex-col z-10 animate-in slide-in-from-right duration-200">
        <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            <h2 className="text-base font-bold text-slate-900">Research History</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Runs List */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
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
                  className={`p-3.5 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                    isSelected
                      ? "bg-blue-50/60 border-blue-300 ring-1 ring-blue-500/20"
                      : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono text-slate-400">
                      ID: {r.id}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        r.status === "completed"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : r.status === "failed"
                          ? "bg-rose-50 text-rose-700 border-rose-200"
                          : "bg-blue-50 text-blue-700 border-blue-200"
                      }`}
                    >
                      {r.status}
                    </span>
                  </div>

                  <p className="text-xs font-semibold text-slate-900 line-clamp-2 mb-2">
                    {r.question}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>
                      {r.created_at
                        ? new Date(r.created_at).toLocaleDateString()
                        : "Just now"}
                    </span>
                    <span className="text-blue-600 font-semibold flex items-center gap-0.5">
                      Open <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-12 text-slate-400 text-xs">
              No previous research runs recorded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
