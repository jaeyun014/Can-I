import type { ConfidenceLevel, ConfidenceReport } from "@/lib/types";
import { ConfidenceDetailToggle } from "./ConfidenceDetailToggle";

type Props = {
  confidence?: ConfidenceReport;
};

const levelText: Record<ConfidenceLevel, string> = {
  HIGH: "높음",
  MEDIUM: "보통",
  LOW: "낮음",
};

const levelClass: Record<ConfidenceLevel, string> = {
  HIGH: "border-mint/30 bg-emerald-50 text-mint",
  MEDIUM: "border-amber-300 bg-amber-50 text-amber-800",
  LOW: "border-coral/30 bg-red-50 text-coral",
};

export function ConfidenceBadge({ confidence }: Props) {
  if (!confidence) {
    return null;
  }

  return (
    <div className={`rounded-md border p-3 ${levelClass[confidence.level]}`}>
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm font-black">
          신뢰도 {confidence.score}% · {levelText[confidence.level]}
        </p>
        <ConfidenceDetailToggle confidence={confidence} />
      </div>
      <p className="mt-2 text-sm font-semibold">{confidence.summary}</p>
    </div>
  );
}
