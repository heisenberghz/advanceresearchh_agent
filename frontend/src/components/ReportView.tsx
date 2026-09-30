"use client";

import React, { useState } from "react";
import {
  Download,
  Copy,
  Check,
  ArrowLeft,
  Calendar,
  ShieldCheck,
  FileDown,
} from "lucide-react";
import { marked } from "marked";
import { ResearchReport, getExportMarkdownUrl, getExportPdfUrl } from "@/lib/api";

interface ReportViewProps {
  report: ResearchReport;
  onBackToDashboard: () => void;
  onNewResearch: () => void;
}

export const ReportView: React.FC<ReportViewProps> = ({
  report,
  onBackToDashboard,
  onNewResearch,
}) => {
  const [viewMode, setViewMode] = useState<"rendered" | "raw">("rendered");
  const [copied, setCopied] = useState(false);

  const markdownContent =
    report.markdown_content ||
    `# ${report.title}\n\n## 1. Executive Summary\n${report.executive_summary}`;

  const renderedHtml = marked.parse(markdownContent, { async: false }) as string;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(markdownContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const exportUrl = getExportMarkdownUrl(report.research_run_id);
  const pdfExportUrl = getExportPdfUrl(report.research_run_id);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-10">
      {/* Top Navigation & Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b-2 border-black">
        <button
          onClick={onBackToDashboard}
          className="neo-btn-secondary text-xs sm:text-xs py-1.5 px-3 self-start"
        >
          <ArrowLeft className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Back to Findings Studio</span>
        </button>

        <div className="flex items-center gap-2 flex-wrap">
          {/* View Toggle */}
          <div className="border-2 border-black rounded-lg p-0.5 bg-white flex items-center shadow-[2px_2px_0px_#000000]">
            <button
              onClick={() => setViewMode("rendered")}
              className={`px-3 py-1 font-mono text-xs font-bold rounded transition ${
                viewMode === "rendered"
                  ? "bg-[#FFE600] text-black border border-black shadow-[1px_1px_0px_#000000]"
                  : "text-black hover:bg-slate-100"
              }`}
            >
              Report
            </button>
            <button
              onClick={() => setViewMode("raw")}
              className={`px-3 py-1 font-mono text-xs font-bold rounded transition ${
                viewMode === "raw"
                  ? "bg-[#FFE600] text-black border border-black shadow-[1px_1px_0px_#000000]"
                  : "text-black hover:bg-slate-100"
              }`}
            >
              Raw MD
            </button>
          </div>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="neo-btn-secondary text-xs sm:text-xs py-1.5 px-3"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 stroke-[3] text-black" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Copy</span>
              </>
            )}
          </button>

          {/* Export Markdown Button */}
          <a
            href={exportUrl}
            download={`research_report_${report.research_run_id}.md`}
            className="neo-btn-secondary text-xs sm:text-xs py-1.5 px-3"
          >
            <Download className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Markdown</span>
          </a>

          {/* Export PDF Button */}
          <a
            href={pdfExportUrl}
            target="_blank"
            rel="noopener noreferrer"
            download={`research_report_${report.research_run_id}.pdf`}
            className="neo-btn-primary text-xs sm:text-xs py-1.5 px-3.5"
          >
            <FileDown className="w-4 h-4 stroke-[2.5]" />
            <span>Download PDF</span>
          </a>
        </div>
      </div>

      {/* Main Dossier Container */}
      <div className="neo-box p-6 sm:p-10 mb-8 bg-white">
        {/* Report Metadata Header */}
        <div className="mb-8 pb-6 border-b-2 border-black">
          <div className="flex items-center gap-2 mb-3">
            <span className="neo-stamp neo-stamp-green">
              Ground-Truth Verified
            </span>
            <span className="neo-stamp neo-stamp-white font-mono">
              RUN: {report.research_run_id}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-black text-black tracking-tight leading-snug mb-3 uppercase">
            {report.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono font-bold text-black">
            <div className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4 stroke-[2.5]" />
              <span>
                {new Date(report.created_at || Date.now()).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 stroke-[2.5]" />
              <span>Deterministic Cross-Verification</span>
            </div>
          </div>
        </div>

        {/* Content View */}
        {viewMode === "rendered" ? (
          <div
            className="prose-report"
            dangerouslySetInnerHTML={{ __html: renderedHtml }}
          />
        ) : (
          <pre className="bg-black text-[#4ADE80] p-5 rounded-lg border-2 border-black overflow-x-auto text-xs font-mono leading-relaxed shadow-[3px_3px_0px_#000000]">
            {markdownContent}
          </pre>
        )}
      </div>

      {/* Bottom Footer Actions */}
      <div className="flex items-center justify-between text-xs font-mono font-bold text-black pb-8">
        <span>RESEARCH OPS // AUTONOMOUS AGENT</span>
        <button
          onClick={onNewResearch}
          className="neo-btn-primary text-xs sm:text-xs py-1.5 px-3"
        >
          Initialize New Research Run
        </button>
      </div>
    </div>
  );
};
