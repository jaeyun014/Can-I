# Can I?

AI 기반 생활 안전 도우미 서비스 MVP입니다.

사용자가 사진을 촬영하거나 이미지를 업로드하면 OCR과 GPT Vision 보조 분석으로 물건과 재질에 관한 단서를 추출합니다. 최종 안전 판단은 JSON 기반 Rule Engine이 수행합니다.

## 주요 기능

* 모바일 카메라 촬영
* 이미지 파일 업로드
* 텍스트 기반 물건 이름 입력
* 다중 이미지 입력: 전체 사진, 재질 코드 사진, 안전 표기/바코드 사진
* 시·도 → 구·군 2단계 지역 선택
* OCR 기반 재질 및 안전 표기 추출
* GPT Vision 기반 이미지 보조 분석
* Rule Engine 기반 최종 안전 판단
* 전자레인지, 에어프라이어, 오븐, 냉동, 식기세척기 사용 가능 여부 판단
* 사용자 입력 물건 이름 기반 재질 우선 판단
* 음식 이미지 및 입력 판단
* 냉동, 냉장, 음식물쓰레기, 일반쓰레기 안내
* 신뢰도 점수 및 계산 근거 표시
* 이미지 품질 검사 및 추가 촬영 안내
* 본체와 뚜껑 분리 표시를 위한 물체 구조 요약
* 지역별 분리배출 안내
* `왜 안돼?` 상세 설명 제공
* `이럴 수도 있어!` 사고 및 위험 상황 예시 제공
* 분석 근거 표시
* Google 계정 로그인
* 계정별 검색 기록 저장, 조회, 삭제
* SQLite 기반 로그 영구 저장
* 바코드 번호 기반 내부 제품 DB 조회
* `잘못 인식했나요?` 피드백 수집
* Active Learning 검수 큐 및 상태 관리
* 최근 사용 로그

## 기술 스택

### Frontend

* Next.js 15
* React
* TypeScript
* Tailwind CSS

### Backend

* FastAPI
* Python
* Tesseract OCR
* OpenAI Vision API

### Authentication

* Google Identity Services
* Google OAuth
* Backend ID Token 검증

### Data and Logic

* JSON 기반 재질 규칙
* JSON 기반 지역 규칙
* Rule Engine
* Evidence Fusion 확장 인터페이스
* Conflict Detector 확장 인터페이스
* SQLite 기반 계정별 분석 로그
* SQLite 기반 제품 DB, 피드백, 검수 큐

## 프로젝트 구조

```txt
backend/   FastAPI, OCR, Vision, Input Normalizer, Rule Engine, JSON Rules
frontend/  Next.js, React, TypeScript, Tailwind CSS
scripts/   개발 서버 실행 및 종료 스크립트
```

## 시스템 흐름

```txt
이미지 촬영/업로드
+ 물건 이름
+ 지역 정보
        ↓
다중 이미지 역할 분류
전체 사진 / 재질 코드 / 안전 표기 또는 바코드
        ↓
이미지 품질 검사 및 재촬영 안내
        ↓
OCR / GPT Vision 단서 추출
        ↓
바코드 / 전용 분류 모델 인터페이스
        ↓
Input Normalizer
        ↓
물건 이름 기반 Rule 우선 매칭
        ↓
음식 여부 판단
        ↓
Rule Engine 최종 판단
        ↓
Confidence Service 신뢰도 계산
        ↓
SQLite 로그 및 분석 결과 저장
        ↓
결과 UI 표시 및 로그 저장
```

## 안전 판단 원칙

* GPT Vision은 최종 판단을 수행하지 않습니다.
* OCR 결과가 명확하면 OCR 결과를 우선합니다.
* 물건 이름이 재질을 명확하게 나타내면 이름 기반 규칙을 우선합니다.
* 음식으로 판단되면 음식 보관 및 폐기 기준으로 전환합니다.
* 최종 판단은 항상 Rule Engine이 수행합니다.
* 확인할 수 없는 재질은 `WARNING`으로 처리합니다.
* 근거가 충돌하면 신뢰도를 낮추고 보수적으로 판단합니다.
* 이미지 모델과 GPT Vision은 최종 판단자가 아니라 근거 제공자입니다.

## 판단 알고리즘

현재 판단 우선순위:

```txt
1. 사용자 직접 입력 물건명
2. OCR 안전 표기
3. OCR 재질 표기
4. 바코드 제품 DB
5. GPT Vision 추정
6. unknown fallback
```

이번 구조 개선으로 다음 확장 인터페이스가 추가되었습니다.

```txt
backend/app/config/source_reliability.json
backend/app/services/evidence_fusion_service.py
backend/app/services/conflict_detector.py
backend/app/services/image_quality_service.py
backend/app/services/barcode_service.py
backend/app/services/material_classifier_service.py
```

