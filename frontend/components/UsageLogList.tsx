import type { UsageLog } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";

export function UsageLogList({ logs }: { logs: UsageLog[] }) {
  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink">최근 사용 로그</h2>
      {logs.length === 0 ? (
        <p className="mt-4 text-sm text-stone-500">아직 저장된 분석 기록이 없습니다.</p>
      ) : (
        <ul className="mt-4 divide-y divide-stone-200">
          {logs.map((log) => (
            <li key={log.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
              <div>
                <p className="font-semibold text-ink">{log.itemName}</p>
                <p className="mt-1 text-xs text-stone-500">
                  {log.region} · {new Date(log.createdAt).toLocaleString("ko-KR")}
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
