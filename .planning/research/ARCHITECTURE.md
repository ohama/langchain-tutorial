# Architecture Research

**Domain:** 실행 가능한 예제를 포함하는 mdBook 기반 한국어 LangChain/LangGraph 튜토리얼 + 캡스톤 코딩 에이전트
**Researched:** 2026-09-11
**Confidence:** HIGH (mdBook include 문법·GitHub Actions 배포·LangChain 1.0 create_agent·LangGraph 체크포인터/스트리밍은 공식 문서로 검증됨) / MEDIUM (드리프트 방지용 해시 체크 스크립트는 golden-file 테스트 패턴을 이 프로젝트에 맞게 종합한 설계 제안 — 특정 오픈소스에서 그대로 가져온 것은 아님)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    LOCAL DEV MACHINE (macOS, M4 Max)                  │
│                                                                        │
│  ┌───────────────────┐        ┌───────────────────────────────────┐  │
│  │  examples/ (uv     │  run   │  Local LLM stack (already running) │  │
│  │  package)          │───────▶│  LiteLLM proxy :4000 (flashnext)   │  │
│  │  ch02_basics/*.py  │        │   → MLX server :8000 (Qwen3.8)     │  │
│  │  ch03_tools/*.py   │◀───────│   → embeddings :8000 (bge / 다국어) │  │
│  │  ch04_rag/*.py     │  resp  └───────────────────────────────────┘  │
│  │  ch05_langgraph/*  │                                               │
│  │  ch06_langsmith/*  │        ┌───────────────────────────────────┐  │
│  │  capstone/*.py     │        │  shared/config.py                  │  │
│  └─────────┬──────────┘        │   reads .env (base_url/model/key)  │  │
│            │ writes             └───────────────────────────────────┘  │
│            ▼                                                          │
│  ┌───────────────────┐                                                │
│  │ outputs/*.out      │  freshness check (scripts/check_fresh.py)     │
│  │ (captured stdout,  │  compares sha256(source) to hash stored       │
│  │  hash header)      │  in .out header before commit                 │
│  └─────────┬──────────┘                                               │
│            │ included via {{#include}}                                │
│            ▼                                                          │
│  ┌───────────────────┐                                                │
│  │ book/src/*.md      │  chapter prose (한국어) + {{#include}} of      │
│  │ (mdBook source)    │  .py source and .out captured output          │
│  └─────────┬──────────┘                                               │
└────────────┼───────────────────────────────────────────────────────── ┘
             │ git commit & push (includes committed .out files,
             │ NOT .env — .env is gitignored)
             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    GITHUB (no access to local LLM)                    │
│                                                                        │
│  ┌───────────────────┐        ┌───────────────────────────────────┐  │
│  │ GitHub Actions CI  │  build │ mdbook build (static HTML only —   │  │
│  │ (push to main)     │───────▶│  never executes .py, never calls   │  │
│  │                    │        │  the LLM; freshness check is       │  │
│  │                    │        │  advisory-only here, see below)    │  │
│  └─────────┬──────────┘        └───────────────────────────────────┘  │
│            │ upload-pages-artifact                                    │
│            ▼                                                          │
│  ┌───────────────────┐                                                │
│  │ GitHub Pages       │  deploy-pages@v5 → public static site         │
│  └───────────────────┘                                                │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `book/` (mdBook source) | 책의 뼈대: `book.toml`, `src/SUMMARY.md`, 챕터별 `.md` 파일, 부록. 코드/출력을 직접 타이핑하지 않고 `{{#include}}`로만 끌어온다 | mdBook 표준 프로젝트, `output.html.redirect`/`git-repository-url` 등 `book.toml` 설정 |
| `examples/` (Python 예제 패키지) | 각 챕터의 실행 가능한 `.py` 파일. 챕터 1개 = 폴더 1개, 파일 1~수개(`01_chat_model.py` 식 번호 접두사로 실행/포함 순서 고정) | uv 워크스페이스 멤버 또는 단일 uv 프로젝트의 하위 패키지 |
| `examples/shared/config.py` (또는 `_shared/`) | `.env`를 읽어 `base_url`, `model`, `api_key`를 하나의 함수/객체로 노출. 모든 예제가 이 모듈을 통해서만 `ChatOpenAI` 등을 생성 — 엔드포인트를 하드코딩한 예제가 하나도 없어야 함 | `os.environ` + 얇은 dataclass, 또는 `pydantic-settings`의 `BaseSettings(env_file=".env")` |
| `outputs/` (캡처된 실행 결과) | 각 예제 실행의 실제 stdout(및 필요 시 stderr)을 `.out` 파일로 저장. 파일 첫 줄에 소스 해시를 주석으로 남겨 드리프트 감지에 사용 | 러너 스크립트가 `subprocess`로 각 `.py`를 실행하고 stdout을 리다이렉트 |
| `scripts/run_examples.py` / `Makefile` | 로컬에서 "예제 전체 재실행 → outputs 갱신" 한 번에 수행. 개별 예제만 재실행하는 옵션도 제공 | `make outputs`, `make outputs FILE=ch03_tools/02_tool_loop.py` |
| `scripts/check_fresh.py` | `.py` 소스의 sha256과 대응 `.out` 헤더에 기록된 해시를 비교. 불일치 시 실패 + "무엇을 재실행해야 하는지" 안내 | 로컬 pre-commit 훅 + CI에서도 실행 가능(LLM 호출 없이 해시만 비교하므로 CI에서 돌려도 안전) |
| GitHub Actions (`.github/workflows/deploy.yml`) | `mdbook build`만 수행(코드 실행도, LLM 호출도 없음) → Pages 아티팩트 업로드 → 배포. 선택적으로 `check_fresh.py`를 별도 job으로 돌려 "출력이 소스와 어긋난 채 커밋됐는지"만 검증 | `actions/checkout` → `mdbook build` → `actions/upload-pages-artifact` → `actions/deploy-pages` |
| GitHub Pages | 정적 사이트 호스팅, 최종 산출물 | `actions/deploy-pages@v5` |
| `capstone/` (코딩 에이전트) | LangGraph `StateGraph`(및 비교용 `create_agent` 버전) 구현. 모델 노드 + 도구 노드 + 샌드박스 강제 + 체크포인터 + 스트리밍 | `langgraph`, `langchain`, 도구는 `pathlib` 기반 경로 검증 + `subprocess` 타임아웃 |

## Recommended Project Structure

```
langchain-tutorial/
├── book/
│   ├── book.toml                  # title, src, git-repository-url, output.html
│   └── src/
│       ├── SUMMARY.md             # 목차 = 빌드 순서 그 자체
│       ├── 00_intro.md
│       ├── ch01_basics/
│       │   ├── 01_chat_model.md
│       │   ├── 02_messages.md
│       │   ├── 03_prompt_templates.md
│       │   ├── 04_output_parsers.md
│       │   └── 05_lcel_runnables.md
│       ├── ch02_tools/
│       │   ├── 01_define_tools.md
│       │   └── 02_tool_call_loop.md
│       ├── ch03_rag/
│       │   ├── 01_load_split.md
│       │   ├── 02_multilingual_embeddings.md
│       │   ├── 03_vectorstore.md
│       │   └── 04_retrieve_generate.md
│       ├── ch04_langgraph/
│       │   ├── 01_state_graph_basics.md
│       │   ├── 02_conditional_edges.md
│       │   └── 03_checkpoint_memory.md
│       ├── ch05_langsmith/
│       │   └── 01_tracing.md
│       ├── ch06_capstone/
│       │   ├── 01_design.md
│       │   ├── 02_tools_and_sandbox.md
│       │   ├── 03_graph_handbuilt.md
│       │   └── 04_graph_create_agent.md
│       └── appendix/
│           ├── local_llm_setup.md      # Ollama 등 신규 설치 방법
│           └── uv_python_setup.md
│
├── examples/
│   ├── pyproject.toml              # uv 프로젝트 루트, 단일 lockfile
│   ├── .env.example                # LITELLM_BASE_URL, LITELLM_MODEL, LITELLM_API_KEY (실값 없음)
│   ├── shared/
│   │   ├── __init__.py
│   │   └── config.py                # get_chat_model(), get_embeddings() 등 진입점
│   ├── ch01_basics/
│   │   ├── 01_chat_model.py
│   │   ├── 02_messages.py
│   │   ├── 03_prompt_templates.py
│   │   ├── 04_output_parsers.py
│   │   └── 05_lcel_runnables.py
│   ├── ch02_tools/…
│   ├── ch03_rag/…
│   ├── ch04_langgraph/…
│   ├── ch05_langsmith/…
│   └── capstone/
│       ├── state.py
│       ├── tools.py                 # list/read/write/run_shell + 경로 검증
│       ├── graph_handbuilt.py        # StateGraph 버전
│       ├── graph_create_agent.py     # langchain.agents.create_agent 버전
│       └── cli.py                    # 실행 진입점(스트리밍 출력)
│
├── outputs/
│   ├── ch01_basics/
│   │   ├── 01_chat_model.out        # 첫 줄: `# source-sha256: <hash>`
│   │   └── …
│   └── …  (examples/ 구조를 그대로 미러링)
│
├── scripts/
│   ├── run_examples.py              # 전체/개별 예제 실행 + outputs 갱신
│   └── check_fresh.py               # 소스 해시 vs outputs 헤더 해시 비교
│
├── Makefile                          # make outputs / make check-fresh / make book / make serve
├── .github/workflows/deploy.yml      # mdbook build → Pages
├── .gitignore                        # .env, book/book/(빌드 산출물), .venv 등
└── .planning/…
```

### Structure Rationale

- **`book/src/chNN_topic/`와 `examples/chNN_topic/`을 동일한 이름으로 병렬 유지:** 챕터와 예제 폴더명을 1:1로 맞추면 "이 챕터가 무엇을 include하는지"를 경로만 보고 알 수 있다. `outputs/`도 같은 트리를 미러링해 세 트리가 항상 대응된다.
- **`examples/`는 단일 uv 프로젝트(멀티 패키지 아님):** 챕터가 늘어나도 의존성(langchain, langgraph, langchain-openai 등)은 공유되므로 워크스페이스로 쪼갤 필요가 없다. 챕터별 폴더는 실행 단위 구분일 뿐 별도 패키지가 아니다.
- **`shared/config.py`를 모든 예제가 import하도록 강제:** `.env`를 읽는 코드가 예제마다 중복되면 어느 하나만 바뀌어도 나머지가 깨진다. 단일 진입점(`get_chat_model()`)으로 base_url/model/key 변경이 한 곳에만 영향을 주게 한다.
- **`outputs/`를 `examples/`와 분리된 최상위 폴더로 둔 이유:** (a) `.py`와 `.out`을 같은 폴더에 섞으면 `{{#include}}` 경로 해석이 헷갈리고, (b) 캡처된 출력은 "생성물"이라는 성격을 명확히 하기 위함이다(수동 편집 금지 대상임을 구조로 드러냄).
- **파일명 번호 접두사(`01_`, `02_`):** SUMMARY.md의 순서, examples 실행 순서, outputs 매칭 순서를 모두 동일한 정렬 기준으로 맞춘다 — 세 디렉터리가 "같은 순서로 정렬되면 같은 것을 가리킨다"는 불변식을 유지.
- **`capstone/`에 handbuilt와 create_agent 버전을 나란히 둔 이유:** 튜토리얼 목적상 "prebuilt로 빠르게 vs 직접 StateGraph로 통제"라는 두 관점을 모두 보여주는 것이 교육적 가치가 크다(아래 패턴 참고).

## Architectural Patterns

### Pattern 1: 소스-출력 결합을 `{{#include}}` + 해시 헤더로 강제

**What:** 챕터 마크다운은 코드 블록을 직접 타이핑하지 않고 `{{#include ../../examples/ch01_basics/01_chat_model.py}}`와 `{{#include ../../outputs/ch01_basics/01_chat_model.out}}`만 사용한다. `.out` 파일 첫 줄에 실행 당시 소스의 sha256을 주석으로 기록해, "이 출력이 지금 소스와 일치하는가"를 자동으로 검사할 수 있게 한다.

**When to use:** 모든 챕터의 모든 코드/출력 블록. 예외 없이 적용해야 "드리프트 없음"이라는 핵심 가치가 구조적으로 보장된다.

**Trade-offs:**
- 장점: 코드나 출력이 바뀌면 반드시 파일이 바뀌므로 git diff에서 즉시 드러남. 손으로 마크다운에 붙여넣다 오타/구식 출력이 섞이는 사고를 원천 차단.
- 단점: 예제 파일 하나에 "책에 보여줄 부분"과 "설정용 보일러플레이트"가 섞이면 include 범위 조정이 필요 — anchor 주석(`// ANCHOR: main` ~ `// ANCHOR_END: main`, 단 Python은 `# ANCHOR: main`)으로 해결.

**Example:**
```markdown
### 최소 코드

{{#include ../../examples/ch01_basics/01_chat_model.py:setup}}

### 실행 결과

{{#include ../../outputs/ch01_basics/01_chat_model.out:body}}
```
`.out` 파일의 `:body` 앵커는 첫 줄(해시 헤더)을 책에는 노출하지 않기 위한 것 — 헤더는 `check_fresh.py`만 읽는다.

**Source:** mdBook 공식 문서의 include/anchor 문법 확인. [mdBook-specific features](https://rust-lang.github.io/mdBook/format/mdbook.html)

### Pattern 2: 실행(로컬 전용) / 조립(CI)의 명확한 분리

**What:** "LLM을 호출해 출력을 만드는 단계"와 "이미 만들어진 출력을 마크다운에 조립해 정적 사이트를 만드는 단계"를 물리적으로 분리한다. 전자는 로컬에서만, 후자는 로컬과 CI 양쪽에서 실행 가능하다.

**When to use:** 로컬 전용 자원(사설 LLM, GPU, 사내망)에 의존하는 모든 문서/예제 프로젝트.

**Trade-offs:**
- 장점: CI가 단순해지고(외부 네트워크·비밀값 불필요), 빌드가 항상 재현 가능(`.out`이 커밋되어 있으므로 CI 환경 차이와 무관).
- 단점: "출력이 실제로 최신 코드에서 나온 것"이라는 보장은 CI가 아니라 저자의 로컬 습관(`make outputs` 후 커밋)과 `check_fresh.py`에 의존한다. → 이 검증을 CI에도 advisory job으로 넣어 최소한 "해시 불일치"는 잡아낸다.

**Example (CI가 하는 일은 build만):**
```yaml
- run: mdbook build book
- run: python scripts/check_fresh.py   # LLM 호출 없이 해시만 비교, 실패해도 배포는 별도 판단
```

**Source:** [GitHub Actions 공식 starter-workflow: pages/mdbook.yml](https://github.com/actions/starter-workflows/blob/main/pages/mdbook.yml) (checkout → mdbook build → upload-pages-artifact → deploy-pages 구조, `actions/deploy-pages@v5`)

### Pattern 3: 캡스톤 에이전트 — 손수 짠 `StateGraph`와 `create_agent`를 나란히 제시

**What:** LangChain 1.0부터 `langgraph.prebuilt.create_react_agent`는 폐기 예정(v2.0에서 제거 예고)이고, 표준 진입점은 `from langchain.agents import create_agent`다. `create_agent`는 내부적으로 LangGraph 런타임 위에서 동작하며 체크포인터·스트리밍·미들웨어를 기본 제공한다. 튜토리얼에서는:
1. 먼저 손수 `StateGraph`로 model 노드 + tool 노드 + 조건부 엣지를 구성해 "에이전트 루프가 실제로 어떻게 도는지" 보여주고,
2. 이어서 동일한 도구·모델로 `create_agent`를 호출해 "같은 것을 프레임워크가 몇 줄로 대신 해준다"를 대비시킨다.

**When to use:** 학습 목적 챕터(캡스톤)에서는 두 버전 모두 가치가 있다. 실무에서 빠르게 시작할 때는 `create_agent`, 커스텀 분기/서브그래프/다중 에이전트가 필요해지면 `StateGraph`로 내려간다는 것이 현재(2026) 커뮤니티 컨센서스다.

**Trade-offs:**
- 손수 StateGraph: 도구 실행 루프, 상태 갱신, 조건 분기를 명시적으로 다루므로 교육적이지만 코드량이 많고 스트리밍/체크포인터 배선을 직접 해야 함.
- `create_agent`: 코드량이 적고 미들웨어로 확장 가능하지만, 내부 동작이 추상화돼 "왜 이렇게 되는가"를 가르치기엔 불투명.

**Example (손수 버전 핵심 구조):**
```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def call_model(state: AgentState):
    return {"messages": [model_with_tools.invoke(state["messages"])]}

graph = StateGraph(AgentState)
graph.add_node("model", call_model)
graph.add_node("tools", ToolNode(tools))          # 또는 커스텀 tool 노드
graph.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
graph.add_edge("tools", "model")
app = graph.compile(checkpointer=InMemorySaver())
```

**Example (create_agent 버전, 대비용):**
```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(model=chat_model, tools=[list_files, read_file, write_file, run_shell], checkpointer=InMemorySaver())
```

**Source:** [LangChain 1.0 create_agent 공식 가이드](https://docs.langchain.com/oss/python/langchain/agents) (import 경로, checkpointer 필수 여부, 스트리밍 확인) / create_react_agent 폐기 관련 [GitHub 이슈 논의](https://github.com/bytedance/deer-flow/issues/799), [LangChain Reference](https://reference.langchain.com/python/langgraph.prebuilt/chat_agent_executor/create_react_agent)

## Data Flow

### Chapter Authoring Flow (콘텐츠 제작 흐름)

```
1. 저자가 examples/chNN/xx_example.py 작성
        ↓
2. `make outputs` (또는 `uv run scripts/run_examples.py --file …`)
   → 로컬 LiteLLM(:4000, flashnext)에 실제 요청
   → stdout 캡처 → outputs/chNN/xx_example.out 저장
   → 파일 첫 줄에 `# source-sha256: <sha256(xx_example.py)>` 기록
        ↓
3. `make check-fresh` (커밋 전 확인)
   → 모든 outputs/*.out 헤더 해시 == 대응 .py의 현재 해시인지 검사
   → 불일치면 실패, 어떤 예제를 재실행해야 하는지 목록 출력
        ↓
4. book/src/chNN/xx.md 작성 — {{#include}}로 .py 원문과 .out 결과를 그대로 삽입
        ↓
5. `mdbook build book` (로컬 미리보기, `mdbook serve`)
        ↓
6. git commit (examples/*.py, outputs/*.out, book/src/*.md 모두 포함 — .env는 제외)
   git push
        ↓
7. GitHub Actions: checkout → mdbook build book → upload-pages-artifact
   (이 단계에서 .py는 "읽기만" 되고 실행되지 않음 — LLM 호출 없음)
        ↓
8. actions/deploy-pages@v5 → GitHub Pages 배포
```

### Capstone Agent Runtime Flow (에이전트 실행 흐름)

```
CLI 실행 (cli.py, thread_id 지정)
    ↓
StateGraph.stream(..., stream_mode="messages" 또는 "updates")
    ↓
[model 노드] chat_model.invoke(state.messages)
    ↓ (tool_calls 있으면)
[조건부 엣지] tools_condition → tools 노드
    ↓
[tools 노드] 각 tool 호출 전:
    - 경로 인자를 pathlib.Path(...).resolve()로 정규화
    - 샌드박스 루트(예: ./workspace) 하위인지 확인, 아니면 즉시 에러 반환(예외로 죽이지 않고 ToolMessage로 실패 사유 전달)
    - run_shell은 subprocess.run(..., timeout=N, cwd=sandbox_root)로 실행, 타임아웃 시 자연스러운 에러 메시지 반환
    ↓
[checkpointer] 매 노드 종료 후 InMemorySaver(또는 SqliteSaver)가 전체 상태 스냅샷 저장
    ↓ (도구 결과를 다시 messages에 append)
[model 노드]로 복귀 → 반복 → 최종 응답 시 END
    ↓
CLI가 스트리밍 토큰/도구 이벤트를 실시간 출력
```

### Key Data Flows

1. **콘텐츠 드리프트 방지 흐름:** `.py` → (실행) → `.out`(해시 헤더 포함) → (해시 검증) → `.md`의 `{{#include}}` → `mdbook build`. 이 사슬의 어느 한 단계라도 건너뛰면 책의 핵심 가치("실제 실행 결과만 싣는다")가 깨지므로, `check_fresh.py`가 사슬의 무결성을 강제하는 유일한 자동 검사 지점이다.
2. **비밀값 격리 흐름:** `.env`(커밋 안 됨, gitignore) → `shared/config.py`(런타임에만 읽음) → 각 예제 스크립트. CI/Pages에는 `.env`도 `LITELLM_API_KEY`도 절대 전달되지 않는다 — CI는애초에 `.py`를 실행하지 않으므로 이 값이 필요조차 없다.
3. **캡스톤 상태 흐름:** 사용자 입력 → `messages` 상태 → 모델(도구 바인딩) → (필요시) 도구 노드(샌드박스 검증) → 상태 갱신 → 체크포인터 저장 → 다음 턴에 동일 `thread_id`로 이어서 로드.

## Scaling Considerations

이 프로젝트는 "1인 학습 기록 + 공개 튜토리얼"이므로 사용자 규모 확장은 해당 없음. 대신 "챕터/예제 수가 늘어날 때"와 "책이 커질 때"의 확장을 고려한다.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 챕터 6개, 예제 20~30개 (이번 마일스톤) | 단일 `examples/` uv 프로젝트, 수동 `make outputs`로 충분. `outputs/`도 통째로 재생성 가능(예제 실행 시간이 수십 초~1분대이므로 전체 재실행도 부담 없음) |
| 챕터가 늘어나 예제 100개+ (향후 확장 시) | `run_examples.py`에 "변경된 파일만 재실행" 옵션 추가(이미 존재하는 해시 비교 로직 재사용), 병렬 실행으로 전체 재생성 시간 단축 |
| 여러 로컬 LLM 백엔드로 예제를 교차 검증하고 싶어질 때 | `shared/config.py`가 프로필(예: `.env.flashnext`, `.env.qwen`) 스위칭을 지원하도록 확장 — outputs 디렉터리를 백엔드별로 분리(`outputs/flashnext/…`) |

### Scaling Priorities

1. **첫 번째 병목:** 예제 수가 늘면 "전체 재실행" 시간이 길어짐(콜드 캐시 첫 요청이 60초대라는 실측 기록 있음) → 변경된 파일만 골라 재실행하는 것이 첫 최적화 포인트.
2. **두 번째 병목:** 챕터가 많아지면 SUMMARY.md와 examples/outputs 트리의 이름 동기화가 수작업으로 어긋나기 쉬움 → 필요해지면 SUMMARY.md를 폴더 구조에서 자동 생성하는 스크립트를 고려(지금 규모에서는 과함).

## Anti-Patterns

### Anti-Pattern 1: 마크다운에 코드/출력을 직접 붙여넣기

**What people do:** 챕터 작성 중 터미널에서 실행한 결과를 복사해 코드 블록에 손으로 붙여넣는다.

**Why it's wrong:** 예제 코드가 나중에 수정되면(리팩터링, API 변경) 마크다운의 사본은 자동으로 갱신되지 않는다. "책의 코드가 실제로 실행되지 않는" 상태가 조용히 발생 — 이 프로젝트의 핵심 가치를 정면으로 위배.

**Do this instead:** `{{#include}}`만 사용. 붙여넣기가 필요해 보이면 그건 "이 파일을 book에 노출할 부분만 anchor로 잘라야 한다"는 신호다.

### Anti-Pattern 2: CI에서 로컬 LLM을 호출하려는 시도(포워딩, ngrok 등)

**What people do:** GitHub Actions에서 예제를 "진짜로" 실행해 최신성을 보장하려고 로컬 서버를 터널링하거나 self-hosted runner를 로컬 머신에 붙인다.

**Why it's wrong:** 사설 LiteLLM/MLX 서버를 공인 네트워크에 노출하는 보안 위험, self-hosted runner를 개인 맥에 상시 띄워야 하는 운영 부담, 그리고 애초에 "출력은 저자가 실제로 확인한 결과여야 한다"는 요구와도 어긋난다(자동 재실행 결과를 저자가 검토 없이 그대로 배포하게 됨).
**Do this instead:** 실행은 로컬에서, CI는 조립(build)만. 최신성은 `check_fresh.py`의 해시 비교로 검증.

### Anti-Pattern 3: `ToolNode`/셸 실행 도구에 타임아웃·경로 검증 없이 그대로 사용

**What people do:** `subprocess.run(cmd, shell=True)`를 타임아웃 없이 호출하거나, LLM이 준 경로 문자열을 검증 없이 `open()`에 바로 전달한다.

**Why it's wrong:** LangGraph의 `ToolNode`는 기본적으로 타임아웃을 강제하지 않으므로, 모델이 무한 루프/대기 명령을 생성하면 에이전트가 멈춘다. 경로 검증 없이 실행하면 `../../etc/passwd` 같은 경로 탈출로 샌드박스 밖 파일에 접근 가능 — "승인 없이 실행"하기로 결정했기 때문에 이 검증은 선택이 아니라 필수 안전장치다.
**Do this instead:** 모든 파일 도구는 `Path(base_dir, user_path).resolve()`가 `base_dir.resolve()`의 하위인지 확인 후 진행. 셸 도구는 `subprocess.run(..., timeout=N, cwd=base_dir)`로 감싸고, 타임아웃/실패를 예외로 죽이지 말고 `ToolMessage(content="...", status="error")`로 모델에 되돌려 스스로 복구 시도하게 한다.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| LiteLLM 프록시 (`http://127.0.0.1:4000/v1`, 모델 별칭 `flashnext`) | `langchain_openai.ChatOpenAI(base_url=..., api_key=..., model="flashnext")` | OpenAI 호환이므로 `langchain-ollama` 불필요. `base_url`/`model`/`api_key`는 반드시 `shared/config.py` 경유 |
| MLX 임베딩 서버 (`:8000`/`:8011`) | `langchain_openai.OpenAIEmbeddings(base_url=..., model=...)` 또는 다국어 임베딩 모델을 별도 추가해 사용 | 기존 `bge-small-en-v1.5`는 영어 전용 — RAG 챕터는 다국어 임베딩 모델 로컬 추가가 선행 조건(부록 또는 RAG 챕터 준비 단계에서 다룸) |
| LangSmith (선택적, 클라우드) | `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY`를 해당 챕터의 예제에서만 설정 | 트레이싱 데이터가 외부로 전송되므로 다른 챕터에서는 절대 기본 활성화하지 않음. `.env`에 별도 키로 분리해 챕터 밖에서는 로드되지 않게 함 |
| GitHub Pages | `actions/deploy-pages@v5` | 저장소 Settings → Pages → Source를 "GitHub Actions"로 설정해야 함(공식 starter workflow 전제조건) |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `book/src/*.md` ↔ `examples/*.py` | `{{#include}}` (mdBook 프리프로세서, 빌드 타임 파일 삽입) | 런타임 의존성 없음 — mdBook은 `.py`를 실행하지 않고 텍스트로만 읽음 |
| `book/src/*.md` ↔ `outputs/*.out` | `{{#include}}` (앵커로 해시 헤더 제외) | 위와 동일, 텍스트 삽입만 |
| `examples/*.py` ↔ `shared/config.py` | 일반 Python import | 모든 예제가 공유하는 유일한 "설정 읽기" 경로 |
| `scripts/check_fresh.py` ↔ `outputs/*.out` | 파일 읽기 + 해시 비교 | LLM 호출 없음 — CI에서 실행해도 안전 |
| `capstone/graph_*.py` ↔ `capstone/tools.py` | LangGraph 도구 바인딩(`bind_tools`) + `ToolNode`/커스텀 tool 노드 | 도구 함수 자체가 샌드박스 검증 로직을 캡슐화 — 그래프 쪽은 도구가 안전하다고 신뢰만 하면 됨 |
| GitHub Actions ↔ 로컬 LLM | 없음(의도적 단절) | 이 단절이 곧 "CI는 조립만 한다"는 아키텍처 결정의 근거 |

## Sources

- [mdBook-specific features (include, rustdoc_include, anchors)](https://rust-lang.github.io/mdBook/format/mdbook.html) — HIGH, 공식 문서
- [GitHub Actions 공식 starter workflow: pages/mdbook.yml](https://github.com/actions/starter-workflows/blob/main/pages/mdbook.yml) — HIGH, GitHub 공식
- [mdbook-cmdrun (참고용, 이번 설계에서는 미채택 — 커밋된 .out 파일을 직접 include하는 방식을 선택)](https://crates.io/crates/mdbook-cmdrun/0.4.0) — MEDIUM
- [LangChain 1.0 create_agent 공식 가이드 (import 경로, checkpointer, 스트리밍)](https://docs.langchain.com/oss/python/langchain/agents) — HIGH, 공식 문서
- [create_react_agent 폐기 예정 관련 논의](https://github.com/bytedance/deer-flow/issues/799), [LangChain Reference: create_react_agent](https://reference.langchain.com/python/langgraph.prebuilt/chat_agent_executor/create_react_agent) — MEDIUM (커뮤니티 이슈 + 레퍼런스 문서 교차 확인)
- [LangGraph Persistence 공식 문서 (체크포인터 종류: InMemorySaver/SqliteSaver/PostgresSaver)](https://docs.langchain.com/oss/python/langgraph/persistence) — HIGH, 공식 문서
- [LangGraph 체크포인트 구현체 개요 (DeepWiki, 참고용 정리)](https://deepwiki.com/langchain-ai/langgraph/4.2-checkpoint-implementations) — MEDIUM
- [ToolNode 타임아웃 미보장에 대한 커뮤니티 가이드](https://www.abstractalgorithms.dev/langgraph-tool-calling-toolnode-and-custom-tools) — MEDIUM, 공식 문서에 명시적 타임아웃 문구는 없으나 다수 커뮤니티 자료가 일치
- [uv `--env-file` 지원 (python-dotenv 대체 가능)](https://docs.astral.sh/uv/reference/environment/) — HIGH, 공식 문서
- 골든 파일/스냅샷 테스트 일반 패턴(해시 기반 드리프트 감지) — LOW/MEDIUM, 이 프로젝트를 위해 종합한 설계 제안이며 특정 툴을 그대로 채택한 것은 아님. 로드맵 단계에서 실제 스크립트 설계 시 세부 구현은 재검토 필요

---
*Architecture research for: mdBook 기반 실행형 튜토리얼 (LangChain/LangGraph, 한국어, 로컬 LLM)*
*Researched: 2026-09-11*
