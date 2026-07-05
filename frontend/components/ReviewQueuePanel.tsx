"use client";

import { ClipboardCheck, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { getReviewQueue, updateReviewQueueStatus } from "@/lib/api";
import type { ReviewQueueItem } from "@/lib/types";

type Props = {
  token?: string | null;
};

const statusLabels: Record<string, string> = {
  pending: "대기",
  approved: "승인",
  rejected: "거절",
  duplicate: "중복",
  needs_more_information: "추가 정보 필요",
};

export function ReviewQueuePanel({ token }: Props) {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [error, setError] = useState("");

  async function load() {
    if (!token) {
      setItems([]);
      return;
    }
    try {
      setItems(await getReviewQueue(token));
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "검수 큐를 불러오지 못했습니다.");
    }
  }

  async function updateStatus(id: number, status: string) {
    if (!token) {
      return;
    }
    await updateReviewQueueStatus(id, status, token);
    await load();
  }

  useEffect(() => {
    load();
  }, [token]);

  if (!token) {
    return null;
  }

  return (
    <section className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ClipboardCheck className="h-4 w-4 text-mint" aria-hidden />
          <h2 className="font-bold text-ink">검수 대기열</h2>
        </div>
        <button
          type="button"
          onClick={load}
          className="inline-flex h-8 items-center gap-1 rounded-md border border-stone-300 px-2 text-xs font-bold text-stone-700 hover:bg-stone-50"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden />
          새로고침
        </button>
      </div>

      {error ? <p className="mt-3 text-sm text-coral">{error}</p> : null}

      <div className="mt-3 grid gap-2">
        {items.length ? (
          items.map((item) => (
            <article key={item.id} className="rounded-md border border-stone-200 bg-stone-50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-bold text-ink">{item.itemName}</p>
                  <p className="text-xs text-stone-500">
                    재질 {item.detectedMaterial} · 위험도 {item.overallRisk} · 우선순위 {Math.round(item.reviewScore * 100)}
                  </p>
                </div>
                <span className="rounded-full bg-white px-2 py-1 text-xs font-bold text-stone-600">
                  {statusLabels[item.status] ?? item.status}
                </span>
              </div>
              <p className="mt-2 text-xs leading-5 text-stone-600">사유: {item.reasons.join(", ")}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {["approved", "rejected", "needs_more_information", "duplicate"].map((status) => (
                  <button
                    key={status}
                    type="button"
                    onClick={() => updateStatus(item.id, status)}
                    className="rounded-md border border-stone-300 bg-white px-2 py-1 text-xs font-bold text-stone-700 hover:border-mint hover:text-mint"
                  >
                    {statusLabels[status]}
                  </button>
                ))}
              </div>
            </article>
          ))
        ) : (
          <p className="text-sm text-stone-500">현재 검수 대기 항목이 없습니다.</p>
        )}
      </div>
    </section>
  );
}
