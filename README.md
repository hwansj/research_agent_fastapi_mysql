# Research Agent Final System

`research_agent_console_project`를 FastAPI 웹 애플리케이션으로 재구성한 최종 프로젝트입니다. 
원본의 웹 검색, 검색 실패 폴백, 심층 조사, 교차 검증, 경쟁사 CSV 분석, 월별 매출 분석, 보고서 저장, 실습문제 해답 기능을 모두 유지했습니다.

## 핵심 구조

```text
사용자 / Web UI / Swagger
        ↓
     FastAPI
        ↓
LangGraph StateGraph
 ├─ ReAct: 여러 도구가 필요한 일반·복합 질문
 ├─ RAG: 내부 PDF·CSV 근거 검색
 ├─ A2A: 전문 에이전트 위임
 └─ MCP: 표준 도구 서버 및 직접 도구 호출
        ↓
OpenAI 또는 Gemini
        ↓
DuckDuckGo / FAISS / data.zip / reports
```

LangChain 1.x의 `create_agent`를 ReAct 실행기로 사용하고, 
전체 경로 제어에는 LangGraph `StateGraph`를 사용합니다. 
A2A 계층에는 에이전트 카드와 메시지 위임 API가 있으며, 
MCP 계층은 공식 Python SDK `FastMCP` 기반 독립 stdio 서버로 실행됩니다.

## 프로젝트 구조

```text
research_agent_fastapi_final/
├── run.py
├── app/
│   ├── main.py
│   ├── api/routes.py
│   ├── core/
│   ├── models/schemas.py
│   ├── services/
│   ├── agents/
│   ├── a2a/specialists.py
│   ├── graph/workflow.py
│   ├── mcp_server/
│   ├── templates/index.html
│   └── static/
├── data/                 # 원본 data 전체
├── reports/
├── logs/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## 실행 방법

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

`.env`에 OpenAI 또는 Gemini API 키를 입력합니다. 두 공급자를 모두 설정하면 화면에서 자유롭게 전환할 수 있습니다.

```dotenv
OPENAI_API_KEY=실제_OpenAI_API_KEY
GOOGLE_API_KEY=실제_Google_API_KEY
```

접속 주소:

```text
웹 UI   http://127.0.0.1:8000
Swagger http://127.0.0.1:8000/docs
ReDoc   http://127.0.0.1:8000/redoc
```

## 주요 API

| 메서드 | 경로 | 기능 |
|---|---|---|
| GET | `/` | 통합 웹 UI |
| GET | `/api/v1/health` | 서버·API 키 상태 |
| POST | `/api/v1/chat` | LangGraph 전체 실행 |
| POST | `/api/v1/tools/call` | MCP 호환 도구 직접 실행 |
| GET | `/api/v1/a2a/agents` | A2A 전문 에이전트 카드 |
| GET | `/api/v1/.well-known/agent-card.json` | 통합 에이전트 카드 |
| POST | `/api/v1/a2a/message` | 전문 에이전트 직접 위임 |
| GET | `/api/v1/data/files` | data.zip 파일 확인 |
| POST | `/api/v1/rag/reset` | RAG 메모리 캐시 초기화 |
| GET | `/api/v1/exercises` | 실습문제 1·2 실행 요청 예시 |
| GET | `/api/v1/reports/{filename}` | 생성 리포트 다운로드 |

## LangGraph 자동 분기

- `mcp:`로 시작하는 질문 → MCP 직접 도구
- 내부 문서·PDF·근거·RAG 질문 → RAG + knowledge-agent
- 경쟁사·매출·CSV 질문 → A2A data-analyst-agent
- 교차 검증·사실 확인 → A2A cross-check-agent
- 심층 조사·다각도 조사 → A2A deep-research-agent
- 최신 시장·뉴스 → A2A web-research-agent
- 그 밖의 복합 질문 → ReAct 에이전트가 도구를 자율 선택

## 독립 MCP 서버 실행

```powershell
python -m app.mcp_server.server
```

공개 도구:

- `search_web_tool`
- `search_knowledge_tool`
- `competitor_data_tool`
- `sales_data_tool`

## 실습문제 실행

실습문제 1은 `data-analyst-agent`에 다음 메시지를 보냅니다.

```json
{
  "agent_name": "data-analyst-agent",
  "message": "경쟁사 CSV를 분석하고 모든 경쟁사를 포함한 리포트를 작성해줘",
  "provider": "openai"
}
```

실습문제 2는 `deep-research-agent`에 다음 메시지를 보냅니다.

```json
{
  "agent_name": "deep-research-agent",
  "message": "무선이어버드 시장을 다각도로 심층 조사해줘",
  "provider": "gemini"
}
```

## 테스트

```powershell
pytest -q
python -m compileall app tests run.py
```

데이터 단위 테스트와 API 기본 테스트는 API 키 없이 실행됩니다.
 `/chat`, RAG 임베딩, 실제 웹 조사 테스트에는 선택한 공급자의 API 키와 인터넷 연결이 필요합니다.
