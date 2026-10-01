/**
 * ResearchOps Frontend API Client
 * Connects Next.js frontend to FastAPI backend endpoints.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CreateResearchPayload {
  question: string;
  assumptions?: string[];
}

export interface CreateResearchResponse {
  research_id: string;
  status: string;
  question: string;
  created_at: string;
}

export interface ResearchRunSummary {
  id: string;
  question: string;
  status: string;
  assumptions: string[];
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
}

export interface ResearchJob {
  id: string;
  research_run_id?: string;
  description: string;
  entity?: string;
  attribute?: string;
  status: "pending" | "running" | "completed" | "failed";
  attempts?: number;
  error?: string;
}

export interface Evidence {
  text: string;
  source_id?: string;
  published_at?: string;
  captured_at?: string;
}

export interface Fact {
  id: string;
  research_run_id?: string;
  entity: string;
  attribute: string;
  value: string;
  trust_tag: "GREEN" | "YELLOW" | "RED";
  verification_status: "VERIFIED" | "PARTIALLY_VERIFIED" | "UNSUPPORTED" | "CONTRADICTED";
  verification_reason?: string;
  source_ids?: string[];
  evidence?: Evidence[];
}

export interface CompetingValue {
  value: string;
  source_id?: string;
  source_url?: string;
  evidence?: string;
}

export interface Conflict {
  id: string;
  research_run_id?: string;
  entity?: string;
  attribute?: string;
  description: string;
  status: string;
  competing_values: CompetingValue[];
  supporting_sources?: string[];
  resolution_note?: string;
}

export interface ResearchGap {
  id: string;
  research_run_id?: string;
  requested_information: string;
  reason: string;
  attempts?: number;
  status?: string;
}

export interface ComparisonCell {
  entity: string;
  dimension?: string;
  metric?: string;
  value: string;
  trust_tag: "GREEN" | "YELLOW" | "RED";
  fact_id?: string;
  source_id?: string;
  source_ids?: string[];
  gap_id?: string;
  notes?: string;
}

export interface ComparisonMatrix {
  entities: string[];
  dimensions?: string[];
  metrics?: string[];
  cells: ComparisonCell[];
}

export interface ResearchReport {
  id: string;
  research_run_id: string;
  title: string;
  executive_summary: string;
  assumptions: string[];
  comparison?: ComparisonMatrix;
  key_findings: string[];
  detailed_findings: Fact[];
  conflicting_information: Conflict[];
  research_gaps: ResearchGap[];
  sources: Array<{
    id: string;
    url: string;
    title: string;
    domain?: string;
    snippet?: string;
  }>;
  markdown_content?: string;
  created_at: string;
  updated_at: string;
}

export interface ResearchStatusResponse {
  id: string;
  research_id: string;
  question: string;
  status: "pending" | "running" | "completed" | "failed";
  current_workflow_stage: string;
  workflow_status: string;
  research_jobs: ResearchJob[];
  findings: Fact[];
  facts: Fact[];
  conflicts: Conflict[];
  gaps: ResearchGap[];
  assumptions: string[];
  has_report: boolean;
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
}

export interface SystemHealth {
  service: string;
  status: string;
  version: string;
  timestamp: string;
  configuration: {
    is_research_ready: boolean;
    missing_keys: string[];
    research_model: string;
    writer_model: string;
    max_research_retries: number;
    max_searches_per_job: number;
  };
}

/** Check backend health status */
export async function checkBackendHealth(): Promise<SystemHealth | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Start a new autonomous research run */
export async function startResearch(payload: CreateResearchPayload): Promise<CreateResearchResponse> {
  const res = await fetch(`${API_BASE_URL}/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start research" }));
    throw new Error(err.detail || "Failed to start research");
  }

  return await res.json();
}

/** Fetch live status of a research run */
export async function getResearchStatus(researchId: string): Promise<ResearchStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/research/${encodeURIComponent(researchId)}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to fetch status" }));
    throw new Error(err.detail || `Status fetch failed: ${res.status}`);
  }

  return await res.json();
}

/** Fetch final synthesized report */
export async function getResearchReport(researchId: string): Promise<ResearchReport> {
  const res = await fetch(`${API_BASE_URL}/research/${encodeURIComponent(researchId)}/report`, {
    cache: "no-store",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Report not ready or not found" }));
    throw new Error(err.detail || `Report fetch failed: ${res.status}`);
  }

  return await res.json();
}

/** List recent research runs */
export async function listResearchRuns(limit = 20): Promise<ResearchRunSummary[]> {
  const res = await fetch(`${API_BASE_URL}/research?limit=${limit}`, {
    cache: "no-store",
  });

  if (!res.ok) return [];
  return await res.json();
}

/** Export markdown download URL */
export function getExportMarkdownUrl(researchId: string): string {
  return `${API_BASE_URL}/research/${encodeURIComponent(researchId)}/export/markdown`;
}

/** Export PDF download URL (Task 34) */
export function getExportPdfUrl(researchId: string): string {
  return `${API_BASE_URL}/research/${encodeURIComponent(researchId)}/export/pdf`;
}
