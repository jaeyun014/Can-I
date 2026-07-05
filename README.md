# Can I?

AI 기반 생활 안전 도우미 서비스 MVP입니다. 사용자가 사진을 찍거나 이미지를 업로드하면 OCR과 GPT Vision 보조 분석으로 물건/재질 단서를 추출하고, 최종 안전 판단은 JSON 기반 Rule Engine이 수행합니다.

## 현재 기능

- 모바일 카메라 촬영 입력
- 이미지 파일 업로드
- 텍스트 물건 이름 입력
- 시/도 → 구/군 2단 지역 선택
- OCR 기반 재질/안전 표기 추출
- GPT Vision 보조 분석
- Rule Engine 기반 최종 안전 판단
- 전자레인지, 에어프라이어, 오븐, 냉동, 식기세척기 가능 여부
- 사용자가 입력한 물건 이름 기반 재질 우선 판단
- 음식 사진/입력 판단 시 냉동, 냉장, 음식물쓰레기, 일반쓰레기 안내
- 분리수거 안내
- `왜 안돼?` 상세 설명 토글: 주의 단계에서만 표시
- `이럴 수도 있어!` 사고/상황 예시 토글: 주의, 위험 단계에서 표시
- 분석 근거 표시
- Google 계정 로그인
- 계정별 검색 기록 저장/조회/삭제
- 최근 사용 로그

## 프로젝트 구조

```txt
backend/   FastAPI, OCR, Vision, Input Normalizer, Rule Engine, JSON rules
frontend/  Next.js 15, React, TypeScript, Tailwind CSS
scripts/   개발 서버 실행/종료 스크립트
```

## 빠른 시작

처음 한 번만 의존성을 설치합니다.

```bash
cd /Users/chojaeyun/Desktop/Can-I-Servise/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```bash
cd /Users/chojaeyun/Desktop/Can-I-Servise/frontend
npm install
```

그 다음부터는 프로젝트 루트에서 한 명령어로 실행합니다.

```bash
cd /Users/chojaeyun/Desktop/Can-I-Servise
make dev
```

브라우저에서 엽니다.

```txt
http://localhost:3000
```

## 개발 서버 명령어

```bash
make dev      # 백엔드 8000 + 프론트엔드 3000 동시 실행
make stop     # 둘 다 종료
make restart  # 둘 다 재시작
make status   # 현재 상태 확인
make logs     # 최근 로그 확인
```

`make dev`는 다음을 자동으로 처리합니다.

- 기존 3000/8000 포트 프로세스 정리
- 백엔드 `127.0.0.1:8000` 실행
- 프론트엔드 `127.0.0.1:3000` 실행
- `frontend/.next` 삭제 후 재생성

이 방식은 Next dev 서버와 `npm run build`가 같은 `.next` 폴더를 건드리며 생기는 스타일 깨짐 문제를 줄입니다.

## 수동 실행

필요하면 직접 실행할 수 있습니다.

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm run dev -- --hostname 127.0.0.1
```

주의: 터미널에 보이는 `http://0.0.0.0:3000`은 접속용 주소가 아닙니다. 브라우저에서는 `http://localhost:3000` 또는 Mac의 실제 IP를 사용하세요.

## 모바일 접속

휴대폰에서 테스트하려면 Mac과 휴대폰이 같은 네트워크에 있어야 합니다.

1. `CAN_I_HOST=0.0.0.0 make dev`로 서버를 실행합니다.
2. Mac의 IP 주소를 확인합니다.
3. 휴대폰 브라우저에서 접속합니다.

```txt
http://맥IP:3000
```

예:

```txt
http://192.168.0.12:3000
```

프론트는 접속한 hostname을 기준으로 API 주소를 자동 계산합니다. 예를 들어 `http://192.168.0.12:3000`으로 접속하면 API는 `http://192.168.0.12:8000`을 호출합니다.

## API

```txt
GET  /health
POST /api/analyze
POST /api/analyze/image
POST /api/logs
GET  /api/logs
```

이미지 분석 흐름:

```txt
Image Upload / Camera Capture
→ OCR Service
→ GPT Vision Service
→ Input Normalizer
→ Rule Engine
→ Log 저장
→ Result 반환
```

중요한 안전 원칙:

- GPT Vision은 최종 판단을 하지 않습니다.
- OCR 결과가 명확하면 OCR을 우선합니다.
- 사용자가 입력한 물건 이름이 재질을 강하게 암시하면 이름 기반 Rule을 우선합니다.
- 음식으로 판단되면 생활 안전 판단을 음식 보관/폐기 판단으로 전환합니다.
- 최종 판단은 항상 Rule Engine이 수행합니다.
- 알 수 없는 재질은 `WARNING`으로 처리합니다.

판단 흐름:

```txt
이미지/카메라 + 물건 이름 + 지역
→ OCR / Vision 단서 추출
→ 입력 정규화
→ 물건 이름 기반 Rule 우선 매칭
→ 음식 여부 판단
→ Rule Engine 최종 판단
→ 결과 UI / 로그 저장
```

## 환경변수

백엔드 `.env` 예시:

```env
OPENAI_API_KEY=
VISION_MODEL=gpt-4o-mini
OCR_ENGINE=tesseract
GOOGLE_CLIENT_ID=
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

프론트엔드 `.env.local` 예시:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
```

일반 로컬 개발에서는 프론트 환경변수를 비워둬도 됩니다. 비워두면 브라우저 접속 hostname을 기준으로 API 주소를 자동 선택합니다.

`OPENAI_API_KEY`가 없으면 GPT Vision 호출은 fallback stub로 동작하며 서버는 죽지 않습니다.

## Google 로그인 설정

