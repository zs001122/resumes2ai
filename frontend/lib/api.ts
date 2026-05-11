const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8010";

export type JDParseResult = {
  responsibilities: string[];
  must_have: string[];
  nice_to_have: string[];
  deal_breakers: string[];
  scoring_dimensions: string[];
};

export type JobPayload = {
  title: string;
  department?: string | null;
  location?: string | null;
  salary_range?: string | null;
  experience_required?: string | null;
  education_required?: string | null;
  jd: string;
  responsibilities: string[];
  must_have: string[];
  nice_to_have: string[];
  deal_breakers: string[];
  scoring_dimensions: string[];
};

export type Job = JobPayload & {
  id: string;
  status: "open" | "closed";
  created_at: string;
  updated_at: string;
};

export type Candidate = {
  id: string;
  name: string | null;
  phone: string | null;
  email: string | null;
  city: string | null;
  current_company: string | null;
  current_title: string | null;
  years_of_experience: number | null;
  highest_education: string | null;
  skills: string[];
  education: Record<string, unknown>[];
  work_experiences: Record<string, unknown>[];
  project_experiences: Record<string, unknown>[];
  low_confidence_fields: string[];
  created_at: string;
  updated_at: string;
};

export type ResumeFile = {
  id: string;
  job_id: string;
  candidate_id: string | null;
  file_name: string;
  file_type: string;
  file_path: string;
  preview_path: string | null;
  parsed_text: string | null;
  upload_status: string;
  parse_status: "pending" | "success" | "failed";
  parse_error: string | null;
  created_at: string;
  updated_at: string;
};

export type ResumeFieldExtraction = {
  id: string;
  resume_file_id: string;
  candidate_id: string | null;
  field_name: string;
  extracted_value: string | null;
  confidence: number | null;
  source_text: string | null;
  page_number: number | null;
  text_start_offset: number | null;
  text_end_offset: number | null;
  bounding_box: Record<string, unknown> | null;
  created_at: string;
};

export type ResumeUploadResult = {
  resume_file: ResumeFile;
  candidate: Candidate | null;
  field_extractions: ResumeFieldExtraction[];
};

export type FieldCorrectionLog = {
  id: string;
  candidate_id: string;
  resume_file_id: string | null;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  editor_id: string | null;
  created_at: string;
};

export type CandidateMatch = {
  id: string;
  job_id: string;
  candidate_id: string;
  score: number;
  level: string;
  summary: string;
  matched_points: string[];
  weak_points: string[];
  risks: string[];
  interview_questions: string[];
  created_at: string;
};

export type CandidateMatchExplanation = {
  id: string;
  match_id: string;
  dimension: string;
  score: number | null;
  conclusion: string;
  evidence_text: string | null;
  confidence: number | null;
  created_at: string;
};

export type CandidateNote = {
  id: string;
  candidate_id: string;
  job_id: string | null;
  content: string;
  created_by: string | null;
  created_at: string;
};

export type CandidateTimelineEvent = {
  id: string;
  candidate_id: string;
  job_id: string | null;
  action_type: string;
  action_summary: string;
  before_value: string | null;
  after_value: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type CandidateTag = {
  id: string;
  name: string;
  created_at: string;
};

export type CandidateJobHistoryItem = {
  job_id: string;
  job_title: string;
  job_status: string;
  candidate_status: string;
  updated_at: string;
};

export type TalentPoolCandidate = {
  candidate: Candidate;
  tags: CandidateTag[];
  job_history: CandidateJobHistoryItem[];
  latest_match: CandidateMatch | null;
};

export type CandidateReviewData = {
  candidate: Candidate;
  resume_file: ResumeFile;
  preview: {
    resume_file_id: string;
    file_name: string;
    content_type: string;
    content: string;
  };
  field_extractions: ResumeFieldExtraction[];
  correction_logs: FieldCorrectionLog[];
};

export type CandidateStatus = {
  id: string;
  job_id: string;
  candidate_id: string;
  status: CandidateStatusValue;
  created_at: string;
  updated_at: string;
};

export type CandidateStatusValue =
  | "pending"
  | "favorite"
  | "pending_contact"
  | "rejected"
  | "archived";

export type CandidateListItem = {
  candidate: Candidate;
  resume_file: ResumeFile;
  match: CandidateMatch | null;
  status: CandidateStatus | null;
};

export type CandidateDetail = CandidateListItem & {
  preview: {
    resume_file_id: string;
    file_name: string;
    content_type: string;
    content: string;
  };
  field_extractions: ResumeFieldExtraction[];
  correction_logs: FieldCorrectionLog[];
};

export type JobListItem = {
  id: string;
  title: string;
  department: string | null;
  location: string | null;
  status: "open" | "closed";
  created_at: string;
  updated_at: string;
  candidate_count: number;
  high_match_count: number;
  pending_count: number;
};

export type DashboardSummary = {
  open_jobs: number;
  total_jobs: number;
  total_candidates: number;
  today_new_candidates: number;
  high_match_candidates: number;
  pending_candidates: number;
  pending_contact_candidates: number;
  parse_failed_resumes: number;
  match_failed_tasks: number;
};

export type DashboardTodo = {
  key: string;
  title: string;
  count: number;
  href: string;
  tone: "default" | "danger" | "success" | string;
};

export type DashboardActivity = {
  id: string;
  kind: string;
  title: string;
  description: string;
  happened_at: string;
  job_id: string | null;
  candidate_id: string | null;
};

export type DashboardPayload = {
  summary: DashboardSummary;
  todos: DashboardTodo[];
  recent_activities: DashboardActivity[];
};

export type UploadProcessingTask = {
  id: string;
  job_id: string;
  resume_file_id: string | null;
  original_filename: string;
  upload_status: string;
  parse_status: string;
  match_status: string;
  error_message: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(normalizeApiError(errorText, `API request failed: ${response.status}`));
  }

  return response.json() as Promise<T>;
}

