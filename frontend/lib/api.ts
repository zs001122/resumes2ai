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
