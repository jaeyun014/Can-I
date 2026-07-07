import type { AnalyzeResult } from "@/lib/types";
import { AnalysisEvidence } from "./AnalysisEvidence";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { FeedbackPanel } from "./FeedbackPanel";
import { InputQualityPanel } from "./InputQualityPanel";
import { RiskBadge } from "./RiskBadge";
import { RiskScenarioToggle } from "./RiskScenarioToggle";
import { WhyToggle } from "./WhyToggle";

const order = ["microwave", "airFryer", "oven", "freezer", "refrigerator", "dishwasher", "foodWaste", "generalWaste"];
const foodOrder = ["refrigerator", "freezer", "foodWaste", "generalWaste"];
const materialOrder = ["disposal", "microwave", "airFryer", "oven", "freezer", "dishwasher"];

export function ResultCard({
  result,
  token,
  onChooseTarget
}: {
  result: AnalyzeResult;
  token?: string | null;
  onChooseTarget?: (targetType: "FOOD" | "MATERIAL_OBJECT") => void;
}) {
  if (result.targetType === "AMBIGUOUS") {
    return <TargetChoiceCard result={result} onChooseTarget={onChooseTarget} />;
  }
  if (result.targetType === "UNKNOWN") {
    return <UnknownResultCard result={result} />;
  }

  const baseOrder = result.targetType === "FOOD" ? foodOrder : result.targetType === "MATERIAL_OBJECT" ? materialOrder : order;
  const displayOrder = [...baseOrder, ...Object.keys(result.decisions).filter((key) => !baseOrder.includes(key))];
  const captureRequest = result.additionalCaptureRequest as
    | { required?: boolean; instructions?: string[] }
    | undefined;

  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 border-b border-stone-200 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-stone-500">분석 결과</p>
          <h2 className="mt-1 text-2xl font-bold text-ink">{result.itemName}</h2>
          {result.summary ? <p className="mt-2 text-sm font-semibold text-stone-700">{result.summary}</p> : null}
          <p className="mt-2 text-sm text-stone-600">
            대상: <span className="font-semibold">{result.targetType === "FOOD" ? "음식" : "용기/재질"}</span>
            {result.targetType === "MATERIAL_OBJECT" ? (
              <>
                {" "}· 감지 재질: <span className="font-semibold">{result.detectedMaterial}</span>
                {result.materialCode ? <span> · 재질 코드: {result.materialCode}</span> : null}
                {result.contaminationLevel ? <span> · 오염도: {contaminationLabel(result.contaminationLevel)}</span> : null}
              </>
            ) : null}
            {result.objectType ? <span> · 유형: {result.objectType}</span> : null}
            {result.ocrText ? <span> · OCR: {result.ocrText}</span> : null}
          </p>
        </div>
        <RiskBadge status={result.overallRisk} />
      </div>

      <div className="mt-4">
        <ConfidenceBadge confidence={result.confidence} />
      </div>

      {result.targetType === "MATERIAL_OBJECT" ? (
        <button
          type="button"
          onClick={() => onChooseTarget?.("FOOD")}
          className="mt-4 w-full rounded-md border border-stone-300 bg-white px-4 py-3 text-sm font-bold text-ink transition hover:border-mint hover:text-mint"
        >
          이 안에 든 음식물 정보가 궁금하신가요?
        </button>
      ) : null}

      {captureRequest?.required && captureRequest.instructions?.length ? (
        <div className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
          <p className="font-bold text-ink">추가 촬영 안내</p>
          <ul className="mt-2 grid gap-1">
            {captureRequest.instructions.map((instruction) => (
              <li key={instruction}>- {instruction}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-5 grid gap-4">
        {displayOrder.filter((key) => result.decisions[key]).map((key) => {
          const decision = result.decisions[key];
          return (
            <article key={key} className="rounded-md border border-stone-200 bg-stone-50 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="font-bold text-ink">{decision.label}</h3>
                  <p className="mt-1 text-sm font-semibold text-stone-700">
                    {key === "disposal" ? (decision.allowed ? "분리배출 가능" : "일반쓰레기 권장") : decision.allowed ? "사용 가능" : "사용 불가"}
                  </p>
                  {decision.category ? <p className="mt-1 text-xs font-semibold text-mint">{decision.category}</p> : null}
                </div>
                <RiskBadge status={decision.status} />
              </div>
              <div className="mt-4 grid gap-3 text-sm leading-6 text-stone-700">
                <p>
                  <span className="font-semibold text-ink">이유: </span>
                  {decision.reason}
                </p>
                <WhyToggle status={decision.status} why={decision.why} />
                <RiskScenarioToggle decision={decision} />
                {decision.instruction ? (
                  <p>
                    <span className="font-semibold text-ink">배출 방법: </span>
                    {decision.instruction}
                  </p>
                ) : null}
                {key === "disposal" && result.disposal.regionRule ? (
                  <p>
                    <span className="font-semibold text-ink">지역 안내: </span>
                    {result.disposal.regionRule}
                  </p>
                ) : null}
                <p>
                  <span className="font-semibold text-ink">대체 행동: </span>
                  {decision.alternative}
                </p>
              </div>
            </article>
          );
        })}
      </div>

      <AnalysisEvidence evidence={result.evidence} confidence={result.confidence} objectType={result.objectType} />

      <InputQualityPanel result={result} />

      <FeedbackPanel result={result} token={token} />
    </section>
  );
}

function TargetChoiceCard({
  result,
  onChooseTarget
}: {
  result: AnalyzeResult;
  onChooseTarget?: (targetType: "FOOD" | "MATERIAL_OBJECT") => void;
}) {
  return (
    <section className="rounded-lg border border-amber-300 bg-white p-5 shadow-sm">
      <p className="text-sm font-bold text-amber-700">판단 대상 선택</p>
      <h2 className="mt-2 text-2xl font-bold text-ink">{result.itemName || "음식과 용기"}</h2>
      <p className="mt-3 text-sm leading-6 text-stone-700">
        {result.message || "음식과 용기가 함께 인식되었습니다. 무엇을 판단할까요?"}
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => onChooseTarget?.("MATERIAL_OBJECT")}
          className="h-12 rounded-md bg-ink px-4 text-sm font-bold text-white transition hover:bg-mint"
        >
          분리수거/용기 판단
        </button>
        <button
          type="button"
          onClick={() => onChooseTarget?.("FOOD")}
          className="h-12 rounded-md border border-stone-300 bg-white px-4 text-sm font-bold text-ink transition hover:border-mint hover:text-mint"
        >
          음식 보관/음식물 판단
        </button>
      </div>
    </section>
  );
}

function contaminationLabel(level: string) {
  if (level === "CLEAN") {
    return "깨끗함";
  }
  if (level === "LIGHT_CONTAMINATION") {
    return "가벼운 오염";
  }
  if (level === "HEAVY_CONTAMINATION") {
    return "심한 오염";
  }
  return "확인 필요";
}

function UnknownResultCard({ result }: { result: AnalyzeResult }) {
  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-bold text-stone-500">분류 필요</p>
      <h2 className="mt-2 text-2xl font-bold text-ink">{result.itemName || "알 수 없는 대상"}</h2>
      <p className="mt-3 text-sm leading-6 text-stone-700">
        {result.message || "대상을 음식 또는 용기/재질로 분류할 수 없습니다. 사진이나 설명을 더 구체적으로 입력해 주세요."}
      </p>
    </section>
  );
}
