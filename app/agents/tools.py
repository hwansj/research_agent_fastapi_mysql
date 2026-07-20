# -*- coding: utf-8 -*-
"""ReAct와 MCP가 공통으로 사용하는 리서치 도구를 정의합니다."""

# LangChain 도구 데코레이터를 가져옵니다.
from langchain_core.tools import tool
# 데이터 분석 문맥 함수를 가져옵니다.
from app.services.data_service import competitor_context, sales_context
# 내부 RAG 검색 함수를 가져옵니다.
from app.services.rag_service import search_knowledge
# 웹 검색 함수를 가져옵니다.
from app.services.search_service import search_web


def build_tools(provider: str, force_fallback: bool = False):
    """현재 요청 공급자와 폴백 옵션이 고정된 LangChain 도구 목록을 만듭니다."""

    @tool
    def web_research(query: str) -> str:
        """최신 공개 시장 정보, 기업 동향, 기술 동향을 웹에서 검색합니다."""
        # 공통 검색 서비스를 호출합니다.
        result, used_fallback = search_web(query, provider, force_fallback)
        # 에이전트가 신뢰도를 판단하도록 검색 방식 표시를 추가합니다.
        return f"검색 방식={'LLM 폴백' if used_fallback else '웹 검색'}\n{result}"

    @tool
    def internal_knowledge_search(query: str) -> str:
        """프로젝트의 PDF와 CSV에서 관련 근거를 벡터 검색합니다."""
        # 공급자별 임베딩을 사용하는 RAG 검색 결과를 반환합니다.
        return search_knowledge(query, provider)

    @tool
    def competitor_csv_data() -> str:
        """competitor_data.csv의 전체 경쟁사 표를 반환합니다."""
        # 경쟁사 표와 회사 목록을 읽습니다.
        table, companies = competitor_context()
        # 누락 검증에 사용할 회사 목록을 표 앞에 함께 반환합니다.
        return f"경쟁사 목록: {', '.join(companies)}\n\n{table}"

    @tool
    def internal_sales_data() -> str:
        """monthly_sales.csv와 products.csv의 내부 판매 데이터를 반환합니다."""
        # 결합된 내부 판매 데이터 문맥을 반환합니다.
        return sales_context()

    # ReAct 에이전트와 MCP 어댑터가 사용할 네 개 도구를 반환합니다.
    return [web_research, internal_knowledge_search, competitor_csv_data, internal_sales_data]
