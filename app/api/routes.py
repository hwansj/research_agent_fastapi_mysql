# -*- coding: utf-8 -*-
"""웹 UI가 호출할 Research Agent REST API 라우터입니다."""

# 파일 다운로드 응답과 HTTP 오류 처리를 위해 FastAPI 구성요소를 가져옵니다.
from fastapi import APIRouter, HTTPException
# 생성된 마크다운 보고서를 내려주기 위해 FileResponse를 가져옵니다.
from fastapi.responses import FileResponse
# 에이전트 카드 목록과 직접 위임 함수를 가져옵니다.
from app.a2a.specialists import dispatch, list_agent_cards
# 공통 경로와 API 키 상태 확인용 os를 가져옵니다.
import os
# 보고서 경로를 가져옵니다.
from app.core.common import REPORTS
# 데이터 파일 목록 함수를 가져옵니다.
from app.services.data_service import list_data_files
# LangGraph 통합 워크플로우를 가져옵니다.
from app.graph.workflow import WORKFLOW
# API 요청·응답 스키마를 가져옵니다.
from app.models.schemas import A2AMessageRequest, ChatRequest, ChatResponse, ToolCallRequest
# MCP 호환 도구 실행 함수를 가져옵니다.
from app.mcp_server.tools import call_tool
# RAG 캐시 초기화 함수를 가져옵니다.
from app.services.rag_service import reset_store

# 모든 REST 엔드포인트를 묶는 라우터 객체를 생성합니다.
router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    """서버 상태와 API 키 설정 여부를 반환합니다."""
    # 키 실제 값은 노출하지 않고 존재 여부만 불리언으로 반환합니다.
    return {"status": "ok", "openai_key": bool(os.getenv("OPENAI_API_KEY")), "gemini_key": bool(os.getenv("GOOGLE_API_KEY"))}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """LangGraph 전체 워크플로우로 사용자 요청을 처리합니다."""
    try:
        # 검증된 요청값을 그래프 공유 상태로 전달합니다.
        result = WORKFLOW.invoke({"message": request.message, "thread_id": request.thread_id, "provider": request.provider, "force_fallback": request.force_fallback, "trace": []})
        # 그래프 결과를 고정된 API 응답 스키마로 변환합니다.
        return ChatResponse(answer=result.get("answer", "답변이 생성되지 않았습니다."), route=result.get("route", "unknown"), agent=result.get("agent"), report_path=result.get("report_path"), used_fallback=result.get("used_fallback", False), elapsed_seconds=result.get("elapsed_seconds", 0.0), trace=result.get("trace", []))
    except Exception as exc:
        # API 키, 네트워크, 패키지, 문서 오류를 HTTP 500으로 명확히 전달합니다.
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc


@router.post("/tools/call")
def tools_call(request: ToolCallRequest) -> dict[str, object]:
    """MCP 서버와 동일한 순수 도구를 HTTP로 직접 실행합니다."""
    try:
        # 요청한 도구 이름과 인수를 공통 실행기에 전달합니다.
        return call_tool(request.tool_name, request.arguments)
    except Exception as exc:
        # 잘못된 도구 또는 실행 오류를 400 응답으로 변환합니다.
        raise HTTPException(status_code=400, detail=f"{type(exc).__name__}: {exc}") from exc


@router.get("/a2a/agents")
def a2a_agents() -> list[dict[str, object]]:
    """사용 가능한 전문 에이전트 카드를 반환합니다."""
    # JSON 변환 가능한 에이전트 카드 목록을 반환합니다.
    return list_agent_cards()


@router.get("/.well-known/agent-card.json")
def public_agent_card() -> dict[str, object]:
    """통합 Research Agent의 공개 A2A 에이전트 카드를 반환합니다."""
    # 통합 서버의 기능과 엔드포인트를 설명하는 카드를 반환합니다.
    return {"name": "research-agent-orchestrator", "description": "ReAct·RAG·A2A·LangGraph·MCP 통합 리서치 에이전트", "url": "/api/v1/a2a/message", "version": "2.0.0", "skills": list_agent_cards()}


@router.post("/a2a/message")
def a2a_message(request: A2AMessageRequest) -> dict[str, object]:
    """지정한 전문 에이전트에 메시지를 직접 위임합니다."""
    try:
        # A2A 디스패처를 호출합니다.
        answer, report_path, fallback = dispatch(request.agent_name, request.message, request.provider, request.force_fallback)
        # 에이전트 결과를 표준 사전으로 반환합니다.
        return {"agent": request.agent_name, "answer": answer, "report_path": report_path, "used_fallback": fallback}
    except Exception as exc:
        # 에이전트 이름 또는 처리 오류를 HTTP 400으로 반환합니다.
        raise HTTPException(status_code=400, detail=f"{type(exc).__name__}: {exc}") from exc


@router.get("/data/files")
def data_files() -> list[dict[str, object]]:
    """프로젝트에 포함된 data.zip 파일 목록을 반환합니다."""
    # 상대 경로와 파일 크기 목록을 반환합니다.
    return list_data_files()


@router.post("/rag/reset")
def rag_reset() -> dict[str, str]:
    """OpenAI·Gemini FAISS 인덱스 메모리 캐시를 초기화합니다."""
    # 모든 공급자별 벡터 저장소를 제거합니다.
    reset_store()
    # 다음 요청에서 다시 구축된다는 안내를 반환합니다.
    return {"message": "RAG 캐시를 초기화했습니다. 다음 검색에서 다시 생성됩니다."}


@router.get("/reports/{filename}")
def download_report(filename: str):
    """reports 폴더에 저장된 마크다운 리포트를 다운로드합니다."""
    # 경로 구분자가 포함된 파일명은 상위 폴더 접근 위험이 있어 차단합니다.
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="잘못된 파일명입니다.")
    # reports 폴더 아래의 파일 경로를 계산합니다.
    path = REPORTS / filename
    # 파일이 없으면 404 오류를 반환합니다.
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="보고서 파일을 찾을 수 없습니다.")
    # 브라우저가 파일을 내려받을 수 있는 응답을 반환합니다.
    return FileResponse(path, media_type="text/markdown", filename=filename)


@router.get("/exercises")
def exercises() -> dict[str, object]:
    """원본 콘솔 프로젝트의 두 실습 해답 실행 방법을 반환합니다."""
    # 별도 중복 코드를 만들지 않고 A2A 엔드포인트로 실행할 요청 예제를 제공합니다.
    return {"exercise_1": {"description": "경쟁사 CSV 리포트", "agent_name": "data-analyst-agent", "message": "경쟁사 CSV를 분석하고 모든 경쟁사를 포함한 리포트를 작성해줘"}, "exercise_2": {"description": "다중 하위 질의 심층 조사", "agent_name": "deep-research-agent", "message": "무선이어버드 시장을 다각도로 심층 조사해줘"}}
