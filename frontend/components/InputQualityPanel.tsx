import type { AnalyzeResult } from "@/lib/types";

export function InputQualityPanel({ result }: { result: AnalyzeResult }) {
  const detectedObjects = result.detectedObjects ?? [];
  const imageQuality = result.imageQuality;
  const normalized = result.normalized ?? {};

  if (!detectedObjects.length && !imageQuality?.images?.length && !Object.keys(normalized).length) {
    return null;
  }

  return (
    <section className="mt-5 rounded-md border border-stone-200 bg-white p-4">
      <h3 className="font-bold text-ink">입력 품질 및 물체 구조</h3>

      {imageQuality?.images?.length ? (
        <div className="mt-3 grid gap-2 text-sm leading-6 text-stone-700">
          {imageQuality.images.map((image) => (
            <div key={`${image.role}-${image.label}`} className="rounded-md bg-stone-50 p-3">
              <p className="font-semibold text-ink">{image.label}</p>
              <p>품질: {image.isAcceptable ? "확인 가능" : "다시 촬영 권장"}</p>
              {image.issues?.length ? <p className="text-stone-500">이슈: {image.issues.join(", ")}</p> : null}
            </div>
          ))}
        </div>
      ) : null}

      {detectedObjects.length ? (
        <div className="mt-4 grid gap-2 text-sm leading-6 text-stone-700">
          <p className="font-semibold text-ink">감지 물체</p>
          {detectedObjects.map((object) => (
            <div key={object.id} className="rounded-md bg-stone-50 p-3">
              <p>
                {object.id === "body" ? "본체" : object.id === "lid" ? "뚜껑" : object.id}: {object.name}
              </p>
              <p className="text-stone-500">
                재질: {object.material || "unknown"} · 유형: {object.objectType || "unknown"}
              </p>
            </div>
          ))}
        </div>
      ) : null}

      {Object.keys(normalized).length ? (
        <div className="mt-4 rounded-md bg-emerald-50 p-3 text-sm leading-6 text-stone-700">
          <p className="font-semibold text-ink">정규화 결과</p>
          <p>본체 재질: {String(normalized.bodyMaterial || normalized.material || "unknown")}</p>
          <p>뚜껑 재질: {String(normalized.lidMaterial || "unknown")}</p>
          <p>금속 포함: {normalized.containsMetal ? "가능성 있음" : "확인되지 않음"}</p>
          <p>음식 포함: {normalized.containsFood ? "가능성 있음" : "확인되지 않음"}</p>
        </div>
      ) : null}
    </section>
  );
}
