import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai


RESULTS_DIR = Path("results")


def parse_args():
    parser = argparse.ArgumentParser(
        description="LLM + Kakao Local API를 이용한 국내 여행지 추천 프로그램"
    )
    parser.add_argument(
        "--date", "-date",
        required=True,
        help='여행 날짜 (YYYY-MM-DD), 예: --date "2026-09-15"',
    )
    return parser, parser.parse_args()


def validate_date(parser, date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return date_text
    except ValueError:
        parser.error('날짜 형식이 올바르지 않습니다. 예: --date "2026-09-15"')


## API 키 처리
def load_keys():
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY")
    kakao_key = os.getenv("KAKAO_REST_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    missing = []
    if not gemini_key:
        missing.append("GEMINI_API_KEY")
    if not kakao_key:
        missing.append("KAKAO_REST_API_KEY")

    if missing:
        print("[오류] API 키가 설정되지 않았습니다:", ", ".join(missing))
        print(".env 파일에 아래 형식으로 설정하세요.")
        print("GEMINI_API_KEY=YOUR_KEY")
        print("KAKAO_REST_API_KEY=YOUR_KEY")
        sys.exit(1)

    return gemini_key, kakao_key, model


def recommendation_schema():
    return {
        "type": "object",
        "properties": {
            "recommended_city": {"type": "string"},
            "weather": {"type": "string"},
            "events": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
        },
        "required": ["recommended_city", "weather", "events", "reason"],
    }


## 추천 프롬프트
def request_recommendation(client, model, date_text, retry=False):
    retry_text = (
        "\n이전 응답을 JSON으로 파싱하지 못했습니다. "
        "설명이나 코드블록 없이 필수 키만 가진 JSON 객체만 출력하세요."
        if retry else ""
    )

    prompt = f"""
사용자가 국내 여행을 갈 날짜는 {date_text} 입니다.

해당 시기에 여행하기 좋은 대한민국의 도시/지역 1곳을 추천하세요.
실제 날씨나 행사의 완벽한 정확도보다, 과제용으로 자연스럽고 합리적인 내용을 작성하세요.

필수 출력:
- recommended_city: 문자열
- weather: 해당 시기의 일반적 날씨 요약 문자열
- events: 행사/축제 후보 문자열 배열 1~3개
- reason: 추천 근거 2~4문장
{retry_text}
""".strip()

    interaction = client.interactions.create(
        model=model,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": recommendation_schema(),
        },
    )
    return interaction.output_text


## AI 답변 
def get_recommendation(client, model, date_text, errors):
    for attempt in range(2):
        try:
            raw_text = request_recommendation(
                client, model, date_text, retry=(attempt == 1)
            )
            data = json.loads(raw_text)

            required = ["recommended_city", "weather", "events", "reason"]
            if not all(key in data for key in required):
                raise ValueError("필수 키가 누락되었습니다.")
            if not isinstance(data["events"], list):
                raise ValueError("events는 배열이어야 합니다.")
            return data

        except (json.JSONDecodeError, ValueError) as e:
            if attempt == 0:
                print("  - JSON 파싱 실패. 1회 재요청합니다.")
                continue
            errors.append({
                "step": "llm_recommendation",
                "type": "JSON_PARSE_ERROR",
                "message": str(e),
            })
            raise

        except Exception as e:
            errors.append({
                "step": "llm_recommendation",
                "type": "LLM_API_ERROR",
                "message": str(e),
            })
            raise


def search_restaurants(kakao_key, city, errors):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    params = {
        "query": f"{city} 맛집",
        "category_group_code": "FD6",
        "size": 5,
        "page": 1,
        "sort": "accuracy",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code in (401, 403):
            errors.append({
                "step": "place_search",
                "type": "AUTH_ERROR",
                "message": f"HTTP {response.status_code}",
            })
            print(f"  - 인증 오류({response.status_code}). 맛집은 '데이터 없음' 처리합니다.")
            return []

        response.raise_for_status()
        payload = response.json()
        docs = payload.get("documents", [])

        if not docs:
            errors.append({
                "step": "place_search",
                "type": "EMPTY_RESULT",
                "message": f"0 results for query={city} 맛집",
            })
            return []

        restaurants = []
        for item in docs[:5]:
            restaurants.append({
                "name": item.get("place_name", ""),
                "address": item.get("road_address_name") or item.get("address_name", ""),
                "category": item.get("category_name", ""),
                "url": item.get("place_url", ""),
                "x": float(item["x"]) if item.get("x") else None,
                "y": float(item["y"]) if item.get("y") else None,
            })
        return restaurants

    except requests.RequestException as e:
        errors.append({
            "step": "place_search",
            "type": "NETWORK_OR_HTTP_ERROR",
            "message": str(e),
        })
        print("  - 장소 API 실패. 맛집은 '데이터 없음' 처리하고 계속합니다.")
        return []
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        errors.append({
            "step": "place_search",
            "type": "PLACE_PARSE_ERROR",
            "message": str(e),
        })
        print("  - 장소 응답 파싱 실패. 맛집은 '데이터 없음' 처리하고 계속합니다.")
        return []


def restaurants_for_prompt(restaurants):
    if not restaurants:
        return "데이터 없음"
    return "\n".join(
        f"{i}. {r['name']} / {r['address']} / {r['category']} / {r['url']}"
        for i, r in enumerate(restaurants, 1)
    )


def generate_report(client, model, date_text, recommendation, restaurants, errors):
    prompt = f"""
아래 데이터를 이용하여 한국어 Markdown 여행 리포트를 작성하세요.

여행 날짜: {date_text}

1차 추천 JSON:
{json.dumps(recommendation, ensure_ascii=False, indent=2)}

맛집 검색 결과:
{restaurants_for_prompt(restaurants)}

오류 목록:
{json.dumps(errors, ensure_ascii=False, indent=2)}

반드시 아래 제목을 모두 포함하세요.
# {date_text} 국내 여행 추천 리포트
## 추천 지역
## 추천 이유
## 날씨 요약
## 행사/축제
## 맛집 추천
## 1일 일정 제안
## 오류 요약(errors)

규칙:
- 맛집이 없으면 '데이터 없음'이라고 표시
- 1일 일정은 오전/오후/저녁 수준으로 간단히 제안
- 오류가 없으면 오류 요약에 '없음'이라고 표시
- Markdown 본문만 출력
""".strip()

    try:
        interaction = client.interactions.create(model=model, input=prompt)
        return interaction.output_text
    except Exception as e:
        errors.append({
            "step": "final_report",
            "type": "LLM_API_ERROR",
            "message": str(e),
        })
        raise


def save_results(date_text, recommendation, restaurants, errors, report):
    RESULTS_DIR.mkdir(exist_ok=True)
    raw_path = RESULTS_DIR / f"{date_text}_raw.json"
    report_path = RESULTS_DIR / f"{date_text}_travel_plan.md"

    raw_data = {
        "date": date_text,
        "recommendation": recommendation,
        "restaurants": restaurants,
        "errors": errors,
    }

    with raw_path.open("w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    with report_path.open("w", encoding="utf-8") as f:
        f.write(report.strip() + "\n")

    return raw_path, report_path


def main():
    parser, args = parse_args()
    date_text = validate_date(parser, args.date)
    gemini_key, kakao_key, model = load_keys()
    errors = []
    client = genai.Client(api_key=gemini_key)

    print("[1/3] 1차 추천 생성 중(LLM)...")
    try:
        recommendation = get_recommendation(client, model, date_text, errors)
    except Exception as e:
        print("[실패] 1차 추천을 만들지 못했습니다.")
        print("원인:", e)
        sys.exit(1)

    print("  - recommended_city:", recommendation["recommended_city"])

    print("[2/3] 맛집 검색 중(지도/장소 API)...")
    restaurants = search_restaurants(
        kakao_key, recommendation["recommended_city"], errors
    )
    if restaurants:
        print(f"  - 맛집 {len(restaurants)}곳 검색 완료")
    else:
        print("  - 맛집 데이터 없음. 다음 단계로 계속합니다.")

    print("[3/3] 최종 리포트 생성 중(LLM)...")
    try:
        report = generate_report(
            client, model, date_text, recommendation, restaurants, errors
        )
    except Exception as e:
        print("[실패] 최종 리포트를 만들지 못했습니다.")
        print("원인:", e)
        sys.exit(1)

    raw_path, report_path = save_results(
        date_text, recommendation, restaurants, errors, report
    )

    print("  - 리포트 생성 완료")
    print("완료!")
    print("원본 JSON:", raw_path)
    print("최종 리포트:", report_path)


if __name__ == "__main__":
    main()
