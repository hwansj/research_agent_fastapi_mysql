# -*- coding: utf-8 -*-
"""A2A 방식으로 역할을 분리한 전문 리서치 에이전트 모듈입니다."""

# 에이전트 메타데이터를 간단히 표현하기 위해 dataclass와 asdict를 가져옵니다.
from dataclasses import asdict, dataclass
# 공급자별 LLM 생성 함수를 가져옵니다.
from app.core.common import get_chat
# 경쟁사와 매출 데이터 문맥을 가져옵니다.
from app.services.data_service import competitor_context, sales_context
# 모델 응답 텍스트 추출 함수를 가져옵니다.
from app.services.message_utils import extract_text
# 리포트 저장 함수를 가져옵니다.
from app.services.report_service import save_report
# 내부 문서 RAG 검색 함수를 가져옵니다.
from app.services.rag_service import search_knowledge
# 웹 검색 함수를 가져옵니다.
from app.services.search_service import search_web


@dataclass(frozen=True)
class AgentCard:
    """전문 에이전트의 기능을 공개하는 A2A 에이전트 카드입니다."""

    # 호출에 사용할 고유 이름입니다.
    name: str
    # 에이전트가 담당하는 역할 설명입니다.
    description: str
    # 에이전트가 제공하는 기술 목록입니다.
    skills: tuple[str, ...]
    # 직접 메시지를 보낼 API 주소입니다.
    endpoint: str = "/api/v1/a2a/message"
    # 카드 스키마의 프로젝트 버전입니다.
    version: str = "2.0.0"


# 외부 오케스트레이터가 발견할 수 있는 전문 에이전트 카드를 정의합니다.
AGENT_CARDS = {
    "web-research-agent": AgentCard(
        "web-research-agent",
        "최신 공개 정보를 검색하고 출처 후보를 수집합니다.",
        ("웹 검색", "검색 폴백", "시장 동향"),
    ),
    "knowledge-agent": AgentCard(
        "knowledge-agent",
        "내부 PDF와 CSV를 RAG 방식으로 검색합니다.",
        ("PDF RAG", "CSV RAG", "근거 검색"),
    ),
    "deep-research-agent": AgentCard(
        "deep-research-agent",
        "주제를 여러 관점으로 분해하고 결과를 종합합니다.",
        ("질의 분해", "다중 검색", "종합 리포트"),
    ),
    "cross-check-agent": AgentCard(
        "cross-check-agent",
        "서로 다른 검색어로 주장을 교차 검증합니다.",
        ("교차 검증", "신뢰도 판정"),
    ),
    "data-analyst-agent": AgentCard(
        "data-analyst-agent",
        "경쟁사와 내부 매출 CSV를 분석합니다.",
        ("경쟁사 분석", "매출 분석", "CSV 리포트"),
    ),
}


def list_agent_cards() -> list[dict[str, object]]:
    """JSON 응답 가능한 에이전트 카드 목록을 반환합니다."""
    # dataclass 객체를 일반 사전으로 변환해 목록으로 반환합니다.
    return [asdict(card) for card in AGENT_CARDS.values()]


def _llm_report(prompt: str, provider: str, temperature: float = 0.2) -> str:
    """공통 프롬프트로 선택한 LLM의 마크다운 답변을 생성합니다."""
    # 선택 공급자의 모델을 생성합니다.
    llm = get_chat(provider=provider, temperature=temperature)
    # 모델을 호출하고 공급자별 형식을 공통 문자열로 바꿉니다.
    return extract_text(llm.invoke(prompt))


