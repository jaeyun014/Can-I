"use client";

import { AlertCircle, Camera, Loader2, Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { ImageUpload } from "@/components/ImageUpload";
import { RegionSelect } from "@/components/RegionSelect";
import { ResultCard } from "@/components/ResultCard";
import { TextQueryForm } from "@/components/TextQueryForm";
import { UsageLogList } from "@/components/UsageLogList";
import { analyzeByImage, analyzeByText, getLogs, saveLog } from "@/lib/api";
import type { AnalyzeResult, UsageLog } from "@/lib/types";

export default function Home() {
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("서울");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [logs, setLogs] = useState<UsageLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getLogs().then(setLogs).catch(() => setLogs([]));
  }, []);

  function analyzeImage(fileToAnalyze: File) {
    return analyzeByImage(fileToAnalyze, region);
  }

  async function handleAnalyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!file && !query.trim()) {
      setError("사진을 선택하거나 물건 이름을 입력해 주세요.");
      return;
    }

    setIsLoading(true);
    try {
      const analyzed = file ? await analyzeImage(file) : await analyzeByText(query.trim(), region);
      setResult(analyzed);
      await saveLog(analyzed);
      setLogs(await getLogs());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <section className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
          <div className="space-y-6">
            <div>
              <p className="text-sm font-bold uppercase tracking-wide text-mint">Can I?</p>
              <h1 className="mt-3 text-4xl font-black leading-tight text-ink sm:text-5xl">이거 해도 돼?</h1>
              <p className="mt-4 text-xl font-semibold text-stone-700">사진 한 장으로 생활 속 안전 판단을 도와드립니다.</p>
              <p className="mt-3 max-w-2xl text-base leading-7 text-stone-600">
                전자레인지, 에어프라이어, 냉동보관, 식기세척기, 분리수거까지 한 번에 확인하세요.
              </p>
            </div>

            <form onSubmit={handleAnalyze} className="rounded-lg border border-stone-200 bg-white/90 p-5 shadow-sm backdrop-blur">
              <div className="grid gap-5">
                <ImageUpload file={file} onChange={setFile} />
                <TextQueryForm value={query} onChange={setQuery} />
                <RegionSelect value={region} onChange={setRegion} />
                {error ? (
                  <div className="flex items-start gap-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                    {error}
                  </div>
                ) : null}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-ink px-5 text-base font-bold text-white transition hover:bg-mint disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isLoading ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> : file ? <Camera className="h-5 w-5" aria-hidden /> : <Search className="h-5 w-5" aria-hidden />}
                  분석하기
                </button>
              </div>
            </form>

            <UsageLogList logs={logs} />
          </div>

          <div className="lg:sticky lg:top-8">
            {result ? (
              <ResultCard result={result} />
            ) : (
              <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold text-ink">시연 예시</h2>
                <div className="mt-4 grid gap-3 text-sm leading-6 text-stone-700">
                  <p>알루미늄 포일을 입력하면 전자레인지 위험, 에어프라이어 주의, 오븐 사용 가능 여부를 확인할 수 있습니다.</p>
                  <p>사진을 선택하면 현재 MVP에서는 플라스틱 배달 용기 stub 결과로 분석됩니다.</p>
                </div>
              </section>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
