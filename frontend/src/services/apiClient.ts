/**
 * SmartSched AI — Unified Full-Stack API Client
 * Connects Next.js Frontend directly to FastAPI Backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function buildHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("smartsched_auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}

async function parseError(res: Response, method: string, endpoint: string): Promise<string> {
  try {
    const text = await res.text();
    try {
      const json = JSON.parse(text);
      if (json.detail) {
        if (res.status === 401) {
          return `Authentication required: ${json.detail}. Please sign in as Administrator.`;
        }
        if (res.status === 403) {
          return `Permission denied: ${json.detail}`;
        }
        return typeof json.detail === "string" ? json.detail : JSON.stringify(json.detail);
      }
    } catch {
      // Not JSON
    }
    return `API Error [${method} ${endpoint}]: ${res.status} - ${text}`;
  } catch {
    return `API Error [${method} ${endpoint}]: ${res.status}`;
  }
}

export class ApiClient {
  static async get<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "GET",
      headers: buildHeaders(),
      credentials: "include",
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(await parseError(res, "GET", endpoint));
    }
    return res.json();
  }

  static async post<T>(endpoint: string, body?: any): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: buildHeaders(),
      credentials: "include",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      throw new Error(await parseError(res, "POST", endpoint));
    }
    return res.json();
  }

  static async put<T>(endpoint: string, body: any): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "PUT",
      headers: buildHeaders(),
      credentials: "include",
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error(await parseError(res, "PUT", endpoint));
    }
    return res.json();
  }

  static async delete<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "DELETE",
      headers: buildHeaders(),
      credentials: "include",
    });
    if (!res.ok) {
      throw new Error(await parseError(res, "DELETE", endpoint));
    }
    return res.json();
  }
}
