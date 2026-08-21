const form = document.getElementById("aiForm");
const submitBtn = document.getElementById("submitBtn");
const statusEl = document.getElementById("status");
const resultBox = document.getElementById("resultBox");
const resultEl = document.getElementById("result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const topic = document.getElementById("topic").value.trim();
  const audience = document.getElementById("audience").value.trim();
  const tone = document.getElementById("tone").value;

  // 필수 실패 처리 1: 빈 입력
  if (!topic || !audience) {
    statusEl.textContent = "발표 주제와 발표 대상을 모두 입력해주세요.";
    resultBox.classList.add("hidden");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "생성 중...";
  statusEl.textContent = "AI가 답변을 만들고 있습니다.";
  resultBox.classList.add("hidden");

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ topic, audience, tone }),
      signal: controller.signal
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "API 요청에 실패했습니다.");
    }

    resultEl.textContent = data.result;
    resultBox.classList.remove("hidden");
    statusEl.textContent = "완료되었습니다.";
  } catch (error) {
    if (error.name === "AbortError") {
      statusEl.textContent = "응답이 늦어지고 있습니다. 잠시 후 다시 시도해주세요.";
    } else {
      statusEl.textContent = error.message || "오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
    }
  } finally {
    clearTimeout(timeoutId);
    submitBtn.disabled = false;
    submitBtn.textContent = "AI로 생성하기";
  }
});
