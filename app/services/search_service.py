# -*- coding: utf-8 -*-
"""DuckDuckGo 검색과 검색 실패 폴백을 담당하는 서비스입니다."""

# 모델 응답을 공통 문자열로 바꾸는 함수를 가져옵니다.
from app.services.message_utils import extract_text
# 공급자별 채팅 모델 생성 함수를 가져옵니다.
from app.core.common import get_chat


def build_search_tool():
    """API 키가 필요 없는 DuckDuckGo LangChain 검색 도구를 생성합니다."""
    # 패키지 미설치가 서버 전체 시작을 막지 않도록 지연 임포트합니다.
    from langchain_community.tools import DuckDuckGoSearchResults
    # 제목·스니펫·링크가 포함된 검색 도구 객체를 반환합니다.
    return DuckDuckGoSearchResults()


def search_web(query: str, provider: str, force_fallback: bool = False) -> tuple[str, bool]:
    """웹을 검색하고 실패하면 선택 모델의 내부 지식으로 제한적 답변을 만듭니다."""
    # 앞뒤 공백을 제거한 검색어를 만듭니다.
    clean_query = query.strip()
    # 빈 검색어로 외부 호출을 하지 않도록 검증합니다.
    if not clean_query:
        raise ValueError("검색어를 입력해야 합니다.")
    # 교육용 폴백 강제 옵션이 아니면 실제 검색을 시도합니다.
    if not force_fallback:
        try:
            # 검색 도구를 생성합니다.
            tool = build_search_tool()
            # 검색 결과를 문자열로 변환해 폴백 미사용 상태로 반환합니다.
            return str(tool.invoke(clean_query)), False
        except Exception as exc:
            # 실제 오류 메시지를 폴백 프롬프트에 넣기 위해 저장합니다.
            error_message = str(exc)
    else:
        # 강제 폴백임을 명확히 기록합니다.
        error_message = "사용자가 교육용 검색 실패 폴백을 강제했습니다."
    # 검색에 실패한 경우 선택 공급자의 LLM을 생성합니다.
    llm = get_chat(provider=provider, temperature=0.2)
    # 최신성 한계와 금지 조건을 포함한 폴백 프롬프트를 만듭니다.
    prompt = (
        f"검색 질의: {clean_query}\n"
        "웹 검색을 사용할 수 없으므로 아는 범위에서 핵심만 정리하라. "
        "최신 검증이 되지 않았음을 첫 줄에 표시하고 확인되지 않은 수치와 출처를 만들지 마라. "
        f"검색 오류 참고: {error_message[:300]}"
    )
    # 모델 응답을 문자열로 변환해 폴백 사용 상태로 반환합니다.
    return extract_text(llm.invoke(prompt)), True
