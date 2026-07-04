"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";

import type { RiskStatus } from "@/lib/types";

type Props = {
  status: RiskStatus;
  why: string;
};

export function WhyToggle({ status, why }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  if (status === "SAFE") {
    return null;
  }

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="inline-flex h-9 items-center gap-2 rounded-md border border-stone-300 bg-white px-3 text-sm font-bold text-ink transition hover:border-coral hover:text-coral"
        aria-expanded={isOpen}
      >
        왜 안돼?
        <ChevronDown className={`h-4 w-4 transition ${isOpen ? "rotate-180" : ""}`} aria-hidden />
      </button>
      {isOpen ? (
        <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm leading-6 text-stone-800">
          {why}
        </div>
      ) : null}
    </div>
  );
}
