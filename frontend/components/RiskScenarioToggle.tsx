"use client";

import { AlertTriangle, ChevronDown } from "lucide-react";
import { useState } from "react";

import type { Decision, RiskStatus } from "@/lib/types";

type Props = {
  decision: Decision;
};

function getScenario(decision: Decision) {
  const label = decision.label;
  const statusText = decision.status === "DANGER" ? "위험 단계" : "주의 단계";

  if (label.includes("냉장")) {
    return "냉장고에 오래 두면 세균이 계속 번식할 수 있어 배탈이나 식중독으로 이어질 수 있습니다. 냄새, 점액, 곰팡이, 색 변화가 보이면 먹지 않는 편이 안전합니다.";
  }

  if (label.includes("냉동")) {
    return "냉동 중에도 품질 저하는 생길 수 있고, 해동과 재냉동을 반복하면 세균 증식 가능성이 커질 수 있습니다. 1회분씩 소분하고 해동 후에는 빨리 먹는 편이 좋습니다.";
  }

  if (label.includes("전자레인지")) {
    return "전자레인지에 맞지 않는 재질은 스파크, 변형, 녹음, 유해 물질 발생으로 이어질 수 있습니다. 특히 금속, 얇은 플라스틱, 코팅 종이는 사고가 자주 나는 편입니다.";
  }

  if (label.includes("에어프라이어")) {
    return "고온 열풍 때문에 가벼운 포장재가 열선 쪽으로 날리거나, 플라스틱과 종이가 녹거나 그을릴 수 있습니다. 음식만 내열 용기에 옮겨 조리하는 편이 안전합니다.";
  }

  if (label.includes("오븐")) {
    return "오븐은 고온이 오래 유지되어 내열 표시가 없는 플라스틱, 종이, 일반 유리는 녹거나 깨지거나 탈 수 있습니다. 예열된 오븐에 차가운 유리를 바로 넣는 것도 파손 위험이 있습니다.";
  }

  if (label.includes("식기세척기")) {
    return "고온수와 건조 열 때문에 얇은 플라스틱은 휘고, 나무는 갈라지고, 종이는 분해될 수 있습니다. 작은 조각이 필터를 막는 일도 생길 수 있습니다.";
  }

  if (label.includes("음식물")) {
    return "음식물쓰레기로 맞지 않는 뼈, 껍데기, 큰 씨앗이 섞이면 처리 설비에 부담이 되고 수거 과정에서 문제가 생길 수 있습니다. 단단한 부산물은 따로 확인하는 편이 좋습니다.";
  }

  if (label.includes("일반쓰레기")) {
    return "일반쓰레기로 버려야 할 것과 재활용 또는 음식물쓰레기를 섞으면 수거 거부나 오염 문제가 생길 수 있습니다. 음식물, 포장재, 딱딱한 부산물을 분리해 확인하세요.";
  }

  return `${statusText}에서는 비슷한 상황에서 ${decision.reason} 같은 문제가 실제로 생길 수 있습니다. 확실하지 않다면 제품 표기와 지역 배출 기준을 먼저 확인하는 편이 안전합니다.`;
}

export function RiskScenarioToggle({ decision }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const status: RiskStatus = decision.status;

  if (status === "SAFE") {
    return null;
  }

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="inline-flex h-9 items-center gap-2 rounded-md border border-coral/40 bg-white px-3 text-sm font-bold text-coral transition hover:bg-red-50"
        aria-expanded={isOpen}
      >
        <AlertTriangle className="h-4 w-4" aria-hidden />
        이럴 수도 있어!
        <ChevronDown className={`h-4 w-4 transition ${isOpen ? "rotate-180" : ""}`} aria-hidden />
      </button>
      {isOpen ? (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm leading-6 text-stone-800">
          {getScenario(decision)}
        </div>
      ) : null}
    </div>
  );
}
