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
          <div className="neo-stamp neo-stamp-yellow mb-1.5">
            Fact-Checked Insights
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-black tracking-tight uppercase">
            Research Findings & Comparison
          </h1>
          <p className="text-xs sm:text-sm font-medium text-slate-700 mt-1">
            Side-by-side competitor comparison, multi-source verified findings, identified discrepancies, and original web citations.
          </p>
        </div>

        <button
          onClick={onViewReport}
          className="neo-btn-primary text-xs sm:text-xs py-2 px-4 self-start sm:self-auto"
        >
          <span>View Final Report</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-1">
        <button
          onClick={() => setActiveTab("matrix")}
          className={`px-3.5 py-2 rounded-lg font-mono text-xs font-bold border-2 border-black transition-all whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === "matrix"
              ? "bg-[#FFE600] text-black shadow-[3px_3px_0px_#000000] translate-x-[-1px] translate-y-[-1px]"
              : "bg-white text-black hover:bg-slate-100"
          }`}
        >
          <TableProperties className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Comparison Table</span>
        </button>

        <button
          onClick={() => setActiveTab("facts")}
          className={`px-3.5 py-2 rounded-lg font-mono text-xs font-bold border-2 border-black transition-all whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === "facts"
              ? "bg-[#FFE600] text-black shadow-[3px_3px_0px_#000000] translate-x-[-1px] translate-y-[-1px]"
              : "bg-white text-black hover:bg-slate-100"
          }`}
        >
          <Search className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Verified Findings ({facts.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("conflicts")}
          className={`px-3.5 py-2 rounded-lg font-mono text-xs font-bold border-2 border-black transition-all whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === "conflicts"
              ? "bg-[#FFE600] text-black shadow-[3px_3px_0px_#000000] translate-x-[-1px] translate-y-[-1px]"
              : "bg-white text-black hover:bg-slate-100"
          }`}
        >
          <Scale className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Conflicting Claims ({conflicts.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("gaps")}
          className={`px-3.5 py-2 rounded-lg font-mono text-xs font-bold border-2 border-black transition-all whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === "gaps"
              ? "bg-[#FFE600] text-black shadow-[3px_3px_0px_#000000] translate-x-[-1px] translate-y-[-1px]"
              : "bg-white text-black hover:bg-slate-100"
          }`}
        >
          <FileQuestion className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Missing Information ({gaps.length})</span>
        </button>
      </div>

      {/* Tab 1: Comparison Matrix */}
      {activeTab === "matrix" && (
        <div className="neo-box overflow-hidden p-6 bg-white">
          <div className="mb-4">
            <h2 className="font-mono text-xs font-black text-black uppercase tracking-wider">
              Side-by-Side Competitor Comparison
            </h2>
            <p className="text-xs font-medium text-slate-700 mt-0.5">
              Key metrics and pricing compared across competitors with source trustworthiness ratings.
            </p>
          </div>

          {comparison && comparison.entities?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs border-2 border-black shadow-[3px_3px_0px_#000000]">
                <thead>
                  <tr className="bg-[#FEF9C3] border-b-2 border-black">
                    <th className="p-3 text-left font-mono font-black text-black border-r-2 border-black w-1/4 uppercase">
                      FEATURE / METRIC
                    </th>
                    {comparison.entities.map((entity) => (
                      <th key={entity} className="p-3 text-left font-mono font-black text-black border-r-2 border-black last:border-r-0 uppercase">
                        {entity}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y-2 divide-black">
                  {(comparison.metrics || comparison.dimensions || []).map((dim) => (
                    <tr key={dim} className="hover:bg-slate-50 transition">
                      <td className="p-3 font-mono font-bold text-black bg-[#FAF9F5] border-r-2 border-black">{dim}</td>
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
                          <td key={entity} className="p-3 text-black border-r-2 border-black last:border-r-0 bg-white">
                            {cell ? (
                              <div className="flex items-start gap-1.5">
                                <span
                                  className={`neo-stamp ${
                                    cell.trust_tag === "GREEN"
                                      ? "neo-stamp-green"
                                      : cell.trust_tag === "YELLOW"
                                      ? "neo-stamp-yellow"
                                      : "neo-stamp-red"
                                  }`}
                                >
                                  {cell.value}
                                </span>
                              </div>
                            ) : (
                              <span className="text-slate-400 font-mono text-xs">Not available</span>
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
            <div className="p-10 text-center text-slate-500 font-mono text-xs border-2 border-dashed border-black rounded-lg">
              Comparison table will appear once multiple competitors or topics are researched.
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Verified Facts */}
      {activeTab === "facts" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="neo-box p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 bg-white">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="font-mono text-xs font-black uppercase text-black">FILTER:</span>
              {[
                { tag: "ALL", label: "All" },
                { tag: "GREEN", label: "Verified (2+ Sources)" },
                { tag: "YELLOW", label: "Single Source" },
                { tag: "RED", label: "Conflicting / Disputed" },
              ].map(({ tag, label }) => (
                <button
                  key={tag}
                  onClick={() => setFactFilter(tag)}
                  className={`px-3 py-1 font-mono text-xs font-bold rounded-md border-2 border-black transition ${
                    factFilter === tag
                      ? "bg-[#FFE600] text-black shadow-[2px_2px_0px_#000000]"
                      : "bg-white text-black hover:bg-slate-100"
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
                placeholder="Search facts, company, or metric..."
                className="w-full pl-8 pr-3 py-1.5 font-mono text-xs text-black bg-[#FAF9F5] border-2 border-black rounded-md focus:bg-white focus:outline-none focus:shadow-[2px_2px_0px_#000000]"
              />
              <Search className="w-3.5 h-3.5 text-black absolute left-2.5 top-2.5" />
            </div>
          </div>

          {/* Facts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {filteredFacts.map((fact) => (
              <div
                key={fact.id}
                onClick={() => setSelectedFact(fact)}
                className="neo-box-interactive p-4 cursor-pointer flex flex-col justify-between group bg-white"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-xs font-black text-white bg-black px-2 py-0.5 rounded border border-black">
                        {fact.entity}
                      </span>
                      <span className="font-mono text-xs font-bold text-slate-700">{fact.attribute}</span>
                    </div>
                    <span
                      className={`neo-stamp ${
                        fact.trust_tag === "GREEN"
                          ? "neo-stamp-green"
                          : fact.trust_tag === "YELLOW"
                          ? "neo-stamp-yellow"
                          : "neo-stamp-red"
                      }`}
                    >
                      {fact.trust_tag === "GREEN" ? "Verified (2+ Sources)" : fact.trust_tag === "YELLOW" ? "Single Source" : "Disputed"}
                    </span>
                  </div>

                  <p className="text-base font-black text-black mb-2.5">{fact.value}</p>

                  {fact.evidence && fact.evidence.length > 0 && (
                    <div className="neo-quote line-clamp-2">
                      "{fact.evidence[0].text}"
                    </div>
                  )}
                </div>

                <div className="mt-3 pt-2.5 border-t-2 border-black flex items-center justify-between font-mono text-xs font-bold text-slate-700">
                  <span className="truncate max-w-[200px] text-[11px]">{fact.verification_reason || "Source verified"}</span>
                  <span className="text-black group-hover:underline">
                    View Source Details
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
          <div className="neo-box p-4 bg-[#FEF9C3] font-mono text-xs text-black leading-relaxed">
            <strong className="font-black uppercase tracking-wider">Conflicting Claims Detected:</strong> When reputable web sources report conflicting numbers, the system displays both figures side-by-side with direct source links instead of guessing or averaging.
          </div>

          {conflicts && conflicts.length > 0 ? (
            <div className="space-y-4">
              {conflicts.map((conf) => (
                <div key={conf.id} className="neo-box p-5 bg-white">
                  <div className="flex items-center justify-between mb-3 pb-2 border-b-2 border-black">
                    <div className="flex items-center gap-2">
                      <Scale className="w-4 h-4 stroke-[2.5]" />
                      <h3 className="font-mono font-black text-sm text-black uppercase">
                        {conf.entity} &bull; {conf.attribute}
                      </h3>
                    </div>
                    <span className="neo-stamp neo-stamp-yellow">
                      Conflicting Figures
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm font-medium text-black mb-4">{conf.description}</p>

                  {/* Competing Values Side-by-Side */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mb-4">
                    {conf.competing_values?.map((claim, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-lg border-2 border-black bg-[#FAF9F5] shadow-[2px_2px_0px_#000000] flex flex-col justify-between"
                      >
                        <div>
                          <div className="font-mono text-[10px] font-black uppercase text-slate-600 mb-1">
                            Reported Figure {idx + 1}
                          </div>
                          <div className="text-base font-black text-black mb-2">{claim.value}</div>
                          {claim.evidence && (
                            <div className="neo-quote">
                              "{claim.evidence}"
                            </div>
                          )}
                        </div>
                        {claim.source_url && (
                          <a
                            href={claim.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-3 font-mono text-xs font-bold text-black underline flex items-center gap-1"
                          >
                            <span>Open original source</span>
                            <ExternalLink className="w-3.5 h-3.5 stroke-[2.5]" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>

                  {conf.resolution_note && (
                    <div className="bg-[#FAF9F5] p-3 rounded-lg border-2 border-black font-mono text-xs text-black">
                      <span className="font-black">ANALYSIS NOTE:</span> {conf.resolution_note}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="neo-box p-10 text-center font-mono text-xs font-bold text-slate-500 bg-white">
              No conflicting figures detected across sources.
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Research Gaps */}
      {activeTab === "gaps" && (
        <div className="space-y-4">
          <div className="neo-box p-4 bg-[#FEE2E2] font-mono text-xs text-black leading-relaxed">
            <strong className="font-black uppercase tracking-wider">No-Guesswork Policy:</strong> When requested metrics cannot be confirmed through trustworthy public sources, the agent explicitly flags them as missing information rather than making up unverified numbers.
          </div>

          {gaps && gaps.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {gaps.map((gap) => (
                <div key={gap.id} className="neo-box p-4 bg-white">
                  <div className="flex items-center justify-between mb-2">
                    <span className="neo-stamp neo-stamp-red">
                      Information Not Found
                    </span>
                    <span className="font-mono text-[11px] font-bold text-slate-600">
                      {gap.attempts || 1} search passes
                    </span>
                  </div>
                  <h3 className="font-mono text-xs font-black text-black mb-1">{gap.requested_information}</h3>
                  <div className="neo-quote mt-2 bg-[#FEE2E2] text-black">
                    <strong className="font-black">WHY IT'S MISSING:</strong> {gap.reason}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="neo-box p-10 text-center font-mono text-xs font-bold text-slate-500 bg-white">
              All targeted metrics were verified. No information gaps remaining.
            </div>
          )}
        </div>
      )}

      {/* Fact Detail Modal */}
      {selectedFact && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="neo-box bg-white max-w-lg w-full p-6 animate-in fade-in duration-100">
            <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-black">
              <div className="flex items-center gap-2">
                <span className="font-mono font-black text-xs bg-black text-white px-2 py-0.5 rounded">
                  {selectedFact.entity}
                </span>
                <span className="font-mono text-xs font-bold text-slate-700">{selectedFact.attribute}</span>
              </div>
              <button
                onClick={() => setSelectedFact(null)}
                className="w-8 h-8 rounded-md border-2 border-black bg-white hover:bg-slate-100 flex items-center justify-center transition shadow-[2px_2px_0px_#000000]"
              >
                <X className="w-4 h-4 stroke-[2.5]" />
              </button>
            </div>

            <div className="mb-4">
              <div className="text-3xl font-black font-mono text-black">{selectedFact.value}</div>
              <div className="mt-2.5 flex items-center gap-2">
                <span
                  className={`neo-stamp ${
                    selectedFact.trust_tag === "GREEN"
                      ? "neo-stamp-green"
                      : selectedFact.trust_tag === "YELLOW"
                      ? "neo-stamp-yellow"
                      : "neo-stamp-red"
                  }`}
                >
                  {selectedFact.trust_tag === "GREEN" ? "Verified (2+ Sources)" : selectedFact.trust_tag === "YELLOW" ? "Single Source" : "Disputed"}
                </span>
              </div>
            </div>

            {selectedFact.verification_reason && (
              <div className="mb-4 bg-[#FEF9C3] p-3 rounded-lg border-2 border-black font-mono text-xs text-black">
                <span className="font-black">VERIFICATION DETAILS: </span>
                {selectedFact.verification_reason}
              </div>
            )}

            {selectedFact.evidence && selectedFact.evidence.length > 0 && (
              <div className="mb-4">
                <div className="font-mono text-xs font-black text-black mb-1.5 uppercase flex items-center gap-1.5">
                  <FileText className="w-4 h-4 stroke-[2.5]" />
                  <span>Exact source quote</span>
                </div>
                {selectedFact.evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="neo-quote"
                  >
                    "{ev.text}"
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={() => setSelectedFact(null)}
              className="w-full neo-btn-secondary py-2 text-xs"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
