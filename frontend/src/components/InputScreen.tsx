"use client";

import React, { useState } from "react";
import {
  Search,
  ArrowRight,
  ShieldCheck,
  Scale,
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp,
  Loader2,
  FileCheck2,
} from "lucide-react";
import { ResearchRunSummary } from "@/lib/api";

interface InputScreenProps {
  onStartResearch: (question: string, assumptions?: string[]) => Promise<void>;
  isLoading: boolean;
  recentRuns: ResearchRunSummary[];
  onSelectRun: (id: string) => void;
}

const EXAMPLE_PROMPTS = [
  {
    title: "Compare Linear vs Jira",
    question: "Compare Linear and Jira on pricing tiers, speed, and market share.",
    category: "Dev Tools",
    badgeColor: "bg-blue-50 text-blue-700 border-blue-200",
  },
  {
    title: "Stripe vs Adyen Fees",
    question: "Compare Stripe and Adyen on global transaction fees and enterprise volume pricing.",
    category: "Fintech",
    badgeColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
  },
  {
    title: "Zoho vs Freshworks",
    question: "Compare Zoho and Freshworks CRM on pricing models and Indian SaaS revenue.",
    category: "SaaS",
    badgeColor: "bg-purple-50 text-purple-700 border-purple-200",
  },
  {
    title: "Datadog vs New Relic",
    question: "Compare Datadog and New Relic on APM pricing per host and log retention costs.",
    category: "Observability",
    badgeColor: "bg-amber-50 text-amber-700 border-amber-200",
  },
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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) {
      setErrorMessage("Please enter a research question.");
      return;
    }
    setErrorMessage(null);
    const assumptions = assumptionsText
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    try {
      await onStartResearch(question.trim(), assumptions.length > 0 ? assumptions : undefined);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to start research run.");
    }
  };

  const handleSelectExample = (prompt: string) => {
    setQuestion(prompt);
    setErrorMessage(null);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 sm:py-16">
      {/* Editorial Hero Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-4">
          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          <span>ResearchOps: Autonomous Research & Verification</span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight sm:leading-tight">
          Autonomous business intelligence,
          <br />
          <span className="text-blue-600">verified with mathematical proof.</span>
        </h1>
        <p className="mt-4 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto">
          Enter any competitive, market, or pricing question. ResearchOps plans tasks, gathers live web
          evidence, checks veracity, resolves conflicts, and generates auditable dossiers.
        </p>
      </div>

      {/* Main Research Console Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="research-input" className="block text-sm font-semibold text-slate-900 mb-2">
              Research Objective
            </label>
            <div className="relative">
              <textarea
                id="research-input"
                rows={3}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g. Compare Stripe vs Adyen on global transaction fees, interchange rates, and volume discounts..."
                className="w-full px-4 py-3.5 pl-11 text-base text-slate-900 bg-slate-50/70 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition placeholder:text-slate-400 resize-none"
                disabled={isLoading}
              />
              <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-4" />
            </div>
            {errorMessage && (
              <p className="text-xs text-rose-600 mt-2 font-medium">{errorMessage}</p>
            )}
          </div>

          {/* Collapsible Assumptions / Scope Accordion */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() => setShowAssumptions(!showAssumptions)}
              className="w-full px-4 py-2.5 bg-slate-50 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-100 transition"
            >
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-slate-500" />
                <span>Advanced Scoping & Assumptions (Optional)</span>
              </div>
              {showAssumptions ? (
                <ChevronUp className="w-4 h-4 text-slate-500" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-500" />
              )}
            </button>
            {showAssumptions && (
              <div className="p-4 bg-white border-t border-slate-200">
                <label className="block text-xs text-slate-600 mb-1.5">
                  Enter specific constraints or hints (one per line, e.g. "Focus on 2026 pricing", "Include only European tiers"):
                </label>
                <textarea
                  rows={2}
                  value={assumptionsText}
                  onChange={(e) => setAssumptionsText(e.target.value)}
                  placeholder="Focus on Enterprise tier pricing&#10;Include domestic payment rails"
                  className="w-full px-3 py-2 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}
          </div>

          {/* Action Row */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <span className="text-xs text-slate-500">
              Deterministic verification tags: 🟢 GREEN &bull; 🟡 YELLOW &bull; 🔴 RED
            </span>
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-md shadow-blue-500/20 active:scale-[0.98]"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Planning Workflow...</span>
                </>
              ) : (
                <>
                  <span>Start Autonomous Research</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Example Quick-Launch Pills */}
        <div className="mt-8 pt-6 border-t border-slate-100">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Suggested Research Inquiries
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {EXAMPLE_PROMPTS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectExample(p.question)}
                className="text-left p-3 rounded-xl border border-slate-200 hover:border-blue-300 hover:bg-blue-50/40 transition group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition">
                    {p.title}
                  </span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${p.badgeColor}`}>
                    {p.category}
                  </span>
                </div>
                <p className="text-xs text-slate-600 line-clamp-1">{p.question}</p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 3 Core Trust Guarantees */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-100">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-900">Zero Hallucination Rule</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Unverified information is strictly filed as an explicit Research Gap. Never fabricated.
            </p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0 border border-amber-100">
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-900">Conflicts Preserved</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Conflicting metrics are preserved side-by-side with citations, never silently resolved.
            </p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 border border-blue-100">
            <FileCheck2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-900">Verbatim Citation Proof</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Every single fact links directly to its source URL and verbatim snippet excerpt.
            </p>
          </div>
        </div>
      </div>

      {/* Recent Runs List */}
      {recentRuns && recentRuns.length > 0 && (
        <div className="mt-12 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span>Recent Research Runs</span>
            <span className="text-xs text-slate-400 font-normal">({recentRuns.length})</span>
          </h2>
          <div className="divide-y divide-slate-100">
            {recentRuns.slice(0, 5).map((run) => (
              <div
                key={run.id}
                onClick={() => onSelectRun(run.id)}
                className="py-3 flex items-center justify-between cursor-pointer hover:bg-slate-50 px-2 rounded-lg transition"
              >
                <div className="min-w-0 pr-4">
                  <p className="text-sm font-medium text-slate-800 truncate">{run.question}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {run.created_at ? new Date(run.created_at).toLocaleDateString() : "Recent"} &bull; ID:{" "}
                    <code className="bg-slate-100 px-1 py-0.5 rounded text-[11px] text-slate-600">
                      {run.id}
                    </code>
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span
                    className={`text-xs font-medium px-2.5 py-0.5 rounded-full border ${
                      run.status === "completed"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : run.status === "failed"
                        ? "bg-rose-50 text-rose-700 border-rose-200"
                        : "bg-blue-50 text-blue-700 border-blue-200"
                    }`}
                  >
                    {run.status}
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-400" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
