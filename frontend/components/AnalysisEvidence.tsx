import type { ConfidenceReport, Evidence } from "@/lib/types";

type Props = {
  evidence?: Evidence;
  confidence?: ConfidenceReport;
  objectType?: string;
};

export function AnalysisEvidence({ evidence, confidence, objectType }: Props) {
  const hasEvidence = evidence?.vision || evidence?.ocr || evidence?.rule || objectType || (confidence?.score ?? 0) > 0;

  if (!hasEvidence) {
    return null;
  }

  return (
    <section className="mt-5 rounded-md border border-stone-200 bg-white p-4">
      <h3 className="font-bold text-ink">분석 근거</h3>
      <div className="mt-3 grid gap-2 text-sm leading-6 text-stone-700">
        {objectType ? <p>물체 유형: {objectType}</p> : null}
        {(confidence?.score ?? 0) > 0 ? <p>판단 신뢰도: {confidence?.score}%</p> : null}
        {evidence?.vision ? <p>Vision: {evidence.vision}</p> : null}
        {evidence?.ocr ? <p>OCR: {evidence.ocr}</p> : null}
        {evidence?.rule ? <p>Rule Engine: {evidence.rule}</p> : null}
      </div>
    </section>
  );
}