`source_reliability.json`은 출처별 초기 신뢰도를 관리합니다. 바코드 기능은 OCR 또는 사용자가 입력한 바코드 번호를 내부 제품 DB와 매칭하고, 제품 DB 결과는 Evidence Fusion에서 `barcode_verified_product_db` 근거로 사용됩니다. 전용 이미지 분류 모델은 아직 stub 인터페이스이며, 실제 학습 모델이 붙어도 최종 판단은 Rule Engine이 담당합니다.

신뢰도는 다음 근거를 조합해 계산합니다.

```txt
OCR 재질 인식
OCR 안전 표기 인식
사용자 직접 입력
GPT Vision 객체 인식
Rule Engine 정확 매칭
재질 + 용도 조합 규칙 매칭
unknown fallback 감점
근거 충돌 감점
```

근거 충돌이나 unknown이 있으면 `review_queue`에 검수 대상으로 자동 등록됩니다.

## 입력 품질 개선

이미지 입력은 최대 3장을 권장합니다.

```txt
1. 물건 전체 사진
2. 바닥 또는 뒷면의 재질 코드 확대 사진
3. 안전 표기 또는 바코드 사진
```

프론트엔드는 촬영 또는 파일 선택으로 여러 이미지를 누적할 수 있고, 백엔드는 `files` form field로 여러 이미지를 받아 다음을 수행합니다.

* 이미지별 밝기, 대비, 해상도 검사
* 누락된 촬영 역할 확인
* 재질 코드/안전 표기/바코드 추가 촬영 안내
* 여러 OCR 결과 병합
* 본체와 뚜껑 구조 요약
* 결과 카드의 `입력 품질 및 물체 구조` 패널 표시

품질이 낮거나 신뢰도 점수가 낮으면 결과 상단에 추가 촬영 안내가 표시됩니다.

## 데이터 저장 방식

검색 기록은 더 이상 메모리 리스트에 저장하지 않습니다. 서버 시작 시 SQLite DB를 초기화하고 다음 파일에 영구 저장합니다.

```txt
backend/can_i.db
```

이 파일은 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다. 따라서 서버를 재시작해도 검색 기록이 유지됩니다.

현재 생성되는 주요 테이블:

```txt
usage_logs
analysis_results
confidence_records
feedback_records
review_queue
evidence_records
conflict_records
product_barcodes
product_materials
product_usage_rules
```

저장 내용:

* `usage_logs`: 계정별 검색 기록, 입력 타입, 물건명, 재질, 지역, 위험도
* `analysis_results`: 정규화 입력과 전체 분석 결과 JSON
* `confidence_records`: 신뢰도 점수, 레벨, 가점/감점 요인
* `feedback_records`: `잘못 인식했나요?` 사용자 피드백
* `review_queue`: 낮은 신뢰도, unknown, 근거 충돌, 사용자 피드백 검수 대상
* `evidence_records`: OCR, Vision, 바코드, 사용자 입력 근거
* `conflict_records`: 근거 간 충돌 내역
* `product_barcodes`: 바코드별 제품명, 제조사, 검증 여부
* `product_materials`: 제품 본체, 뚜껑, 라벨 재질
* `product_usage_rules`: 제품별 사용 조건

로그인한 사용자는 Google 이메일 기준으로 본인 기록만 조회/삭제합니다. 로그인하지 않은 사용자의 기록은 익명 기록으로 분리됩니다.

## 빠른 시작

### 1. 백엔드 설치

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 프론트엔드 설치

```bash
cd frontend
npm install
```

### 3. 개발 서버 실행

프로젝트 루트에서 실행합니다.

```bash
make dev
```

브라우저에서 다음 주소로 접속합니다.

```txt
http://localhost:3000
```

## 개발 서버 명령어

```bash
make dev      # 백엔드와 프론트엔드 실행
make stop     # 개발 서버 종료
make restart  # 개발 서버 재시작
make status   # 실행 상태 확인
make logs     # 최근 로그 확인
```

`make dev`는 다음 작업을 수행합니다.

* 기존 3000번 및 8000번 포트 프로세스 정리
* FastAPI 백엔드 실행
* Next.js 프론트엔드 실행
* `frontend/.next` 캐시 삭제 후 재생성

## 수동 실행

### Backend

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm run dev -- --hostname 127.0.0.1
```

## 모바일 테스트

휴대폰과 개발 PC가 같은 네트워크에 연결되어 있어야 합니다.

```bash
CAN_I_HOST=0.0.0.0 make dev
```

개발 PC의 로컬 IP를 확인한 후 휴대폰 브라우저에서 접속합니다.

```txt
http://개발PC_IP:3000
```

프론트엔드는 접속한 hostname을 기준으로 백엔드 API 주소를 자동으로 계산합니다.

## API

```txt
GET    /health
POST   /api/analyze
POST   /api/analyze/image
POST   /api/logs
GET    /api/logs
DELETE /api/logs
POST   /api/feedback
GET    /api/review-queue
PATCH  /api/review-queue/{review_id}
```

## 환경변수

### Backend

`backend/.env`

```env
OPENAI_API_KEY=
VISION_MODEL=gpt-4o-mini
OCR_ENGINE=tesseract
GOOGLE_CLIENT_ID=
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
DATABASE_URL=sqlite:///can_i.db
```

### Frontend

`frontend/.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
```

`OPENAI_API_KEY`가 없으면 GPT Vision은 fallback stub으로 동작합니다.

API 키와 인증 정보가 포함된 `.env` 파일은 GitHub에 업로드하지 않아야 합니다.

## Google 로그인 설정

프론트엔드는 Google Identity Services를 통해 ID Token을 발급받습니다.

백엔드는 `google-auth`를 이용해 ID Token을 검증한 뒤 서비스 내부 인증 토큰을 발급합니다.

동일한 Google OAuth Client ID를 백엔드와 프론트엔드에 설정합니다.

```env
# backend/.env
GOOGLE_CLIENT_ID=Google_OAuth_Client_ID

