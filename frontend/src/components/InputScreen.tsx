"use client";

import React, { useState } from "react";
import {
  Search,
  ShieldCheck,
  Scale,
  FileText,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  Loader2,
  ArrowUpRight,
  Layers,
  Coins,
  Cpu,
  BarChart3,
  Flame,
} from "lucide-react";
import { ResearchRunSummary } from "@/lib/api";

interface InputScreenProps {
  onStartResearch: (question: string, assumptions?: string[]) => Promise<void>;
  isLoading: boolean;
  recentRuns: ResearchRunSummary[];
  onSelectRun: (id: string) => void;
}

interface BenchmarkPreset {
  entityA: string;
  entityB: string;
  question: string;
  category: string;
  metrics: string[];
  tintClass: string;
}

const BENCHMARK_PRESETS: BenchmarkPreset[] = [
  {
    entityA: "Linear",
    entityB: "Jira",
    question: "Compare Linear and Jira on pricing tiers, issue speed, and enterprise security compliance.",
    category: "Dev Tools",
    metrics: ["Seat pricing", "Cycle latency", "SSO/SAML"],
    tintClass: "hover:bg-[#DCFCE7]",
  },
  {
    entityA: "Stripe",
    entityB: "Adyen",
    question: "Compare Stripe and Adyen on global transaction fees, interchange-plus pricing, and settlement currencies.",
    category: "Fintech",
    metrics: ["Interchange++", "FX markup", "Volume tiers"],
    tintClass: "hover:bg-[#FEF9C3]",
  },
  {
    entityA: "Datadog",
    entityB: "New Relic",
    question: "Compare Datadog and New Relic on APM pricing per host, log retention costs, and synthetic testing limits.",
    category: "Infra",
    metrics: ["Host compute", "Log ingestion", "Data egress"],
    tintClass: "hover:bg-[#E0F2FE]",
  },
  {
    entityA: "Zoho",
    entityB: "Freshworks",
    question: "Compare Zoho and Freshworks CRM on tier pricing models, enterprise customizations, and Indian market revenue.",
    category: "SaaS CRM",
    metrics: ["Tier limits", "API calls", "ARR disclosure"],
    tintClass: "hover:bg-[#F3E8FF]",
  },
];

const RESEARCH_SCOPES = [
  { id: "all", label: "Comprehensive", icon: Layers, hint: "Broad web & technical disclosures" },
  { id: "pricing", label: "Pricing & Tiers", icon: Coins, hint: "Per-seat, usage & enterprise terms" },
  { id: "infra", label: "Specs & Limits", icon: Cpu, hint: "APIs, latency, SLAs & benchmarks" },
  { id: "market", label: "Revenue & Market", icon: BarChart3, hint: "Financial filings & public ARR" },
];

