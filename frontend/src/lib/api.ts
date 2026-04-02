const BASE_URL = "http://localhost:8000";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Job {
  job_id: string;
  title: string;
  company_name: string;
  description_text: string;
  relevance_score: number | null;
  cv_generated: boolean;
  cover_generated: boolean;
  status: string;
  location: string;
  work_type: string;
  deadline: string;
  url: string;
  posted_date: string;
}

export interface JobsResponse {
  jobs: Job[];
  total: number;
  offset: number;
  limit: number;
}

export interface TaskStatus {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  result?: unknown;
  error?: string;
}

export interface ScrapeRequest {
  deadline: string;
  location: string;
  role?: string;
  work_type?: string;
  limit: number;
}

export interface ContinueScrapeRequest {
  new_limit: number;
}

export interface CVGenerateRequest {
  job_id: string;
  template: "t1" | "t2" | "t3";
}

export interface CoverGenerateRequest {
  job_id: string;
}

export interface CustomJobRequest {
  title: string;
  company_name: string;
  description_text: string;
  deadline?: string;
  location?: string;
  work_type?: string;
}

export interface JobStats {
  total_jobs: number;
  total_applied: number;
  upcoming_deadlines: { job_id: string; title: string; company_name: string; deadline: string }[];
}

export interface Profile {
  [key: string]: unknown;
}

export interface ProfileValidation {
  valid: boolean;
  errors?: string[];
}

export interface GitHubRefreshResult {
  repo_count?: number;
  file_path?: string;
  [key: string]: unknown;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ─── Jobs ─────────────────────────────────────────────────────────────────────

export interface JobsQueryParams {
  status?: string;
  min_score?: number;
  sort?: string;
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
  search?: string;
}

export async function getJobs(params: JobsQueryParams = {}): Promise<JobsResponse> {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.min_score !== undefined) qs.set("min_score", String(params.min_score));
  if (params.sort) qs.set("sort", params.sort);
  if (params.order) qs.set("order", params.order);
  if (params.limit !== undefined) qs.set("limit", String(params.limit));
  if (params.offset !== undefined) qs.set("offset", String(params.offset));
  if (params.search) qs.set("search", params.search);
  const query = qs.toString();
  return request<JobsResponse>(`/api/jobs${query ? `?${query}` : ""}`);
}

export async function getTopJobs(limit = 10): Promise<Job[]> {
  return request<Job[]>(`/api/jobs/top?limit=${limit}`);
}

export async function getJob(jobId: string): Promise<Job> {
  return request<Job>(`/api/jobs/${jobId}`);
}

export async function deleteJob(jobId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/api/jobs/${jobId}`, { method: "DELETE" });
}

export async function deleteAllJobs(): Promise<{ message: string }> {
  return request<{ message: string }>("/api/jobs", { method: "DELETE" });
}

export async function createCustomJob(body: CustomJobRequest): Promise<Job> {
  return request<Job>("/api/jobs/custom", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateJobStatus(jobId: string, status: string): Promise<Job> {
  return request<Job>(`/api/jobs/${jobId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function getJobStats(): Promise<JobStats> {
  return request<JobStats>("/api/jobs/stats");
}

export async function scrapeJobs(body: ScrapeRequest): Promise<TaskStatus> {
  return request<TaskStatus>("/api/jobs/scrape", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function continueScrape(body: ContinueScrapeRequest): Promise<TaskStatus> {
  return request<TaskStatus>("/api/jobs/scrape/continue", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function reviewDeadlines(): Promise<TaskStatus> {
  return request<TaskStatus>("/api/jobs/deadline-review", { method: "POST" });
}

export async function scoreJobs(): Promise<TaskStatus> {
  return request<TaskStatus>("/api/jobs/score", { method: "POST" });
}

// ─── Tasks ────────────────────────────────────────────────────────────────────

export async function getTask(taskId: string): Promise<TaskStatus> {
  return request<TaskStatus>(`/api/tasks/${taskId}`);
}

// ─── CV ──────────────────────────────────────────────────────────────────────

export async function generateCV(body: CVGenerateRequest): Promise<TaskStatus> {
  return request<TaskStatus>("/api/cv/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function cvDownloadUrl(jobId: string): string {
  return `${BASE_URL}/api/cv/${jobId}/download`;
}

export interface CustomCVGenerateRequest {
  title: string;
  company_name: string;
  description: string;
  template: "t1" | "t2" | "t3";
}

export interface CVGenerateResponse {
  pdf_path: string;
  job_id: string;
  job_title: string;
  company_name: string;
  template_used: string;
}

export async function generateCustomCV(body: CustomCVGenerateRequest): Promise<CVGenerateResponse> {
  return request<CVGenerateResponse>("/api/cv/generate-custom", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ─── Cover Letter ─────────────────────────────────────────────────────────────

export async function generateCover(body: CoverGenerateRequest): Promise<TaskStatus> {
  return request<TaskStatus>("/api/cover/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function coverDownloadUrl(jobId: string): string {
  return `${BASE_URL}/api/cover/${jobId}/download`;
}

// ─── Profile ─────────────────────────────────────────────────────────────────

export async function getProfile(): Promise<Profile> {
  return request<Profile>("/api/profile");
}

export async function validateProfile(): Promise<ProfileValidation> {
  return request<ProfileValidation>("/api/profile/validate");
}

export async function updateProfile(data: Partial<Profile>): Promise<Profile> {
  return request<Profile>("/api/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ─── GitHub ──────────────────────────────────────────────────────────────────

export async function refreshGitHub(): Promise<GitHubRefreshResult> {
  return request<GitHubRefreshResult>("/api/github/refresh", { method: "POST" });
}

// ─── CV Editor ───────────────────────────────────────────────────────────────

export interface CVFile {
  filename: string;
  stem: string;
  has_pdf: boolean;
  modified: number;
}

export async function listCVFiles(): Promise<CVFile[]> {
  const res = await request<{ files: CVFile[] }>("/api/cv/files");
  return res.files;
}

export async function getCVSource(filename: string): Promise<{ filename: string; latex: string }> {
  return request(`/api/cv/source/${encodeURIComponent(filename)}`);
}

export async function saveCVSource(filename: string, latex: string): Promise<{ saved: boolean }> {
  return request(`/api/cv/source/${encodeURIComponent(filename)}`, {
    method: "PUT",
    body: JSON.stringify({ latex }),
  });
}

export async function recompileCV(filename: string): Promise<{ pdf_path: string; filename: string }> {
  return request(`/api/cv/recompile/${encodeURIComponent(filename)}`, { method: "POST" });
}

export async function cvChatEdit(filename: string, latex: string, message: string): Promise<{ latex: string }> {
  return request(`/api/cv/chat/${encodeURIComponent(filename)}`, {
    method: "POST",
    body: JSON.stringify({ latex, message }),
  });
}

export function cvSourceDownloadUrl(stem: string): string {
  return `${BASE_URL}/api/cv/${stem}/download`;
}

export function cvPreviewUrl(stem: string): string {
  return `${BASE_URL}/api/cv/preview/${encodeURIComponent(stem)}`;
}
