// 주요 DOM 요소를 한 번만 찾아 재사용합니다.
const messageInput = document.querySelector("#message");
const sendButton = document.querySelector("#send");
const answerBox = document.querySelector("#answer");
const statusBox = document.querySelector("#status");
const traceList = document.querySelector("#trace");
const metaBox = document.querySelector("#meta");
const reportLink = document.querySelector("#report");
const saveDbButton = document.querySelector("#saveDb");

// 'DB에 저장' 버튼이 사용할 마지막 실행 결과를 보관합니다.
let lastResult = null;

// 예제 질문 버튼을 누르면 해당 질문을 입력창에 채웁니다.
document.querySelectorAll("[data-q]").forEach((button) => {
    // 각 버튼에 클릭 이벤트를 등록합니다.
    button.addEventListener("click", () => {
        // data-q 속성의 예제 질문을 textarea에 넣습니다.
        messageInput.value = button.dataset.q;
        // 바로 수정할 수 있도록 입력창에 포커스를 이동합니다.
        messageInput.focus();
    });
});

// 통합 에이전트 실행 버튼의 클릭 이벤트를 등록합니다.
sendButton.addEventListener("click", async () => {
    // 앞뒤 공백을 제거한 질문을 읽습니다.
    const message = messageInput.value.trim();
    // 빈 질문이면 API를 호출하지 않고 안내합니다.
    if (!message) {
        statusBox.textContent = "질문을 입력하세요.";
        return;
    }
    // 중복 실행을 막고 처리 중 상태를 표시합니다.
    sendButton.disabled = true;
    statusBox.textContent = "LangGraph 워크플로우를 실행하고 있습니다...";
    answerBox.textContent = "";
    traceList.innerHTML = "";
    metaBox.textContent = "";
    reportLink.hidden = true;
    // 새 실행이 시작되면 이전 결과 저장 버튼을 숨기고 상태를 초기화합니다.
    saveDbButton.hidden = true;
    lastResult = null;
    try {
        // FastAPI 통합 채팅 엔드포인트를 호출합니다.
        const response = await fetch("/api/v1/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: message,
                thread_id: document.querySelector("#threadId").value.trim() || "web-user",
                provider: document.querySelector("#provider").value,
                force_fallback: document.querySelector("#fallback").checked
            })
        });
        // JSON 응답을 파싱합니다.
        const data = await response.json();
        // 오류 응답이면 서버의 detail 메시지를 예외로 변환합니다.
        if (!response.ok) throw new Error(data.detail || "요청 처리 실패");
        // 최종 답변을 화면에 출력합니다.
        answerBox.textContent = data.answer;
        // 선택 경로와 처리 시간을 표시합니다.
        metaBox.textContent = `route=${data.route} / agent=${data.agent || "-"} / ${data.elapsed_seconds}초 / fallback=${data.used_fallback}`;
        // 각 trace 항목을 순서대로 목록에 추가합니다.
        data.trace.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = `${item.stage}: ${item.detail}`;
            traceList.appendChild(li);
        });
        // 'DB에 저장' 버튼이 사용할 주제·답변·완료 시각을 기록합니다.
        lastResult = {topic: message, result: data.answer, completed_at: new Date().toISOString()};
        // 답변이 준비되었으므로 DB 저장 버튼을 표시합니다.
        saveDbButton.hidden = false;
        saveDbButton.disabled = false;
        saveDbButton.textContent = "DB에 저장";
        // 보고서가 생성된 경우 다운로드 링크를 표시합니다.
        if (data.report_path) {
            reportLink.href = `/api/v1/reports/${encodeURIComponent(data.report_path)}`;
            reportLink.hidden = false;
        }
        // 정상 완료 상태를 표시합니다.
        statusBox.textContent = "처리가 완료되었습니다.";
    } catch (error) {
        // 네트워크 또는 서버 오류 메시지를 답변 영역에 출력합니다.
        statusBox.textContent = "실행 오류";
        answerBox.textContent = error.message;
    } finally {
        // 성공 여부와 관계없이 버튼을 다시 사용할 수 있게 합니다.
        sendButton.disabled = false;
    }
});


// 'DB에 저장' 버튼의 클릭 이벤트를 등록합니다.
saveDbButton.addEventListener("click", async () => {
    // 저장할 결과가 없으면 안내만 하고 종료합니다.
    if (!lastResult) {
        statusBox.textContent = "먼저 에이전트를 실행해 답변을 생성하세요.";
        return;
    }
    // 중복 저장을 막고 진행 상태를 표시합니다.
    saveDbButton.disabled = true;
    statusBox.textContent = "MySQL REPORT 테이블에 저장하고 있습니다...";
    try {
        // MCP 서버와 동일한 save_report 도구를 HTTP 경로로 실행합니다.
        const response = await fetch("/api/v1/tools/call", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                tool_name: "save_report",
                arguments: lastResult
            })
        });
        // JSON 응답을 파싱합니다.
        const data = await response.json();
        // 오류 응답이면 서버의 detail 메시지를 예외로 변환합니다.
        if (!response.ok) throw new Error(data.detail || "DB 저장 실패");
        // 저장 완료 메시지를 상태 영역에 표시합니다.
        statusBox.textContent = data.content;
        // 같은 답변의 중복 저장을 막기 위해 버튼 문구를 바꿉니다.
        saveDbButton.textContent = "저장 완료";
    } catch (error) {
        // 실패 시 오류를 표시하고 다시 시도할 수 있게 버튼을 되돌립니다.
        statusBox.textContent = `DB 저장 오류: ${error.message}`;
        saveDbButton.disabled = false;
    }
});
