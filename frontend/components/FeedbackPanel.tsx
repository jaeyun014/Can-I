"use client";

import { AlertCircle, CheckCircle2, MessageSquareWarning } from "lucide-react";
import { useState } from "react";

import { submitFeedback } from "@/lib/api";
import type { AnalyzeResult } from "@/lib/types";

type Props = {
  result: AnalyzeResult;
  token?: string | null;
};

const feedbackOptions = [
  ["wrong_object", "물건을 잘못 인식함"],
  ["wrong_material", "재질을 잘못 인식함"],
  ["missed_safety_label", "안전 표기를 놓침"],
  ["wrong_microwave", "전자레인지 판단이 틀림"],
  ["wrong_air_fryer", "에어프라이어 판단이 틀림"],
  ["wrong_oven", "오븐 판단이 틀림"],
  ["wrong_storage", "냉동 또는 냉장 판단이 틀림"],
  ["wrong_dishwasher", "식기세척기 판단이 틀림"],
  ["wrong_disposal", "분리수거 안내가 틀림"],
  ["wrong_food_waste", "음식물 또는 일반쓰레기 판단이 틀림"],
  ["other", "기타"],
];

export function FeedbackPanel({ result, token }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState(feedbackOptions[0][0]);
  const [objectName, setObjectName] = useState(result.itemName);
  const [material, setMaterial] = useState(result.detectedMaterial);
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    setIsSubmitting(true);
    setError("");
    setMessage("");
    try {
      await submitFeedback(
        {
          logId: result.logId,
          feedbackType,
          originalPrediction: {
            objectName: result.itemName,
            material: result.detectedMaterial,
            overallRisk: result.overallRisk,
          },
          userCorrection: {
            objectName,
            material,
          },
          comment,
        },
        token
      );
      setMessage("피드백이 검수 대기열에 등록되었습니다.");
      setIsOpen(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "피드백 저장에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="mt-5 rounded-md border border-stone-200 bg-white p-4">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="inline-flex h-10 items-center gap-2 rounded-md border border-stone-300 bg-white px-3 text-sm font-bold text-ink transition hover:border-coral hover:text-coral"
      >
        <MessageSquareWarning className="h-4 w-4" aria-hidden />
        잘못 인식했나요?
      </button>

      {isOpen ? (
        <div className="mt-4 grid gap-3">
          <label className="grid gap-1 text-sm font-semibold text-ink">
            오류 유형
            <select
              value={feedbackType}
              onChange={(event) => setFeedbackType(event.target.value)}
              className="h-10 rounded-md border border-stone-300 bg-white px-3 text-sm font-medium text-stone-700"
            >
              {feedbackOptions.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-1 text-sm font-semibold text-ink">
            올바른 물건명
            <input
              value={objectName}
              onChange={(event) => setObjectName(event.target.value)}
              className="h-10 rounded-md border border-stone-300 px-3 text-sm font-medium text-stone-700"
            />
          </label>

          <label className="grid gap-1 text-sm font-semibold text-ink">
            올바른 재질
            <input
              value={material}
              onChange={(event) => setMaterial(event.target.value)}
              className="h-10 rounded-md border border-stone-300 px-3 text-sm font-medium text-stone-700"
            />
          </label>

          <label className="grid gap-1 text-sm font-semibold text-ink">
            의견
            <textarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              className="min-h-20 rounded-md border border-stone-300 p-3 text-sm font-medium text-stone-700"
              placeholder="예: 종이컵인데 플라스틱으로 인식됐어요."
            />
          </label>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="inline-flex h-10 items-center justify-center rounded-md bg-ink px-4 text-sm font-bold text-white transition hover:bg-mint disabled:opacity-60"
          >
            피드백 보내기
          </button>
        </div>
      ) : null}

      {message ? (
        <p className="mt-3 flex items-center gap-2 text-sm font-semibold text-mint">
          <CheckCircle2 className="h-4 w-4" aria-hidden />
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="mt-3 flex items-center gap-2 text-sm font-semibold text-coral">
          <AlertCircle className="h-4 w-4" aria-hidden />
          {error}
        </p>
      ) : null}
    </section>
  );
}
