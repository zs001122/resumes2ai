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
    throw new Error(errorText || `API request failed: ${response.status}`);
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
    throw new Error(errorText || `Upload failed: ${response.status}`);
  }

  return response.json() as Promise<ResumeUploadResult>;
}
