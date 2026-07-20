# -*- coding: utf-8 -*-
"""외부 LLM 호출 없이 확인 가능한 FastAPI 기본 엔드포인트 테스트입니다."""

# FastAPI 테스트 클라이언트를 가져옵니다.
from fastapi.testclient import TestClient
# 실제 애플리케이션 객체를 가져옵니다.
from app.main import app

# 테스트에서 재사용할 클라이언트 객체를 생성합니다.
client = TestClient(app)


def test_health() -> None:
    """상태 확인 엔드포인트가 정상 응답하는지 검사합니다."""
    # health API를 호출합니다.
    response = client.get("/api/v1/health")
    # HTTP 200 상태인지 확인합니다.
    assert response.status_code == 200
    # JSON 상태 값이 ok인지 확인합니다.
    assert response.json()["status"] == "ok"


def test_agent_cards() -> None:
    """A2A 전문 에이전트 카드가 공개되는지 검사합니다."""
    # 카드 목록 API를 호출합니다.
    response = client.get("/api/v1/a2a/agents")
    # 요청이 성공했는지 확인합니다.
    assert response.status_code == 200
    # 다섯 개 전문 에이전트가 등록됐는지 확인합니다.
    assert len(response.json()) == 5


def test_exercises() -> None:
    """두 실습 해답 실행 정보가 유지되는지 검사합니다."""
    # 실습 정보 API를 호출합니다.
    response = client.get("/api/v1/exercises")
    # 정상 응답인지 확인합니다.
    assert response.status_code == 200
    # 실습문제 1과 2가 모두 포함됐는지 확인합니다.
    assert {"exercise_1", "exercise_2"}.issubset(response.json())
