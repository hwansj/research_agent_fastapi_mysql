# -*- coding: utf-8 -*-
"""ReAct·RAG·A2A·MCP를 연결하는 LangGraph 오케스트레이션 모듈입니다."""

# 누적 trace 상태를 안전하게 합치기 위해 operator를 가져옵니다.
import operator
# 실행 시간을 계산하기 위해 time을 가져옵니다.
import time
# 상태 필드 타입을 정의하기 위해 Annotated와 TypedDict를 가져옵니다.
from typing import Annotated, TypedDict
# LangGraph 시작·종료 상수와 상태 그래프 클래스를 가져옵니다.
from langgraph.graph import END, START, StateGraph
# ReAct 실행 함수를 가져옵니다.
from app.agents.react_agent import run_react
# A2A 전문 에이전트 위임 함수를 가져옵니다.
from app.a2a.specialists import dispatch
# MCP 호환 도구 실행 함수를 가져옵니다.
from app.mcp_server.tools import call_tool


class ResearchState(TypedDict, total=False):
    """LangGraph 노드들이 공유하는 리서치 요청 상태입니다."""

    # 사용자가 보낸 원문 메시지입니다.
    message: str
    # 멀티턴 요청을 구분하는 식별자입니다.
    thread_id: str
    # OpenAI 또는 Gemini 공급자입니다.
    provider: str
    # 검색 실패 폴백 강제 여부입니다.
    force_fallback: bool
    # 분류 노드가 선택한 최상위 경로입니다.
    route: str
    # A2A 경로에서 선택한 전문 에이전트입니다.
    agent: str
    # 최종 마크다운 답변입니다.
    answer: str
    # 저장된 보고서 파일명입니다.
    report_path: str | None
    # 검색 폴백 사용 여부입니다.
    used_fallback: bool
    # 시작 시간 값입니다.
    started_at: float
    # 전체 처리 시간입니다.
    elapsed_seconds: float
    # 각 노드의 실행 설명을 누적하는 목록입니다.
    trace: Annotated[list[dict[str, str]], operator.add]


def start_node(state: ResearchState) -> ResearchState:
    """요청 시작 시각과 최초 실행 기록을 설정합니다."""
    # 현재 고해상도 시간을 기록하고 시작 trace를 반환합니다.
    return {"started_at": time.perf_counter(), "trace": [{"stage": "START", "detail": f"thread={state.get('thread_id', 'web-user')} 요청 시작"}]}


def classify_node(state: ResearchState) -> ResearchState:
    """질문의 목적을 규칙 기반으로 분류해 다음 계층을 선택합니다."""
    # 대소문자와 공백 차이를 줄이기 위해 메시지를 정규화합니다.
    message = state["message"].strip().lower()
    # 직접 도구 실행 표현은 MCP 경로로 보냅니다.
    if message.startswith("mcp:") or "도구 직접" in message:
        route, agent = "mcp", "mcp-tool-server"
    # 내부 자료, 문서, PDF, 지식베이스 질문은 RAG 전문 에이전트로 보냅니다.
    elif any(keyword in message for keyword in ["내부 문서", "pdf", "자료에서", "근거", "지식베이스", "rag"]):
        route, agent = "rag", "knowledge-agent"
    # 경쟁사 또는 매출 CSV 분석은 A2A 데이터 분석가로 보냅니다.
    elif any(keyword in message for keyword in ["경쟁사", "매출", "상품 분석", "csv", "내부 데이터"]):
        route, agent = "a2a", "data-analyst-agent"
    # 사실 확인·교차 검증 요청은 A2A 교차 검증가로 보냅니다.
    elif any(keyword in message for keyword in ["교차 검증", "사실 확인", "검증해", "맞는지"]):
        route, agent = "a2a", "cross-check-agent"
    # 심층 조사·하위 질의 요청은 A2A 심층 조사 에이전트로 보냅니다.
    elif any(keyword in message for keyword in ["심층", "깊이 조사", "하위 질의", "다각도"]):
        route, agent = "a2a", "deep-research-agent"
    # 일반 최신 시장 조사 요청은 웹 전문 A2A 에이전트로 보냅니다.
    elif any(keyword in message for keyword in ["최신", "시장 동향", "웹 검색", "뉴스"]):
        route, agent = "a2a", "web-research-agent"
    # 여러 도구 조합이 필요하거나 일반 질문이면 ReAct가 자율 결정합니다.
    else:
        route, agent = "react", "research-react-agent"
    # 선택 결과와 trace를 상태에 반영합니다.
    return {"route": route, "agent": agent, "trace": [{"stage": "LangGraph", "detail": f"route={route}, agent={agent}로 분류"}]}


def route_after_classify(state: ResearchState) -> str:
    """분류된 route 문자열을 조건부 간선 키로 반환합니다."""
    # route 값이 없을 경우 안전하게 ReAct를 기본 경로로 사용합니다.
    return state.get("route", "react")


