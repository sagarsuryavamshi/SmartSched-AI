/**
 * SmartSched AI — Unified Full-Stack API Client
 * Connects Next.js Frontend directly to FastAPI Backend on port 8000.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiClient {
  static async get<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`API Error [GET ${endpoint}]: ${res.status} - ${err}`);
    }
    return res.json();
  }

  static async post<T>(endpoint: string, body?: any): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`API Error [POST ${endpoint}]: ${res.status} - ${err}`);
    }
    return res.json();
  }

  static async put<T>(endpoint: string, body: any): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`API Error [PUT ${endpoint}]: ${res.status} - ${err}`);
    }
    return res.json();
  }

  static async delete<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`API Error [DELETE ${endpoint}]: ${res.status} - ${err}`);
    }
    return res.json();
  }
}
