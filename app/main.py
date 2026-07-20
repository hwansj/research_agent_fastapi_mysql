# -*- coding: utf-8 -*-
"""FastAPI Research Agent 애플리케이션 객체를 구성하는 메인 모듈입니다."""

# 앱 시작과 종료 시 초기화 작업을 처리하기 위해 asynccontextmanager를 가져옵니다.
from contextlib import asynccontextmanager
# FastAPI와 정적 파일, 템플릿 기능을 가져옵니다.
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# API 라우터를 가져옵니다.
from app.api.routes import router
# 공통 루트 경로를 가져옵니다.
from app.core.common import ROOT, REPORTS, LOGS
# 로그 설정 함수를 가져옵니다.
from app.core.logging_config import setup_logging
# 애플리케이션 설정을 가져옵니다.
from app.core.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 전에 폴더와 로그를 준비하고 종료 후 제어를 반환합니다."""
    # 생성 파일 폴더가 없으면 자동으로 만듭니다.
    REPORTS.mkdir(parents=True, exist_ok=True)
    # 로그 폴더가 없으면 자동으로 만듭니다.
    LOGS.mkdir(parents=True, exist_ok=True)
    # 콘솔과 파일 로깅을 설정합니다.
    setup_logging()
    # FastAPI가 실제 요청을 받을 수 있도록 실행 제어를 넘깁니다.
    yield

# 캐시된 앱 설정을 읽습니다.
settings = get_settings()
# Swagger 문서와 lifespan을 포함한 FastAPI 앱 객체를 생성합니다.
app = FastAPI(title=settings.app_name, version=settings.app_version, description="ReAct → RAG → A2A → LangGraph → MCP 통합 Research Agent", lifespan=lifespan)
# CSS와 JavaScript를 제공하는 정적 파일 경로를 연결합니다.
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
# Jinja2 HTML 템플릿 폴더를 등록합니다.
templates = Jinja2Templates(directory=ROOT / "app" / "templates")
# 모든 REST API에 공통 접두사를 적용해 라우터를 등록합니다.
app.include_router(router, prefix=settings.api_prefix, tags=["Research Agent"])


@app.get("/", include_in_schema=False)
def index(request: Request):
    """Swagger 없이 사용할 수 있는 통합 웹 UI를 반환합니다."""
    # 화면 템플릿에 요청 객체와 애플리케이션 정보를 전달합니다.
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.app_name, "version": settings.app_version})
