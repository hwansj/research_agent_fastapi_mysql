# -*- coding: utf-8 -*-
"""공급자별 LLM 응답을 공통 문자열로 변환하는 도우미 모듈입니다."""

# 다양한 메시지 형식을 받을 수 있도록 Any를 가져옵니다.
from typing import Any


def extract_text(message: Any) -> str:
    """LangChain 메시지 또는 일반 객체에서 텍스트를 안전하게 추출합니다."""
    # None 값은 화면에 None 문자열이 나오지 않도록 빈 문자열로 바꿉니다.
    if message is None:
        return ""
    # 이미 문자열이면 그대로 반환합니다.
    if isinstance(message, str):
        return message
    # LangChain 메시지의 content 속성을 읽습니다.
    content = getattr(message, "content", None)
    # content가 일반 문자열이면 즉시 반환합니다.
    if isinstance(content, str):
        return content
    # Gemini 등에서 content가 블록 목록이면 텍스트 블록을 합칩니다.
    if isinstance(content, list):
        # 추출된 텍스트를 저장할 목록을 준비합니다.
        parts: list[str] = []
        # 각 콘텐츠 블록을 순서대로 검사합니다.
        for block in content:
            # 사전 블록의 text 키를 우선 사용합니다.
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            # 객체 블록의 text 속성이 있으면 사용합니다.
            elif isinstance(getattr(block, "text", None), str):
                parts.append(block.text)
        # 추출한 텍스트 블록을 줄바꿈으로 결합합니다.
        if parts:
            return "\n".join(parts)
    # 알 수 없는 객체도 디버깅할 수 있도록 문자열로 변환합니다.
    return str(message)


def last_message_text(result: Any) -> str:
    """LangChain create_agent 결과의 마지막 AI 메시지를 문자열로 반환합니다."""
    # 일반적인 create_agent 결과인 사전 형식을 검사합니다.
    if isinstance(result, dict):
        # messages 키의 목록을 안전하게 가져옵니다.
        messages = result.get("messages", [])
        # 메시지가 있으면 가장 마지막 응답을 추출합니다.
        if messages:
            return extract_text(messages[-1])
    # 예상하지 못한 형식이면 전체 값을 문자열로 변환합니다.
    return extract_text(result)
