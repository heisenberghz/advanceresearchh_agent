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
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Terminal,
} from "lucide-react";
import { ResearchStatusResponse } from "@/lib/api";

interface ProgressDashboardProps {
  statusData: ResearchStatusResponse;
  streamEvents: Array<{ timestamp: string; message: string; stage?: string }>;
  onViewReport: () => void;
  onViewFindings: () => void;
}

const PIPELINE_STAGES = [
  { key: "planned", label: "1. Planner", icon: Brain, color: "text-purple-600 bg-purple-50 border-purple-200" },
  { key: "researched", label: "2. Researchers", icon: Globe, color: "text-blue-600 bg-blue-50 border-blue-200" },
  { key: "checked", label: "3. Checker", icon: CheckCircle, color: "text-emerald-600 bg-emerald-50 border-emerald-200" },
  { key: "retrying", label: "4. Retries", icon: Repeat, color: "text-amber-600 bg-amber-50 border-amber-200" },
  { key: "compared", label: "5. Comparer", icon: TableProperties, color: "text-indigo-600 bg-indigo-50 border-indigo-200" },
  { key: "completed", label: "6. Writer", icon: PenTool, color: "text-teal-600 bg-teal-50 border-teal-200" },
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

  // Helper to determine stage status
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
  const redFacts = statusData.findings?.filter((f) => f.trust_tag === "RED").length || 0;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Run Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                Run ID: <code className="font-mono text-slate-900">{statusData.research_id}</code>
              </span>
              <span
                className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                  isFinished
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : isFailed
                    ? "bg-rose-50 text-rose-700 border-rose-200"
                    : "bg-blue-50 text-blue-700 border-blue-200 animate-pulse"
                }`}
              >
                {statusData.status.toUpperCase()}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 leading-snug">
              {statusData.question}
            </h1>
          </div>

          {/* Action button when report is ready */}
          {statusData.has_report && (
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={onViewFindings}
                className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs transition"
              >
                Inspect Findings
              </button>
              <button
                onClick={onViewReport}
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white font-semibold text-xs flex items-center gap-1.5 shadow-sm shadow-blue-500/20 transition"
              >
                <span>Read Full Report</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Real-time 6-Stage Pipeline Stepper */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-6">
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">
          Autonomous Pipeline Execution Status
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {PIPELINE_STAGES.map((s, idx) => {
            const state = getStageState(s.key, idx);
            const Icon = s.icon;
            return (
              <div
                key={s.key}
                className={`p-3.5 rounded-xl border flex flex-col items-start justify-between transition-all ${
                  state === "running"
                    ? "bg-blue-50/50 border-blue-400 ring-2 ring-blue-500/20 shadow-sm"
                    : state === "completed"
                    ? "bg-emerald-50/30 border-emerald-200"
                    : state === "failed"
                    ? "bg-rose-50 border-rose-300"
                    : "bg-slate-50/70 border-slate-200 opacity-60"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center border ${s.color}`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  {state === "running" ? (
                    <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                  ) : state === "completed" ? (
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                  ) : state === "failed" ? (
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-slate-300" />
                  )}
                </div>
                <div className="w-full">
                  <p className="text-xs font-bold text-slate-900 truncate">{s.label}</p>
                  <p className="text-[11px] font-medium text-slate-500 capitalize">{state}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Metric Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-1">
            <span>Verified Findings</span>
            <span className="flex items-center gap-1 text-[11px]">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>{greenFacts}</span>
              <span className="w-2 h-2 rounded-full bg-amber-500 ml-1" />
              <span>{yellowFacts}</span>
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {statusData.findings?.length || 0}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Grounding verified against source text</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 mb-1">Sub-Research Tasks</div>
          <div className="text-2xl font-bold text-blue-600">
            {statusData.research_jobs?.length || 0}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {statusData.research_jobs?.filter((j) => j.status === "completed").length || 0} tasks completed
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 mb-1 flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-amber-500" />
            <span>Contradictions</span>
          </div>
          <div className="text-2xl font-bold text-amber-600">
            {statusData.conflicts?.length || 0}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Competing metrics preserved</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 mb-1 flex items-center gap-1.5">
            <FileQuestion className="w-3.5 h-3.5 text-rose-500" />
            <span>Research Gaps</span>
          </div>
          <div className="text-2xl font-bold text-rose-600">
            {statusData.gaps?.length || 0}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Undisclosed information flagged</p>
        </div>
      </div>

      {/* Research Jobs Grid */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-6">
        <h2 className="text-sm font-bold text-slate-900 mb-3 flex items-center justify-between">
          <span>Active & Completed Research Tasks</span>
          <span className="text-xs text-slate-400 font-normal">
            ({statusData.research_jobs?.length || 0} jobs)
          </span>
        </h2>

        {statusData.research_jobs && statusData.research_jobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {statusData.research_jobs.map((job) => (
              <div
                key={job.id}
                className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {job.entity && (
                      <span className="text-xs font-bold text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200">
                        {job.entity}
                      </span>
                    )}
                    {job.attribute && (
                      <span className="text-xs font-medium text-slate-600 bg-slate-200/60 px-2 py-0.5 rounded">
                        {job.attribute}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-700 leading-snug">{job.description}</p>
                </div>
                <span
                  className={`text-[11px] font-semibold px-2 py-0.5 rounded-full shrink-0 border ${
                    job.status === "completed"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : job.status === "failed"
                      ? "bg-rose-50 text-rose-700 border-rose-200"
                      : "bg-blue-50 text-blue-700 border-blue-200"
                  }`}
                >
                  {job.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 py-4 text-center">
            Planner is formulating sub-research tasks...
          </p>
        )}
      </div>

      {/* Collapsible SSE Event Terminal */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <button
          onClick={() => setShowLogTerminal(!showLogTerminal)}
          className="w-full px-6 py-3.5 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-500" />
            <span>Workflow Activity Stream ({streamEvents.length} events logged)</span>
          </div>
          {showLogTerminal ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>

        {showLogTerminal && (
          <div className="bg-slate-900 text-slate-200 p-4 font-mono text-xs max-h-60 overflow-y-auto space-y-1.5">
            {streamEvents.length > 0 ? (
              streamEvents.map((ev, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-slate-500 shrink-0">{ev.timestamp}</span>
                  {ev.stage && (
                    <span className="text-blue-400 font-semibold shrink-0">[{ev.stage}]</span>
                  )}
                  <span className="text-slate-200">{ev.message}</span>
                </div>
              ))
            ) : (
              <p className="text-slate-500">Listening to server-sent events...</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
