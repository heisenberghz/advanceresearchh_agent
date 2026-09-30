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
        className="fixed inset-0 bg-black/30 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-md bg-white h-full shadow-xl border-l border-gray-200 p-5 flex flex-col z-10 animate-in slide-in-from-right duration-150">
        <div className="flex items-center justify-between pb-3.5 border-b border-gray-100 mb-3.5">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-gray-500" />
            <h2 className="text-sm font-semibold text-gray-900">
              Previous research
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 flex items-center justify-center transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Runs List */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
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
                  className={`p-3 rounded-lg border cursor-pointer transition flex flex-col justify-between ${
                    isSelected
                      ? "bg-blue-50/60 border-blue-300 ring-1 ring-blue-300"
                      : "bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50/60"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs text-gray-400">
                      {r.created_at ? new Date(r.created_at).toLocaleDateString() : "Recent"}
                    </span>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded-full border ${
                        r.status === "completed"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : r.status === "failed"
                          ? "bg-red-50 text-red-700 border-red-200"
                          : "bg-gray-100 text-gray-700 border-gray-200"
                      }`}
                    >
                      {r.status}
                    </span>
                  </div>

                  <p className="text-xs font-medium text-gray-900 line-clamp-2 mb-2">
                    {r.question}
                  </p>

                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span className="text-[11px] text-gray-400">ID: {r.id.slice(0, 8)}...</span>
                    <span className="text-gray-900 font-medium">
                      Open
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-12 text-gray-400 text-xs">
              No previous research runs recorded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};


