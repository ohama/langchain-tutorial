# Phase 4: LangGraph + LangSmith - Research

**Researched:** 2026-09-11
**Domain:** LangGraph 1.2.x `StateGraph`(도구 루프 재구성, 체크포인터, `recursion_limit`) + LangSmith 트레이싱(로컬 튜토리얼 관점)
**Confidence:** HIGH (모든 핵심 API는 이 저장소의 실제 `examples/` uv 환경 — Python 3.14, `langgraph==1.2.11`, `langchain==1.4.0`, `langsmith==0.12.4` — 에서 로컬 LLM 엔드포인트(`shared.config.get_chat_model()`)에 직접 라이브 호출해 검증함. 스크린샷이 필요한 LangSmith 클라우드 UI 부분만 MEDIUM — 클라우드 전송을 하지 않는 로컬 대체 설계로 회피)

## Summary

Phase 4는 Phase 2의 수동 도구 루프를 `StateGraph`로 재구성하고, 체크포인터로 대화를 이어가고, `recursion_limit`으로 무한 루프를 막고, LangSmith로 내부 동작을 들여다보는 4개 축(GRAPH-01~06, TRACE-01~03)을 다룬다. 이번 연구에서 가장 중요한 확인 사항은 다음 세 가지다.

첫째, `StateGraph(MessagesState) + ToolNode(ALL_TOOLS) + tools_condition`으로 만든 그래프를 이 저장소의 로컬 엔드포인트에 `temperature=0`으로 실제 호출하면, Phase 2의 기준선(질문·3회 모델 호출·병렬 `lookup_stock` 2개·`multiply(a=12, b=5)`·최종 답 `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.`)과 **메시지 흐름·도구 인자·최종 답변 텍스트가 완전히 동일하게** 재현된다. 단, `ToolNode`의 기본 `handle_tool_errors`는 도구 함수 내부에서 발생한 일반 예외(우리 `lookup_stock`의 `ValueError`)는 잡지 않고 그래프를 그대로 죽인다 — Phase 2의 "모든 예외를 `ToolMessage`로 되돌린다"는 동작을 재현하려면 **`ToolNode(ALL_TOOLS, handle_tool_errors=True)`를 명시적으로 써야 한다.** (알 수 없는 도구 이름·인자 누락 같은 "호출 자체가 잘못된" 오류는 기본값도 이미 `ToolMessage`로 처리한다.)

둘째, GRAPH-04(`recursion_limit`)는 모델 호출 없이 순수 Python 2노드(`bump` → 조건부 엣지가 항상 자기 자신으로 되돌아감) 그래프로 완전히 결정론적으로 재현할 수 있다 — `config={"recursion_limit": 5}`로 `GraphRecursionError`를 즉시, 매번 동일한 메시지로 일으킨다. 모델에 의존하지 않으므로 Phase 3에서 배운 "산문-캡처 불일치" 위험이 아예 없는 가장 안전한 예제다.

셋째, LangSmith는 이 환경에 API 키가 전혀 없다(환경변수 이름으로 확인, 값 없음). TRACE-01~03을 클라우드 UI 스크린샷 없이도 정직하게 만족시키는 방법이 있다: `langsmith.utils.tracing_is_enabled()`는 순수하게 환경변수만 검사하므로(`LANGSMITH_TRACING` + `LANGSMITH_API_KEY` 존재 여부, 네트워크 접속 없음) TRACE-01의 온/오프 스위치를 안전하게 실증할 수 있고, `graph.stream(..., stream_mode="debug")`가 만드는 `task`/`task_result` 이벤트는 그래프 노드 이름과 1:1 대응하는 호출 트리이며 `usage_metadata`(input/output/total 토큰)까지 로컬에서 그대로 얻을 수 있다 — LangSmith UI가 보여주는 것과 동일한 정보를, 클라우드 전송이나 계정 없이, 재현 가능한 실제 출력으로 보여줄 수 있다.

**Primary recommendation:** GRAPH-02는 `ToolNode(ALL_TOOLS, handle_tool_errors=True)` + `tools_condition`으로 만들고, GRAPH-04는 모델과 무관한 순수 Python 카운터 그래프로 만들고, TRACE-02/03은 LangSmith 클라우드를 켜지 않고 `stream_mode="debug"`의 로컬 호출 트리로 만족시키며(계정 유무와 무관하게 항상 재현 가능), mermaid는 `draw_mermaid()`의 텍스트 출력을 기존 `.out` 캡처 파이프라인 그대로 `text` include로 싣는다(mdbook-mermaid 같은 CI 변경은 불필요).

## Standard Stack

### Core

| Library | Version(lock) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `langgraph` | 1.2.11 (이미 `langchain` 1.4.0의 전이 의존성으로 `examples/uv.lock`에 존재, `pyproject.toml`에는 아직 직접 선언 안 됨) | `StateGraph`, `add_conditional_edges`, 체크포인터, mermaid | LangChain 1.0 이후 표준 에이전트 실행 엔진. `langgraph.prebuilt.create_react_agent`는 폐기 경로(기존 PITFALLS.md 확인) |
| `langgraph-checkpoint` | 4.2.0 (전이 의존성, 이미 설치됨) | `InMemorySaver` 등 체크포인터 베이스 | `langgraph`의 필수 하위 패키지 |
| `langgraph-checkpoint-sqlite` | **아직 미설치** — dry-run 해석 결과 `3.1.1`로 해석됨(`aiosqlite==0.22.1`, `sqlite-vec==0.1.9`를 함께 끌어옴) | GRAPH-06용 `SqliteSaver` | 공식 영속 체크포인터 패키지. Python 3.14와 문제 없이 해석됨(라이브 확인) |
| `langsmith` | 0.12.4 (전이 의존성, 이미 설치됨 — `langchain-core`가 요구) | TRACE-01~03 | LangChain 생태계 표준 트레이싱 SDK. 이미 설치돼 있으므로 새 의존성 추가가 필요 없음 |

