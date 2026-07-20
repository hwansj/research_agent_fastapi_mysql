# -*- coding: utf-8 -*-
"""도구 사용과 관찰을 반복하는 ReAct 리서치 에이전트입니다."""

# 최신 LangChain 표준 에이전트 생성 함수를 가져옵니다.
from langchain.agents import create_agent
# 공급자별 LLM 생성 함수를 가져옵니다.
from app.core.common import get_chat
# 최종 메시지 텍스트 추출 함수를 가져옵니다.
from app.services.message_utils import last_message_text
# 요청별로 구성된 공통 도구 목록을 가져옵니다.
from app.agents.tools import build_tools


def run_react(message: str, provider: str, force_fallback: bool = False) -> str:
    """질문을 분석하고 필요한 도구를 자율 선택하여 최종 답변을 만듭니다."""
    # 선택 공급자의 낮은 온도 채팅 모델을 생성합니다.
    model = get_chat(provider=provider, temperature=0.2)
    # 현재 요청에 맞춰 웹·RAG·CSV 도구를 생성합니다.
    tools = build_tools(provider, force_fallback)
    # 도구 호출 기반 ReAct 루프를 수행할 표준 LangChain 에이전트를 만듭니다.
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=(
            "너는 승승장구몰의 리서치 책임자다. 질문을 먼저 분석하고 필요한 도구만 호출하라. "
            "최신 공개 사실은 web_research, 내부 PDF·CSV 근거는 internal_knowledge_search, "
            "경쟁사 표는 competitor_csv_data, 내부 매출은 internal_sales_data를 사용하라. "
            "관찰한 근거 밖의 수치와 출처를 만들지 말고, 웹 검색 실패 폴백은 명확히 표시하라. "
            "최종 답변은 한국어 마크다운으로 작성하라."
        ),
    )
    # 사용자의 자연어 질문을 에이전트 메시지 형식으로 전달합니다.
    result = agent.invoke({"messages": [{"role": "user", "content": message}]})
    # 마지막 AI 메시지만 추출해 반환합니다.
    return last_message_text(result)