def web_research_agent(
    message: str,
    provider: str,
    force_fallback: bool = False,
) -> tuple[str, str | None, bool]:
    """최신 공개 정보를 검색하고 근거 기반 보고서를 작성합니다."""
    # 사용자의 메시지를 검색어로 웹 검색합니다.
    result, fallback = search_web(message, provider, force_fallback)
    # 검색 결과만 근거로 사용하도록 최종 작성 프롬프트를 만듭니다.
    prompt = (
        f"조사 주제: {message}\n\n"
        f"[검색 결과]\n{result[:7000]}\n\n"
        "검색 결과를 근거로 한국어 마크다운 리포트를 작성하라. "
        "## 개요, ## 핵심 동향, ## 시사점, ## 참고 출처, ## 한계를 포함하라. "
        "확인하지 못한 URL이나 수치를 만들지 마라."
    )
    # 검색 근거를 종합한 보고서 본문을 생성합니다.
    body = _llm_report(prompt, provider, 0.2)
    # 보고서를 파일로 저장합니다.
    path = save_report(message, body, provider, "web_research")
    # 본문, 상대 경로, 폴백 여부를 반환합니다.
    return body, path.name, fallback


def knowledge_agent(message: str, provider: str) -> tuple[str, None, bool]:
    """내부 자료를 RAG로 검색하고 근거 고정 답변을 작성합니다."""
    # 질문과 유사한 내부 근거를 검색합니다.
    context = search_knowledge(message, provider)
    # 문서 근거 밖의 내용을 만들지 않도록 프롬프트를 구성합니다.
    prompt = (
        f"질문: {message}\n\n"
        f"[내부 근거]\n{context}\n\n"
        "내부 근거만 사용해 한국어로 답하라. 근거가 부족하면 부족하다고 명시하라. "
        "답변 끝에 사용한 source와 page를 정리하라."
    )
    # 근거 고정 답변을 생성합니다.
    body = _llm_report(prompt, provider, 0.0)
    # 저장 경로 없음과 폴백 미사용 상태를 함께 반환합니다.
    return body, None, False


def deep_research_agent(
    message: str,
    provider: str,
    force_fallback: bool = False,
) -> tuple[str, str | None, bool]:
    """주제를 네 관점으로 분해하고 A2A 하위 검색 결과를 종합합니다."""
    # 범용적으로 겹치지 않는 네 하위 질의를 생성합니다.
    queries = [
        f"{message} 시장 규모 성장",
        f"{message} 기술 제품 동향",
        f"{message} 소비자 가격 동향",
        f"{message} 주요 기업 경쟁 구도",
    ]
    # 검색 결과 블록을 저장할 목록을 준비합니다.
    findings: list[str] = []
    # 하나라도 폴백이 사용됐는지 누적할 변수를 준비합니다.
    used_fallback = False
    # 각 하위 질의를 독립적으로 검색합니다.
    for query in queries:
        # 웹 검색 전문 기능에 하위 질의를 전달합니다.
        result, fallback = search_web(query, provider, force_fallback)
        # 폴백 여부를 누적합니다.
        used_fallback = used_fallback or fallback
        # 종합 프롬프트에 넣을 제한된 검색 결과 블록을 추가합니다.
        findings.append(
            f"[하위 질의] {query}\n"
            f"[방식] {'LLM 폴백' if fallback else '웹 검색'}\n"
            f"{result[:2500]}"
        )
    # 모든 하위 조사 결과를 연결합니다.
    context = "\n\n".join(findings)
    # 중복과 충돌을 처리하는 종합 프롬프트를 구성합니다.
    prompt = (
        f"원래 주제: {message}\n\n"
        f"{context}\n\n"
        "모든 하위 질의를 반영한 심층 리포트를 작성하라. ## 개요, ## 시장, ## 기술·제품, "
        "## 소비자·가격, ## 경쟁 구도, ## 시사점, ## 조사 한계를 포함하라. "
        "상충 내용은 단정하지 마라."
    )
    # 심층 종합 리포트를 생성합니다.
    body = _llm_report(prompt, provider, 0.2)
    # 생성된 심층 리포트를 저장합니다.
    path = save_report(message, body, provider, "deep_research")
    # 본문, 파일명, 누적 폴백 여부를 반환합니다.
    return body, path.name, used_fallback


