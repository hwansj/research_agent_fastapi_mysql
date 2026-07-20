# -*- coding: utf-8 -*-
"""PDF와 내부 CSV를 임베딩하여 근거 문맥을 검색하는 RAG 서비스입니다."""

# 여러 공급자별 벡터 저장소를 재사용하기 위해 threading을 가져옵니다.
import threading
# 타입 힌트용 Any를 가져옵니다.
from typing import Any
# 공통 데이터와 문서 경로, 임베딩 생성 함수를 가져옵니다.
from app.core.common import DATA, DOCS, get_embeddings
# RAG 청크 설정을 가져옵니다.
from app.core.settings import get_settings

# 동시에 여러 요청이 인덱스를 중복 생성하지 않도록 잠금 객체를 만듭니다.
_LOCK = threading.Lock()
# 공급자별 메모리 FAISS 인덱스를 저장하는 캐시 사전을 만듭니다.
_STORES: dict[str, Any] = {}


def _load_documents() -> list[Any]:
    """data/docs PDF와 주요 CSV를 LangChain Document 목록으로 읽습니다."""
    # LangChain Document 객체를 생성하기 위해 클래스를 가져옵니다.
    from langchain_core.documents import Document
    # PDF 텍스트를 읽기 위해 PyPDFLoader를 가져옵니다.
    from langchain_community.document_loaders import PyPDFLoader
    # 전체 문서 목록을 준비합니다.
    documents: list[Any] = []
    # 모든 PDF 파일을 이름에 의존하지 않고 자동 탐색합니다.
    for pdf_path in sorted(DOCS.glob("*.pdf")):
        try:
            # PDF의 각 페이지를 LangChain Document로 읽습니다.
            loaded = PyPDFLoader(str(pdf_path)).load()
            # 각 문서 메타데이터에 사람이 확인할 상대 파일명을 추가합니다.
            for document in loaded:
                document.metadata["source"] = str(pdf_path.relative_to(DATA))
            # 읽은 페이지를 전체 문서 목록에 추가합니다.
            documents.extend(loaded)
        except Exception as exc:
            # 손상된 한 PDF가 전체 RAG 생성을 막지 않도록 오류 문서를 남깁니다.
            documents.append(Document(page_content=f"PDF 읽기 실패: {exc}", metadata={"source": str(pdf_path.name)}))
    # 내부 지식 검색에 포함할 핵심 CSV 파일명을 정의합니다.
    csv_names = ["competitor_data.csv", "monthly_sales.csv", "products.csv", "marketing_brief.csv", "reviews.csv"]
    # 각 CSV의 원문을 문서 하나로 추가합니다.
    for csv_name in csv_names:
        # 실제 CSV 경로를 만듭니다.
        csv_path = DATA / csv_name
        # 파일이 존재할 때만 읽습니다.
        if csv_path.exists():
            # UTF-8 BOM을 제거해 텍스트를 읽습니다.
            text = csv_path.read_text(encoding="utf-8-sig", errors="replace")
            # 검색 가능한 Document 객체로 변환합니다.
            documents.append(Document(page_content=text, metadata={"source": csv_name}))
    # 읽은 문서가 하나도 없으면 잘못된 빈 인덱스를 막습니다.
    if not documents:
        raise FileNotFoundError("RAG에 사용할 PDF 또는 CSV 문서가 없습니다.")
    # 수집된 원본 문서 목록을 반환합니다.
    return documents


def _build_store(provider: str):
    """원본 문서를 분할하고 임베딩하여 FAISS 저장소를 생성합니다."""
    # 메모리 벡터 저장소 구현을 가져옵니다.
    from langchain_community.vectorstores import FAISS
    # 긴 문서를 겹치는 청크로 분리하는 클래스를 가져옵니다.
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    # 현재 RAG 설정을 읽습니다.
    settings = get_settings()
    # 원본 문서 목록을 읽습니다.
    documents = _load_documents()
    # 한글 문맥 보존을 고려한 문자 기반 분할기를 생성합니다.
    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.rag_chunk_size, chunk_overlap=settings.rag_chunk_overlap)
    # 원본 문서를 검색 가능한 작은 청크로 나눕니다.
    chunks = splitter.split_documents(documents)
    # 선택한 공급자의 임베딩 모델을 생성합니다.
    embeddings = get_embeddings(provider)
    # 모든 청크를 임베딩해 메모리 FAISS 인덱스를 반환합니다.
    return FAISS.from_documents(chunks, embeddings)


def get_store(provider: str):
    """공급자별 FAISS 저장소를 캐시하여 반환합니다."""
    # 공급자 이름을 소문자로 정규화합니다.
    normalized = provider.lower()
    # 이미 생성한 저장소가 있으면 즉시 재사용합니다.
    if normalized in _STORES:
        return _STORES[normalized]
    # 동시에 들어온 최초 요청이 중복 인덱스를 만들지 않도록 잠급니다.
    with _LOCK:
        # 잠금을 기다리는 동안 다른 요청이 만들었는지 다시 확인합니다.
        if normalized not in _STORES:
            # 해당 공급자의 임베딩을 사용하는 새 저장소를 생성합니다.
            _STORES[normalized] = _build_store(normalized)
    # 생성 또는 재사용된 저장소를 반환합니다.
    return _STORES[normalized]


def search_knowledge(query: str, provider: str, top_k: int | None = None) -> str:
    """내부 문서에서 질문과 유사한 근거를 검색해 출처와 함께 반환합니다."""
    # 빈 질문을 사전에 거부합니다.
    if not query.strip():
        raise ValueError("RAG 검색 질문을 입력해야 합니다.")
    # 설정 기본값 또는 요청값으로 검색 개수를 결정합니다.
    k = top_k or get_settings().rag_top_k
    # 선택한 공급자의 FAISS 저장소를 가져옵니다.
    store = get_store(provider)
    # 유사도 검색을 수행합니다.
    documents = store.similarity_search(query, k=k)
    # 검색 결과를 사람이 읽을 수 있는 블록 목록으로 만듭니다.
    blocks: list[str] = []
    # 각 검색 문서를 순서대로 처리합니다.
    for index, document in enumerate(documents, start=1):
        # 메타데이터의 출처와 페이지 번호를 읽습니다.
        source = document.metadata.get("source", "unknown")
        page = document.metadata.get("page", "-")
        # 과도한 토큰을 막으면서 근거 본문을 포함합니다.
        blocks.append(f"[근거 {index}] source={source}, page={page}\n{document.page_content[:1800]}")
    # 검색 결과가 없으면 명확한 안내를 반환합니다.
    return "\n\n".join(blocks) if blocks else "관련 내부 근거를 찾지 못했습니다."


def reset_store() -> None:
    """공급자별 RAG 인덱스 캐시를 모두 초기화합니다."""
    # 인덱스 생성과 동시에 초기화되지 않도록 잠금을 사용합니다.
    with _LOCK:
        # 모든 캐시 항목을 제거합니다.
        _STORES.clear()
