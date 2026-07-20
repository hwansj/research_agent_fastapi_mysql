# -*- coding: utf-8 -*-
"""애플리케이션 환경 설정을 타입 안전하게 관리하는 모듈입니다."""

# 반복 생성 비용 없이 설정을 한 번만 만들기 위해 lru_cache를 가져옵니다.
from functools import lru_cache
# Pydantic 기반 환경 설정 클래스를 사용하기 위해 BaseSettings를 가져옵니다.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """FastAPI 서버와 에이전트 기본 설정을 정의합니다."""

    # 브라우저와 Swagger에 표시할 애플리케이션 이름입니다.
    app_name: str = "Research Agent Final System"
    # API 버전과 화면 표시용 버전 문자열입니다.
    app_version: str = "2.0.0"
    # API의 공통 URL 접두사입니다.
    api_prefix: str = "/api/v1"
    # 기본 LLM 공급자를 지정합니다.
    default_provider: str = "gemini"
    # RAG 검색 결과 개수를 지정합니다.
    rag_top_k: int = 4
    # 문서 청크 최대 문자 수를 지정합니다.
    rag_chunk_size: int = 700
    # 인접 청크의 문맥 중복 문자 수를 지정합니다.
    rag_chunk_overlap: int = 100
    # .env를 읽고 알 수 없는 값을 무시하도록 Pydantic 설정을 정의합니다.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """프로세스 전체에서 재사용할 설정 객체를 반환합니다."""
    # 설정 파일과 환경변수를 읽어 Settings 객체를 한 번 생성합니다.
    return Settings()
