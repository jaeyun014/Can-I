"use client";

import { AlertCircle, Camera, Loader2, Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { GoogleLoginButton } from "@/components/GoogleLoginButton";
import { ImageUpload } from "@/components/ImageUpload";
import { RegionSelect } from "@/components/RegionSelect";
import { ResultCard } from "@/components/ResultCard";
import { TextQueryForm } from "@/components/TextQueryForm";
import { UsageLogList } from "@/components/UsageLogList";
import { analyzeByImage, analyzeByText, deleteLogs, getLogs, saveLog } from "@/lib/api";
import type { AnalyzeResult, AuthSession, UsageLog } from "@/lib/types";

const SESSION_STORAGE_KEY = "can-i-auth-session";

export default function Home() {
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("서울특별시 강남구");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [logs, setLogs] = useState<UsageLog[]>([]);
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const savedSession = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (savedSession) {
      try {
        setSession(JSON.parse(savedSession) as AuthSession);
      } catch {
        window.localStorage.removeItem(SESSION_STORAGE_KEY);
      }
    }
  }, []);

  useEffect(() => {
    getLogs(session?.token).then(setLogs).catch(() => setLogs([]));
  }, [session?.token]);

  function analyzeImage(fileToAnalyze: File) {
    return analyzeByImage(fileToAnalyze, region, session?.token);
  }

  function handleLogin(nextSession: AuthSession) {
    setSession(nextSession);
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
  }

  function handleLogout() {
    setSession(null);
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    setLogs([]);
  }

  async function handleDeleteLogs() {
    if (!session) {
      return;
    }
    await deleteLogs(session.token);
    setLogs([]);
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
      if (!file) {
        await saveLog(analyzed, session?.token);
      }
      setLogs(await getLogs(session?.token));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-md md:max-w-6xl">
        <section className="grid gap-6 md:grid-cols-2 md:items-start lg:gap-8">
          <div className="space-y-6">
            <div className="pt-2">
              <p className="text-2xl font-black text-ink">Can I?</p>
              <h1 className="mt-4 text-4xl font-black leading-tight text-ink sm:text-5xl">이거 해도 돼?</h1>
              <p className="mt-4 text-lg font-semibold text-stone-700">사진 한 장으로 생활 속 안전 판단을 도와드립니다.</p>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-600 sm:text-base sm:leading-7">
                전자레인지, 에어프라이어, 냉동보관, 식기세척기, 분리수거까지 한 번에 확인하세요.
              </p>
            </div>

            <GoogleLoginButton session={session} onLogin={handleLogin} onLogout={handleLogout} />

            <form onSubmit={handleAnalyze} className="rounded-lg border border-stone-200 bg-white/90 p-5 shadow-sm backdrop-blur">
              <div className="grid gap-5">
                <ImageUpload file={file} onChange={setFile} />
                <RegionSelect value={region} onChange={setRegion} />
                <TextQueryForm value={query} onChange={setQuery} />
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

            <UsageLogList logs={logs} isLoggedIn={Boolean(session)} onDeleteAll={handleDeleteLogs} />
          </div>

          <div className="md:sticky md:top-6">
            {result ? (
              <ResultCard result={result} />
            ) : (
              <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold text-ink">사진을 찍으면 바로 판단합니다</h2>
                <div className="mt-4 grid gap-3 text-sm leading-6 text-stone-700">
                  <p>왼쪽에서 사진 촬영 또는 파일 선택 후 분석하면 OCR, Vision 근거와 Rule Engine 결과가 이 영역에 표시됩니다.</p>
                  <p>OpenAI API Key가 없으면 fallback 분석으로 서비스 흐름을 유지합니다.</p>
                </div>
              </section>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
