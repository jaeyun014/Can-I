import type { ConfidenceReport } from "@/lib/types";

type Props = {
  confidence: ConfidenceReport;
};

export function ConfidenceBreakdown({ confidence }: Props) {
  return (
    <div className="mt-3 rounded-md border border-stone-200 bg-white p-4 text-sm leading-6 text-stone-700">
      <h3 className="font-bold text-ink">신뢰도 계산</h3>

      <div className="mt-3 grid gap-2">
        {confidence.factors.map((factor) => (
          <p key={`${factor.label}-${factor.score}`}>
            <span className="font-bold text-mint">+{factor.score}</span> {factor.label}
            <span className="block text-xs text-stone-500">{factor.reason}</span>
          </p>
        ))}
        {confidence.penalties.map((penalty) => (
          <p key={`${penalty.label}-${penalty.score}`}>
            <span className="font-bold text-coral">{penalty.score}</span> {penalty.label}
            <span className="block text-xs text-stone-500">{penalty.reason}</span>
          </p>
        ))}
      </div>

      <div className="mt-4 rounded-md bg-stone-50 p-3">
        <p className="font-semibold text-ink">계산식</p>
        <p className="mt-1">{confidence.calculation}</p>
      </div>

      {confidence.lowConfidenceReasons.length ? (
        <div className="mt-4">
          <p className="font-semibold text-ink">신뢰도가 낮은 이유</p>
          <ul className="mt-2 grid gap-1">
            {confidence.lowConfidenceReasons.map((reason) => (
              <li key={reason}>- {reason}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-4">
        <p className="font-semibold text-ink">판단 우선순위</p>
        <ol className="mt-2 grid gap-1">
          {confidence.priority.map((item, index) => (
            <li key={item}>
              {index + 1}. {item}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
