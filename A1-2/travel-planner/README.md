# 국내 여행지 추천 프로그램

## 1. 프로그램 개요
사용자가 `--date "YYYY-MM-DD"` 형식으로 여행 날짜를 입력하면,
Google Gemini API가 여행하기 좋은 국내 지역과 일반적인 날씨/행사 정보를 JSON으로 생성합니다.
이후 Kakao Local API로 해당 지역의 맛집을 검색하고,
Gemini API가 최종 Markdown 여행 리포트를 생성합니다.

## 2. 개발 환경
- Python 3.10 이상
- CLI(터미널) 실행

## 3. 설치 방법
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. API 키 설정
프로젝트 루트에 `.env` 파일을 만들고 아래처럼 설정합니다.

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
KAKAO_REST_API_KEY=YOUR_KAKAO_REST_API_KEY
GEMINI_MODEL=gemini-3.6-flash
```

API 키는 코드나 README에 직접 작성하지 않습니다.
`.env` 파일은 `.gitignore`에 등록하여 Git 저장소에 업로드되지 않도록 합니다.

## 5. 실행 방법
```bash
.venv/bin/python travel_planner.py --date "2026-09-15"
```

`-date`도 사용할 수 있습니다.

```bash
.venv/bin/python travel_planner.py -date "2026-09-15"
```

## 6. 결과물 확인
실행 후 `results/` 폴더에 다음 파일이 생성됩니다.

- `YYYY-MM-DD_raw.json`
  - 1차 추천 JSON
  - 맛집 검색 결과
  - errors 배열
- `YYYY-MM-DD_travel_plan.md`
  - 추천 지역/이유
  - 날씨 요약
  - 행사/축제
  - 맛집 추천
  - 1일 일정
  - 오류 요약

## 7. 오류 처리
- API 키가 없으면 프로그램을 즉시 종료하고 설정 방법을 안내합니다.
- Gemini JSON 파싱 실패 시 최대 1회 재요청합니다.
- Kakao Local API의 인증/네트워크/검색 실패가 발생해도 프로그램은 중단하지 않고,
  맛집을 `데이터 없음`으로 처리한 뒤 최종 리포트 생성을 계속합니다.
- 오류 내용은 원본 JSON의 `errors` 배열에 저장합니다.

## 8. 보안 주의사항
- API 키를 코드, README, 실행 로그, 결과 파일에 직접 작성하지 않습니다.
- `.env`는 제출/Git 업로드 대상에서 제외합니다.
- 화면 캡처 시에도 API 키 전체가 보이지 않게 가립니다.
