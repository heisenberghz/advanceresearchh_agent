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
  CheckCircle2,
  Layers,
  Coins,
  Cpu,
  BarChart3,
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
}

const BENCHMARK_PRESETS: BenchmarkPreset[] = [
  {
    entityA: "Linear",
    entityB: "Jira",
    question: "Compare Linear and Jira on pricing tiers, issue speed, and enterprise security compliance.",
    category: "Dev Tools",
    metrics: ["Seat pricing", "Cycle performance", "SSO/SAML"],
  },
  {
    entityA: "Stripe",
    entityB: "Adyen",
    question: "Compare Stripe and Adyen on global transaction fees, interchange-plus pricing, and settlement currencies.",
    category: "Fintech",
    metrics: ["Interchange++", "FX markup", "Enterprise volume"],
  },
  {
    entityA: "Datadog",
    entityB: "New Relic",
    question: "Compare Datadog and New Relic on APM pricing per host, log retention costs, and synthetic testing limits.",
    category: "Infrastructure",
    metrics: ["Host compute", "Log ingestion", "Data egress"],
  },
  {
    entityA: "Zoho",
    entityB: "Freshworks",
    question: "Compare Zoho and Freshworks CRM on tier pricing models, enterprise customizations, and Indian market revenue.",
    category: "SaaS CRM",
    metrics: ["Tier limits", "API calls", "ARR disclosure"],
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

    // If a specific scope is selected, augment assumptions transparently
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
    <div className="max-w-4xl mx-auto px-4 py-10 sm:py-14">
      {/* Precision Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200/80 text-[11px] font-mono font-medium text-slate-700 tracking-tight mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          DETERMINISTIC RESEARCH ENGINE
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-slate-950 tracking-tight leading-[1.15]">
          Investigate competitors. Verify pricing. Resolve claims.
        </h1>
        <p className="mt-3.5 text-sm sm:text-base text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Primary-source intelligence with verified citations and zero hallucinations. Every claim is cross-examined against public filings and live documentation.
        </p>
      </div>

      {/* Command Console Workbench */}
      <div className="command-console p-5 sm:p-6 mb-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Scope Selectors */}
          <div className="flex flex-wrap items-center gap-1.5 pb-3 border-b border-slate-100">
            <span className="text-[11px] font-mono text-slate-400 mr-2 uppercase tracking-wider">
              Scope
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
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition ${
                    isActive
                      ? "bg-slate-900 text-white shadow-xs"
                      : "bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon className="w-3 h-3" />
                  <span>{scope.label}</span>
                </button>
              );
            })}
          </div>

          {/* Prompt Input */}
          <div className="relative">
            <textarea
              id="research-input"
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a competitive or factual query (e.g. Compare Stripe vs Adyen on enterprise interchange fees & European volume pricing)..."
              className="w-full p-3.5 text-sm sm:text-base text-slate-900 placeholder:text-slate-400 bg-transparent border-none rounded-none focus:outline-none resize-none leading-relaxed"
              disabled={isLoading}
            />
            {errorMessage && (
              <p className="text-xs text-rose-600 mt-2 font-medium flex items-center gap-1">
                <span>✕</span> {errorMessage}
              </p>
            )}
          </div>

          {/* Expandable Scope Constraints */}
          <div className="border border-slate-200/80 rounded-lg overflow-hidden bg-slate-50/50">
            <button
              type="button"
              onClick={() => setShowAssumptions(!showAssumptions)}
              className="w-full px-3.5 py-2 flex items-center justify-between text-xs font-medium text-slate-700 hover:bg-slate-100/60 transition"
            >
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
                <span>Custom research constraints (optional)</span>
              </div>
              {showAssumptions ? (
                <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              )}
            </button>
            {showAssumptions && (
              <div className="p-3.5 bg-white border-t border-slate-200/80">
                <label className="block text-[11px] font-mono text-slate-500 mb-1.5 uppercase">
                  Directives (one per line)
                </label>
                <textarea
                  rows={2}
                  value={assumptionsText}
                  onChange={(e) => setAssumptionsText(e.target.value)}
                  placeholder="Focus on 2026 contract terms&#10;Exclude US domestic-only processing"
                  className="w-full px-3 py-2 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
                />
              </div>
            )}
          </div>

          {/* Console Action Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
            <div className="flex items-center gap-3 text-xs text-slate-500 font-mono">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Dual-source verified
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                Single source
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                Contradiction
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="btn-command-primary text-xs px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed justify-center"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                  <span>Synthesizing plan...</span>
                </>
              ) : (
                <>
                  <span>Run research</span>
                  <span className="kbd-shortcut ml-2">⌘↵</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Suggested Comparison Briefs */}
      <div className="mb-10">
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-xs font-mono font-medium text-slate-500 uppercase tracking-wider">
            Benchmark Queries
          </span>
          <span className="text-[11px] text-slate-400">
            Click to load scenario
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {BENCHMARK_PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectPreset(preset)}
              className="precision-card p-3.5 text-left group transition relative"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-900 text-white">
                    {preset.entityA}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">vs</span>
                  <span className="px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-100 text-slate-800 border border-slate-200">
                    {preset.entityB}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[11px] text-slate-400 group-hover:text-slate-900 transition">
                  <span>{preset.category}</span>
                  <ArrowUpRight className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </div>
              </div>
              <p className="text-xs text-slate-600 line-clamp-1 group-hover:text-slate-900 transition mb-2">
                {preset.question}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {preset.metrics.map((metric, mIdx) => (
                  <span
                    key={mIdx}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-50 text-slate-500 border border-slate-200/60"
                  >
                    {metric}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Verification Protocol Architecture (Unified Panel) */}
      <div className="precision-card p-5 mb-10">
        <div className="text-[11px] font-mono font-medium text-slate-400 uppercase tracking-wider mb-4">
          Verification Standards
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 divide-y md:divide-y-0 md:divide-x divide-slate-100">
          <div className="pt-3 md:pt-0 md:pr-4">
            <div className="w-7 h-7 rounded-md bg-emerald-50 text-emerald-700 flex items-center justify-center mb-2.5">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-semibold text-slate-900 tracking-tight">
              Strict Corroboration
            </h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Claims without independent secondary verification are tagged as single-source or quarantined as research gaps.
            </p>
          </div>

          <div className="pt-4 md:pt-0 md:px-4">
            <div className="w-7 h-7 rounded-md bg-amber-50 text-amber-700 flex items-center justify-center mb-2.5">
              <Scale className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-semibold text-slate-900 tracking-tight">
              Preserved Contradictions
            </h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Contradictory disclosures between vendors are preserved side-by-side with verbatim quotes rather than smoothed over.
            </p>
          </div>

          <div className="pt-4 md:pt-0 md:pl-4">
            <div className="w-7 h-7 rounded-md bg-sky-50 text-sky-700 flex items-center justify-center mb-2.5">
              <FileText className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-semibold text-slate-900 tracking-tight">
              Direct Citation Graph
            </h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Every metric maps directly to its source domain, document snapshot, and exact passage used to corroborate it.
            </p>
          </div>
        </div>
      </div>

      {/* Previous Research Ledger */}
      {recentRuns && recentRuns.length > 0 && (
        <div className="precision-card p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-2">
            <span className="text-xs font-mono font-medium text-slate-700 uppercase tracking-wider">
              Research Ledger ({recentRuns.length})
            </span>
            <span className="text-[11px] text-slate-400">
              Click to restore workspace
            </span>
          </div>
          <div className="divide-y divide-slate-100">
            {recentRuns.slice(0, 5).map((run) => (
              <div
                key={run.id}
                onClick={() => onSelectRun(run.id)}
                className="py-2.5 flex items-center justify-between cursor-pointer hover:bg-slate-50/80 px-2 rounded-md transition group"
              >
                <div className="min-w-0 pr-4">
                  <p className="text-xs font-medium text-slate-900 group-hover:text-slate-950 truncate">
                    {run.question}
                  </p>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    {run.created_at ? new Date(run.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "Recent session"}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                      run.status === "completed"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : run.status === "failed"
                        ? "bg-rose-50 text-rose-700 border-rose-200"
                        : "bg-slate-100 text-slate-700 border-slate-200"
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
