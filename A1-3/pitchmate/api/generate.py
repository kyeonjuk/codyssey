import json
import os
import requests
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body or b"{}")

            topic = str(data.get("topic", "")).strip()
            audience = str(data.get("audience", "")).strip()
            tone = str(data.get("tone", "")).strip()

            if not topic or not audience:
                self._send_json(400, {
                    "error": "발표 주제와 발표 대상을 모두 입력해주세요."
                })
                return

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                self._send_json(500, {
                    "error": "서버 환경 변수 설정이 필요합니다."
                })
                return

            prompt = f"""
너는 발표 준비를 돕는 코치다.
아래 정보를 바탕으로 한국어로 짧고 실제로 말하기 쉬운 발표 시작안을 만들어라.

발표 주제: {topic}
발표 대상: {audience}
분위기: {tone}

반드시 다음 형식으로 작성:
[시작 멘트]
2~3문장

[발표 흐름]
1. 핵심 포인트
2. 핵심 포인트
3. 핵심 포인트

[마무리 연결 문장]
1문장

과장된 표현은 피하고 전체 답변은 500자 이내로 작성해라.
""".strip()

            url = (
                "https://generativelanguage.googleapis.com/v1beta/"
                "models/gemini-2.5-flash:generateContent"
            )

            response = requests.post(
                url,
                params={"key": api_key},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                },
                timeout=12
            )

            if response.status_code != 200:
                self._send_json(502, {
                    "error": "AI API 호출에 실패했습니다. 잠시 후 다시 시도해주세요."
                })
                return

            result_data = response.json()
            result_text = (
                result_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            )

            self._send_json(200, {"result": result_text})

        except requests.Timeout:
            self._send_json(504, {
                "error": "AI 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            })
        except Exception:
            self._send_json(500, {
                "error": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            })