### Supporting

| Library | Purpose | When to Use |
|---------|---------|-------------|
| `langgraph.prebuilt.ToolNode` / `tools_condition` | 도구 실행 노드 + 조건부 라우팅 | GRAPH-02 — Phase 2 루프를 그대로 재현할 정도로 검증됨(아래 코드 예시) |
| `langgraph.checkpoint.memory.InMemorySaver` | 프로세스 내 대화 기억 | GRAPH-03 |
| `langgraph.checkpoint.sqlite.SqliteSaver` (컨텍스트 매니저 `from_conn_string`) | 프로세스 재시작 후에도 기억 | GRAPH-06 |
| `langgraph.errors.GraphRecursionError` | `recursion_limit` 초과 시 예외 | GRAPH-04 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ToolNode`(prebuilt) | 손으로 짠 tool 노드(Phase 2 `run_tool_call`을 그대로 노드 함수로 이식) | prebuilt가 Phase 2 기준선을 **완전히 동일하게** 재현함(라이브 검증)이 이미 확인됐고, "프레임워크가 같은 걸 몇 줄로 해준다"는 교육적 대비 효과도 있음 → prebuilt를 권장. 손수 버전은 "왜 `handle_tool_errors=True`가 필요한가"를 설명하는 보조 코드로만 짧게 다뤄도 충분 |
| `SqliteSaver`(동기) | `AsyncSqliteSaver` | 이 책의 예제는 전부 동기 `invoke()`이므로 동기 `SqliteSaver`로 충분. 비동기 버전은 스코프 밖 |
| LangSmith 클라우드 UI로 TRACE-02/03 실증 | `stream_mode="debug"` 로컬 호출 트리 | 클라우드 UI는 API 키 필요 + 캡처 불가(스크린샷은 "실제 출력"이 아님) + 값이 자동으로 book에 안 실림. 로컬 스트림은 100% 재현 가능한 텍스트 출력이고 토큰 사용량까지 포함 → 기본값으로 권장 |

**Installation (pyproject.toml에 추가 필요 — 계획 단계에서 반영):**
```toml
dependencies = [
    ...,
    "langgraph>=1.2.11",
    "langgraph-checkpoint-sqlite>=3.1.1",
]
```
`langsmith`는 이미 전이 의존성으로 lock에 있으므로 추가 선언 불필요(원한다면 명시적으로 `langsmith>=0.12.4`를 추가해 "직접 import하는 패키지는 직접 선언한다"는 기존 관례를 따를 수 있음 — Claude's discretion).

## Architecture Patterns

### Recommended Project Structure

```
examples/ch04_langgraph/
├── 01_state_graph.py        # GRAPH-01, GRAPH-02, GRAPH-05: MessagesState + ToolNode 루프 재구성 + mermaid
├── 02_checkpointer.py        # GRAPH-03, GRAPH-04: InMemorySaver+thread_id, recursion_limit
├── 03_sqlite_checkpoint.py   # GRAPH-06: SqliteSaver, 두 서브프로세스로 "재시작" 실연
└── 04_langsmith_trace.py     # TRACE-01, TRACE-02, TRACE-03: 로컬 호출 트리 + 토글 실증

book/src/ch04_langgraph/
├── 01_state_graph.md
├── 02_checkpointer.md
├── 03_sqlite_checkpoint.md   # (또는 02와 합쳐도 됨 — Open Questions 참고)
└── 04_langsmith.md
```

### Pattern 1: `MessagesState` + `ToolNode` + `tools_condition`으로 Phase 2 루프 재현

**What:** `TypedDict`를 손으로 선언하지 않고 `langgraph.graph.MessagesState`(내부적으로 `Annotated[list[AnyMessage], add_messages]` 하나만 있는 미리 만들어진 상태)를 쓰고, 도구 노드는 `ToolNode`, 라우팅은 `tools_condition`을 쓴다. `GRAPH-01` 요구사항(`TypedDict`/`add_messages`)은 `MessagesState`의 정의 자체가 그 패턴이므로, 챕터 1장에서 `MessagesState`의 소스(`Annotated[list[AnyMessage], add_messages]`)를 먼저 손으로 보여준 뒤 실제 코드에서는 `MessagesState`를 재사용하는 두 단계 구성을 권장한다(직접 손으로 짠 `TypedDict` 버전도 짧게 대조해 보여주면 GRAPH-01의 "TypedDict/add_messages 상태" 요구를 문자 그대로도 만족시킬 수 있음).

**When to use:** GRAPH-01, GRAPH-02, GRAPH-05 모두 이 하나의 그래프 구성으로 커버된다.

**Example (라이브 검증 완료 — `<repo>` 기준):**
```python
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from shared.config import get_chat_model
from shared.tools import ALL_TOOLS

model_with_tools = get_chat_model().bind_tools(ALL_TOOLS)

def call_model(state: MessagesState):
    return {"messages": [model_with_tools.invoke(state["messages"])]}

graph = StateGraph(MessagesState)
graph.add_node("model", call_model)
graph.add_node("tools", ToolNode(ALL_TOOLS, handle_tool_errors=True))  # Phase 2와 동일하게 모든 예외를 ToolMessage로
graph.add_edge(START, "model")
graph.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
graph.add_edge("tools", "model")
app = graph.compile()

