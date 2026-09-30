"use client";

import React, { useState } from "react";
import {
  Brain,
  Globe,
  CheckCircle,
  Repeat,
  TableProperties,
  PenTool,
  Loader2,
  AlertTriangle,
  Scale,
  FileQuestion,
  ChevronDown,
  ChevronUp,
  Terminal,
  ArrowRight,
} from "lucide-react";
import { ResearchStatusResponse } from "@/lib/api";

interface ProgressDashboardProps {
  statusData: ResearchStatusResponse;
  streamEvents: Array<{ timestamp: string; message: string; stage?: string }>;
  onViewReport: () => void;
  onViewFindings: () => void;
}

const PIPELINE_STAGES = [
  { key: "planned", label: "Query Planning", icon: Brain },
  { key: "researched", label: "Web Extraction", icon: Globe },
  { key: "checked", label: "Corroboration", icon: CheckCircle },
  { key: "retrying", label: "Gap Resolution", icon: Repeat },
  { key: "compared", label: "Matrix Synthesis", icon: TableProperties },
  { key: "completed", label: "Audit Report", icon: PenTool },
];

export const ProgressDashboard: React.FC<ProgressDashboardProps> = ({
  statusData,
  streamEvents,
  onViewReport,
  onViewFindings,
}) => {
  const [showLogTerminal, setShowLogTerminal] = useState(false);

  const currentStage = statusData.workflow_status || statusData.current_workflow_stage || "planned";
  const isFinished = statusData.status === "completed";
  const isFailed = statusData.status === "failed";

  const getStageState = (stageKey: string, index: number) => {
    const stageOrder = ["planned", "researched", "checked", "retrying", "compared", "completed"];
    const currentIndex = stageOrder.indexOf(currentStage);
    const thisIndex = stageOrder.indexOf(stageKey);

    if (isFinished) return "completed";
    if (isFailed && thisIndex === currentIndex) return "failed";
    if (thisIndex < currentIndex) return "completed";
    if (thisIndex === currentIndex) return "running";
    return "waiting";
  };

  const greenFacts = statusData.findings?.filter((f) => f.trust_tag === "GREEN").length || 0;
  const yellowFacts = statusData.findings?.filter((f) => f.trust_tag === "YELLOW").length || 0;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:py-10">
      {/* Run Header Banner */}
      <div className="precision-card p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2 font-mono">
              <span
                className={`text-[10px] px-2 py-0.5 rounded border uppercase tracking-wider font-semibold ${
                  isFinished
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : isFailed
                    ? "bg-rose-50 text-rose-700 border-rose-200"
                    : "bg-sky-50 text-sky-700 border-sky-200 animate-pulse"
                }`}
              >
                {statusData.status === "running" ? "Active Pipeline" : isFinished ? "Synthesized" : "Halted"}
              </span>
              <span className="text-xs text-slate-400">
                id: {statusData.research_id}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-semibold text-slate-900 tracking-tight leading-snug">
              {statusData.question}
            </h1>
          </div>

          {/* Action buttons when report is ready */}
          {statusData.has_report && (
            <div className="flex items-center gap-2.5 shrink-0 self-start md:self-auto">
              <button
                onClick={onViewFindings}
                className="btn-command-secondary text-xs px-3.5 py-2"
              >
                Inspect Findings
              </button>
              <button
                onClick={onViewReport}
                className="btn-command-primary text-xs px-4 py-2"
              >
                View Audit Report
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 6-Stage Pipeline Stepper */}
      <div className="precision-card p-5 mb-6">
        <div className="flex items-center justify-between mb-3.5">
          <span className="text-xs font-mono font-medium text-slate-600 uppercase tracking-wider">
            Verification Pipeline
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            {isFinished ? "100% verified" : `Current node: ${currentStage}`}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {PIPELINE_STAGES.map((s, idx) => {
            const state = getStageState(s.key, idx);
            const Icon = s.icon;
            return (
              <div
                key={s.key}
                className={`p-3 rounded-lg border flex flex-col justify-between transition min-h-[92px] ${
                  state === "running"
                    ? "bg-sky-50/50 border-sky-300 ring-1 ring-sky-300 shadow-xs"
                    : state === "completed"
                    ? "bg-white border-slate-200"
                    : state === "failed"
                    ? "bg-rose-50/50 border-rose-200"
                    : "bg-slate-50/60 border-slate-200/70 opacity-60"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <div
                    className={`w-6 h-6 rounded flex items-center justify-center text-xs ${
                      state === "running"
                        ? "bg-sky-600 text-white"
                        : state === "completed"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : state === "failed"
                        ? "bg-rose-100 text-rose-800"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  {state === "running" ? (
                    <Loader2 className="w-3.5 h-3.5 text-sky-600 animate-spin" />
                  ) : state === "completed" ? (
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                  ) : state === "failed" ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                  )}
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-900 tracking-tight truncate">{s.label}</p>
                  <p className="text-[10px] font-mono text-slate-400 capitalize mt-0.5">{state}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 mb-6">
        <div className="precision-card p-4">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1 font-mono">
            <span>Verified claims</span>
            <span className="flex items-center gap-1 text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>{greenFacts}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 ml-1" />
              <span>{yellowFacts}</span>
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 tracking-tight">
            {statusData.findings?.length || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Cross-examined with source text</p>
        </div>

        <div className="precision-card p-4">
          <div className="text-xs text-slate-500 mb-1 font-mono">Web inquiries</div>
          <div className="text-2xl font-bold font-mono text-slate-900 tracking-tight">
            {statusData.research_jobs?.length || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {statusData.research_jobs?.filter((j) => j.status === "completed").length || 0} completed searches
          </p>
        </div>

        <div className="precision-card p-4">
          <div className="text-xs text-slate-500 mb-1 flex items-center gap-1.5 font-mono">
            <Scale className="w-3 h-3 text-amber-600" />
            <span>Contradictions</span>
          </div>
          <div className="text-2xl font-bold font-mono text-amber-700 tracking-tight">
            {statusData.conflicts?.length || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Preserved conflicting claims</p>
        </div>

        <div className="precision-card p-4">
          <div className="text-xs text-slate-500 mb-1 flex items-center gap-1.5 font-mono">
            <FileQuestion className="w-3 h-3 text-rose-600" />
            <span>Research gaps</span>
          </div>
          <div className="text-2xl font-bold font-mono text-rose-700 tracking-tight">
            {statusData.gaps?.length || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Unverified metrics flagged</p>
        </div>
      </div>

      {/* Active Sub-tasks */}
      <div className="precision-card p-5 mb-6">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
          <span className="text-xs font-mono font-medium text-slate-700 uppercase tracking-wider">
            Targeted Sub-queries ({statusData.research_jobs?.length || 0})
          </span>
        </div>

        {statusData.research_jobs && statusData.research_jobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {statusData.research_jobs.map((job) => (
              <div
                key={job.id}
                className="p-3 rounded-md border border-slate-200 bg-slate-50/50 flex items-start justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {job.entity && (
                      <span className="text-[11px] font-mono font-semibold text-slate-800 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                        {job.entity}
                      </span>
                    )}
                    {job.attribute && (
                      <span className="text-xs text-slate-500 font-mono">
                        {job.attribute}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-700 leading-snug">{job.description}</p>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded shrink-0 border ${
                    job.status === "completed"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : job.status === "failed"
                      ? "bg-rose-50 text-rose-700 border-rose-200"
                      : "bg-sky-50 text-sky-700 border-sky-200"
                  }`}
                >
                  {job.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 py-4 text-center font-mono">
            Formulating research execution plan...
          </p>
        )}
      </div>

      {/* Activity Log */}
      <div className="precision-card overflow-hidden">
        <button
          onClick={() => setShowLogTerminal(!showLogTerminal)}
          className="w-full px-5 py-3 flex items-center justify-between text-xs text-slate-700 hover:bg-slate-50 transition"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-mono text-xs font-medium">
              Telemetry stream ({streamEvents.length} events)
            </span>
          </div>
          {showLogTerminal ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </button>

        {showLogTerminal && (
          <div className="bg-slate-950 text-slate-200 p-4 font-mono text-xs max-h-60 overflow-y-auto space-y-1.5 border-t border-slate-800">
            {streamEvents.length > 0 ? (
              streamEvents.map((ev, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <span className="text-slate-500 shrink-0 text-[11px]">{ev.timestamp}</span>
                  {ev.stage && (
                    <span className="text-sky-400 font-semibold shrink-0 text-[11px]">
                      [{ev.stage}]
                    </span>
                  )}
                  <span className="text-slate-300 text-xs">{ev.message}</span>
                </div>
              ))
            ) : (
              <p className="text-slate-500 text-xs">Awaiting telemetry stream events...</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
