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

export type AnalyzeResult = {
  itemName: string;
  detectedMaterial: string;
  ocrText: string;
  region: string;
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
