# -*- coding: utf-8 -*-
"""표준 MCP 클라이언트가 stdio로 연결할 수 있는 독립 MCP 서버입니다."""

# 공식 MCP Python SDK의 FastMCP 서버 클래스를 가져옵니다.
from mcp.server.fastmcp import FastMCP
# 공통 도구 실행 함수를 가져옵니다.
from app.mcp_server.tools import call_tool

# 도구 이름과 설명을 공개할 MCP 서버 객체를 생성합니다.
mcp = FastMCP("research-agent-tools")


@mcp.tool()
def search_web_tool(query: str, provider: str = "gemini", force_fallback: bool = False) -> str:
    """최신 공개 정보를 웹에서 검색하고 실패 시 제한적 LLM 폴백을 반환합니다."""
    # 공통 도구 실행기를 호출하고 본문을 문자열로 반환합니다.
    return str(call_tool("search_web", {"query": query, "provider": provider, "force_fallback": force_fallback})["content"])


@mcp.tool()
def search_knowledge_tool(query: str, provider: str = "gemini") -> str:
    """프로젝트 PDF와 CSV를 임베딩 검색하여 관련 근거를 반환합니다."""
    # 공통 도구 실행기로 RAG 검색을 호출합니다.
    return str(call_tool("search_knowledge", {"query": query, "provider": provider})["content"])


@mcp.tool()
def competitor_data_tool() -> str:
    """competitor_data.csv의 경쟁사 분석용 표를 반환합니다."""
    # 공통 도구 실행기로 경쟁사 데이터를 읽습니다.
    return str(call_tool("analyze_competitors", {})["content"])


@mcp.tool()
def sales_data_tool() -> str:
    """monthly_sales.csv와 products.csv의 내부 판매 자료를 반환합니다."""
    # 공통 도구 실행기로 내부 판매 데이터를 읽습니다.
    return str(call_tool("analyze_sales", {})["content"])


@mcp.tool()
def save_report_tool(topic: str, result: str, completed_at: str = "") -> str:
    """최종 답변을 MySQL REPORT 테이블(TOPIC·RESULT·RESULT_TIME)에 저장합니다."""
    # 공통 도구 실행기로 MySQL 저장을 호출하고 결과 요약을 반환합니다.
    return str(call_tool("save_report", {"topic": topic, "result": result, "completed_at": completed_at})["content"])


# 모듈을 직접 실행한 경우에만 표준 입출력 MCP 서버를 시작합니다.
if __name__ == "__main__":
    # PyCharm 또는 MCP 호스트가 자식 프로세스로 실행할 수 있도록 stdio 전송을 사용합니다.
    mcp.run(transport="stdio")