result = app.invoke({"messages": [HumanMessage(
    "사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘."
)]})
```
**실제 검증 결과 (byte-identical, 2회 재실행):**
- 메시지 흐름: `HumanMessage AIMessage ToolMessage ToolMessage AIMessage ToolMessage AIMessage` — Phase 2 기준선과 동일
- `AIMessage` 1번째: `tool_calls=[('lookup_stock', {'item': '사과'}), ('lookup_stock', {'item': '바나나'})]`
- `ToolMessage`: `사과 재고: 12개` / `바나나 재고: 5개`
- `AIMessage` 2번째: `tool_calls=[('multiply', {'a': 12, 'b': 5})]` → `ToolMessage`: `60`
- 최종 답변: `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.` — Phase 2 기준선과 **글자까지 완전히 동일**

**Source:** `<repo>` 내 `shared.config.get_chat_model()` + `shared.tools.ALL_TOOLS`를 이용한 라이브 호출(2026-09-11, 이 세션에서 직접 실행). `ToolNode`/`tools_condition` import 경로는 `langgraph==1.2.11`의 `langgraph.prebuilt` 소스(로컬 `.venv`)로 직접 확인.

### Pattern 2: `ToolNode`의 `handle_tool_errors` — 기본값이 Phase 2의 "모든 예외 → ToolMessage"와 다름

**What:** `ToolNode`의 `handle_tool_errors` 기본값(`_default_handle_tool_errors`)은 **호출 자체가 잘못된 경우**(알 수 없는 도구 이름, 필수 인자 누락 등 `ToolInvocationError`)만 `ToolMessage(status="error")`로 바꾸고, **도구 함수 몸체 안에서 일어난 일반 예외**(우리 `lookup_stock`의 `ValueError`)는 잡지 않고 그대로 `raise`해 그래프 실행 자체를 실패시킨다. Phase 2의 02_tool_loop.py는 `try/except Exception`으로 **모든** 예외를 잡으므로, 이를 그대로 재현하려면 `ToolNode(ALL_TOOLS, handle_tool_errors=True)`처럼 명시적으로 켜야 한다.

**When to use:** GRAPH-02 예제, 그리고 캡스톤(Phase 5)에서 손수 도구 노드를 만들 때도 같은 함정이 재발할 수 있으므로 챕터에서 명시적으로 짚어줄 가치가 큼.

**라이브 검증 (수박 재고 조회 → `ValueError` 발생 케이스):**

| 설정 | 결과 |
|------|------|
| `ToolNode(ALL_TOOLS)` (기본값) | `ValueError: 재고 목록에 없는 품목: 수박`가 **그대로 전파**되어 `app.invoke()`가 예외로 끝남 (Traceback 발생) |
| `ToolNode(ALL_TOOLS, handle_tool_errors=True)` | `ToolMessage(status='error', content="Error: ValueError('재고 목록에 없는 품목: 수박')\n Please fix your mistakes.")` |
| 알 수 없는 도구 이름 (`not_a_real_tool`) | **기본값도** 이미 `ToolMessage(status='error', content='Error: not_a_real_tool is not a valid tool, try one of [add, multiply, lookup_stock].')`로 처리함 (차이 없음) |
| 필수 인자 누락 (`multiply(a=1)`, `b` 없음) | **기본값도** 이미 `ToolMessage(status='error', ...)`로 처리함 (차이 없음) |

**Source:** `<repo>` 라이브 실행(2026-09-11), `langgraph/prebuilt/tool_node.py`(`langgraph==1.2.11`) 소스의 `_default_handle_tool_errors`/`_handle_tool_error` 함수 직접 확인.

### Pattern 3: `recursion_limit`을 모델과 무관하게, 결정론적으로 트리거하기 (GRAPH-04)

**What:** 무한 루프를 "일부러 모델이 도구를 영원히 호출하게 유도"하는 방식으로 재현하면 모델 의존적이라 재현성이 떨어진다(Phase 3에서 배운 "산문-캡처 불일치" 위험과 같은 종류). 대신 조건부 엣지가 항상 자기 자신으로 돌아가는 순수 Python 2노드 그래프를 쓰면 100% 결정론적이다.

**Example (라이브 검증 완료):**
```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError

class State(TypedDict):
    count: int

def bump(state: State) -> dict:
    return {"count": state["count"] + 1}

def always_continue(state: State) -> str:
    return "bump"  # END로 가는 경로가 없음 → 무한 루프

graph = StateGraph(State)
graph.add_node("bump", bump)
graph.add_edge(START, "bump")
graph.add_conditional_edges("bump", always_continue, {"bump": "bump"})
app = graph.compile()

try:
    app.invoke({"count": 0}, config={"recursion_limit": 5})
except GraphRecursionError as e:
    print(type(e).__name__)
    print(e)
```
**실제 캡처될 텍스트 (재현 가능, ID/시간 없음):**
```
GraphRecursionError
Recursion limit of 5 reached without hitting a stop condition. You can increase the limit by setting the `recursion_limit` config key.
For troubleshooting, visit: https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT
```
(URL 하나가 포함되지만 공식 langchain 문서 링크일 뿐 비밀값/개인 경로가 아니므로 누출 스캔에 걸리지 않는다.)

`recursion_limit` 기본값은 25(PITFALLS.md에서 이미 확인됨). 캡처에서는 `config={"recursion_limit": 5}`처럼 작게 줘서 빠르고 짧게 트리거하는 것을 권장.

**Source:** `<repo>` 라이브 실행(2026-09-11).

### Pattern 4: `SqliteSaver`로 "프로세스 재시작 후에도 기억" 실연 (GRAPH-06)

**What:** 한 캡처 스크립트 안에서 실제로 **두 개의 별도 OS 프로세스**(파이썬 인터프리터를 두 번 `subprocess.run`으로 띄움)가 같은 SQLite 파일을 통해 상태를 공유하게 만들면, "재시작해도 유지된다"는 주장을 실제로 증명할 수 있다(같은 프로세스 안에서 SqliteSaver 인스턴스만 새로 만드는 것은 "재시작"을 증명하지 못함).

**라이브 검증 결과 (별도 `uv run` 두 번, 같은 DB 파일 공유):**
- 1번째 프로세스: `HumanMessage("내 이름은 철수야. 기억해줘.")` → 모델이 정상 응답, 체크포인트 저장됨
- 2번째 프로세스(완전히 새 파이썬 프로세스, 같은 `thread_id="demo-thread"`): `HumanMessage("내 이름이 뭐라고 했지?")` → `당신의 이름은 **철수**입니다.` — 정확히 1번째 프로세스에서 저장된 이름을 기억함. `messages` 개수가 4개(1턴째 Human+AI, 2턴째 Human+AI)로 누적되어 있음을 확인.

**API 요약:**
```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string(db_path) as saver:  # db_path: str, 상대경로 권장
    app = graph.compile(checkpointer=saver)
    config = {"configurable": {"thread_id": "demo-thread"}}
    app.invoke({"messages": [...]}, config)
