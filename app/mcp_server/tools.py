# -*- coding: utf-8 -*-
"""MCP 서버와 FastAPI 직접 호출 API가 공유하는 순수 도구 함수입니다."""

# 데이터 분석 문맥 함수를 가져옵니다.
from app.services.data_service import competitor_context, sales_context
# MySQL 저장 함수를 가져옵니다.
from app.services.db_service import save_report
# 내부 RAG 검색 함수를 가져옵니다.
from app.services.rag_service import search_knowledge
# 웹 검색 함수를 가져옵니다.
from app.services.search_service import search_web


def call_tool(tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
    """도구 이름과 인수를 검증해 공통 결과 사전으로 반환합니다."""
    # 공급자를 문자열로 읽고 기본값을 Gemini로 지정합니다.
    provider = str(arguments.get("provider", "gemini"))
    # 웹 검색 도구를 처리합니다.
    if tool_name == "search_web":
        # 검색어를 문자열로 읽습니다.
        query = str(arguments.get("query", ""))
        # 강제 폴백 플래그를 불리언으로 읽습니다.
        force_fallback = bool(arguments.get("force_fallback", False))
        # 검색 서비스를 호출합니다.
        result, fallback = search_web(query, provider, force_fallback)
        # 표준화된 MCP 호환 결과를 반환합니다.
        return {"tool": tool_name, "content": result, "used_fallback": fallback}
    # 내부 지식 검색 도구를 처리합니다.
    if tool_name == "search_knowledge":
        # 질문을 읽고 RAG 검색을 실행합니다.
        result = search_knowledge(str(arguments.get("query", "")), provider)
        # 표준 결과를 반환합니다.
        return {"tool": tool_name, "content": result, "used_fallback": False}
    # 경쟁사 분석 원본 데이터 도구를 처리합니다.
    if tool_name == "analyze_competitors":
        # 표와 회사 목록을 읽습니다.
        table, companies = competitor_context()
        # 표준 결과를 반환합니다.
        return {"tool": tool_name, "content": table, "companies": companies}
    # 내부 매출 데이터 도구를 처리합니다.
    if tool_name == "analyze_sales":
        # 결합된 내부 매출 문맥을 반환합니다.
        return {"tool": tool_name, "content": sales_context()}
    # 최종 답변 MySQL 저장 도구를 처리합니다.
    if tool_name == "save_report":
        # 주제·답변·완료 시각을 문자열로 읽어 REPORT 테이블에 저장합니다.
        saved = save_report(str(arguments.get("topic", "")), str(arguments.get("result", "")), str(arguments.get("completed_at", "")))
        # 저장 행 ID와 기록된 완료 시각을 표준 결과로 반환합니다.
        return {"tool": tool_name, "content": f"REPORT 테이블 저장 완료 (ID={saved['row_id']}, RESULT_TIME={saved['result_time']})", "row_id": saved["row_id"], "result_time": saved["result_time"]}
    # 등록되지 않은 도구는 오류로 알립니다.
    raise ValueError(f"알 수 없는 MCP 도구입니다: {tool_name}")
