# Can I?

AI 기반 생활 안전 도우미 서비스의 초기 MVP입니다. 현재 단계에서는 실제 AI/OCR 연동 전까지의 전체 구조, FastAPI API, JSON Rule Engine, 메모리 사용 로그, Next.js UI를 구현합니다.

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
- 이미지 분석은 `backend/app/services/ai_stub.py`의 stub 결과를 사용합니다.
- OCR은 `backend/app/services/ocr_stub.py`에서 빈 문자열을 반환하며, 추후 EasyOCR 또는 Tesseract로 교체할 수 있습니다.
- 사용 로그는 현재 메모리 배열에 저장하며, `backend/app/db/` 폴더는 PostgreSQL/SQLAlchemy 전환을 위한 자리입니다.