export const InputScreen: React.FC<InputScreenProps> = ({
  onStartResearch,
  isLoading,
  recentRuns,
  onSelectRun,
}) => {
  const [question, setQuestion] = useState("");
  const [assumptionsText, setAssumptionsText] = useState("");
  const [showAssumptions, setShowAssumptions] = useState(false);
  const [selectedScope, setSelectedScope] = useState("all");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!question.trim()) {
      setErrorMessage("Please enter a research query or select a benchmark.");
      return;
    }
    setErrorMessage(null);

    const assumptions = assumptionsText
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const activeAssumptions = [...assumptions];
    if (selectedScope === "pricing") {
      activeAssumptions.unshift("Prioritize exact tier pricing, billing frequency, and hidden seat minimums.");
    } else if (selectedScope === "infra") {
      activeAssumptions.unshift("Prioritize API rate limits, technical uptime SLAs, and architecture specs.");
    } else if (selectedScope === "market") {
      activeAssumptions.unshift("Prioritize verifiable public revenue, financial filings, and authoritative market share reports.");
    }

    try {
      await onStartResearch(question.trim(), activeAssumptions.length > 0 ? activeAssumptions : undefined);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to start research run.");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (!isLoading && question.trim()) {
        handleSubmit();
      }
    }
  };

  const handleSelectPreset = (preset: BenchmarkPreset) => {
    setQuestion(preset.question);
    setErrorMessage(null);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12">
      {/* Hero Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 mb-3">
          <span className="neo-stamp neo-stamp-yellow">
            <Flame className="w-3.5 h-3.5 fill-black stroke-black inline-block mr-1" />
            Evidence-Based Market Research
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-black tracking-tight uppercase leading-[1.1]">
          Investigate Competitors. <br className="hidden sm:inline" />
          Verify Pricing. Resolve Claims.
        </h1>
        <p className="mt-3 text-sm sm:text-base font-medium text-slate-800 max-w-2xl mx-auto leading-relaxed">
          Accurate competitive intelligence backed by verified web citations. Every metric is checked against official sources and live documentation.
        </p>
      </div>

      {/* Main Neo-Brutalist Command Console */}
      <div className="neo-box p-5 sm:p-7 mb-8 bg-white">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Scope Selectors */}
          <div className="flex flex-wrap items-center gap-2 pb-3 border-b-2 border-black">
            <span className="font-mono text-xs font-black uppercase tracking-wider text-black mr-1">
              RESEARCH FOCUS:
            </span>
            {RESEARCH_SCOPES.map((scope) => {
              const Icon = scope.icon;
              const isActive = selectedScope === scope.id;
              return (
                <button
                  key={scope.id}
                  type="button"
                  onClick={() => setSelectedScope(scope.id)}
                  title={scope.hint}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-mono text-xs font-bold border-2 border-black transition-all ${
                    isActive
                      ? "bg-[#FFE600] text-black shadow-[2px_2px_0px_#000000] translate-x-[-1px] translate-y-[-1px]"
                      : "bg-white text-black hover:bg-slate-100"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 stroke-[2.5]" />
                  <span>{scope.label}</span>
                </button>
              );
            })}
          </div>

          {/* Prompt Input Area */}
          <div className="relative">
            <textarea
              id="research-input"
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a competitive or factual query (e.g. Compare Stripe vs Adyen on enterprise interchange fees & European volume pricing)..."
              className="w-full p-4 text-base sm:text-lg font-medium text-black placeholder:text-slate-400 bg-[#FAF9F5] border-2 border-black rounded-lg focus:outline-none focus:bg-white focus:shadow-[3px_3px_0px_#000000] resize-none leading-relaxed transition-all"
              disabled={isLoading}
            />
            {errorMessage && (
              <div className="neo-stamp neo-stamp-red mt-2 flex items-center gap-1">
                <span>✕</span> {errorMessage}
              </div>
            )}
          </div>

          {/* Expandable Custom Constraints */}
          <div className="border-2 border-black rounded-lg overflow-hidden bg-white shadow-[2px_2px_0px_#000000]">
            <button
              type="button"
              onClick={() => setShowAssumptions(!showAssumptions)}
              className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-black uppercase tracking-wider text-black bg-[#FEF9C3] hover:bg-[#FEF08A] transition"
            >
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 stroke-[2.5]" />
                <span>Custom Filters & Guidelines (Optional)</span>
              </div>
              {showAssumptions ? (
                <ChevronUp className="w-4 h-4 stroke-[3]" />
              ) : (
                <ChevronDown className="w-4 h-4 stroke-[3]" />
              )}
            </button>
            {showAssumptions && (
              <div className="p-4 bg-white border-t-2 border-black">
                <label className="block font-mono text-[11px] font-bold text-black uppercase mb-1.5">
                  Specific requirements (one per line):
                </label>
                <textarea
                  rows={2}
                  value={assumptionsText}
                  onChange={(e) => setAssumptionsText(e.target.value)}
                  placeholder="Focus on 2026 contract terms&#10;Exclude US domestic-only processing"
                  className="w-full p-3 font-mono text-xs text-black bg-[#FAF9F5] border-2 border-black rounded-md focus:bg-white focus:outline-none focus:shadow-[2px_2px_0px_#000000]"
                />
              </div>
            )}
          </div>

          {/* Console Action Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t-2 border-black">
            <div className="flex flex-wrap items-center gap-2">
              <span className="neo-stamp neo-stamp-green">
                <span className="w-1.5 h-1.5 rounded-full bg-black" />
                Verified (2+ Sources)
              </span>
              <span className="neo-stamp neo-stamp-yellow">
                <span className="w-1.5 h-1.5 rounded-full bg-black" />
                Single Source
              </span>
              <span className="neo-stamp neo-stamp-red">
                <span className="w-1.5 h-1.5 rounded-full bg-black" />
                Conflicting Info
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="neo-btn-primary disabled:opacity-50 disabled:cursor-not-allowed justify-center text-sm"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  <span>Researching market...</span>
                </>
              ) : (
                <>
                  <span>Start Research</span>
                  <span className="neo-kbd ml-1.5">⌘↵</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Suggested Comparison Briefs */}
      <div className="mb-10">
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="font-mono text-xs font-black uppercase tracking-wider text-black">
            Sample Research Queries
          </span>
          <span className="font-mono text-xs font-bold text-slate-600">
            Click to test query
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {BENCHMARK_PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectPreset(preset)}
              className={`neo-box-interactive p-4 text-left group transition-all relative ${preset.tintClass}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="font-mono font-black text-xs px-2 py-0.5 rounded bg-black text-white border-2 border-black">
                    {preset.entityA}
                  </span>
                  <span className="font-mono text-xs font-black text-black">vs</span>
                  <span className="font-mono font-black text-xs px-2 py-0.5 rounded bg-white text-black border-2 border-black">
                    {preset.entityB}
                  </span>
                </div>
                <div className="flex items-center gap-1 font-mono text-xs font-bold text-black">
                  <span>{preset.category}</span>
                  <ArrowUpRight className="w-3.5 h-3.5 stroke-[2.5] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </div>
              </div>
              <p className="text-xs sm:text-sm font-semibold text-black line-clamp-1 mb-2.5">
                {preset.question}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {preset.metrics.map((metric, mIdx) => (
                  <span
                    key={mIdx}
                    className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-white text-black border-1.5 border-black shadow-[1px_1px_0px_#000000]"
                  >
                    {metric}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Verification Protocol Architecture (3-Pillar Neo Panel) */}
      <div className="neo-box p-6 mb-10 bg-white">
        <div className="font-mono text-xs font-black text-black uppercase tracking-wider mb-5 flex items-center gap-2">
          <span className="w-2.5 h-2.5 bg-black" />
          <span>How The Agent Works</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 divide-y-2 md:divide-y-0 md:divide-x-2 divide-black">
          <div className="pt-4 md:pt-0 md:pr-5">
            <div className="w-9 h-9 rounded-lg bg-[#DCFCE7] border-2 border-black shadow-[2px_2px_0px_#000000] text-black flex items-center justify-center mb-3">
              <ShieldCheck className="w-5 h-5 stroke-[2.5]" />
            </div>
            <h3 className="text-sm font-black text-black uppercase tracking-tight">
              Multi-Source Verification
            </h3>
            <p className="text-xs font-medium text-slate-700 mt-1.5 leading-relaxed">
              Facts are cross-referenced across multiple authoritative websites before being confirmed.
            </p>
          </div>

          <div className="pt-5 md:pt-0 md:px-5">
            <div className="w-9 h-9 rounded-lg bg-[#FEF9C3] border-2 border-black shadow-[2px_2px_0px_#000000] text-black flex items-center justify-center mb-3">
              <Scale className="w-5 h-5 stroke-[2.5]" />
            </div>
            <h3 className="text-sm font-black text-black uppercase tracking-tight">
              Discrepancy Detection
            </h3>
            <p className="text-xs font-medium text-slate-700 mt-1.5 leading-relaxed">
              When competitors or sources dispute a figure, both perspectives are clearly presented side-by-side.
            </p>
          </div>

          <div className="pt-5 md:pt-0 md:pl-5">
            <div className="w-9 h-9 rounded-lg bg-[#E0F2FE] border-2 border-black shadow-[2px_2px_0px_#000000] text-black flex items-center justify-center mb-3">
              <FileText className="w-5 h-5 stroke-[2.5]" />
            </div>
            <h3 className="text-sm font-black text-black uppercase tracking-tight">
              Transparent Citations
            </h3>
            <p className="text-xs font-medium text-slate-700 mt-1.5 leading-relaxed">
              Every data point links directly to its live web source and exact excerpt.
            </p>
          </div>
        </div>
      </div>

      {/* Previous Research Ledger */}
      {recentRuns && recentRuns.length > 0 && (
        <div className="neo-box p-6 bg-white">
          <div className="flex items-center justify-between pb-3 border-b-2 border-black mb-3">
            <span className="font-mono text-xs font-black text-black uppercase tracking-wider">
              Recent Research Projects ({recentRuns.length})
            </span>
            <span className="font-mono text-xs font-bold text-slate-600">
              Click to view project
            </span>
          </div>
          <div className="divide-y-2 divide-slate-100">
            {recentRuns.slice(0, 5).map((run) => (
              <div
                key={run.id}
                onClick={() => onSelectRun(run.id)}
                className="py-3 flex items-center justify-between cursor-pointer hover:bg-[#FEF9C3] px-3 rounded-lg border border-transparent hover:border-black transition-all group"
              >
                <div className="min-w-0 pr-4">
                  <p className="text-xs sm:text-sm font-bold text-black truncate">
                    {run.question}
                  </p>
                  <p className="font-mono text-[11px] font-semibold text-slate-600 mt-0.5">
                    {run.created_at ? new Date(run.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "Recent session"}
                  </p>
                </div>
                <div className="shrink-0">
                  <span
                    className={`neo-stamp ${
                      run.status === "completed"
                        ? "neo-stamp-green"
                        : run.status === "failed"
                        ? "neo-stamp-red"
                        : "neo-stamp-blue"
                    }`}
                  >
                    {run.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
