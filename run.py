# -*- coding: utf-8 -*-
"""PyCharm에서 FastAPI 서버를 직접 실행하는 진입 파일입니다."""

# ASGI 서버를 실행하기 위해 uvicorn 패키지를 가져옵니다.
import uvicorn

# 이 파일을 직접 실행한 경우에만 아래 서버 실행 코드를 수행합니다.
if __name__ == "__main__":
    # 문자열 import 경로를 사용하면 reload 기능이 수정된 모듈을 다시 불러올 수 있습니다.
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
