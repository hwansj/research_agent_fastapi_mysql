# -*- coding: utf-8 -*-
"""시장 조사 결과를 UTF-8 마크다운 파일로 저장하는 모듈입니다."""

# 파일명에 날짜와 시간을 넣기 위해 datetime을 가져옵니다.
import datetime
# 저장 경로 객체 타입을 사용하기 위해 pathlib을 가져옵니다.
import pathlib
# 공통 보고서 폴더 경로를 가져옵니다.
from app.core.common import REPORTS


def safe_filename(text: str, max_length: int = 50) -> str:
    """Windows에서도 사용할 수 있는 안전한 파일명 조각을 만듭니다."""
    # Windows 파일명에서 사용할 수 없는 문자를 정의합니다.
    invalid_chars = '<>:"/\\|?*'
    # 금지 문자를 밑줄로 치환합니다.
    cleaned = "".join("_" if char in invalid_chars else char for char in text.strip())
    # 연속 공백을 하나의 밑줄로 바꿉니다.
    cleaned = "_".join(cleaned.split())
    # 입력이 비어 있으면 기본 이름을 사용합니다.
    if not cleaned:
        cleaned = "research"
    # 지나치게 긴 경로를 막기 위해 최대 길이까지만 반환합니다.
    return cleaned[:max_length]


def save_report(topic: str, body: str, provider: str, prefix: str = "research") -> pathlib.Path:
    """리포트 제목과 생성 정보를 포함한 마크다운 파일을 저장합니다."""
    # 보고서 폴더가 없으면 자동으로 생성합니다.
    REPORTS.mkdir(parents=True, exist_ok=True)
    # 현재 날짜와 시간을 파일명에 사용할 형식으로 만듭니다.
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # 사용자가 입력한 주제를 안전한 파일명으로 변환합니다.
    topic_name = safe_filename(topic)
    # 최종 파일 경로를 구성합니다.
    path = REPORTS / f"{prefix}_{timestamp}_{topic_name}.md"
    # 파일 상단에 표시할 메타데이터 헤더를 만듭니다.
    header = f"# 리서치 리포트 — {topic}\n\n> 생성 시각: {timestamp} / 모델 공급자: {provider}\n\n"
    # 한글이 깨지지 않도록 UTF-8로 헤더와 본문을 저장합니다.
    path.write_text(header + body.strip() + "\n", encoding="utf-8")
    # API가 다운로드 경로를 반환할 수 있도록 저장 경로를 반환합니다.
    return path