def mcp_node(state: ResearchState) -> ResearchState:
    """MCP 호환 순수 도구를 직접 실행합니다."""
    # mcp: 접두사를 제거한 실제 검색어를 만듭니다.
    query = state["message"].removeprefix("mcp:").strip()
    # 현재 예제에서는 MCP 웹 검색 도구를 직접 호출합니다.
    result = call_tool("search_web", {"query": query, "provider": state["provider"], "force_fallback": state.get("force_fallback", False)})
    # 도구 결과를 최종 답변과 trace로 반환합니다.
    return {"answer": str(result["content"]), "used_fallback": bool(result.get("used_fallback", False)), "trace": [{"stage": "MCP", "detail": "search_web 도구를 직접 호출"}]}


def rag_node(state: ResearchState) -> ResearchState:
    """A2A knowledge-agent를 통해 RAG 근거 답변을 생성합니다."""
    # 전문 지식 에이전트로 질문을 위임합니다.
    answer, report_path, fallback = dispatch("knowledge-agent", state["message"], state["provider"], state.get("force_fallback", False))
    # RAG 실행 결과를 상태에 반영합니다.
    return {"answer": answer, "report_path": report_path, "used_fallback": fallback, "trace": [{"stage": "RAG", "detail": "PDF·CSV FAISS 검색 후 근거 고정 답변 생성"}, {"stage": "A2A", "detail": "knowledge-agent가 작업 수행"}]}


def a2a_node(state: ResearchState) -> ResearchState:
    """선택된 A2A 전문 에이전트에 작업을 위임합니다."""
    # 분류 노드에서 지정한 전문 에이전트를 호출합니다.
    answer, report_path, fallback = dispatch(state["agent"], state["message"], state["provider"], state.get("force_fallback", False))
    # 전문 에이전트 결과를 상태에 반영합니다.
    return {"answer": answer, "report_path": report_path, "used_fallback": fallback, "trace": [{"stage": "A2A", "detail": f"{state['agent']}에 메시지 위임 및 결과 수신"}]}


def react_node(state: ResearchState) -> ResearchState:
    """ReAct 에이전트가 질문에 필요한 도구를 자율 선택하도록 실행합니다."""
    # ReAct 에이전트에 질문과 공급자 설정을 전달합니다.
    answer = run_react(state["message"], state["provider"], state.get("force_fallback", False))
    # 최종 ReAct 응답과 실행 기록을 반환합니다.
    return {"answer": answer, "used_fallback": False, "trace": [{"stage": "ReAct", "detail": "추론→도구 선택→실행→관찰→최종 답변 루프 수행"}]}


def finish_node(state: ResearchState) -> ResearchState:
    """전체 실행 시간을 계산하고 완료 trace를 추가합니다."""
    # 시작 시간이 없으면 현재 시간을 사용해 음수 시간을 방지합니다.
    started_at = state.get("started_at", time.perf_counter())
    # 전체 경과 시간을 소수점 네 자리로 계산합니다.
    elapsed = round(time.perf_counter() - started_at, 4)
    # 경과 시간과 완료 기록을 반환합니다.
    return {"elapsed_seconds": elapsed, "trace": [{"stage": "END", "detail": f"전체 처리 완료: {elapsed:.4f}초"}]}


def build_workflow():
    """전체 상태 그래프를 구성하고 실행 가능한 그래프로 컴파일합니다."""
    # ResearchState를 공유 상태로 사용하는 그래프 빌더를 생성합니다.
    graph = StateGraph(ResearchState)
    # 요청 시작 노드를 등록합니다.
    graph.add_node("start", start_node)
    # 경로 분류 노드를 등록합니다.
    graph.add_node("classify", classify_node)
    # MCP 직접 도구 노드를 등록합니다.
    graph.add_node("mcp", mcp_node)
    # RAG 전문 노드를 등록합니다.
    graph.add_node("rag", rag_node)
    # A2A 전문 에이전트 노드를 등록합니다.
    graph.add_node("a2a", a2a_node)
    # ReAct 자율 도구 노드를 등록합니다.
    graph.add_node("react", react_node)
    # 공통 완료 노드를 등록합니다.
    graph.add_node("finish", finish_node)
    # 그래프 시작점을 start 노드에 연결합니다.
    graph.add_edge(START, "start")
    # start 다음에 classify를 실행합니다.
    graph.add_edge("start", "classify")
    # classify 결과에 따라 네 실행 경로 중 하나를 선택합니다.
    graph.add_conditional_edges("classify", route_after_classify, {"mcp": "mcp", "rag": "rag", "a2a": "a2a", "react": "react"})
    # 각 실행 경로가 완료되면 공통 finish 노드로 연결합니다.
    graph.add_edge("mcp", "finish")
    graph.add_edge("rag", "finish")
    graph.add_edge("a2a", "finish")
    graph.add_edge("react", "finish")
    # finish 노드에서 그래프 실행을 종료합니다.
    graph.add_edge("finish", END)
    # 정의한 그래프를 실행 가능한 객체로 컴파일합니다.
    return graph.compile()

# 서버 전체에서 재사용할 컴파일된 그래프를 한 번 생성합니다.
WORKFLOW = build_workflow()
