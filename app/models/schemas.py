# -*- coding: utf-8 -*-
"""REST API 요청과 응답 데이터 구조를 정의하는 Pydantic 스키마입니다."""

# 고정 선택 문자열을 표현하기 위해 Literal을 가져옵니다.
from typing import Any, Literal
# 입력값 검증과 설명을 위해 BaseModel과 Field를 가져옵니다.
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """통합 LangGraph 채팅 요청 스키마입니다."""

    # 사용자가 조사하려는 질문 또는 명령입니다.
    message: str = Field(min_length=2, max_length=3000)
    # 대화 기억을 구분하는 세션 식별자입니다.
    thread_id: str = Field(default="web-user", min_length=1, max_length=100)
    # 요청별로 선택하는 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = "gemini"
    # 교육용 검색 실패 폴백을 강제할지 지정합니다.
    force_fallback: bool = False


class TraceItem(BaseModel):
    """LangGraph 실행 단계 하나를 표현합니다."""

    # 실행 계층 또는 노드 이름입니다.
    stage: str
    # 해당 단계에서 수행한 작업 설명입니다.
    detail: str


class ChatResponse(BaseModel):
    """통합 에이전트의 최종 응답 스키마입니다."""

    # 사용자에게 보여 줄 최종 마크다운 답변입니다.
    answer: str
    # LangGraph가 선택한 최상위 실행 경로입니다.
    route: str
    # 실제 작업을 수행한 A2A 전문 에이전트 이름입니다.
    agent: str | None = None
    # 결과가 저장된 보고서의 상대 경로입니다.
    report_path: str | None = None
    # 검색 실패로 LLM 폴백이 사용되었는지 나타냅니다.
    used_fallback: bool = False
    # 요청 처리에 걸린 초 단위 시간입니다.
    elapsed_seconds: float
    # 각 계층의 실행 과정을 순서대로 반환합니다.
    trace: list[TraceItem]


class ToolCallRequest(BaseModel):
    """MCP 호환 도구 직접 호출 요청 스키마입니다."""

    # 실행할 도구 식별자입니다.
    tool_name: Literal["search_web", "search_knowledge", "analyze_competitors", "analyze_sales", "save_report"]
    # 도구에 전달할 문자열 인수 사전입니다.
    arguments: dict[str, Any] = Field(default_factory=dict)


class A2AMessageRequest(BaseModel):
    """전문 에이전트에 직접 위임하는 A2A 요청 스키마입니다."""

    # 호출할 전문 에이전트 이름입니다.
    agent_name: str
    # 전문 에이전트가 처리할 메시지입니다.
    message: str = Field(min_length=2, max_length=3000)
    # 선택한 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = "gemini"
    # 검색 폴백 강제 여부입니다.
    force_fallback: bool = False
