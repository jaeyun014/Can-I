# Can I?

AI 기반 생활 안전 도우미 서비스의 MVP입니다. 현재 단계에서는 모바일 촬영 중심 UI, OCR, GPT Vision 보조 분석, JSON Rule Engine, 메모리 사용 로그, Next.js UI를 구현합니다.

## 구조

```txt
backend/   FastAPI, Rule Engine, JSON rules, logs API
frontend/  Next.js 15, React, TypeScript, Tailwind CSS
```

## Backend 실행

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

확인:

```bash
curl http://localhost:8000/health
```

주요 API:

```bash
POST /api/analyze
POST /api/analyze/image
POST /api/logs
GET  /api/logs
```

백엔드 환경변수 예시:

```bash
OPENAI_API_KEY=
VISION_MODEL=gpt-4o-mini
OCR_ENGINE=tesseract
```

`OPENAI_API_KEY`가 없으면 GPT Vision 호출은 fallback stub로 동작하며 서버는 죽지 않습니다. OCR은 Tesseract를 사용하도록 구성되어 있고, 로컬에 Tesseract 실행 파일이 없으면 빈 OCR 결과로 안전하게 fallback합니다.

## Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

환경변수 예시:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

브라우저에서 `http://localhost:3000`을 열면 됩니다.

## 쉬운 개발 서버 명령어

프로젝트 루트에서 프론트엔드와 백엔드를 같이 켜고 끌 수 있습니다.

```bash
make dev      # 백엔드 8000 + 프론트엔드 3000 동시 실행
make stop     # 둘 다 종료
make restart  # 둘 다 재시작
make status   # 현재 상태 확인
make logs     # 최근 로그 확인
```

`make dev`는 프론트 스타일 캐시 문제를 줄이기 위해 `frontend/.next`를 지운 뒤 dev 서버를 시작합니다.

## 현재 지원 항목

- 알루미늄 포일
- 플라스틱 배달 용기
- 종이컵
- 유리 밀폐용기
- 보조배터리
- 나무젓가락
- PET/PS 재질 기본 룰

## 구현 메모

- 안전 판단은 `backend/app/services/rule_engine.py`가 수행합니다.
- 규칙 데이터는 `backend/app/data/material_rules.json`과 `backend/app/data/region_rules.json`에 있습니다.
- 이미지 분석은 `backend/app/services/vision_service.py`에서 GPT Vision을 보조 분석으로 사용합니다.
- OCR은 `backend/app/services/ocr_service.py`에서 Tesseract를 사용해 PP, PET, PS, microwave safe 같은 표기를 추출합니다.
- `backend/app/services/input_normalizer.py`가 OCR과 Vision 결과를 Rule Engine 입력으로 통합합니다.
- 사용 로그는 현재 메모리 배열에 저장하며, `backend/app/db/` 폴더는 PostgreSQL/SQLAlchemy 전환을 위한 자리입니다.
