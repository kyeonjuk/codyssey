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

    # -------------------------------------------------
    # 브라우저에서 /api/generate 직접 접속 테스트
    # -------------------------------------------------
    def do_GET(self):
        self._send_json(200, {
            "status": "ok",
            "message": "PitchMate AI API is running."
        })

    # -------------------------------------------------
    # AI 생성 요청
    # -------------------------------------------------
    def do_POST(self):

        try:

            # =============================================
            # 1. 사용자 요청 데이터 읽기
            # =============================================
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

            # =============================================
            # 2. 필수 입력 검증
            # =============================================
            if not topic or not audience:

                self._send_json(400, {
                    "error": "발표 주제와 발표 대상을 모두 입력해주세요."
                })

                return

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

            # 분위기가 비어 있으면 기본값
            if not tone:
                tone = "자연스럽고 자신감 있게"

            # =============================================
            # 3. Gemini API 환경 변수 확인
            # =============================================
            api_key = os.environ.get("GEMINI_API_KEY")

            if not api_key:

                print(
                    "ERROR: GEMINI_API_KEY is not configured."
                )

                self._send_json(500, {
                    "error":
                    "AI 서버 설정이 완료되지 않았습니다."
                })

                return

            # =============================================
            # 4. AI 프롬프트
            # =============================================
            prompt = f"""
너는 대학생의 발표 준비를 도와주는 전문 발표 코치다.

사용자가 입력한 정보를 바탕으로
실제 발표에서 그대로 읽어도 자연스러운 발표 시작안을 작성하라.

발표 주제:
{topic}

발표 대상:
{audience}

원하는 분위기:
{tone}


반드시 아래의 형식을 정확하게 유지하여
모든 항목을 끝까지 작성하라.


[시작 멘트]

발표자가 청중에게 실제로 말하는 형식의
자연스러운 시작 멘트 2~3문장을 작성한다.


[발표 흐름]

1. 첫 번째 핵심 내용
2. 두 번째 핵심 내용
3. 세 번째 핵심 내용


[마무리 연결 문장]

시작 멘트에서 발표 본론으로
자연스럽게 넘어가는 문장 1개를 작성한다.


작성 규칙:

- 반드시 모든 항목을 끝까지 작성한다.
- 문장을 중간에서 끝내지 않는다.
- [시작 멘트]를 작성한 뒤 반드시 [발표 흐름]도 작성한다.
- [발표 흐름]을 작성한 뒤 반드시 [마무리 연결 문장]도 작성한다.
- 전체 답변은 약 300~700자 정도로 작성한다.
- 발표 대상이 이해하기 쉬운 표현을 사용한다.
- 문법적으로 자연스러운 한국어를 사용한다.
- 발표자가 청중에게 직접 말하는 형태로 작성한다.
- 반말은 사용하지 않는다.
- 어색한 구어체를 사용하지 않는다.
- 너무 전문적인 표현은 피한다.
- 과장된 표현은 사용하지 않는다.
- 불필요한 서론이나 설명은 추가하지 않는다.
- 요청한 결과 외의 설명은 작성하지 않는다.
- 한국어로만 작성한다.
""".strip()

            # =============================================
            # 5. Gemini API 주소
            # =============================================
            url = (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/"
                "gemini-3.6-flash:generateContent"
            )

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }

            # =============================================
            # 6. Gemini 요청 설정
            # =============================================
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

                    # 답변이 너무 랜덤하지 않게
                    "temperature": 0.6,

                    # 출력이 중간에 끊기지 않도록 충분히 설정
                    "maxOutputTokens": 2048,

                    # Gemini 3.6 Flash의 thinking 양을 낮춤
                    # 단순 발표문 생성에는 깊은 추론이 필요 없음
                    "thinkingConfig": {
                        "thinkingLevel": "low"
                    }
                }
            }

            # =============================================
            # 7. Gemini API 호출
            # =============================================
            try:

                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=25
                )

            except requests.Timeout:

                print(
                    "ERROR: Gemini request timeout."
                )

                self._send_json(504, {
                    "error":
                    "AI 응답이 늦어지고 있습니다. "
                    "잠시 후 다시 시도해주세요."
                })

                return

            except requests.RequestException as error:

                print(
                    "ERROR: Gemini network error:",
                    str(error)
                )

                self._send_json(502, {
                    "error":
                    "AI 서버와 연결할 수 없습니다. "
                    "잠시 후 다시 시도해주세요."
                })

                return

            # =============================================
            # 8. Gemini HTTP 오류 확인
            # =============================================
            if response.status_code != 200:

                print(
                    "Gemini status:",
                    response.status_code
                )

                print(
                    "Gemini response:",
                    response.text[:3000]
                )

                # API 키 오류
                if response.status_code in (401, 403):

                    self._send_json(502, {
                        "error":
                        "AI API 인증에 실패했습니다. "
                        "API 키 설정을 확인해주세요."
                    })

                    return

                # 무료 호출 한도
                if response.status_code == 429:

                    self._send_json(429, {
                        "error":
                        "현재 AI 무료 사용 한도 또는 "
                        "요청 한도에 도달했습니다. "
                        "잠시 후 다시 시도해주세요."
                    })

                    return

                # 잘못된 요청
                if response.status_code == 400:

                    self._send_json(502, {
                        "error":
                        "AI 요청 형식에 문제가 발생했습니다."
                    })

                    return

                # 모델 없음
                if response.status_code == 404:

                    self._send_json(502, {
                        "error":
                        "현재 사용할 수 없는 AI 모델입니다."
                    })

                    return

                self._send_json(502, {
                    "error":
                    "AI API 호출에 실패했습니다. "
                    "잠시 후 다시 시도해주세요."
                })

                return

            # =============================================
            # 9. Gemini 응답 JSON 읽기
            # =============================================
            try:

                result_data = response.json()

                # 디버깅용
                # API 키는 출력되지 않음
                print(
                    "Gemini response data:",
                    json.dumps(
                        result_data,
                        ensure_ascii=False
                    )[:5000]
                )

                candidates = result_data.get(
                    "candidates",
                    []
                )

                # =============================================
                # 10. 후보 응답 존재 여부
                # =============================================
                if not candidates:

                    print(
                        "ERROR: No Gemini candidates:",
                        json.dumps(
                            result_data,
                            ensure_ascii=False
                        )[:3000]
                    )

                    self._send_json(502, {
                        "error":
                        "AI가 답변을 생성하지 못했습니다. "
                        "다시 시도해주세요."
                    })

                    return

                candidate = candidates[0]

                # =============================================
                # 11. finishReason 확인
                # =============================================
                finish_reason = candidate.get(
                    "finishReason",
                    "UNKNOWN"
                )

                print(
                    "Gemini finish reason:",
                    finish_reason
                )

                content = candidate.get(
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

                # =============================================
                # 12. 빈 답변 처리
                # =============================================
                if not result_text:

                    print(
                        "ERROR: Empty Gemini text:",
                        json.dumps(
                            result_data,
                            ensure_ascii=False
                        )[:3000]
                    )

                    self._send_json(502, {
                        "error":
                        "AI 답변이 비어 있습니다. "
                        "다시 시도해주세요."
                    })

                    return

                # =============================================
                # 13. 출력이 토큰 제한으로 끊긴 경우
                # =============================================
                if finish_reason == "MAX_TOKENS":

                    print(
                        "WARNING: Gemini output reached MAX_TOKENS."
                    )

                    self._send_json(502, {
                        "error":
                        "AI 답변이 너무 길어 중간에 종료되었습니다. "
                        "다시 생성해주세요."
                    })

                    return

            except Exception as error:

                print(
                    "ERROR parsing Gemini response:",
                    repr(error)
                )

                self._send_json(502, {
                    "error":
                    "AI 응답을 처리하는 중 "
                    "오류가 발생했습니다."
                })

                return

            # =============================================
            # 14. 정상 성공 응답
            # =============================================
            self._send_json(200, {
                "result": result_text
            })

        # =============================================
        # 15. 예상하지 못한 서버 오류
        # =============================================
        except Exception as error:

            print(
                "UNEXPECTED SERVER ERROR:",
                repr(error)
            )

            self._send_json(500, {
                "error":
                "서버 오류가 발생했습니다. "
                "잠시 후 다시 시도해주세요."
            })