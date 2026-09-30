"use client";

import React, { useState } from "react";
import {
  TableProperties,
  Search,
  Scale,
  FileQuestion,
  ExternalLink,
  FileText,
  X,
  Layers,
  ArrowRight,
} from "lucide-react";
import {
  Fact,
  Conflict,
  ResearchGap,
  ComparisonMatrix,
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
    <div className="max-w-5xl mx-auto px-4 py-8 sm:py-10">
      {/* Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Analysis & Ground Truth
          </div>
          <h1 className="text-xl sm:text-2xl font-semibold text-slate-900 tracking-tight">
            Research Findings Studio
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Cross-examined claims, side-by-side matrices, preserved contradictions, and verified primary citations.
          </p>
        </div>

        <button
          onClick={onViewReport}
          className="btn-command-primary text-xs px-4 py-2 self-start sm:self-auto"
        >
          <span>View Audit Report</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200/80 mb-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab("matrix")}
          className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap ${
            activeTab === "matrix"
              ? "border-slate-900 text-slate-900 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          <TableProperties className="w-3.5 h-3.5" />
          <span>Comparison Matrix</span>
        </button>

        <button
          onClick={() => setActiveTab("facts")}
          className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap ${
            activeTab === "facts"
              ? "border-slate-900 text-slate-900 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          <Search className="w-3.5 h-3.5" />
          <span>Corroborated Facts ({facts.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("conflicts")}
          className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap ${
            activeTab === "conflicts"
              ? "border-slate-900 text-slate-900 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          <Scale className="w-3.5 h-3.5" />
          <span>Contradictions ({conflicts.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("gaps")}
          className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap ${
            activeTab === "gaps"
              ? "border-slate-900 text-slate-900 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          <FileQuestion className="w-3.5 h-3.5" />
          <span>Research Gaps ({gaps.length})</span>
        </button>
      </div>

      {/* Tab 1: Comparison Matrix */}
      {activeTab === "matrix" && (
        <div className="precision-card overflow-hidden p-5">
          <div className="mb-4">
            <h2 className="text-xs font-mono font-medium text-slate-700 uppercase tracking-wider">
              Cross-Entity Dimension Matrix
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Extracted metrics per entity with source veracity indicators and dual-check tags.
            </p>
          </div>

          {comparison && comparison.entities?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50/80 border-y border-slate-200">
                    <th className="p-3 text-left font-mono font-medium text-slate-600 w-1/4">
                      DIMENSION
                    </th>
                    {comparison.entities.map((entity) => (
                      <th key={entity} className="p-3 text-left font-mono font-semibold text-slate-900">
                        {entity}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(comparison.metrics || comparison.dimensions || []).map((dim) => (
                    <tr key={dim} className="hover:bg-slate-50/60 transition">
                      <td className="p-3 font-medium text-slate-800 bg-slate-50/40 font-mono text-[11px]">{dim}</td>
                      {comparison.entities.map((entity) => {
                        const cell = comparison.cells?.find(
                          (c) => {
                            const cDim = (c.metric || c.dimension || "").toLowerCase();
                            const cEnt = (c.entity || "").toLowerCase();
                            const eMatch = cEnt === entity.toLowerCase() || cEnt.includes(entity.toLowerCase()) || entity.toLowerCase().includes(cEnt);
                            const dMatch = cDim === dim.toLowerCase() || cDim.includes(dim.toLowerCase()) || dim.toLowerCase().includes(cDim);
                            return eMatch && dMatch;
                          }
                        );
                        return (
                          <td key={entity} className="p-3 text-slate-800">
                            {cell ? (
                              <div className="flex items-start gap-1.5">
                                <span
                                  className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border ${
                                    cell.trust_tag === "GREEN"
                                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                      : cell.trust_tag === "YELLOW"
                                      ? "bg-amber-50 text-amber-700 border-amber-200"
                                      : "bg-rose-50 text-rose-700 border-rose-200"
                                  }`}
                                >
                                  <span
                                    className={`w-1.5 h-1.5 rounded-full mr-1.5 inline-block ${
                                      cell.trust_tag === "GREEN"
                                        ? "bg-emerald-500"
                                        : cell.trust_tag === "YELLOW"
                                        ? "bg-amber-500"
                                        : "bg-rose-500"
                                    }`}
                                  />
                                  {cell.value}
                                </span>
                              </div>
                            ) : (
                              <span className="text-slate-400 text-xs italic font-mono">Not evaluated</span>
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
            <div className="p-10 text-center text-slate-400 text-xs font-mono">
              Comparison matrix is formulated once multiple entities are researched.
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Verified Facts */}
      {activeTab === "facts" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="precision-card p-3 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 w-full sm:w-auto">
              <span className="text-xs font-mono text-slate-500 mr-1 uppercase">Filter:</span>
              {[
                { tag: "ALL", label: "All" },
                { tag: "GREEN", label: "Dual verified" },
                { tag: "YELLOW", label: "Single source" },
                { tag: "RED", label: "Disputed" },
              ].map(({ tag, label }) => (
                <button
                  key={tag}
                  onClick={() => setFactFilter(tag)}
                  className={`px-2.5 py-1 text-xs rounded-md border font-mono transition ${
                    factFilter === tag
                      ? "bg-slate-900 text-white border-slate-900 shadow-xs"
                      : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="relative w-full sm:w-64">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter by metric or entity..."
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
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
                className="precision-card p-4 hover:border-slate-300 transition cursor-pointer flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] font-mono font-semibold text-slate-900 bg-slate-100 px-1.5 py-0.5 rounded">
                        {fact.entity}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">{fact.attribute}</span>
                    </div>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                        fact.trust_tag === "GREEN"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : fact.trust_tag === "YELLOW"
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-rose-50 text-rose-700 border-rose-200"
                      }`}
                    >
                      {fact.trust_tag === "GREEN" ? "Dual verified" : fact.trust_tag === "YELLOW" ? "Single source" : "Disputed"}
                    </span>
                  </div>

                  <p className="text-base font-semibold text-slate-900 mb-2">{fact.value}</p>

                  {fact.evidence && fact.evidence.length > 0 && (
                    <p className="text-xs text-slate-600 italic bg-slate-50 p-2.5 rounded border border-slate-100 line-clamp-2">
                      "{fact.evidence[0].text}"
                    </p>
                  )}
                </div>

                <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                  <span className="truncate max-w-[200px] font-mono text-[11px]">{fact.verification_reason || "Source verified"}</span>
                  <span className="text-slate-900 font-medium group-hover:underline">
                    View Citation
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
          <div className="precision-card p-3.5 bg-amber-50/50 border-amber-200/80 text-xs text-amber-900 leading-relaxed font-mono">
            <strong className="font-semibold uppercase tracking-wider">Contradiction Preservation Protocol:</strong> When authoritative sources report conflicting metrics, ResearchOps holds both figures side-by-side with full citation context rather than averaging or guessing.
          </div>

          {conflicts && conflicts.length > 0 ? (
            <div className="space-y-3.5">
              {conflicts.map((conf) => (
                <div key={conf.id} className="precision-card p-5 border-amber-200/80">
                  <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <Scale className="w-4 h-4 text-amber-600" />
                      <h3 className="text-sm font-semibold text-slate-900">
                        {conf.entity} &bull; {conf.attribute}
                      </h3>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-medium">
                      Discrepancy Preserved
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 mb-3.5">{conf.description}</p>

                  {/* Competing Values Side-by-Side */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3.5">
                    {conf.competing_values?.map((claim, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 flex flex-col justify-between"
                      >
                        <div>
                          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">
                            Disclosed Claim {idx + 1}
                          </div>
                          <div className="text-base font-semibold text-slate-900 mb-2">{claim.value}</div>
                          {claim.evidence && (
                            <p className="text-xs text-slate-600 italic bg-white p-2.5 rounded border border-slate-200">
                              "{claim.evidence}"
                            </p>
                          )}
                        </div>
                        {claim.source_url && (
                          <a
                            href={claim.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-3 text-xs text-sky-700 hover:underline flex items-center gap-1 font-mono"
                          >
                            <span>Open source page</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>

                  {conf.resolution_note && (
                    <div className="bg-slate-50 p-2.5 rounded border border-slate-200 text-xs text-slate-700 font-mono">
                      <span className="font-semibold text-slate-900">Analysis Note:</span> {conf.resolution_note}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="precision-card p-10 text-center text-slate-400 text-xs font-mono">
              Zero conflicting metrics detected among primary sources.
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Research Gaps */}
      {activeTab === "gaps" && (
        <div className="space-y-4">
          <div className="precision-card p-3.5 bg-rose-50/50 border-rose-200/80 text-xs text-rose-900 leading-relaxed font-mono">
            <strong className="font-semibold uppercase tracking-wider">Zero Hallucination Protocol:</strong> When requested metrics cannot be verified through credible primary sources, ResearchOps logs an explicit research gap rather than synthesizing ungrounded estimates.
          </div>

          {gaps && gaps.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {gaps.map((gap) => (
                <div key={gap.id} className="precision-card p-4 border-rose-200/60">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded font-semibold uppercase">
                      Unverified Metric
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      {gap.attempts || 1} search cycles
                    </span>
                  </div>
                  <h3 className="text-xs font-semibold text-slate-900 mb-1">{gap.requested_information}</h3>
                  <p className="text-xs text-slate-600 mt-2 bg-slate-50 p-2.5 rounded border border-slate-100 font-mono">
                    <strong className="font-medium text-slate-800">Gap Reason:</strong> {gap.reason}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="precision-card p-10 text-center text-slate-400 text-xs font-mono">
              All targeted metrics were corroborated. Zero research gaps remaining.
            </div>
          )}
        </div>
      )}

      {/* Fact Detail Modal */}
      {selectedFact && (
        <div className="fixed inset-0 z-50 bg-slate-950/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full p-6 animate-in fade-in duration-100">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold bg-slate-900 text-white px-2 py-0.5 rounded">
                  {selectedFact.entity}
                </span>
                <span className="text-xs font-mono text-slate-500">{selectedFact.attribute}</span>
              </div>
              <button
                onClick={() => setSelectedFact(null)}
                className="w-7 h-7 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mb-4">
              <div className="text-2xl font-bold font-mono text-slate-950">{selectedFact.value}</div>
              <div className="mt-2 flex items-center gap-2">
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase tracking-wider font-semibold ${
                    selectedFact.trust_tag === "GREEN"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : selectedFact.trust_tag === "YELLOW"
                      ? "bg-amber-50 text-amber-700 border-amber-200"
                      : "bg-rose-50 text-rose-700 border-rose-200"
                  }`}
                >
                  {selectedFact.trust_tag === "GREEN" ? "Dual verified" : selectedFact.trust_tag === "YELLOW" ? "Single source" : "Disputed"}
                </span>
              </div>
            </div>

            {selectedFact.verification_reason && (
              <div className="mb-4 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs text-slate-700 font-mono">
                <span className="font-semibold text-slate-900">Verification reason: </span>
                {selectedFact.verification_reason}
              </div>
            )}

            {selectedFact.evidence && selectedFact.evidence.length > 0 && (
              <div className="mb-4">
                <div className="text-xs font-mono font-medium text-slate-700 mb-1.5 flex items-center gap-1.5 uppercase">
                  <FileText className="w-3.5 h-3.5 text-slate-500" />
                  <span>Verbatim source excerpt</span>
                </div>
                {selectedFact.evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 italic"
                  >
                    "{ev.text}"
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={() => setSelectedFact(null)}
              className="w-full btn-command-secondary py-2 text-xs"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
