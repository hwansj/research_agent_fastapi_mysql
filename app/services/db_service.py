# -*- coding: utf-8 -*-
"""최종 답변을 MySQL REPORT 테이블에 저장하는 데이터베이스 서비스 모듈입니다."""

# MySQL 접속 정보를 환경변수에서 읽기 위해 os 모듈을 가져옵니다.
import os
# RESULT_TIME 값을 파싱하고 생성하기 위해 datetime을 가져옵니다.
from datetime import datetime


def _read_config() -> dict[str, object]:
    """환경변수에서 MySQL 접속 설정을 읽어 사전으로 반환합니다."""
    # .env에 값이 없으면 로컬 개발 기본값을 사용합니다.
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "research_agent"),
    }


def _connect(with_database: bool = True):
    """PyMySQL 연결 객체를 생성해 반환합니다."""
    # pymysql 미설치 시 앱 전체가 아닌 도구 호출 시점에만 실패하도록 지연 임포트합니다.
    import pymysql
    # 공통 접속 설정을 읽습니다.
    config = _read_config()
    # 데이터베이스 생성 전 접속을 위해 database 인수를 선택적으로 제외합니다.
    database = str(config["database"]) if with_database else None
    # 한글 저장을 위해 utf8mb4 문자셋과 자동 커밋을 사용합니다.
    return pymysql.connect(host=str(config["host"]), port=int(config["port"]), user=str(config["user"]), password=str(config["password"]), database=database, charset="utf8mb4", autocommit=True)


def ensure_report_table() -> None:
    """데이터베이스와 REPORT 테이블이 없으면 생성합니다."""
    # 데이터베이스가 아직 없을 수 있으므로 database 지정 없이 먼저 접속합니다.
    connection = _connect(with_database=False)
    try:
        # 커서를 열어 DDL을 실행합니다.
        with connection.cursor() as cursor:
            # 실습용 데이터베이스를 없으면 생성합니다.
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {_read_config()['database']} CHARACTER SET utf8mb4")
    finally:
        # 접속 자원을 반드시 반환합니다.
        connection.close()
    # 이번에는 생성된 데이터베이스를 지정해 다시 접속합니다.
    connection = _connect(with_database=True)
    try:
        # 커서를 열어 테이블 DDL을 실행합니다.
        with connection.cursor() as cursor:
            # 실습 요구사항의 TOPIC·RESULT·RESULT_TIME 칼럼과 조회용 기본키를 정의합니다.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS REPORT (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    TOPIC VARCHAR(1000) NOT NULL,
                    RESULT LONGTEXT NOT NULL,
                    RESULT_TIME DATETIME NOT NULL
                ) CHARACTER SET utf8mb4
                """
            )
    finally:
        # 접속 자원을 반드시 반환합니다.
        connection.close()


def _parse_result_time(completed_at: str) -> datetime:
    """프런트가 보낸 ISO 완료 시각을 DATETIME 값으로 변환합니다."""
    try:
        # 자바스크립트 toISOString의 Z 표기를 파이썬 호환 오프셋으로 바꿉니다.
        parsed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        # 타임존 정보를 서버 로컬 시각의 naive 값으로 정규화합니다.
        return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed
    except (ValueError, AttributeError):
        # 값이 비었거나 형식이 잘못되면 저장 시점의 현재 시각을 사용합니다.
        return datetime.now()


def save_report(topic: str, result: str, completed_at: str = "") -> dict[str, object]:
    """최종 답변 한 건을 REPORT 테이블에 INSERT 하고 저장 결과를 반환합니다."""
    # 저장 전에 데이터베이스와 테이블 존재를 보장합니다.
    ensure_report_table()
    # RESULT_TIME에 넣을 답변 완료 시각을 계산합니다.
    result_time = _parse_result_time(completed_at)
    # 데이터베이스를 지정해 접속합니다.
    connection = _connect(with_database=True)
    try:
        # 커서를 열어 INSERT를 실행합니다.
        with connection.cursor() as cursor:
            # SQL 인젝션을 막기 위해 반드시 파라미터 바인딩을 사용합니다.
            cursor.execute("INSERT INTO REPORT (TOPIC, RESULT, RESULT_TIME) VALUES (%s, %s, %s)", (topic, result, result_time))
            # 방금 저장된 행의 자동 증가 ID를 읽습니다.
            row_id = int(cursor.lastrowid)
    finally:
        # 접속 자원을 반드시 반환합니다.
        connection.close()
    # 저장 결과를 표준 사전으로 반환합니다.
    return {"row_id": row_id, "result_time": result_time.strftime("%Y-%m-%d %H:%M:%S")}
