import type { AnalyzeResult, UsageLog } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
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

export function analyzeByImage(file: File, region: string): Promise<AnalyzeResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("region", region);

  return request<AnalyzeResult>("/api/analyze/image", {
    method: "POST",
    body: formData
  });
}

export function getLogs(): Promise<UsageLog[]> {
  return request<UsageLog[]>("/api/logs");
}

export function saveLog(result: AnalyzeResult): Promise<UsageLog> {
  return request<UsageLog>("/api/logs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      itemName: result.itemName,
      detectedMaterial: result.detectedMaterial,
      region: result.region,
      overallRisk: result.overallRisk
    })
  });
}
