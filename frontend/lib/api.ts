import type { AnalyzeResult, AuthSession, UsageLog } from "./types";

function getApiBaseUrl() {
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }

  if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
    return `http://${window.location.hostname}:8000`;
  }

  return "http://localhost:8000";
}

function authHeaders(token?: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const API_BASE_URL = getApiBaseUrl();
  const url = `${API_BASE_URL}${path}`;
  let response: Response;

  try {
    response = await fetch(url, init);
  } catch (error) {
    throw new Error(
      `API 서버에 연결하지 못했습니다. 백엔드가 켜져 있는지 확인하세요. 호출 주소: ${url}`
    );
  }

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "API request failed");
  }
  return response.json() as Promise<T>;
}

export function analyzeByText(query: string, region: string): Promise<AnalyzeResult> {
  return request<AnalyzeResult>("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, region })
  });
}

export function analyzeByImage(file: File, region: string, token?: string | null): Promise<AnalyzeResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("region", region);

  return request<AnalyzeResult>("/api/analyze/image", {
    method: "POST",
    headers: authHeaders(token),
    body: formData
  });
}

export function getLogs(token?: string | null): Promise<UsageLog[]> {
  return request<UsageLog[]>("/api/logs", {
    headers: authHeaders(token)
  });
}

export function saveLog(result: AnalyzeResult, token?: string | null): Promise<UsageLog> {
  return request<UsageLog>("/api/logs", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({
      itemName: result.itemName,
      detectedMaterial: result.detectedMaterial,
      region: result.region,
      overallRisk: result.overallRisk
    })
  });
}

export function loginWithGoogle(credential: string): Promise<AuthSession> {
  return request<AuthSession>("/api/auth/google", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ credential })
  });
}

export function deleteLogs(token: string): Promise<{ deleted: number }> {
  return request<{ deleted: number }>("/api/logs", {
    method: "DELETE",
    headers: authHeaders(token)
  });
}
