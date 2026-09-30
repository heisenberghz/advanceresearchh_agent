"use client";

import React, { useState } from "react";
import {
  Download,
  Copy,
  Check,
  ArrowLeft,
  Calendar,
  ShieldCheck,
  Printer,
  Sparkles,
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200/80">
        <button
          onClick={onBackToDashboard}
          className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 transition self-start font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Findings Studio</span>
        </button>

        <div className="flex items-center gap-2 flex-wrap">
          {/* View Toggle */}
          <div className="bg-slate-100 p-0.5 rounded-lg border border-slate-200/70 flex items-center text-xs">
            <button
              onClick={() => setViewMode("rendered")}
              className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                viewMode === "rendered"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Executive Report
            </button>
            <button
              onClick={() => setViewMode("raw")}
              className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                viewMode === "raw"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Raw Markdown
            </button>
          </div>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="btn-command-secondary text-xs px-3 py-1.5"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                <span>Copy</span>
              </>
            )}
          </button>

          {/* Export Markdown Button */}
          <a
            href={exportUrl}
            download={`research_report_${report.research_run_id}.md`}
            className="btn-command-secondary text-xs px-3 py-1.5"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Markdown</span>
          </a>

          {/* Export PDF Button */}
          <a
            href={pdfExportUrl}
            target="_blank"
            rel="noopener noreferrer"
            download={`research_report_${report.research_run_id}.pdf`}
            className="btn-command-primary text-xs px-3.5 py-1.5"
          >
            <FileDown className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </a>
        </div>
      </div>

      {/* Main Dossier Container */}
      <div className="precision-card p-6 sm:p-10 mb-8 bg-white shadow-sm">
        {/* Report Metadata Header */}
        <div className="mb-8 pb-6 border-b border-slate-100">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
              Ground-Truth Verified
            </span>
            <span className="text-xs font-mono text-slate-400">
              run: {report.research_run_id}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-semibold text-slate-950 tracking-tight leading-snug mb-3">
            {report.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 font-mono">
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>
                {new Date(report.created_at || Date.now()).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-slate-700 font-medium">Deterministic Cross-Verification</span>
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
          <pre className="bg-slate-950 text-slate-100 p-5 rounded-lg overflow-x-auto text-xs font-mono leading-relaxed border border-slate-800">
            {markdownContent}
          </pre>
        )}
      </div>

      {/* Bottom Footer Actions */}
      <div className="flex items-center justify-between text-xs text-slate-500 pb-8 font-mono">
        <span>ResearchOps Intelligence Workbench</span>
        <button
          onClick={onNewResearch}
          className="text-slate-900 hover:underline font-semibold"
        >
          Initialize New Research Run
        </button>
      </div>
    </div>
  );
};