Google 로그인은 프론트엔드가 Google Identity Services로 ID 토큰을 받고, 백엔드가 `google-auth`로 토큰을 검증한 뒤 앱 내부 세션 토큰을 발급하는 구조입니다.

Google Cloud Console에서 OAuth Client ID를 만든 뒤 같은 Client ID를 백엔드와 프론트에 넣습니다.

```env
# backend/.env
GOOGLE_CLIENT_ID=구글_OAuth_Client_ID

# frontend/.env.local
NEXT_PUBLIC_GOOGLE_CLIENT_ID=구글_OAuth_Client_ID
```

Google OAuth Client의 Authorized JavaScript origins에는 개발 주소를 추가하세요.

```txt
http://localhost:3000
http://127.0.0.1:3000
```

휴대폰에서 Mac IP로 테스트한다면 해당 주소도 추가해야 합니다.

```txt
http://맥IP:3000
```

예:

```txt
http://192.168.0.12:3000
```

설정 후 서버를 재시작합니다.

```bash
make restart
```

로그인하지 않은 상태에서도 분석은 가능합니다. 로그인하면 검색 기록이 해당 Google 계정 기준으로 저장되고, `내역 삭제` 버튼으로 본인 계정 기록만 삭제할 수 있습니다.

## OCR 안내

Python 패키지 `pytesseract`는 설치되지만, 실제 OCR을 하려면 시스템에 Tesseract 실행 파일이 필요합니다.

macOS 예시:

```bash
brew install tesseract
brew install tesseract-lang
```

Tesseract가 없거나 한국어 언어팩이 없어도 서버는 죽지 않고 빈 OCR 결과로 fallback합니다.

## 지원 지역

- 서울특별시 강남구
- 서울특별시 마포구
- 부산광역시 해운대구
- 전주시 완산구
- 제주특별자치도 제주시

기존 호환 지역:

- 서울
- 부산
- 전주

## 지원 물건/재질

- 알루미늄 포일
- 플라스틱 배달 용기
- 종이컵
- 유리 밀폐용기
- 보조배터리
- 나무젓가락
- PET 플라스틱 병
- PS 플라스틱 용기

음식 판단 예시:

- 밥
- 국, 찌개, 탕, 수프, 카레
- 고기, 생선, 해산물
- 채소, 과일
- 뼈, 조개껍데기, 달걀껍데기, 큰 씨앗

지원 재질:

- `aluminum`
- `pp`
- `pet`
- `ps`
- `paper_coated`
- `glass`
- `lithium_battery`
- `wood`
- `food`

음식으로 판단되면 결과 카드가 다음 항목으로 바뀝니다.

- 냉동 보관
- 냉장 보관
- 음식물쓰레기
- 일반쓰레기

예를 들어 냉장 보관이 `주의`라면 `이럴 수도 있어!` 버튼을 눌렀을 때 냉장고에 오래 두면 세균이 번식해 배탈이나 식중독으로 이어질 수 있다는 식의 상황 예시를 보여줍니다.

## 주요 코드 위치

- 안전 판단: `backend/app/services/rule_engine.py`
- OCR: `backend/app/services/ocr_service.py`
- GPT Vision: `backend/app/services/vision_service.py`
- 입력 통합: `backend/app/services/input_normalizer.py`
- 분석 API: `backend/app/api/analyze.py`
- 재질 규칙: `backend/app/data/material_rules.json`
- 지역 규칙: `backend/app/data/region_rules.json`
- 메인 화면: `frontend/app/page.tsx`
- 이미지 입력: `frontend/components/ImageUpload.tsx`
- 지역 선택: `frontend/components/RegionSelect.tsx`
- 결과 카드: `frontend/components/ResultCard.tsx`
- 왜 안돼 토글: `frontend/components/WhyToggle.tsx`
- 이럴 수도 있어 토글: `frontend/components/RiskScenarioToggle.tsx`
- 분석 근거: `frontend/components/AnalysisEvidence.tsx`
- Google 로그인: `frontend/components/GoogleLoginButton.tsx`
- Google 인증 검증: `backend/app/services/auth_service.py`
- 계정별 로그 API: `backend/app/api/logs.py`

## 문제 해결

### 스타일이 깨질 때

대부분 Next `.next` 캐시가 꼬인 경우입니다.

```bash
make restart
```

또는 수동으로:

```bash
cd frontend
rm -rf .next
npm run dev -- --hostname 0.0.0.0
```

개발 서버가 켜져 있는 동안 `npm run build`를 같이 돌리면 CSS 경로가 꼬일 수 있습니다. 빌드 검증이 필요하면 dev 서버를 끈 뒤 실행하세요.

### Failed to fetch가 뜰 때

백엔드가 켜져 있는지 확인합니다.

```bash
curl http://localhost:8000/health
```

정상 응답:

```json
{"status":"ok"}
```

휴대폰에서 테스트 중이라면 `localhost`가 휴대폰 자기 자신을 뜻합니다. 반드시 Mac의 실제 IP로 접속하세요.

```txt
http://맥IP:3000
```

### Google credential verification failed가 뜰 때

먼저 로그를 확인합니다.

```bash
make logs
```

`Token used too early`가 보이면 Mac의 시간이 Google 토큰 시간과 어긋난 상태입니다. macOS의 날짜 및 시간 자동 설정을 켜고 서버를 재시작하세요.

```bash
make restart
```

Google Cloud Console의 Authorized JavaScript origins에는 실제 접속 주소가 들어 있어야 합니다.

```txt
http://localhost:3000
http://127.0.0.1:3000
http://맥IP:3000
```

### 포트가 이미 사용 중일 때

```bash
make restart
```

스크립트가 3000/8000 포트의 기존 프로세스를 정리한 뒤 다시 시작합니다.

## GitHub에 올리기

```bash
git status
git add .
git commit -m "Update Can I MVP"
git push
```
