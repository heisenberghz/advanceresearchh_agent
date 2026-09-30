"use client";

import React, { useState, useEffect, useRef } from "react";
import { Header } from "@/components/Header";
import { InputScreen } from "@/components/InputScreen";
import { ProgressDashboard } from "@/components/ProgressDashboard";
import { ResearchStudio } from "@/components/ResearchStudio";
import { ReportView } from "@/components/ReportView";
import { HistoryDrawer } from "@/components/HistoryDrawer";
import {
  startResearch,
  getResearchStatus,
  getResearchReport,
  listResearchRuns,
  ResearchStatusResponse,
  ResearchReport,
  ResearchRunSummary,
  API_BASE_URL,
} from "@/lib/api";

type ViewState = "input" | "progress" | "studio" | "report";

export default function Home() {
  const [currentView, setCurrentView] = useState<ViewState>("input");
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<ResearchStatusResponse | null>(null);
  const [reportData, setReportData] = useState<ResearchReport | null>(null);
  const [recentRuns, setRecentRuns] = useState<ResearchRunSummary[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [streamEvents, setStreamEvents] = useState<
    Array<{ timestamp: string; message: string; stage?: string }>
  >([]);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Fetch recent runs on initial load
  const loadRecentRuns = async () => {
    try {
      const runs = await listResearchRuns(20);
      setRecentRuns(runs);
    } catch (err) {
      console.error("Failed to load runs:", err);
    }
  };

  useEffect(() => {
    loadRecentRuns();
  }, []);

  // Clean up polling & SSE stream on unmount or run switch
  const cleanupWatchers = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  useEffect(() => {
    return () => cleanupWatchers();
  }, []);

  // Monitor research run progress via Polling + SSE Stream
  const watchResearchRun = (runId: string) => {
    cleanupWatchers();
    setStreamEvents([]);

    // Initial status fetch
    const fetchStatus = async () => {
      try {
        const data = await getResearchStatus(runId);
        setStatusData(data);

        // If completed and has report, attempt to fetch report
        if (data.status === "completed" && data.has_report) {
          try {
            const report = await getResearchReport(runId);
            setReportData(report);
          } catch (err) {
            console.warn("Report not yet retrievable:", err);
          }
          cleanupWatchers();
          loadRecentRuns();
        } else if (data.status === "failed") {
          cleanupWatchers();
          loadRecentRuns();
        }
      } catch (err) {
        console.error("Error polling research status:", err);
      }
    };

    fetchStatus();

    // Start 1.5s interval polling
    pollIntervalRef.current = setInterval(fetchStatus, 1500);

    // Setup SSE connection
    try {
      const es = new EventSource(`${API_BASE_URL}/research/${encodeURIComponent(runId)}/stream`);
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const time = new Date().toLocaleTimeString();
          setStreamEvents((prev) => [
            ...prev,
            {
              timestamp: time,
              stage: payload.stage,
              message: `Stage: ${payload.stage || "processing"} | Facts: ${payload.facts_count || 0} | Jobs: ${payload.jobs_count || 0}`,
            },
          ]);

          if (payload.status === "completed" || payload.status === "failed") {
            fetchStatus();
          }
        } catch (e) {
          console.debug("SSE parse error", e);
        }
      };

      es.onerror = () => {
        // SSE error, gracefully rely on HTTP polling
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      };
    } catch (e) {
      console.debug("SSE setup error", e);
    }
  };

  // Start new research handler
  const handleStartResearch = async (question: string, assumptions?: string[]) => {
    setIsLoading(true);
    try {
      const res = await startResearch({ question, assumptions });
      setActiveRunId(res.research_id);
      setCurrentView("progress");
      setIsLoading(false);
      watchResearchRun(res.research_id);
    } catch (err) {
      setIsLoading(false);
      throw err;
    }
  };

  // Open existing run from history or recent runs
  const handleSelectRun = async (runId: string) => {
    cleanupWatchers();
    setActiveRunId(runId);
    try {
      const status = await getResearchStatus(runId);
      setStatusData(status);

      if (status.has_report) {
        try {
          const report = await getResearchReport(runId);
          setReportData(report);
          setCurrentView("report");
          return;
        } catch {
          // If report fetch fails, show studio or progress
        }
      }

      if (status.status === "completed") {
        setCurrentView("studio");
      } else {
        setCurrentView("progress");
        watchResearchRun(runId);
      }
    } catch (err) {
      console.error("Failed to load run:", err);
    }
  };

  // Reset to clean input screen
  const handleNewResearch = () => {
    cleanupWatchers();
    setActiveRunId(null);
    setStatusData(null);
    setReportData(null);
    setStreamEvents([]);
    setCurrentView("input");
    loadRecentRuns();
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans text-slate-900 selection:bg-blue-100 selection:text-blue-900">
      <Header
        onNewResearch={handleNewResearch}
        onToggleHistory={() => setIsHistoryOpen(!isHistoryOpen)}
        isHistoryOpen={isHistoryOpen}
      />

      <main className="flex-1 pb-16">
        {currentView === "input" && (
          <InputScreen
            onStartResearch={handleStartResearch}
            isLoading={isLoading}
            recentRuns={recentRuns}
            onSelectRun={handleSelectRun}
          />
        )}

        {currentView === "progress" && statusData && (
          <ProgressDashboard
            statusData={statusData}
            streamEvents={streamEvents}
            onViewReport={() => setCurrentView("report")}
            onViewFindings={() => setCurrentView("studio")}
          />
        )}

        {currentView === "studio" && statusData && (
          <ResearchStudio
            facts={statusData.findings || []}
            conflicts={statusData.conflicts || []}
            gaps={statusData.gaps || []}
            comparison={
              reportData?.comparison || undefined
            }
            onViewReport={() => {
              if (reportData) {
                setCurrentView("report");
              } else if (activeRunId) {
                getResearchReport(activeRunId)
                  .then((rep) => {
                    setReportData(rep);
                    setCurrentView("report");
                  })
                  .catch(() => setCurrentView("progress"));
              }
            }}
          />
        )}

        {currentView === "report" && reportData && (
          <ReportView
            report={reportData}
            onBackToDashboard={() => {
              if (statusData) setCurrentView("studio");
              else setCurrentView("input");
            }}
            onNewResearch={handleNewResearch}
          />
        )}
      </main>

      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        runs={recentRuns}
        onSelectRun={handleSelectRun}
        currentRunId={activeRunId || undefined}
      />
    </div>
  );
}
