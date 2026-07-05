"use client";

import { Info } from "lucide-react";
import { useState } from "react";

import type { ConfidenceReport } from "@/lib/types";
import { ConfidenceBreakdown } from "./ConfidenceBreakdown";

type Props = {
  confidence: ConfidenceReport;
};

export function ConfidenceDetailToggle({ confidence }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="w-full sm:w-auto">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-current bg-white/70 transition hover:bg-white"
        aria-label="신뢰도 계산 상세 보기"
        aria-expanded={isOpen}
      >
        <Info className="h-4 w-4" aria-hidden />
      </button>
      {isOpen ? <ConfidenceBreakdown confidence={confidence} /> : null}
    </div>
  );
}
