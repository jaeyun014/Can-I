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

export type ConfidenceLevel = "LOW" | "MEDIUM" | "HIGH";

export type ConfidenceFactor = {
  label: string;
  score: number;
  reason: string;
};

export type ConfidenceReport = {
  score: number;
  level: ConfidenceLevel;
  summary: string;
  factors: ConfidenceFactor[];
  penalties: ConfidenceFactor[];
  calculation: string;
  lowConfidenceReasons: string[];
  priority: string[];
  conflictDetected: boolean;
};

export type DetectedObject = {
  id: string;
  name: string;
  objectType?: string;
  material?: string;
  confidence?: number;
  classifierPredictions?: unknown[];
};

export type ImageQualityImage = {
  role: string;
  label: string;
  isAcceptable?: boolean;
  issues?: string[];
  captureAdvice?: string[];
  blurScore?: number;
  brightnessScore?: number;
};

export type ImageQuality = {
  isAcceptable?: boolean;
  issues?: string[];
  captureAdvice?: string[];
  recommendedShots?: string[];
  images?: ImageQualityImage[];
};

export type AdditionalCaptureRequest = {
  required?: boolean;
  instructions?: string[];
  recommendedShots?: string[];
};

export type AnalyzeResult = {
  logId?: number | null;
  itemName: string;
  detectedMaterial: string;
  objectType?: string;
  ocrText: string;
  region: string;
  confidence?: ConfidenceReport;
  evidence?: Evidence;
  overallRisk: RiskStatus;
  decisions: Record<string, Decision>;
  disposal: Disposal;
  imageQuality?: ImageQuality;
  detectedObjects?: DetectedObject[];
  normalized?: Record<string, unknown>;
  additionalCaptureRequest?: AdditionalCaptureRequest;
  versions?: Record<string, string>;
};

export type FeedbackPayload = {
  logId?: number | null;
  feedbackType: string;
  originalPrediction: Record<string, unknown>;
  userCorrection: Record<string, unknown>;
  comment: string;
};

export type FeedbackRecord = FeedbackPayload & {
  id: number;
  userEmail?: string | null;
  reviewStatus: string;
  createdAt: string;
  updatedAt: string;
};

export type ReviewQueueItem = {
  id: number;
  usageLogId: number;
  reviewScore: number;
  reasons: string[];
  status: string;
  assignedTo?: string | null;
  itemName: string;
  detectedMaterial: string;
  overallRisk: string;
  createdAt: string;
  updatedAt: string;
};

export type UsageLog = {
  id: number;
  itemName: string;
  detectedMaterial: string;
  region: string;
  overallRisk: RiskStatus;
  createdAt: string;
  userEmail?: string | null;
};

export type AuthUser = {
  email: string;
  name: string;
  picture: string;
};

export type AuthSession = {
  token: string;
  user: AuthUser;
};