# frontend/.env.local
NEXT_PUBLIC_GOOGLE_CLIENT_ID=Google_OAuth_Client_ID
```

Google OAuth의 Authorized JavaScript Origins에는 실제 접속 주소를 등록해야 합니다.

```txt
http://localhost:3000
http://127.0.0.1:3000
```

모바일 테스트 시에는 개발 PC의 로컬 IP 주소도 등록합니다.

```txt
http://개발PC_IP:3000
```

로그인하지 않은 사용자도 분석 기능을 사용할 수 있습니다.

로그인한 사용자의 분석 기록은 해당 Google 계정을 기준으로 저장되며, 사용자는 자신의 기록만 조회하거나 삭제할 수 있습니다.

## OCR 설정

Python 패키지 `pytesseract` 외에도 운영체제에 Tesseract 실행 파일이 설치되어 있어야 합니다.

macOS:

```bash
brew install tesseract
brew install tesseract-lang
```

Tesseract 또는 한국어 언어팩이 설치되지 않은 경우 서버는 중단되지 않으며 빈 OCR 결과를 반환합니다.

## 지원 지역

* 서울특별시 강남구
* 서울특별시 마포구
* 부산광역시 해운대구
* 전주시 완산구
* 제주특별자치도 제주시

기존 호환 지역:

* 서울
* 부산
* 전주

## 지원 물건 및 재질

### 물건 예시

* 알루미늄 포일
* 플라스틱 배달 용기
* 종이컵
* 유리 밀폐용기
* 보조배터리
* 나무젓가락
* PET 플라스틱 병
* PS 플라스틱 용기

### 음식 예시

* 밥
* 국, 찌개, 탕, 수프, 카레
* 고기, 생선, 해산물
* 채소, 과일
* 뼈, 조개껍데기, 달걀껍데기, 큰 씨앗

### 지원 재질 코드

* `aluminum`
* `pp`
* `pet`
* `ps`
* `paper_coated`
* `glass`
* `lithium_battery`
* `wood`
* `food`

음식으로 판단되면 결과 항목이 다음과 같이 변경됩니다.

* 냉동 보관
* 냉장 보관
* 음식물쓰레기
* 일반쓰레기

## 주요 코드 위치

```txt
backend/app/services/rule_engine.py
backend/app/services/ocr_service.py
backend/app/services/vision_service.py
backend/app/services/input_normalizer.py
backend/app/services/confidence_service.py
backend/app/services/evidence_fusion_service.py
backend/app/services/conflict_detector.py
backend/app/services/image_quality_service.py
backend/app/services/barcode_service.py
backend/app/services/material_classifier_service.py
backend/app/services/auth_service.py
backend/app/db/database.py
backend/app/api/analyze.py
backend/app/api/logs.py
backend/app/api/feedback.py
backend/app/data/material_rules.json
backend/app/data/region_rules.json

frontend/app/page.tsx
frontend/components/ImageUpload.tsx
frontend/components/RegionSelect.tsx
frontend/components/ResultCard.tsx
frontend/components/FeedbackPanel.tsx
frontend/components/ReviewQueuePanel.tsx
frontend/components/InputQualityPanel.tsx
frontend/components/ConfidenceBadge.tsx
frontend/components/ConfidenceBreakdown.tsx
frontend/components/ConfidenceDetailToggle.tsx
frontend/components/WhyToggle.tsx
frontend/components/RiskScenarioToggle.tsx
frontend/components/AnalysisEvidence.tsx
frontend/components/GoogleLoginButton.tsx
```

## 프로젝트 상태

현재 버전은 MVP 단계입니다.

지원 지역과 재질은 제한적이며, 안전 정보는 실제 제품의 표시사항과 제조사 지침을 우선해야 합니다.

## 향후 개선 계획

* 지원 물건 및 재질 확대
* 지역별 분리배출 규칙 확대
* Rule 데이터 검증 및 관리 기능
* 관리자 검수 화면 고도화
* 모바일 앱 배포
* 운영 환경용 데이터베이스 적용
* 실제 이미지 바코드 디코더 연결
* 제품 DB 데이터 확대
* 실제 전용 이미지 분류 모델 연결
* 자동 테스트 및 배포 파이프라인 구축