def cross_check_agent(
    message: str,
    provider: str,
    force_fallback: bool = False,
) -> tuple[str, None, bool]:
    """하나의 주장을 표현이 다른 두 검색어로 교차 검증합니다."""
    # 첫 번째는 주장 원문을 중심으로 검색합니다.
    result_a, fallback_a = search_web(message, provider, force_fallback)
    # 두 번째는 사실 확인 키워드를 추가해 독립적으로 검색합니다.
    result_b, fallback_b = search_web(
        f"{message} fact check evidence",
        provider,
        force_fallback,
    )
    # 두 결과를 비교하는 판정 프롬프트를 구성합니다.
    prompt = (
        f"검증할 주장: {message}\n\n"
        f"[검색 A]\n{result_a[:3000]}\n\n"
        f"[검색 B]\n{result_b[:3000]}\n\n"
        "일치 여부를 일치/부분일치/불일치로, 신뢰도를 높음/보통/낮음으로 판정하라. "
        "검색 폴백이나 약한 출처가 있으면 보수적으로 판정하고 근거와 주의사항을 작성하라."
    )
    # 교차 검증 결과를 생성합니다.
    body = _llm_report(prompt, provider, 0.0)
    # 두 검색 중 하나라도 폴백이면 True를 반환합니다.
    return body, None, fallback_a or fallback_b


def data_analyst_agent(message: str, provider: str) -> tuple[str, str | None, bool]:
    """사용자 질문에 따라 경쟁사 또는 내부 매출 CSV를 분석합니다."""
    # 경쟁사 관련 키워드가 있으면 경쟁사 데이터로 분기합니다.
    if "경쟁" in message or "competitor" in message.lower():
        # 경쟁사 표와 필수 회사 목록을 읽습니다.
        table, companies = competitor_context()
        # 모든 회사를 빠짐없이 언급하도록 프롬프트를 구성합니다.
        prompt = (
            f"요청: {message}\n"
            f"경쟁사 목록: {', '.join(companies)}\n\n"
            f"{table}\n\n"
            "이 표만 사용해 ## 개요, ## 경쟁사별 강약점, ## 비교 요약, ## 시사점을 작성하라. "
            "모든 경쟁사 이름을 한 번 이상 포함하고 표에 없는 사실을 만들지 마라."
        )
        # 경쟁사 보고서를 생성합니다.
        body = _llm_report(prompt, provider, 0.2)
        # 경쟁사 전용 접두사로 저장합니다.
        path = save_report("경쟁사 CSV 분석", body, provider, "competitor")
    else:
        # 월별 매출과 상품 데이터를 결합해 읽습니다.
        context = sales_context()
        # 내부 데이터에만 근거한 분석 프롬프트를 구성합니다.
        prompt = (
            f"요청: {message}\n\n"
            f"{context}\n\n"
            "데이터만 사용해 ## 데이터 개요, ## 판매 동향, ## 상품 분석, ## 실행 제안, ## 한계를 작성하라. "
            "데이터에 없는 수치를 만들지 마라."
        )
        # 내부 매출 보고서를 생성합니다.
        body = _llm_report(prompt, provider, 0.2)
        # 내부 데이터 전용 접두사로 저장합니다.
        path = save_report("내부 매출 분석", body, provider, "internal_sales")
    # 본문, 저장 파일명, 폴백 미사용 상태를 반환합니다.
    return body, path.name, False


def dispatch(
    agent_name: str,
    message: str,
    provider: str,
    force_fallback: bool = False,
) -> tuple[str, str | None, bool]:
    """에이전트 이름에 따라 해당 전문 에이전트로 메시지를 위임합니다."""
    # 지원되는 이름과 실행 함수를 연결합니다.
    handlers = {
        "web-research-agent": lambda: web_research_agent(
            message,
            provider,
            force_fallback,
        ),
        "knowledge-agent": lambda: knowledge_agent(message, provider),
        "deep-research-agent": lambda: deep_research_agent(
            message,
            provider,
            force_fallback,
        ),
        "cross-check-agent": lambda: cross_check_agent(
            message,
            provider,
            force_fallback,
        ),
        "data-analyst-agent": lambda: data_analyst_agent(message, provider),
    }
    # 등록되지 않은 이름은 명확히 거부합니다.
    if agent_name not in handlers:
        raise ValueError(f"알 수 없는 A2A 에이전트입니다: {agent_name}")
    # 선택된 전문 에이전트를 실행하고 결과를 반환합니다.
    return handlers[agent_name]()
