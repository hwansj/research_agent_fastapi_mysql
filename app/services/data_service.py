# -*- coding: utf-8 -*-
"""data.zip의 CSV·JSON 파일을 읽고 정량 분석 결과를 제공하는 모듈입니다."""

# 표 데이터를 읽고 계산하기 위해 pandas를 가져옵니다.
import pandas as pd
# 공통 데이터 폴더 경로를 가져옵니다.
from app.core.common import DATA


def read_csv(filename: str) -> pd.DataFrame:
    """data 폴더의 CSV 파일을 UTF-8 BOM 호환 방식으로 읽습니다."""
    # 경로 조작 공격을 막기 위해 파일명에서 폴더 부분을 허용하지 않습니다.
    if "/" in filename or "\\" in filename:
        raise ValueError("CSV 파일명에는 경로 구분자를 사용할 수 없습니다.")
    # data 폴더 아래의 실제 파일 경로를 만듭니다.
    path = DATA / filename
    # 파일이 없으면 어떤 데이터가 필요한지 명확하게 알립니다.
    if not path.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {filename}")
    # BOM이 포함된 한글 CSV도 안전하게 읽습니다.
    return pd.read_csv(path, encoding="utf-8-sig")


def dataframe_table(dataframe: pd.DataFrame, max_rows: int = 40) -> str:
    """DataFrame 앞부분을 LLM 프롬프트용 마크다운 표로 변환합니다."""
    # 지나치게 큰 데이터를 모델에 전송하지 않도록 행 수를 제한합니다.
    preview = dataframe.head(max_rows)
    # 설치된 tabulate를 이용해 읽기 좋은 마크다운 표를 반환합니다.
    return preview.to_markdown(index=False)


def competitor_context() -> tuple[str, list[str]]:
    """경쟁사 데이터 표와 검증용 회사 목록을 반환합니다."""
    # 경쟁사 원본 CSV를 읽습니다.
    dataframe = read_csv("competitor_data.csv")
    # company 열의 모든 값을 문자열 목록으로 변환합니다.
    companies = dataframe["company"].astype(str).tolist()
    # 표 문자열과 회사 목록을 함께 반환합니다.
    return dataframe_table(dataframe), companies


def sales_context() -> str:
    """월별 매출과 상품 데이터를 하나의 분석 문맥으로 결합합니다."""
    # 월별 매출 CSV를 읽습니다.
    monthly_sales = read_csv("monthly_sales.csv")
    # 상품 기준정보 CSV를 읽습니다.
    products = read_csv("products.csv")
    # 두 표를 구분된 문자열로 결합해 반환합니다.
    return f"[monthly_sales.csv]\n{dataframe_table(monthly_sales)}\n\n[products.csv]\n{dataframe_table(products)}"


def list_data_files() -> list[dict[str, object]]:
    """프로젝트에 포함된 데이터 파일 목록과 크기를 반환합니다."""
    # API 응답에 사용할 파일 정보 목록을 준비합니다.
    items: list[dict[str, object]] = []
    # data 폴더 아래의 모든 실제 파일을 정렬해 순회합니다.
    for path in sorted(DATA.rglob("*")):
        # 폴더는 제외하고 파일만 처리합니다.
        if path.is_file():
            # 프로젝트 내부 상대 경로와 바이트 크기를 기록합니다.
            items.append({"path": str(path.relative_to(DATA)), "size_bytes": path.stat().st_size})
    # 완성된 파일 목록을 반환합니다.
    return items
