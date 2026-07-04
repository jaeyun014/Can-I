import type { RiskStatus } from "@/lib/types";

const styles: Record<RiskStatus, string> = {
  SAFE: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  WARNING: "bg-amber-100 text-amber-900 ring-amber-200",
  DANGER: "bg-red-100 text-red-800 ring-red-200"
};

const labels: Record<RiskStatus, string> = {
  SAFE: "안전",
  WARNING: "주의",
  DANGER: "위험"
};

export function RiskBadge({ status }: { status: RiskStatus }) {
  return (
    <span className={`inline-flex min-w-14 items-center justify-center rounded-full px-3 py-1 text-xs font-bold ring-1 ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}
