# PitchMate

발표 주제와 대상을 입력하면 AI가 발표 시작 멘트와 간단한 발표 흐름을 생성해주는 웹 서비스입니다.

## 기술 스택
- Frontend: HTML, CSS, JavaScript
- Backend: Vercel Serverless Functions (Python)
- AI API: Google Gemini API
- Deploy: Vercel
- Repository: GitHub

## 프로젝트 구조
```text
.
├── index.html
├── css/
│   └── style.css
├── js/
│   └── app.js
├── api/
│   └── generate.py
├── requirements.txt
├── SERVICE_PLAN.md
└── README.md
```

## 환경 변수
Vercel 프로젝트의 Settings > Environment Variables에서 아래 값을 추가합니다.

- Name: `GEMINI_API_KEY`
- Value: Google AI Studio에서 발급받은 Gemini API Key

API 키는 코드, README, 스크린샷, GitHub 커밋에 절대 직접 작성하지 않습니다.

## 실행/배포 방법
1. GitHub 저장소에 프로젝트 코드를 push합니다.
2. Vercel에서 해당 GitHub 저장소를 Import합니다.
3. Environment Variables에 `GEMINI_API_KEY`를 등록합니다.
4. Deploy 또는 Redeploy를 실행합니다.
5. 배포 URL에서 홈/AI 생성/사용법 메뉴, 모바일 화면, AI 생성 기능을 확인합니다.

## 배포 URL
- 제출 전 여기에 실제 Vercel URL을 작성하세요:
- https://codyssey-taupe.vercel.app/

## AI 기능
- 입력: 발표 주제, 발표 대상, 원하는 분위기
- 출력: 시작 멘트 + 발표 흐름 3개 + 마무리 연결 문장
- 실패 처리: 빈 입력, API 오류, 타임아웃 안내
