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
} from "lucide-react";
import { ResearchStatusResponse } from "@/lib/api";

interface ProgressDashboardProps {
  statusData: ResearchStatusResponse;
  streamEvents: Array<{ timestamp: string; message: string; stage?: string }>;
  onViewReport: () => void;
  onViewFindings: () => void;
}

const PIPELINE_STAGES = [
  { key: "planned", label: "Planning Research", icon: Brain },
  { key: "researched", label: "Searching Web", icon: Globe },
  { key: "checked", label: "Fact Checking", icon: CheckCircle },
  { key: "retrying", label: "Deepening Search", icon: Repeat },
  { key: "compared", label: "Comparing Data", icon: TableProperties },
  { key: "completed", label: "Final Report", icon: PenTool },
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
      <div className="neo-box p-6 mb-6 bg-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2 font-mono">
              <span
                className={`neo-stamp ${
                  isFinished
                    ? "neo-stamp-green"
                    : isFailed
                    ? "neo-stamp-red"
                    : "neo-stamp-yellow animate-pulse"
                }`}
              >
                {statusData.status === "running" ? "Research in Progress" : isFinished ? "Completed" : "Stopped"}
              </span>
              <span className="neo-stamp neo-stamp-white font-mono">
                ID: {statusData.research_id}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-black tracking-tight leading-snug">
              {statusData.question}
            </h1>
          </div>

          {/* Action buttons when report is ready */}
          {statusData.has_report && (
            <div className="flex items-center gap-2.5 shrink-0 self-start md:self-auto">
              <button
                onClick={onViewFindings}
                className="neo-btn-secondary text-xs sm:text-xs py-2 px-3.5"
              >
                View Findings
              </button>
              <button
                onClick={onViewReport}
                className="neo-btn-primary text-xs sm:text-xs py-2 px-4"
              >
                View Report
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 6-Stage Pipeline Stepper */}
      <div className="neo-box p-5 sm:p-6 mb-6 bg-white">
        <div className="flex items-center justify-between mb-4">
          <span className="font-mono text-xs font-black text-black uppercase tracking-wider">
            Research Progress
          </span>
          <span className="neo-stamp neo-stamp-black">
            {isFinished ? "100% COMPLETE" : `STEP: ${currentStage.toUpperCase()}`}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {PIPELINE_STAGES.map((s, idx) => {
            const state = getStageState(s.key, idx);
            const Icon = s.icon;
            return (
              <div
                key={s.key}
                className={`p-3 rounded-lg border-2 border-black flex flex-col justify-between transition-all min-h-[96px] ${
                  state === "running"
                    ? "bg-[#FEF9C3] shadow-[3px_3px_0px_#000000] translate-x-[-1px] translate-y-[-1px]"
                    : state === "completed"
                    ? "bg-[#DCFCE7] shadow-[2px_2px_0px_#000000]"
                    : state === "failed"
                    ? "bg-[#FEE2E2] shadow-[2px_2px_0px_#000000]"
                    : "bg-[#F4F4F5] opacity-60"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <div
                    className={`w-7 h-7 rounded border-2 border-black flex items-center justify-center text-xs ${
                      state === "running"
                        ? "bg-[#FFE600] text-black shadow-[1px_1px_0px_#000000]"
                        : state === "completed"
                        ? "bg-[#4ADE80] text-black"
                        : state === "failed"
                        ? "bg-[#F87171] text-black"
                        : "bg-white text-black"
                    }`}
                  >
                    <Icon className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  {state === "running" ? (
                    <Loader2 className="w-4 h-4 text-black animate-spin stroke-[2.5]" />
                  ) : state === "completed" ? (
                    <CheckCircle className="w-4 h-4 text-black stroke-[2.5]" />
                  ) : state === "failed" ? (
                    <AlertTriangle className="w-4 h-4 text-black stroke-[2.5]" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-slate-300" />
                  )}
                </div>
                <div>
                  <p className="font-mono text-xs font-bold text-black truncate">{s.label}</p>
                  <p className="font-mono text-[10px] font-bold text-slate-700 uppercase mt-0.5">{state}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="neo-box p-4 bg-white">
          <div className="flex items-center justify-between text-xs font-mono font-bold text-black mb-1">
            <span>VERIFIED FACTS</span>
            <span className="flex items-center gap-1 font-mono text-[11px]">
              <span className="w-2 h-2 rounded-full bg-[#4ADE80] border border-black" />
              <span>{greenFacts}</span>
              <span className="w-2 h-2 rounded-full bg-[#FDE047] border border-black ml-1" />
              <span>{yellowFacts}</span>
            </span>
          </div>
          <div className="text-3xl font-black font-mono text-black">
            {statusData.findings?.length || 0}
          </div>
          <p className="font-mono text-[11px] font-semibold text-slate-600 mt-1">Confirmed facts</p>
        </div>

        <div className="neo-box p-4 bg-white">
          <div className="text-xs font-mono font-bold text-black mb-1">SEARCHES RUN</div>
          <div className="text-3xl font-black font-mono text-black">
            {statusData.research_jobs?.length || 0}
          </div>
          <p className="font-mono text-[11px] font-semibold text-slate-600 mt-1">
            {statusData.research_jobs?.filter((j) => j.status === "completed").length || 0} completed
          </p>
        </div>

        <div className="neo-box p-4 bg-[#FEF9C3]">
          <div className="text-xs font-mono font-bold text-black mb-1 flex items-center gap-1">
            <Scale className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>DISCREPANCIES</span>
          </div>
          <div className="text-3xl font-black font-mono text-black">
            {statusData.conflicts?.length || 0}
          </div>
          <p className="font-mono text-[11px] font-semibold text-slate-800 mt-1">Disputed claims</p>
        </div>

        <div className="neo-box p-4 bg-[#FEE2E2]">
          <div className="text-xs font-mono font-bold text-black mb-1 flex items-center gap-1">
            <FileQuestion className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>MISSING DATA</span>
          </div>
          <div className="text-3xl font-black font-mono text-black">
            {statusData.gaps?.length || 0}
          </div>
          <p className="font-mono text-[11px] font-semibold text-slate-800 mt-1">Not found publicly</p>
        </div>
      </div>

      {/* Active Sub-tasks */}
      <div className="neo-box p-6 mb-6 bg-white">
        <div className="flex items-center justify-between pb-3 border-b-2 border-black mb-3">
          <span className="font-mono text-xs font-black text-black uppercase tracking-wider">
            Research Tasks ({statusData.research_jobs?.length || 0})
          </span>
        </div>

        {statusData.research_jobs && statusData.research_jobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {statusData.research_jobs.map((job) => (
              <div
                key={job.id}
                className="p-3.5 rounded-lg border-2 border-black bg-[#FAF9F5] shadow-[2px_2px_0px_#000000] flex items-start justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    {job.entity && (
                      <span className="font-mono font-bold text-[11px] bg-black text-white px-2 py-0.5 rounded border border-black">
                        {job.entity}
                      </span>
                    )}
                    {job.attribute && (
                      <span className="font-mono text-xs font-bold text-slate-700">
                        {job.attribute}
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-medium text-black leading-snug">{job.description}</p>
                </div>
                <span
                  className={`neo-stamp shrink-0 ${
                    job.status === "completed"
                      ? "neo-stamp-green"
                      : job.status === "failed"
                      ? "neo-stamp-red"
                      : "neo-stamp-yellow"
                  }`}
                >
                  {job.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="font-mono text-xs font-semibold text-slate-500 py-4 text-center">
            Formulating research execution plan...
          </p>
        )}
      </div>

      {/* Activity Log */}
      <div className="neo-box overflow-hidden bg-white">
        <button
          onClick={() => setShowLogTerminal(!showLogTerminal)}
          className="w-full px-5 py-3.5 flex items-center justify-between font-mono text-xs font-bold text-black hover:bg-[#FEF9C3] transition"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 stroke-[2.5]" />
            <span className="uppercase">
              Telemetry Stream ({streamEvents.length} events)
            </span>
          </div>
          {showLogTerminal ? (
            <ChevronUp className="w-4 h-4 stroke-[3]" />
          ) : (
            <ChevronDown className="w-4 h-4 stroke-[3]" />
          )}
        </button>

        {showLogTerminal && (
          <div className="bg-black text-[#4ADE80] p-4 font-mono text-xs max-h-64 overflow-y-auto space-y-1.5 border-t-2 border-black">
            {streamEvents.length > 0 ? (
              streamEvents.map((ev, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <span className="text-slate-500 shrink-0 text-[11px]">{ev.timestamp}</span>
                  {ev.stage && (
                    <span className="text-[#FFE600] font-black shrink-0 text-[11px]">
                      [{ev.stage.toUpperCase()}]
                    </span>
                  )}
                  <span className="text-white text-xs">{ev.message}</span>
                </div>
              ))
            ) : (
              <p className="text-slate-400 text-xs">Awaiting telemetry stream events...</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
