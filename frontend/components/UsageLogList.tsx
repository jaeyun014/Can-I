import type { UsageLog } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";

type Props = {
  logs: UsageLog[];
  isLoggedIn?: boolean;
  onDeleteAll?: () => void;
  onOpenResult?: (result: UsageLog["analysisResult"]) => void;
};

export function UsageLogList({ logs, isLoggedIn, onDeleteAll, onOpenResult }: Props) {
  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-ink">{isLoggedIn ? "내 검색 기록" : "최근 사용 로그"}</h2>
          <p className="mt-1 text-xs text-stone-500">
            {isLoggedIn ? "로그인한 계정에 저장된 기록입니다." : "로그인하면 계정별 기록을 저장할 수 있습니다."}
          </p>
        </div>
        {isLoggedIn && logs.length > 0 && onDeleteAll ? (
          <button
            type="button"
            onClick={onDeleteAll}
            className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-bold text-red-700 hover:bg-red-100"
          >
            내역 삭제
          </button>
        ) : null}
      </div>
      {logs.length === 0 ? (
        <p className="mt-4 text-sm text-stone-500">아직 저장된 분석 기록이 없습니다.</p>
      ) : (
        <ul className="mt-4 divide-y divide-stone-200">
          {logs.map((log) => (
            <li key={log.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
              <div>
                <button
                  type="button"
                  onClick={() => log.analysisResult && onOpenResult?.(log.analysisResult)}
                  disabled={!log.analysisResult}
                  className="text-left font-semibold text-ink transition enabled:hover:text-mint disabled:cursor-default"
                >
                  {log.itemName}
                </button>
                <p className="mt-1 text-xs text-stone-500">
                  {log.targetType} · {log.region} · {new Date(log.createdAt).toLocaleString("ko-KR")}
                </p>
              </div>
              <RiskBadge status={log.overallRisk} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
