import json
import os
import requests
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def _send_json(self, status_code, payload):
        body = json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # 브라우저에서 /api/generate 직접 접속했을 때
    # 501 오류가 뜨지 않도록 GET도 처리
    def do_GET(self):
        self._send_json(200, {
            "status": "ok",
            "message": "PitchMate AI API is running."
        })

    def do_POST(self):
        try:
            # -------------------------------------------------
            # 1. 요청 데이터 읽기
            # -------------------------------------------------
            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            raw_body = self.rfile.read(content_length)

            try:
                data = json.loads(raw_body or b"{}")
            except json.JSONDecodeError:
                self._send_json(400, {
                    "error": "잘못된 요청 형식입니다."
                })
                return

            topic = str(
                data.get("topic", "")
            ).strip()

            audience = str(
                data.get("audience", "")
            ).strip()

            tone = str(
                data.get("tone", "")
            ).strip()

            # -------------------------------------------------
            # 2. 필수 입력 검증
            # -------------------------------------------------
            if not topic or not audience:
                self._send_json(400, {
                    "error": "발표 주제와 발표 대상을 모두 입력해주세요."
                })
                return

            # 너무 긴 입력 방지
            if len(topic) > 100:
                self._send_json(400, {
                    "error": "발표 주제는 100자 이내로 입력해주세요."
                })
                return

            if len(audience) > 60:
                self._send_json(400, {
                    "error": "발표 대상은 60자 이내로 입력해주세요."
                })
                return

            # -------------------------------------------------
            # 3. 환경 변수 확인
            # -------------------------------------------------
            api_key = os.environ.get("GEMINI_API_KEY")

            if not api_key:
                print("ERROR: GEMINI_API_KEY is not configured.")

                self._send_json(500, {
                    "error": (
                        "AI 서버 설정이 완료되지 않았습니다. "
                        "관리자에게 문의해주세요."
                    )
                })
                return

            # -------------------------------------------------
            # 4. 프롬프트 구성
            # -------------------------------------------------
            if not tone:
                tone = "자연스럽고 자신감 있게"

            prompt = f"""
너는 대학생의 발표 준비를 도와주는 발표 코치다.

아래 정보를 바탕으로 실제 발표에서 바로 사용할 수 있는
짧고 자연스러운 한국어 발표 시작안을 만들어라.

발표 주제:
{topic}

발표 대상:
{audience}

원하는 분위기:
{tone}

반드시 아래 형식을 지켜라.

[시작 멘트]
발표자가 실제로 말하기 쉬운 자연스러운 문장 2~3문장

[발표 흐름]
1. 첫 번째 핵심 내용
2. 두 번째 핵심 내용
3. 세 번째 핵심 내용

[마무리 연결 문장]
본론으로 자연스럽게 넘어가는 문장 1개

규칙:
- 전체 답변은 500자 이내
- 너무 전문적이거나 어려운 표현은 피할 것
- 과장된 표현은 사용하지 말 것
- 불필요한 설명은 넣지 말 것
- 한국어로만 작성할 것
""".strip()

            # -------------------------------------------------
            # 5. Gemini API 호출
            # -------------------------------------------------
            url = (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/"
                "gemini-2.5-flash:generateContent"
            )

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 700
                }
            }

            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=15
                )

            except requests.Timeout:
                print("ERROR: Gemini request timeout.")

                self._send_json(504, {
                    "error": (
                        "AI 응답이 늦어지고 있습니다. "
                        "잠시 후 다시 시도해주세요."
                    )
                })
                return

            except requests.RequestException as error:
                print(
                    "ERROR: Gemini network error:",
                    str(error)
                )

                self._send_json(502, {
                    "error": (
                        "AI 서버와 연결할 수 없습니다. "
                        "잠시 후 다시 시도해주세요."
                    )
                })
                return

            # -------------------------------------------------
            # 6. Gemini 오류 확인
            # -------------------------------------------------
            if response.status_code != 200:

                # API Key 자체는 출력하지 않음
                print(
                    "Gemini status:",
                    response.status_code
                )

                print(
                    "Gemini response:",
                    response.text[:2000]
                )

                # 인증 문제
                if response.status_code in (401, 403):
                    self._send_json(502, {
                        "error": (
                            "AI API 인증에 실패했습니다. "
                            "API 키 설정을 확인해주세요."
                        )
                    })
                    return

                # 무료 할당량 / 호출 제한
                if response.status_code == 429:
                    self._send_json(429, {
                        "error": (
                            "현재 AI 무료 사용 한도 또는 "
                            "요청 한도에 도달했습니다. "
                            "잠시 후 다시 시도해주세요."
                        )
                    })
                    return

                # 요청 오류
                if response.status_code == 400:
                    self._send_json(502, {
                        "error": (
                            "AI 요청 형식에 문제가 발생했습니다."
                        )
                    })
                    return

                self._send_json(502, {
                    "error": (
                        "AI API 호출에 실패했습니다. "
                        "잠시 후 다시 시도해주세요."
                    )
                })
                return

            # -------------------------------------------------
            # 7. Gemini 응답 파싱
            # -------------------------------------------------
            try:
                result_data = response.json()

                candidates = result_data.get(
                    "candidates",
                    []
                )

                if not candidates:
                    print(
                        "ERROR: No Gemini candidates:",
                        json.dumps(
                            result_data,
                            ensure_ascii=False
                        )[:2000]
                    )

                    self._send_json(502, {
                        "error": (
                            "AI가 답변을 생성하지 못했습니다. "
                            "다시 시도해주세요."
                        )
                    })
                    return

                content = candidates[0].get(
                    "content",
                    {}
                )

                parts = content.get(
                    "parts",
                    []
                )

                text_parts = []

                for part in parts:
                    text = part.get("text")

                    if text:
                        text_parts.append(text)

                result_text = "\n".join(
                    text_parts
                ).strip()

                if not result_text:
                    print(
                        "ERROR: Empty Gemini text:",
                        json.dumps(
                            result_data,
                            ensure_ascii=False
                        )[:2000]
                    )

                    self._send_json(502, {
                        "error": (
                            "AI 답변이 비어 있습니다. "
                            "다시 시도해주세요."
                        )
                    })
                    return

            except Exception as error:
                print(
                    "ERROR parsing Gemini response:",
                    str(error)
                )

                self._send_json(502, {
                    "error": (
                        "AI 응답을 처리하는 중 "
                        "오류가 발생했습니다."
                    )
                })
                return

            # -------------------------------------------------
            # 8. 성공
            # -------------------------------------------------
            self._send_json(200, {
                "result": result_text
            })

        except Exception as error:

            # 예상하지 못한 서버 오류
            print(
                "UNEXPECTED SERVER ERROR:",
                repr(error)
            )

            self._send_json(500, {
                "error": (
                    "서버 오류가 발생했습니다. "
                    "잠시 후 다시 시도해주세요."
                )
            })