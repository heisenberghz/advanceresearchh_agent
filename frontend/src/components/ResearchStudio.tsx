"use client";

import React, { useState } from "react";
import {
  TableProperties,
  Search,
  Scale,
  FileQuestion,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  FileText,
  X,
  Calendar,
  Layers,
  ArrowRight,
} from "lucide-react";
import {
  Fact,
  Conflict,
  ResearchGap,
  ComparisonMatrix,
  ComparisonCell,
  Evidence,
} from "@/lib/api";

interface ResearchStudioProps {
  facts: Fact[];
  conflicts: Conflict[];
  gaps: ResearchGap[];
  comparison?: ComparisonMatrix;
  onViewReport: () => void;
}

export const ResearchStudio: React.FC<ResearchStudioProps> = ({
  facts,
  conflicts,
  gaps,
  comparison,
  onViewReport,
}) => {
  const [activeTab, setActiveTab] = useState<"matrix" | "facts" | "conflicts" | "gaps">("matrix");
  const [selectedFact, setSelectedFact] = useState<Fact | null>(null);
  const [factFilter, setFactFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredFacts = facts.filter((f) => {
    const matchesTag = factFilter === "ALL" || f.trust_tag === factFilter;
    const matchesSearch =
      !searchQuery ||
      f.entity.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.attribute.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.value.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTag && matchesSearch;
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Studio Navigation & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Research Analysis Studio</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Inspect verified claims, comparison dimensions, contradictory sources, and research gaps.
          </p>
        </div>

        <button
          onClick={onViewReport}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm shadow-blue-500/20 active:scale-[0.98] self-start sm:self-auto"
        >
          <span>Read Executive Dossier</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 mb-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab("matrix")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === "matrix"
              ? "border-blue-600 text-blue-600 bg-blue-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <TableProperties className="w-4 h-4" />
          <span>Comparison Matrix</span>
        </button>

        <button
          onClick={() => setActiveTab("facts")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === "facts"
              ? "border-blue-600 text-blue-600 bg-blue-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <Search className="w-4 h-4" />
          <span>Verified Findings ({facts.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("conflicts")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === "conflicts"
              ? "border-amber-600 text-amber-600 bg-amber-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <Scale className="w-4 h-4" />
          <span>Contradictions & Conflicts ({conflicts.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("gaps")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === "gaps"
              ? "border-rose-600 text-rose-600 bg-rose-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <FileQuestion className="w-4 h-4" />
          <span>Research Gaps ({gaps.length})</span>
        </button>
      </div>

      {/* Tab 1: Comparison Matrix */}
      {activeTab === "matrix" && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6">
          <div className="mb-4">
            <h2 className="text-sm font-bold text-slate-900">Side-by-Side Comparison Matrix</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Structured dimension alignment. All cells are mathematically grounded with deterministic trust tags.
            </p>
          </div>

          {comparison && comparison.entities?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="p-3 text-left font-bold text-slate-700 w-1/4">Metric / Dimension</th>
                    {comparison.entities.map((entity) => (
                      <th key={entity} className="p-3 text-left font-bold text-slate-900">
                        {entity}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {comparison.dimensions?.map((dim) => (
                    <tr key={dim} className="hover:bg-slate-50/60 transition">
                      <td className="p-3 font-semibold text-slate-800 bg-slate-50/30">{dim}</td>
                      {comparison.entities.map((entity) => {
                        const cell = comparison.cells?.find(
                          (c) => c.entity.toLowerCase() === entity.toLowerCase() && c.dimension.toLowerCase() === dim.toLowerCase()
                        );
                        return (
                          <td key={entity} className="p-3 text-slate-700">
                            {cell ? (
                              <div className="flex items-start gap-1.5">
                                <span
                                  className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${
                                    cell.trust_tag === "GREEN"
                                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                      : cell.trust_tag === "YELLOW"
                                      ? "bg-amber-50 text-amber-700 border-amber-200"
                                      : "bg-rose-50 text-rose-700 border-rose-200"
                                  }`}
                                >
                                  {cell.trust_tag === "GREEN" ? "🟢" : cell.trust_tag === "YELLOW" ? "🟡" : "🔴"}{" "}
                                  {cell.value}
                                </span>
                              </div>
                            ) : (
                              <span className="text-slate-400 italic">Not evaluated</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs">
              Comparison matrix is being compiled by the Comparer node...
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Verified Findings (Facts) */}
      {activeTab === "facts" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 w-full sm:w-auto">
              <span className="text-xs font-semibold text-slate-500 mr-1">Filter Trust:</span>
              {["ALL", "GREEN", "YELLOW", "RED"].map((tag) => (
                <button
                  key={tag}
                  onClick={() => setFactFilter(tag)}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-lg border transition ${
                    factFilter === tag
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>

            <div className="relative w-full sm:w-64">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search findings..."
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            </div>
          </div>

          {/* Facts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredFacts.map((fact) => (
              <div
                key={fact.id}
                onClick={() => setSelectedFact(fact)}
                className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                        {fact.entity}
                      </span>
                      <span className="text-xs font-medium text-slate-500">{fact.attribute}</span>
                    </div>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        fact.trust_tag === "GREEN"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : fact.trust_tag === "YELLOW"
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-rose-50 text-rose-700 border-rose-200"
                      }`}
                    >
                      {fact.trust_tag}
                    </span>
                  </div>

                  <p className="text-base font-bold text-slate-900 mb-2">{fact.value}</p>

                  {fact.evidence && fact.evidence.length > 0 && (
                    <p className="text-xs text-slate-600 italic bg-slate-50 p-2.5 rounded-lg border border-slate-100 line-clamp-2">
                      "{fact.evidence[0].text}"
                    </p>
                  )}
                </div>

                <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                  <span>{fact.verification_reason || "Verified against cited source"}</span>
                  <span className="text-blue-600 font-semibold flex items-center gap-1">
                    Details &rarr;
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Conflicts & Contradictions */}
      {activeTab === "conflicts" && (
        <div className="space-y-4">
          <div className="bg-amber-50/60 p-4 rounded-xl border border-amber-200 text-xs text-amber-900">
            <strong>Contradiction Preservation Invariant:</strong> When different authoritative sources disclose contradictory figures (e.g. global revenue vs Indian filing), ResearchOps preserves both claims side-by-side rather than arbitrarily discarding either one.
          </div>

          {conflicts && conflicts.length > 0 ? (
            <div className="space-y-4">
              {conflicts.map((conf) => (
                <div key={conf.id} className="bg-white rounded-2xl border border-amber-200 p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Scale className="w-5 h-5 text-amber-600" />
                      <h3 className="text-sm font-bold text-slate-900">
                        {conf.entity} &bull; {conf.attribute}
                      </h3>
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                      Discrepancy Detected
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 mb-4">{conf.description}</p>

                  {/* Competing Values Side-by-Side */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                    {conf.competing_values?.map((claim, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/60 flex flex-col justify-between"
                      >
                        <div>
                          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                            Claim #{idx + 1}
                          </div>
                          <div className="text-lg font-bold text-slate-900 mb-2">{claim.value}</div>
                          {claim.evidence && (
                            <p className="text-xs text-slate-600 italic bg-white p-2 rounded border border-slate-200">
                              "{claim.evidence}"
                            </p>
                          )}
                        </div>
                        {claim.source_url && (
                          <a
                            href={claim.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-3 text-xs text-blue-600 hover:underline flex items-center gap-1"
                          >
                            <span>Inspect source URL</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>

                  {conf.resolution_note && (
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs text-slate-700">
                      <strong>Analysis:</strong> {conf.resolution_note}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center text-slate-500 text-xs">
              Zero contradictions detected among verified sources.
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Research Gaps */}
      {activeTab === "gaps" && (
        <div className="space-y-4">
          <div className="bg-rose-50/60 p-4 rounded-xl border border-rose-200 text-xs text-rose-900">
            <strong>Zero Hallucination Guarantee:</strong> When required information cannot be publicly verified within research bounds, ResearchOps explicitly declares an information gap rather than guessing or fabricating numbers.
          </div>

          {gaps && gaps.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {gaps.map((gap) => (
                <div key={gap.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded">
                      Unverified Gap
                    </span>
                    <span className="text-[11px] text-slate-400 font-medium">
                      {gap.attempts || 1} search attempts made
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mb-1">{gap.requested_information}</h3>
                  <p className="text-xs text-slate-600 mt-2 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <strong>Reason:</strong> {gap.reason}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center text-slate-500 text-xs">
              All targeted metrics were successfully verified. Zero information gaps found.
            </div>
          )}
        </div>
      )}

      {/* Fact Detail Modal / Drawer */}
      {selectedFact && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold bg-slate-100 text-slate-900 px-2.5 py-1 rounded-md">
                  {selectedFact.entity}
                </span>
                <span className="text-xs font-medium text-slate-500">{selectedFact.attribute}</span>
              </div>
              <button
                onClick={() => setSelectedFact(null)}
                className="w-8 h-8 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-4">
              <div className="text-2xl font-extrabold text-slate-900">{selectedFact.value}</div>
              <div className="mt-2 flex items-center gap-2">
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded-full border ${
                    selectedFact.trust_tag === "GREEN"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : selectedFact.trust_tag === "YELLOW"
                      ? "bg-amber-50 text-amber-700 border-amber-200"
                      : "bg-rose-50 text-rose-700 border-rose-200"
                  }`}
                >
                  Trust Level: {selectedFact.trust_tag}
                </span>
                <span className="text-xs text-slate-400 font-mono">ID: {selectedFact.id}</span>
              </div>
            </div>

            {selectedFact.verification_reason && (
              <div className="mb-4 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs text-slate-700">
                <span className="font-semibold text-slate-900">Verification Logic: </span>
                {selectedFact.verification_reason}
              </div>
            )}

            {selectedFact.evidence && selectedFact.evidence.length > 0 && (
              <div className="mb-4">
                <div className="text-xs font-bold text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-blue-600" />
                  <span>Verbatim Snippet Grounding</span>
                </div>
                {selectedFact.evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-blue-50/50 border border-blue-100 rounded-xl text-xs text-slate-800 italic"
                  >
                    "{ev.text}"
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={() => setSelectedFact(null)}
              className="w-full py-2.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl transition"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
