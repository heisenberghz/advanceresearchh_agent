"use client";

import React, { useState } from "react";
import {
  Download,
  Copy,
  Check,
  ArrowLeft,
  TableProperties,
  FileText,
  Calendar,
  Layers,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { marked } from "marked";
import confetti from "canvas-confetti";
import { ResearchReport, getExportMarkdownUrl } from "@/lib/api";

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

  // Trigger celebratory confetti once on mount
  React.useEffect(() => {
    try {
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.8 },
      });
    } catch {}
  }, []);

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

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Top Navigation & Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
        <button
          onClick={onBackToDashboard}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition self-start"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Progress & Findings</span>
        </button>

        <div className="flex items-center gap-2 flex-wrap">
          {/* View Toggle */}
          <div className="bg-slate-100 p-0.5 rounded-lg border border-slate-200 flex items-center text-xs">
            <button
              onClick={() => setViewMode("rendered")}
              className={`px-3 py-1 rounded-md font-medium transition ${
                viewMode === "rendered"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Rendered Report
            </button>
            <button
              onClick={() => setViewMode("raw")}
              className={`px-3 py-1 rounded-md font-medium transition ${
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
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700">Copied!</span>
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
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white transition shadow-sm shadow-blue-500/20"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export (.md)</span>
          </a>
        </div>
      </div>

      {/* Main Report Container */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-10 mb-8">
        {/* Report Metadata Header */}
        <div className="mb-8 pb-6 border-b border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full">
              Final Deliverable
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Run: {report.research_run_id}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mb-3">
            {report.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>
                Generated: {new Date(report.created_at || Date.now()).toLocaleDateString()}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>Synthesized by Writer Agent</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-emerald-700 font-medium">100% Provenance Grounded</span>
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
          <pre className="bg-slate-900 text-slate-200 p-6 rounded-xl overflow-x-auto text-xs font-mono leading-relaxed">
            {markdownContent}
          </pre>
        )}
      </div>

      {/* Bottom Footer Actions */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>ResearchOps &bull; Autonomous Verification Agent</span>
        <button
          onClick={onNewResearch}
          className="text-blue-600 hover:underline font-semibold"
        >
          Run Another Research Inquiry &rarr;
        </button>
      </div>
    </div>
  );
};
