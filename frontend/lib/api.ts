import type { AuthResponse, Report, UploadResponse } from "@/lib/types";

const normalizeBase = (base: string) => (base.endsWith("/") ? base.slice(0, -1) : base);
const configuredBase = process.env.NEXT_PUBLIC_API_URL?.trim();
const localBackendBases = ["http://localhost:8000", "http://127.0.0.1:8000"];

const API_BASES = [configuredBase, ...localBackendBases, "/api"]
  .filter((value): value is string => Boolean(value && value.trim()))
  .map((value) => normalizeBase(value))
  .filter((value, index, arr) => arr.indexOf(value) === index);

const buildUrl = (base: string, path: string) => `${base}${path}`;

async function parseErrorMessage(response: Response, fallback: string): Promise<string> {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    const body = await response.json().catch(() => ({ detail: fallback }));
    return body?.detail || fallback;
  }

  const text = await response.text().catch(() => "");
  return text?.trim() || fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response | null = null;

  for (const base of API_BASES) {
    try {
      const nextResponse = await fetch(buildUrl(base, path), {
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...(init?.headers || {})
        }
      });

      if (nextResponse.ok) {
        response = nextResponse;
        break;
      }

      if (
        nextResponse.status === 404 ||
        nextResponse.status === 500 ||
        nextResponse.status === 502 ||
        nextResponse.status === 503 ||
        nextResponse.status === 504
      ) {
        response = nextResponse;
        continue;
      }

      response = nextResponse;
      break;
    } catch (error) {
      void error;
    }
  }

  if (!response) {
    throw new Error("Backend is unreachable. Please ensure the API server is running on port 8000.");
  }

  if (!response.ok) {
    if (response.status === 502 || response.status === 503 || response.status === 504) {
      throw new Error("Backend is temporarily unavailable. Please start/restart the API server and try again.");
    }
    throw new Error(await parseErrorMessage(response, "Request failed"));
  }

  return response.json() as Promise<T>;
}

export async function signup(payload: {
  email: string;
  password: string;
  full_name: string;
}) {
  return request<AuthResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function login(payload: { email: string; password: string }) {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getReports(token: string) {
  return request<Report[]>("/reports", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}

export async function getReportById(token: string, reportId: string) {
  return request<Report>(`/reports/${reportId}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}

export async function uploadReport(token: string, file: File, saveResult = true) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("save_result", String(saveResult));

  let response: Response | null = null;

  for (const base of API_BASES) {
    try {
      const nextResponse = await fetch(buildUrl(base, "/reports/upload"), {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (nextResponse.ok) {
        response = nextResponse;
        break;
      }

      if (
        nextResponse.status === 404 ||
        nextResponse.status === 500 ||
        nextResponse.status === 502 ||
        nextResponse.status === 503 ||
        nextResponse.status === 504
      ) {
        response = nextResponse;
        continue;
      }

      response = nextResponse;
      break;
    } catch {
      // try next base
    }
  }

  if (!response) {
    throw new Error("Backend is unreachable. Please ensure the API server is running on port 8000.");
  }

  if (!response.ok) {
    if (response.status === 502 || response.status === 503 || response.status === 504) {
      throw new Error("Backend is temporarily unavailable. Please start/restart the API server and try again.");
    }
    throw new Error(await parseErrorMessage(response, "Upload failed"));
  }

  return response.json() as Promise<UploadResponse>;
}

export async function simplifyReportText(token: string, text: string, saveResult = true) {
  return request<UploadResponse>(`/reports/simplify-text?save_result=${String(saveResult)}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ text })
  });
}
