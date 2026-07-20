# -*- coding: utf-8 -*-
"""API 키 없이 실행 가능한 data.zip 서비스 단위 테스트입니다."""

# 실제 데이터 서비스 함수를 가져옵니다.
from app.services.data_service import competitor_context, list_data_files, sales_context


def test_competitor_context_contains_companies() -> None:
    """경쟁사 표와 회사 목록이 비어 있지 않은지 검사합니다."""
    # 실제 CSV에서 표와 회사 목록을 읽습니다.
    table, companies = competitor_context()
    # 표 본문이 비어 있지 않은지 확인합니다.
    assert table.strip()
    # 회사가 한 개 이상 존재하는지 확인합니다.
    assert len(companies) > 0
    # 첫 회사명이 표에도 포함되는지 확인합니다.
    assert companies[0] in table


def test_sales_context_contains_sources() -> None:
    """결합 매출 문맥에 두 데이터 파일 표시가 포함되는지 검사합니다."""
    # 실제 월별 매출과 상품 문맥을 읽습니다.
    context = sales_context()
    # 월별 매출 출처 표시를 검사합니다.
    assert "monthly_sales.csv" in context
    # 상품 출처 표시를 검사합니다.
    assert "products.csv" in context


def test_data_files_include_original_assets() -> None:
    """원본 프로젝트의 핵심 데이터 파일이 보존되었는지 검사합니다."""
    # 파일 목록에서 상대 경로 집합을 만듭니다.
    paths = {item["path"] for item in list_data_files()}
    # 경쟁사 CSV가 포함됐는지 검사합니다.
    assert "competitor_data.csv" in paths
    # PDF 문서가 한 개 이상 포함됐는지 검사합니다.
    assert any(str(path).endswith(".pdf") for path in paths)
