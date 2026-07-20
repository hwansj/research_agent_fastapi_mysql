# -*- coding: utf-8 -*-
"""OpenAI·Gemini 모델, 임베딩, 프로젝트 경로를 공통 제공하는 모듈입니다."""

# 운영체제 환경변수를 읽기 위해 os 모듈을 가져옵니다.
import os
# 운영체제에 독립적인 경로 처리를 위해 pathlib 모듈을 가져옵니다.
import pathlib
# 루트 .env 파일을 읽기 위해 load_dotenv 함수를 가져옵니다.
from dotenv import load_dotenv

# 현재 파일에서 세 단계 위 폴더를 프로젝트 루트로 계산합니다.
ROOT = pathlib.Path(__file__).resolve().parents[2]
# data.zip에서 추출된 데이터 폴더 경로를 정의합니다.
DATA = ROOT / "data"
# 정책·문서 PDF가 저장된 폴더 경로를 정의합니다.
DOCS = DATA / "docs"
# 생성한 마크다운 보고서를 저장할 폴더 경로를 정의합니다.
REPORTS = ROOT / "reports"
# 실행 로그를 저장할 폴더 경로를 정의합니다.
LOGS = ROOT / "logs"

# 프로젝트 루트의 .env 파일을 현재 프로세스 환경변수로 불러옵니다.
load_dotenv(ROOT / ".env")

# OpenAI 채팅 모델명을 환경변수에서 읽고 값이 없으면 교육용 기본 모델을 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# OpenAI 임베딩 모델명을 환경변수에서 읽고 값이 없으면 기본 임베딩 모델을 사용합니다.
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
# Gemini 채팅 모델명을 환경변수에서 읽고 값이 없으면 기본 모델을 사용합니다.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Gemini 임베딩 모델명을 환경변수에서 읽고 값이 없으면 기본 모델을 사용합니다.
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")


def require_key(name: str) -> str:
    """API 키 환경변수를 검사하고 정상 값만 반환합니다."""
    # 요청한 이름의 환경변수 값을 읽습니다.
    value = os.getenv(name, "").strip()
    # 값이 없거나 예제 문구가 그대로 남아 있으면 명확한 설정 오류를 발생시킵니다.
    if not value or value.startswith("여기에"):
        raise RuntimeError(f"{name}가 .env에 설정되지 않았습니다.")
    # 검사를 통과한 실제 API 키 문자열을 반환합니다.
    return value


def get_chat(provider: str = "gemini", temperature: float = 0.0):
    """선택한 공급자의 LangChain 채팅 모델 객체를 생성합니다."""
    # 공급자 문자열을 소문자로 정규화합니다.
    normalized = provider.strip().lower()
    # Gemini가 선택된 경우 Gemini API 키와 모델 클래스를 사용합니다.
    if normalized == "gemini":
        # 잘못된 키로 늦게 실패하지 않도록 먼저 키를 검증합니다.
        require_key("GOOGLE_API_KEY")
        # 설치 비용과 앱 시작 오류를 줄이기 위해 실제 사용 시점에 클래스를 가져옵니다.
        from langchain_google_genai import ChatGoogleGenerativeAI
        # 환경변수 모델명과 요청 온도를 적용한 객체를 반환합니다.
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=temperature)
    # OpenAI가 선택된 경우 OpenAI API 키와 모델 클래스를 사용합니다.
    if normalized == "openai":
        # 실제 모델 생성 전에 OpenAI API 키를 검증합니다.
        require_key("OPENAI_API_KEY")
        # 실제 사용 시점에 OpenAI LangChain 클래스를 가져옵니다.
        from langchain_openai import ChatOpenAI
        # 환경변수 모델명과 요청 온도를 적용한 객체를 반환합니다.
        return ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)
    # 지원하지 않는 공급자는 즉시 ValueError로 알립니다.
    raise ValueError("provider는 'openai' 또는 'gemini'여야 합니다.")


def get_embeddings(provider: str = "gemini"):
    """선택한 공급자의 LangChain 임베딩 객체를 생성합니다."""
    # 공급자 문자열을 소문자로 정규화합니다.
    normalized = provider.strip().lower()
    # Gemini 임베딩 분기를 처리합니다.
    if normalized == "gemini":
        # Gemini API 키를 먼저 검증합니다.
        require_key("GOOGLE_API_KEY")
        # Gemini 임베딩 클래스를 지연 임포트합니다.
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        # 실습용 저장 크기를 줄이기 위해 출력 차원을 768로 고정합니다.
        return GoogleGenerativeAIEmbeddings(model=GEMINI_EMBED_MODEL, output_dimensionality=768)
    # OpenAI 임베딩 분기를 처리합니다.
    if normalized == "openai":
        # OpenAI API 키를 먼저 검증합니다.
        require_key("OPENAI_API_KEY")
        # OpenAI 임베딩 클래스를 지연 임포트합니다.
        from langchain_openai import OpenAIEmbeddings
        # 환경변수에 지정된 임베딩 모델 객체를 반환합니다.
        return OpenAIEmbeddings(model=OPENAI_EMBED_MODEL)
    # 허용되지 않은 공급자를 명확하게 거부합니다.
    raise ValueError("provider는 'openai' 또는 'gemini'여야 합니다.")
