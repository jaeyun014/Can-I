import type { AnalyzeResult } from "@/lib/types";
import { AnalysisEvidence } from "./AnalysisEvidence";
import { RiskBadge } from "./RiskBadge";
import { WhyToggle } from "./WhyToggle";

const order = ["microwave", "airFryer", "oven", "freezer", "refrigerator", "dishwasher", "foodWaste", "generalWaste"];

export function ResultCard({ result }: { result: AnalyzeResult }) {
  const displayOrder = [...order, ...Object.keys(result.decisions).filter((key) => !order.includes(key))];

  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 border-b border-stone-200 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-stone-500">분석 결과</p>
          <h2 className="mt-1 text-2xl font-bold text-ink">{result.itemName}</h2>
          <p className="mt-2 text-sm text-stone-600">
            감지 재질: <span className="font-semibold">{result.detectedMaterial}</span>
            {result.objectType ? <span> · 유형: {result.objectType}</span> : null}
            {result.ocrText ? <span> · OCR: {result.ocrText}</span> : null}
          </p>
        </div>
        <RiskBadge status={result.overallRisk} />
      </div>

      <div className="mt-5 grid gap-4">
        {displayOrder.filter((key) => result.decisions[key]).map((key) => {
          const decision = result.decisions[key];
          return (
            <article key={key} className="rounded-md border border-stone-200 bg-stone-50 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="font-bold text-ink">{decision.label}</h3>
                  <p className="mt-1 text-sm font-semibold text-stone-700">{decision.allowed ? "사용 가능" : "사용 불가"}</p>
                </div>
                <RiskBadge status={decision.status} />
              </div>
              <div className="mt-4 grid gap-3 text-sm leading-6 text-stone-700">
                <p>
                  <span className="font-semibold text-ink">이유: </span>
                  {decision.reason}
                </p>
                <WhyToggle status={decision.status} why={decision.why} />
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

      <div className="mt-5 rounded-md border border-mint/20 bg-emerald-50 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-bold text-ink">분리수거</h3>
          <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-mint ring-1 ring-mint/20">{result.disposal.category}</span>
        </div>
        <p className="mt-3 text-sm leading-6 text-stone-700">{result.disposal.regionRule}</p>
        <p className="mt-2 text-sm leading-6 text-stone-700">{result.disposal.instruction}</p>
      </div>
    </section>
  );
}
