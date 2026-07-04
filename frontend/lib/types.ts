export type RiskStatus = "SAFE" | "WARNING" | "DANGER";

export type Decision = {
  status: RiskStatus;
  label: string;
  allowed: boolean;
  reason: string;
  why: string;
  alternative: string;
};

export type Disposal = {
  category: string;
  regionRule: string;
  instruction: string;
};

export type Evidence = {
  vision: string;
  ocr: string;
  rule: string;
};

export type AnalyzeResult = {
  itemName: string;
  detectedMaterial: string;
  objectType?: string;
  ocrText: string;
  region: string;
  confidence?: number;
  evidence?: Evidence;
  overallRisk: RiskStatus;
  decisions: Record<string, Decision>;
  disposal: Disposal;
};

export type UsageLog = {
  id: number;
  itemName: string;
  detectedMaterial: string;
  region: string;
  overallRisk: RiskStatus;
  createdAt: string;
};