```
- `setup()`(스키마 생성)은 **자동으로, 필요할 때 지연 호출**된다(`is_setup` 플래그로 1회만) — 사용자가 직접 호출할 필요 없음(소스로 확인).
- 내부적으로 `PRAGMA journal_mode=WAL`을 쓰므로 DB 파일과 함께 `<db_path>-wal`, `<db_path>-shm` 사이드카 파일이 같이 생긴다 — **`.gitignore`에 이 세 가지를 모두 커버해야 함** (예: `examples/ch04_langgraph/*.db*`).
- **경로 규칙:** 이 캡처의 실제 출력에는 파일 경로를 아예 찍지 않고, DB 파일은 저장소-상대 경로(예: `examples/ch04_langgraph/.checkpoint_demo.db`, 점 접두사로 "생성물"임을 표시)로 고정하는 것을 권장. 캡처마다 재현 가능하도록 **스크립트 시작 시 기존 DB 파일을 삭제**하고, 두 서브프로세스 실행이 끝난 뒤 **스크립트 끝에서도 삭제**해 커밋 트리에 흔적을 남기지 않는다(Phase 3의 "Chroma는 휘발성" 관례와 동일한 정신).

**Source:** `<repo>` 라이브 실행(2026-09-11, 별도 `uv run` 프로세스 2회), `langgraph-checkpoint-sqlite==3.1.1` 소스(`SqliteSaver.setup`/`from_conn_string`) 직접 확인.

### Pattern 5: mermaid 다이어그램을 기존 `.out` 파이프라인 그대로 싣기 (GRAPH-05)

**What:** `app.get_graph().draw_mermaid()`는 순수 텍스트를 반환하며, 두 번 실행해도 완전히 동일한 문자열이 나온다(byte-identical, 라이브 확인). mdBook 0.5.3은 mermaid를 내장 렌더링하지 않으므로 세 가지 선택지가 있다.

| 옵션 | 필요 작업 | 위험/비용 |
|------|-----------|-----------|
| **(a) 텍스트 소스만 include (권장)** | 예제가 `draw_mermaid()` 결과를 stdout에 찍고, 기존 `run_examples.py` → `.out` → `{{#include ...:2:}}` 파이프라인을 그대로 재사용(`check_book.py`의 `INCLUDE_ONLY_LANGS = ("python", "text", "ini")`에 `text`가 이미 허용되어 있음 — 스크립트/설정 변경 전혀 불필요) | 없음. 독자는 mermaid.live 등에 붙여넣어야 렌더링을 봄(프로즈에서 안내) |
| (b) `mdbook-mermaid` 프리프로세서 도입 | `book.toml`에 `[preprocessor.mermaid]` 추가, `mdbook-mermaid install book`으로 `mermaid.min.js`/`mermaid-init.js`를 `book/src`에 커밋, **CI(`deploy.yml`)에 mdbook-mermaid 바이너리 다운로드 스텝 추가**(mdbook과 같은 curl 패턴으로 가능 — v0.17.0이 mdBook 0.5와 호환됨을 웹 검색으로 확인) | CI 변경 필요(파이썬/uv 관련은 아니라서 기존 "CI는 mdBook-only" 불변식은 깨지지 않지만, 새 바이너리 버전 고정·검증 스텝이 늘어남). 이번 phase의 "quick" 범위에는 과함 |
| (c) `draw_mermaid_png()` | Mermaid.ink 원격 API 호출 | 네트워크 필요 + 이 책의 "로컬 전용" 원칙과 배치 → 채택 안 함 |

**권장:** (a). `check_book.py`/`run_examples.py`/`book.toml` 어느 것도 바꿀 필요가 없다. `GRAPH-05`의 "볼 수 있다"는 "mermaid 소스를 실제 출력으로 확인하고, 원하면 외부 뷰어에 붙여넣어 그림으로 볼 수 있다"로 충분히 해석 가능하며, 이는 기존 전체 파이프라인의 "생성물은 손으로 안 건드린다" 철학과도 가장 잘 맞는다. (b)는 Open Questions에 남겨 사용자가 "그림을 페이지에 직접 렌더링하고 싶다"고 명시적으로 원할 때만 채택.

**Source:** `<repo>` 라이브 실행(mermaid 텍스트, byte-identical 재확인), mdbook-mermaid 웹 검색(2026-09, v0.17.0/mdBook 0.5 호환) — MEDIUM(웹 검색만, 공식 changelog 설명 기반, 리포에서 실제 설치 검증은 하지 않음).

### Pattern 6: LangSmith를 계정/키 없이도 정직하게 다루기 (TRACE-01~03)

**What:** 이 환경에는 LangSmith 관련 환경변수가 전혀 없다(이름으로만 확인, 값 없음: `env | grep LANGSMITH` 빈 결과). `.env`/`.env.example`에도 LangSmith 키가 없다. 이 책의 핵심 가치("실제 출력만 싣는다")를 지키려면 LangSmith 클라우드 UI 스크린샷을 캡처 대신 쓸 수 없다 — 대신 다음 3단 구성을 권장한다.

**1) TRACE-01 (토글, 기본 꺼짐)** — `langsmith.utils.tracing_is_enabled()`는 순수하게 환경변수(`LANGSMITH_TRACING` + `LANGSMITH_API_KEY`의 존재 여부)만 검사하고 **네트워크 접속을 하지 않는다**(라이브 확인: 가짜 값을 넣어도 즉시 `True`로 바뀜, 실제 API 호출 없음). 이를 이용해 `.env`에 아무 것도 없을 때 `False`, `LANGSMITH_TRACING=true`+키가 있을 때 `True`로 바뀌는 것을 클라우드 전송 없이 실제 출력으로 보여줄 수 있다.
```python
import os
from langsmith import utils

print("기본값:", utils.tracing_is_enabled())          # False
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "<사용자의 키>"        # 실제로는 .env에서만 옴
print("켠 뒤:", utils.tracing_is_enabled())             # True
```
`.env.example`에는 `LANGSMITH_TRACING=false`(주석: 기본값, 이 챕터에서만 의미 있음)와 `LANGSMITH_API_KEY=`(빈 값)를 추가하는 것을 권장. **`scripts/masking.py`는 이미 `LANGSMITH_API_KEY`를 `SECRET_ENV_VARS`에 포함하고 있고(`("LLM_API_KEY", "LITELLM_API_KEY", "OPENAI_API_KEY", "LANGSMITH_API_KEY")`), `scripts/test_masking.py`도 이미 이 변수를 `monkeypatch.delenv`로 다루고 있다 — Phase 1에서 이미 선제 대응이 돼 있으므로 이번 phase에서 `masking.py`/`test_masking.py`를 바꿀 필요가 전혀 없다.**

**2) TRACE-02/03 (호출 트리·토큰·1:1 대응)** — `graph.stream(..., stream_mode="debug")`가 만드는 이벤트를 직접 실행해 확인함:
```python
for event in app.stream({"messages": [...]}, stream_mode="debug"):
    print(event["type"], event["payload"]["name"])
```
실제로 나온 시퀀스(3회 모델 호출 루프 기준): `task model` → `task_result model` → `task tools` → `task_result tools` → (반복) → `task model` → `task_result model`. **`payload["name"]`이 그래프에 `add_node("model", ...)`/`add_node("tools", ...)`로 등록한 이름과 정확히 같다** — 이것이 TRACE-03의 "트레이스 트리와 그래프 노드의 1:1 대응"을 코드로 검증 가능하게 보여주는 지점이다(LangSmith UI에서도 정확히 이 노드 이름들이 run 이름으로 나타남).

각 `AIMessage`에는 `usage_metadata`가 실제로 채워져 있다(로컬 엔드포인트가 토큰 사용량을 반환함, 확인 완료):
```
{'input_tokens': 450, 'output_tokens': 55, 'total_tokens': 505, 'input_token_details': {'cache_read': 0}, 'output_token_details': {}}
```
이 값을 단계별로 뽑아 출력하면 TRACE-02의 "토큰"을 클라우드 없이 실증한다.

**3) 지연시간(latency)은 캡처하지 않는다** — `debug` 이벤트의 원시 payload에는 `timestamp`(비결정)와 `id`(UUID)가 들어 있어 그대로 찍으면 안 된다(기존 규칙 "tool_call id/checkpoint id 비출력"과 동일선상). 이 프로젝트의 기존 관례(Phase 1~3)는 **타이밍을 출력에 아예 찍지 않는 것**이고(재현성 게이트가 "printed timing = 버그"로 취급), 이미 PITFALLS.md에 콜드 63초 vs 웜 1.7초처럼 극단적으로 들쭉날쭉하다는 실측이 있다. 따라서 latency는 **버킷화하지 않고 프로즈로만** 설명하고(예: "LangSmith UI에서는 각 run 옆에 실제 소요 시간이 뜬다"), 캡처 출력에는 노드 이름·순서·토큰·도구 인자/결과만 남기는 것을 권장.

**Sources:** `<repo>` 라이브 실행(`tracing_is_enabled()`, `stream_mode="debug"`, `usage_metadata`) — 2026-09-11, 이 세션. `scripts/masking.py`/`scripts/test_masking.py`는 이 저장소의 기존 커밋된 코드 직접 열람.

### Anti-Patterns to Avoid

- **`ToolNode(ALL_TOOLS)`를 기본값 그대로 써서 GRAPH-02의 "오류도 ToolMessage로 돌아온다"를 재현하려는 것:** 도구 함수 내부 예외는 기본값에서 전파되어 그래프가 죽는다(위 Pattern 2). 반드시 `handle_tool_errors=True`.
- **LangSmith 트레이스 URL/스크린샷을 캡처 대신 붙이는 것:** 기존 PITFALLS.md가 이미 강하게 경고("트레이스 공유 링크는 위험, 스크린샷도 안전하지 않음"). 이번 연구로 확인된 로컬 대체(Pattern 6)가 이 문제를 원천적으로 피한다.
- **`recursion_limit` 데모를 실제 모델 루프로 만드는 것:** 모델이 "언제" 무한히 도구를 호출할지 보장할 수 없어 재현성이 흔들린다(Pattern 3의 순수 Python 대안을 쓸 것).
- **SqliteSaver 데모를 한 프로세스 안에서 두 개의 `SqliteSaver` 인스턴스만 새로 만드는 것으로 "재시작"이라 주장하는 것:** 실제 프로세스 재시작을 증명하지 못한다. 반드시 `subprocess`로 별도 OS 프로세스를 두 번 띄울 것(Pattern 4).
- **`draw_mermaid_png()`(mermaid.ink 원격 API)를 쓰는 것:** 네트워크 필요, "로컬 전용" 원칙 위반.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 도구 호출 → 실행 → 결과 병합 루프 | 손으로 짠 tool 노드(Phase 2 스타일을 그래프 노드로 복사) | `langgraph.prebuilt.ToolNode` + `tools_condition` | 라이브 검증으로 Phase 2 기준선과 완전히 동일한 결과를 내는 것이 이미 확인됨; `handle_tool_errors=True` 하나만 추가하면 끝 |
| LangSmith API 키 마스킹 | `scripts/masking.py`에 새 패턴 추가 | 이미 있음(`SECRET_ENV_VARS`에 `LANGSMITH_API_KEY` 포함, `test_masking.py`도 이미 다룸) | Phase 1에서 선제적으로 대비돼 있음 — 손댈 필요 없음 |
| mermaid 렌더링 파이프라인 | mdbook-mermaid CI 통합을 직접 설계 | 텍스트 include(Pattern 5 옵션 a) | 기존 `.out`/`{{#include}}` 파이프라인이 이미 이 문제를 풀어놓은 형태이고 `text` fence가 이미 허용돼 있음 |
| 체크포인터 스키마 생성 | `CREATE TABLE` 수동 실행 | `SqliteSaver`가 첫 사용 시 자동으로 `setup()` 호출 | 소스로 확인 — 사용자가 직접 호출하면 안 된다고 문서화까지 돼 있음 |

**Key insight:** 이번 phase의 대부분은 "새 라이브러리를 배우는 것"이 아니라 "이미 검증된 prebuilt 컴포넌트가 Phase 2/3에서 만든 관례(단일 factory, 마스킹, 재현성 게이트)와 정확히 어떻게 맞물리는지"를 라이브로 확인하는 것이었다 — 실제로 새로 손볼 인프라 코드는 거의 없다(`pyproject.toml` 의존성 추가, `.gitignore`에 sqlite 패턴 추가 정도).

## Common Pitfalls

### Pitfall 1: `ToolNode` 기본 오류 처리가 Phase 2와 다르다
**What goes wrong:** GRAPH-02 예제에서 "수박 재고 조회" 같은 Phase 2의 에러 시나리오를 그대로 넣으면 그래프가 `ValueError`로 죽는다(Traceback이 `.out`에 그대로 남음 → 누출 스캔은 통과하지만 "실제 출력"이 지저분해지고 GRAPH-02 success criteria인 "Phase 2와 동일한 최종 답"을 증명할 기회를 놓침).
**Why it happens:** `ToolNode`의 기본 오류 처리는 "호출 형식 오류"만 잡고 "도구 로직 내부 예외"는 잡지 않도록 설계돼 있다(의도적 설계 — 도구 버그를 숨기지 않기 위함으로 추정).
**How to avoid:** `ToolNode(ALL_TOOLS, handle_tool_errors=True)`를 항상 쓴다.
**Warning signs:** 캡처 실행이 `Traceback`으로 끝남, `.out`에 `ValueError` 스택트레이스가 그대로 찍힘.

### Pitfall 2: SqliteSaver의 WAL 사이드카 파일이 안 지워진 채 남는다
**What goes wrong:** `PRAGMA journal_mode=WAL` 때문에 `<db>.db` 하나가 아니라 `<db>.db-wal`, `<db>.db-shm`까지 생긴다. `.gitignore`에 `*.db`만 추가하면 두 사이드카 파일이 추적되지 않은 채 남아 `git status --porcelain`이 지저분해지거나(Phase 3의 "ephemeral 아티팩트 없음" 불변식 위반), 실수로 커밋될 위험이 있다.
**How to avoid:** `.gitignore`에 `*.db*`(또는 `examples/ch04_langgraph/*.db*`) 패턴을 추가하고, 캡처 스크립트가 시작/종료 시점에 모두 세 파일을 정리(삭제)하게 만든다.

### Pitfall 3: `stream_mode="debug"`의 원시 payload를 그대로 찍으면 ID/타임스탬프가 샌다
**What goes wrong:** `event["payload"]["id"]`(UUID), `event["timestamp"]`, 메시지 객체의 `repr()`(그 안에 `id=` 필드 포함) 등을 그대로 print하면 기존 프로젝트 규칙("tool_call id/checkpoint id 비출력")을 어기고 재현성도 깨진다.
**How to avoid:** payload에서 필요한 필드(`name`, 도구 이름/인자, 메시지 `content`, `usage_metadata`)만 골라서 직접 포맷팅해 출력한다. Phase 2의 `fmt_call()` 같은 헬퍼를 재사용/확장하는 패턴을 그대로 따른다.

### Pitfall 4: LangSmith 관련 새 의존성을 추가했다고 착각하기 쉽다
**What goes wrong:** `langsmith` 패키지가 이미 `langchain-core`의 전이 의존성으로 설치돼 있다는 것을 모르고 `pip install langsmith`류 작업을 계획에 넣을 수 있다.
**How to avoid:** `examples/uv.lock`에 이미 `langsmith==0.12.4`가 있음을 계획 단계에서 확인하고 넘어간다(이번 연구로 확인 완료).

## Code Examples

### 그래프 재구성 전체 (GRAPH-01/02/05)
```python
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from shared.config import get_chat_model
from shared.tools import ALL_TOOLS

model_with_tools = get_chat_model().bind_tools(ALL_TOOLS)

def call_model(state: MessagesState):
    return {"messages": [model_with_tools.invoke(state["messages"])]}

graph = StateGraph(MessagesState)
graph.add_node("model", call_model)
graph.add_node("tools", ToolNode(ALL_TOOLS, handle_tool_errors=True))
graph.add_edge(START, "model")
graph.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
graph.add_edge("tools", "model")
app = graph.compile()

print(app.get_graph().draw_mermaid())  # GRAPH-05: mermaid 텍스트, 재실행해도 동일
```
*Source: `<repo>` 라이브 실행, `langgraph==1.2.11`.*

### `InMemorySaver` + `thread_id` (GRAPH-03)
```python
from langgraph.checkpoint.memory import InMemorySaver

app = graph.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "t1"}}
app.invoke({"messages": [HumanMessage("내 이름은 영희야.")]}, config)
app.invoke({"messages": [HumanMessage("내 이름이 뭐라고 했지?")]}, config)  # "영희"를 기억함
# 다른 thread_id로 같은 질문을 하면 기억하지 못함 (실측 확인)
```

### `recursion_limit` (GRAPH-04)
```python
from langgraph.errors import GraphRecursionError
try:
    app.invoke(initial_state, config={"recursion_limit": 5})
except GraphRecursionError as e:
    print(e)  # "Recursion limit of 5 reached without hitting a stop condition. ..."
```

### `SqliteSaver` 두 프로세스 (GRAPH-06) — 개념 스케치
```python
# capture script pseudocode
import subprocess, sys
DB = "examples/ch04_langgraph/.checkpoint_demo.db"
for path in (DB, DB + "-wal", DB + "-shm"):
    Path(path).unlink(missing_ok=True)  # 시작 시 클린

subprocess.run([sys.executable, "sqlite_worker.py", "run1", DB], check=True)
subprocess.run([sys.executable, "sqlite_worker.py", "run2", DB], check=True)  # 별도 프로세스, 같은 DB

for path in (DB, DB + "-wal", DB + "-shm"):
    Path(path).unlink(missing_ok=True)  # 종료 시 정리
```

### LangSmith 토글 + 로컬 호출 트리 (TRACE-01/02/03)
```python
import os
from langsmith import utils

print("기본값 (LANGSMITH_TRACING 미설정):", utils.tracing_is_enabled())  # False, 네트워크 없음

for event in app.stream({"messages": [...]}, stream_mode="debug"):
    name = event["payload"]["name"]
    if event["type"] == "task":
        print(f"[{name}] 시작")
    elif event["type"] == "task_result":
        # payload에서 안전한 필드만 추출해 출력 (id/timestamp는 절대 출력하지 않음)
        ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `langgraph.prebuilt.create_react_agent` | `langchain.agents.create_agent` (Phase 5에서 다룸) 또는 손수 `StateGraph`(Phase 4) | LangChain/LangGraph 1.0 (2025-10) | Phase 4는 `create_agent`를 쓰지 않고 `StateGraph`를 직접 구성 — 이미 표준 경로 |
| `ToolNode` 구버전의 "모든 예외를 기본으로 잡아줌" 기대 | `handle_tool_errors`가 세분화됨(호출 오류 vs 도구 내부 예외) | 확인된 현재(`langgraph==1.2.11`) 동작 | GRAPH-02 구현 시 명시적으로 `True` 설정 필요 |

**Deprecated/outdated:** 해당 없음(이번 phase에서 다루는 API는 모두 현재 표준 경로).

## Open Questions

1. **mermaid를 실제로 페이지에 렌더링할지 (mdbook-mermaid 도입 여부)**
   - What we know: 텍스트 include(Pattern 5 옵션 a)는 CI/스크립트 변경 없이 GRAPH-05를 만족시킨다. `mdbook-mermaid` v0.17.0이 mdBook 0.5와 호환된다는 것은 웹 검색으로만 확인(공식 changelog 설명, 리포에서 실제 설치·빌드는 검증 안 함).
   - What's unclear: 사용자가 "그림으로 실제 렌더링된 페이지"를 원하는지, 아니면 텍스트+외부 뷰어 안내로 충분한지.
   - Recommendation: 기본은 옵션 (a)로 진행. 사용자가 명시적으로 원하면 별도 소규모 후속 작업(CI에 mdbook-mermaid 바이너리 다운로드 스텝 추가, `book.toml` 프리프로세서 등록, `mdbook-mermaid install`로 정적 JS 자산을 `book/src`에 커밋)으로 처리.

2. **LangSmith 실제 계정/키로 클라우드 데모를 한 번이라도 곁들일지**
   - What we know: 현재 환경에 LangSmith 키가 전혀 없다(환경변수 이름으로 확인). Pattern 6의 로컬 전용 설계만으로 TRACE-01~03의 success criteria(토글, 호출 트리, 토큰, 1:1 대응)를 클라우드 없이도 전부 실제 출력으로 증명할 수 있다.
   - What's unclear: 사용자가 "진짜로 LangSmith 웹 UI에 트레이스가 뜨는 것"까지 (책에는 스크린샷/링크 없이) 저자 개인 확인용으로 한 번 해보고 싶어할 수도 있다 — 이는 책 콘텐츠에는 영향이 없지만 계정 생성 등 사용자 액션이 필요.
   - Recommendation: 기본은 로컬 전용(Pattern 6)으로 계획하고 push. 사용자가 원하면 `.env`에 개인 `LANGSMITH_API_KEY`를 (커밋 없이) 넣어 저자 로컬에서만 한 번 실제로 켜보는 것을 "선택적 확인 단계"로 플랜에 추가할 수 있음 — **이 결정은 planner/사용자에게 넘김**.

3. **4부 구성: LangGraph와 LangSmith를 몇 개 챕터/부로 나눌지**
   - What we know: `introduction.md`의 기존 여정 문장이 "LangGraph·LangSmith"를 하나로 묶어 표현하고 있고, ROADMAP.md는 Phase 4 하나에 GRAPH-01~06 + TRACE-01~03을 모두 담는다(= "4부" 하나에 대응). 초기 `ARCHITECTURE.md` 초안(Phase 0 리서치, 확정 아님)은 `ch04_langgraph`/`ch05_langsmith`를 별도 폴더로 그렸지만, 이는 "5부 = Capstone"인 현재 ROADMAP과 안 맞음(그 초안은 캡스톤을 `ch06_capstone`으로 그렸었음 — 이후 ROADMAP에서 Phase 5로 통합됨).
   - Recommendation: 기존 phase→부 1:1 관례(1부 기초=Phase1, 2부 도구 호출=Phase2, 3부 RAG=Phase3)를 유지해 **`# 4부 LangGraph`** 하나로 만들고, `ch04_langgraph/` 아래 4개 챕터(그래프 재구성, 체크포인터+recursion_limit, SQLite 재시작, LangSmith)로 구성할 것을 권장. LangSmith를 위해 별도 "5부"를 새로 만들면 Phase 5(Capstone)의 번호가 밀리므로, 같은 부 안의 마지막 챕터로 두는 편이 기존 구조와 가장 잘 맞는다.

## Sources

### Primary (HIGH confidence — 이 세션에서 `<repo>`의 실제 uv 환경으로 라이브 검증)
- `<repo>` 라이브 실행: `StateGraph`+`MessagesState`+`ToolNode`+`tools_condition`로 Phase 2 기준선 재현(메시지 흐름/도구 인자/최종 답변 완전 일치, 2회 재실행 byte-identical) — 2026-09-11
- `<repo>` 라이브 실행: `ToolNode` 기본값 vs `handle_tool_errors=True`의 예외 처리 차이(3가지 오류 시나리오: 도구 내부 예외/알 수 없는 도구/인자 누락) — 2026-09-11
- `<repo>` 라이브 실행: 순수 Python 카운터 그래프로 `recursion_limit=5` → `GraphRecursionError` 결정론적 트리거 — 2026-09-11
- `<repo>` 라이브 실행: `SqliteSaver.from_conn_string` + 별도 `uv run` 프로세스 2회로 프로세스 재시작 후 대화 기억 실증(`철수` 이름 기억) — 2026-09-11
- `<repo>` 라이브 실행: `InMemorySaver`+`thread_id` 멀티턴 기억, 다른 `thread_id`는 기억 못함, `get_state`/`get_state_history` — 2026-09-11
- `<repo>` 라이브 실행: `langsmith.utils.tracing_is_enabled()`가 환경변수만 검사(네트워크 없음), `stream_mode="debug"`의 `task`/`task_result` 이벤트와 그래프 노드 이름 1:1 대응, `AIMessage.usage_metadata`에 실제 토큰 수 포함 — 2026-09-11
- `examples/uv.lock` 직접 열람: `langgraph==1.2.11`(전이), `langgraph-checkpoint==4.2.0`(전이), `langsmith==0.12.4`(전이) 이미 설치돼 있음; `langgraph-checkpoint-sqlite`는 미설치, dry-run 해석 결과 `3.1.1`
- `langgraph-checkpoint-sqlite==3.1.1` 소스 직접 열람: `SqliteSaver.setup()`이 지연 자동 호출됨, WAL 저널 모드 사용
- `langgraph==1.2.11`의 `langgraph/prebuilt/tool_node.py` 소스 직접 열람: `_default_handle_tool_errors`/`_handle_tool_error` 로직
- `<repo>` 기존 코드 직접 열람: `scripts/masking.py`(`LANGSMITH_API_KEY`가 이미 `SECRET_ENV_VARS`에 포함), `scripts/test_masking.py`(이미 이 변수를 다룸), `scripts/check_book.py`(`text` fence가 이미 include-only 허용 언어에 포함)
- 환경변수 이름 확인(값 없음): `env | grep LANGSMITH*` 계열 — 결과 없음(LangSmith 관련 키가 이 환경에 전혀 없음을 확인)

### Secondary (MEDIUM confidence)
- [mdbook-mermaid GitHub Releases / CHANGELOG](https://github.com/badboy/mdbook-mermaid) — v0.17.0이 mdBook 0.5(mdbook-preprocessor 기반)를 지원한다는 것을 웹 검색으로 확인. 이 저장소에서 실제 설치·빌드까지 검증하지는 않음
- `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md` (Phase 0 리서치, 2026-09-11) — LangGraph 손수 구성 vs `create_agent` 패턴, `recursion_limit` 기본값 25, LangSmith 트레이스 링크 위험, 콜드 스타트 63초 vs 웜 1.7초 등 이미 검증된 내용을 재사용

### Tertiary (LOW confidence)
- 없음 (이번 연구의 모든 핵심 주장은 라이브 실행 또는 리포 내 소스 열람으로 뒷받침됨)

## Metadata

**Confidence breakdown:**
- Standard Stack (langgraph/langgraph-checkpoint-sqlite/langsmith 버전, 의존성 상태): HIGH — uv.lock/dry-run으로 직접 확인
- Architecture (StateGraph 재구성, ToolNode 오류 처리, recursion_limit, SqliteSaver): HIGH — 전부 `<repo>` 로컬 엔드포인트에 라이브 호출로 검증
- LangSmith(TRACE-01~03) 설계: MEDIUM-HIGH — 로컬 대체 메커니즘은 라이브 검증(HIGH)했지만, 실제 LangSmith 클라우드 UI가 이 로컬 정보와 "그대로" 대응하는지는 계정이 없어 직접 눈으로 확인하지 못함(공식 문서 서술에 근거, 라이브 검증은 아님) — 챕터 프로즈에서 "~것으로 알려져 있다/공식 문서에 따르면" 톤으로 서술 권장
- mermaid 렌더링 옵션(b, mdbook-mermaid): MEDIUM — 웹 검색만, 이 저장소에서 실제 설치 검증 안 함

**Research date:** 2026-09-11
**Valid until:** 이 phase의 계획·실행이 이어지는 동안 유효(같은 세션의 lockfile 상태 기준). LangGraph/LangSmith 마이너 버전이 올라가면(특히 `ToolNode.handle_tool_errors` 관련) 재확인 권장 — 안정 축(StateGraph 기본 API)은 30일, 이번 phase처럼 최근 세분화된 세부 동작(`handle_tool_errors`)은 7~14일 정도로 보수적으로 잡는 것을 권장.
