# -*- coding: utf-8 -*-
"""콘솔과 파일 로그를 동시에 구성하는 모듈입니다."""

# 표준 Python 로깅 기능을 사용하기 위해 logging을 가져옵니다.
import logging
# 날짜별 회전 로그를 만들기 위해 TimedRotatingFileHandler를 가져옵니다.
from logging.handlers import TimedRotatingFileHandler
# 공통 로그 폴더 경로를 가져옵니다.
from app.core.common import LOGS


def setup_logging() -> None:
    """애플리케이션 루트 로거를 중복 없이 설정합니다."""
    # 로그 폴더가 없으면 부모 폴더까지 생성합니다.
    LOGS.mkdir(parents=True, exist_ok=True)
    # 현재 프로세스의 루트 로거를 가져옵니다.
    root_logger = logging.getLogger()
    # 이미 핸들러가 있으면 reload 과정의 중복 로그를 막기 위해 종료합니다.
    if root_logger.handlers:
        return
    # INFO 이상의 운영 로그를 기록하도록 수준을 설정합니다.
    root_logger.setLevel(logging.INFO)
    # 시간, 수준, 모듈, 메시지를 표시하는 공통 포맷을 생성합니다.
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    # 터미널에 로그를 출력하는 핸들러를 생성합니다.
    console_handler = logging.StreamHandler()
    # 콘솔 핸들러에 공통 포맷을 연결합니다.
    console_handler.setFormatter(formatter)
    # 매일 자정에 새 파일을 만들고 최근 7개를 보관하는 파일 핸들러를 생성합니다.
    file_handler = TimedRotatingFileHandler(LOGS / "research_agent.log", when="midnight", backupCount=7, encoding="utf-8")
    # 파일 핸들러에도 공통 포맷을 연결합니다.
    file_handler.setFormatter(formatter)
    # 루트 로거에 콘솔 핸들러를 추가합니다.
    root_logger.addHandler(console_handler)
    # 루트 로거에 파일 핸들러를 추가합니다.
    root_logger.addHandler(file_handler)