export async function getApiHealth() {
  return requestJson<{
    status: string;
    service: string;
    version: string;
  }>("/api/health");
}

export async function getDashboard() {
  return requestJson<DashboardPayload>("/api/dashboard");
}

export async function listJobs() {
  return requestJson<JobListItem[]>("/api/jobs");
}

export async function getJob(jobId: string) {
  return requestJson<Job>(`/api/jobs/${jobId}`);
}

export async function createJob(payload: JobPayload) {
  return requestJson<Job>("/api/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function parseJD(payload: {
  title?: string;
  jd: string;
  experience_required?: string;
  education_required?: string;
}) {
  return requestJson<JDParseResult>("/api/jobs/parse-jd", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function closeJob(jobId: string) {
  return requestJson<Job>(`/api/jobs/${jobId}/close`, {
    method: "POST",
  });
}

export async function uploadResume(jobId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/resumes/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(normalizeApiError(errorText, `Upload failed: ${response.status}`));
  }

  return response.json() as Promise<ResumeUploadResult>;
}

export async function listUploadTasks(jobId: string) {
  return requestJson<UploadProcessingTask[]>(`/api/jobs/${jobId}/upload-tasks`);
}

export async function retryUploadTask(jobId: string, taskId: string) {
  return requestJson<UploadProcessingTask>(`/api/jobs/${jobId}/upload-tasks/${taskId}/retry`, {
    method: "POST",
  });
}

export async function retryFailedUploadTasks(jobId: string) {
  return requestJson<UploadProcessingTask[]>(`/api/jobs/${jobId}/upload-tasks/retry-failed`, {
    method: "POST",
  });
}

export async function retryParseResume(resumeFileId: string) {
  return requestJson<ResumeUploadResult>(`/api/resume-files/${resumeFileId}/parse`, {
    method: "POST",
  });
}

export async function getCandidateReviewData(jobId: string, candidateId: string) {
  return requestJson<CandidateReviewData>(`/api/jobs/${jobId}/candidates/${candidateId}/review`);
}

export async function updateCandidate(candidateId: string, payload: Partial<Candidate>) {
  return requestJson<Candidate>(`/api/candidates/${candidateId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function createCandidateMatch(jobId: string, candidateId: string) {
  return requestJson<CandidateMatch>(`/api/jobs/${jobId}/candidates/${candidateId}/match`, {
    method: "POST",
  });
}

export async function getCandidateMatch(jobId: string, candidateId: string) {
  return requestJson<CandidateMatch>(`/api/jobs/${jobId}/candidates/${candidateId}/match`);
}

export async function getCandidateMatchExplanations(jobId: string, candidateId: string) {
  return requestJson<CandidateMatchExplanation[]>(`/api/jobs/${jobId}/candidates/${candidateId}/match/explanations`);
}

export async function listCandidateNotes(jobId: string, candidateId: string) {
  return requestJson<CandidateNote[]>(`/api/jobs/${jobId}/candidates/${candidateId}/notes`);
}

export async function createCandidateNote(jobId: string, candidateId: string, content: string) {
  return requestJson<CandidateNote>(`/api/jobs/${jobId}/candidates/${candidateId}/notes`, {
    method: "POST",
    body: JSON.stringify({ candidate_id: candidateId, job_id: jobId, content, created_by: "local" }),
  });
}

export async function listCandidateTimeline(jobId: string, candidateId: string) {
  return requestJson<CandidateTimelineEvent[]>(`/api/jobs/${jobId}/candidates/${candidateId}/timeline`);
}

export async function listTalentPoolCandidates(filters?: {
  query?: string;
  skill?: string;
  city?: string;
  education?: string;
  min_years?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.query) params.set("query", filters.query);
  if (filters?.skill) params.set("skill", filters.skill);
  if (filters?.city) params.set("city", filters.city);
  if (filters?.education) params.set("education", filters.education);
  if (filters?.min_years) params.set("min_years", filters.min_years);
  const query = params.toString();
  return requestJson<TalentPoolCandidate[]>(`/api/talent-pool/candidates${query ? `?${query}` : ""}`);
}

export async function addCandidateToTalentPool(candidateId: string, jobId?: string) {
  return requestJson<CandidateStatus>(`/api/candidates/${candidateId}/talent-pool`, {
    method: "POST",
    body: JSON.stringify({ job_id: jobId ?? null }),
  });
}

export async function removeCandidateFromTalentPool(candidateId: string) {
  return requestJson<CandidateStatus[]>(`/api/candidates/${candidateId}/talent-pool`, {
    method: "DELETE",
  });
}

export async function listCandidateJobHistory(candidateId: string) {
  return requestJson<CandidateJobHistoryItem[]>(`/api/candidates/${candidateId}/job-history`);
}

export async function listCandidateTags(candidateId: string) {
  return requestJson<CandidateTag[]>(`/api/candidates/${candidateId}/tags`);
}

export async function addCandidateTag(candidateId: string, name: string) {
  return requestJson<{ id: string; candidate_id: string; tag_id: string; created_at: string }>(
    `/api/candidates/${candidateId}/tags`,
    {
      method: "POST",
      body: JSON.stringify({ name }),
    },
  );
}

export async function removeCandidateTag(candidateId: string, tagId: string) {
  const response = await fetch(`${API_BASE_URL}/api/candidates/${candidateId}/tags/${tagId}`, {
    method: "DELETE",
    cache: "no-store",
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(normalizeApiError(errorText, `API request failed: ${response.status}`));
  }
}

export async function listCandidates(
  jobId: string,
  filters?: {
    status?: string;
    level?: string;
    min_score?: string;
    max_score?: string;
    city?: string;
    min_years?: string;
    max_years?: string;
    education?: string;
    skill?: string;
    has_risk?: string;
    low_confidence?: string;
    archived?: string;
  },
) {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status_filter", filters.status);
  if (filters?.level) params.set("level", filters.level);
  if (filters?.min_score) params.set("min_score", filters.min_score);
  if (filters?.max_score) params.set("max_score", filters.max_score);
  if (filters?.city) params.set("city", filters.city);
  if (filters?.min_years) params.set("min_years", filters.min_years);
  if (filters?.max_years) params.set("max_years", filters.max_years);
  if (filters?.education) params.set("education", filters.education);
  if (filters?.skill) params.set("skill", filters.skill);
  if (filters?.has_risk) params.set("has_risk", filters.has_risk);
  if (filters?.low_confidence) params.set("low_confidence", filters.low_confidence);
  if (filters?.archived) params.set("archived", filters.archived);
  const query = params.toString();
  return requestJson<CandidateListItem[]>(`/api/jobs/${jobId}/candidates${query ? `?${query}` : ""}`);
}

export async function bulkUpdateCandidateStatus(
  jobId: string,
  candidateIds: string[],
  status: CandidateStatusValue,
) {
  return requestJson<CandidateStatus[]>(`/api/jobs/${jobId}/candidates/bulk-status`, {
    method: "POST",
    body: JSON.stringify({ candidate_ids: candidateIds, status }),
  });
}

export async function bulkAddCandidatesToTalentPool(jobId: string, candidateIds: string[]) {
  return requestJson<CandidateStatus[]>(`/api/jobs/${jobId}/candidates/bulk-add-to-talent-pool`, {
    method: "POST",
    body: JSON.stringify({ candidate_ids: candidateIds }),
  });
}

export async function bulkCreateCandidateMatches(jobId: string, candidateIds: string[]) {
  return requestJson<CandidateMatch[]>(`/api/jobs/${jobId}/candidates/bulk-match`, {
    method: "POST",
    body: JSON.stringify({ candidate_ids: candidateIds }),
  });
}

export async function getCandidateDetail(jobId: string, candidateId: string) {
  return requestJson<CandidateDetail>(`/api/jobs/${jobId}/candidates/${candidateId}`);
}

export async function updateCandidateStatus(
  jobId: string,
  candidateId: string,
  status: CandidateStatusValue,
) {
  return requestJson<CandidateStatus>(`/api/jobs/${jobId}/candidates/${candidateId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

function normalizeApiError(raw: string, fallback: string) {
  if (!raw) return fallback;
  try {
    const parsed = JSON.parse(raw) as { detail?: unknown };
    if (typeof parsed.detail === "string") return parsed.detail;
    if (Array.isArray(parsed.detail)) {
      return parsed.detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) return String(item.msg);
          return "";
        })
        .filter(Boolean)
        .join("；") || fallback;
    }
  } catch {
    return raw;
  }
  return raw;
}
