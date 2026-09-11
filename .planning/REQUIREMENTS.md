# Requirements: LangChain Tutorial (한국어)

**Defined:** 2026-09-11
**Core Value:** 책을 순서대로 따라가면, 실제로 돌아가는 코드와 실제 출력으로 LangChain/LangGraph를 이해하고 마지막에 스스로 코딩 에이전트를 구현할 수 있어야 한다. 책에 실린 코드는 반드시 실행되고 출력은 실제 결과여야 한다.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### 책 인프라 (INFRA)

- [x] **INFRA-01**: 독자는 GitHub Pages URL에서 목차·챕터·부록을 갖춘 한국어 mdBook을 열어 볼 수 있다
- [x] **INFRA-02**: main에 push하면 GitHub Actions가 LLM 호출 없이 mdBook을 빌드해 GitHub Pages에 자동 배포한다
- [x] **INFRA-03**: 독자는 `.env.example`을 복사해 base_url/모델명/API 키만 바꾸면 모든 예제를 자기 LLM 환경에서 실행할 수 있다 (`.env`는 git에서 제외)
- [x] **INFRA-04**: 모든 예제는 `shared/config.py` 한 곳에서 채팅 모델을 생성한다 (구조화 출력은 `method="function_calling", strict=False` 규약 포함)
- [x] **INFRA-05**: 저자는 명령 한 번으로 챕터 예제를 warm-up 후 로컬 LLM에 대해 실행하고 출력을 `.out` 파일로 저장할 수 있다
- [x] **INFRA-06**: 캡처된 출력에서 API 키와 로컬 절대 경로(`/Users/...`)가 자동으로 마스킹된다
- [x] **INFRA-07**: 챕터는 예제 소스와 실제 출력을 `{{#include}}`로만 불러오며, 손으로 붙여넣은 코드/출력이 없다
- [x] **INFRA-08**: 모든 챕터가 개념(왜 필요한가) → 최소 코드 → 실제 출력 → 요점 정리 형식을 따른다

### 기초 (BASIC)

- [x] **BASIC-01**: 독자는 `ChatOpenAI(base_url=...)`로 로컬 `flashnext`를 `invoke`/`stream` 호출하는 예제와 실제 출력을 볼 수 있다
- [x] **BASIC-02**: 독자는 System/Human/AI 메시지로 멀티턴 대화를 이어가는 예제를 볼 수 있다
- [x] **BASIC-03**: 독자는 변수와 few-shot을 쓰는 `ChatPromptTemplate` 예제를 볼 수 있다
- [x] **BASIC-04**: 독자는 `|` 파이프, `RunnableParallel`/`RunnableLambda`, `batch`/`stream`으로 LCEL 체인을 구성하는 예제를 볼 수 있다
- [x] **BASIC-05**: 독자는 Pydantic 모델로 구조화 출력을 받는 예제와, speculative decoding 500 에러의 원인·해결책(`function_calling`) 설명을 볼 수 있다

### 도구 호출 (TOOL)

- [ ] **TOOL-01**: 독자는 `@tool`로 도구를 정의하고 `bind_tools`로 모델이 생성한 `tool_calls`를 확인하는 예제를 볼 수 있다
- [ ] **TOOL-02**: 독자는 모델 → tool call → `ToolMessage` → 재호출 루프를 손으로 구현해 최종 답을 얻는 예제를 볼 수 있다

### RAG

- [ ] **RAG-01**: 독자는 한국어 텍스트/마크다운 문서를 `Document`로 읽고 `RecursiveCharacterTextSplitter`로 분할하는 예제를 볼 수 있다
- [ ] **RAG-02**: 독자는 `bge-m3` 로컬 임베딩(MPS)으로 문서를 임베딩하는 예제를 볼 수 있다
- [ ] **RAG-03**: 독자는 Chroma에 저장한 뒤 한국어 질의로 관련 문서를 검색하는 예제를 볼 수 있다
- [ ] **RAG-04**: 독자는 검색 결과를 프롬프트에 주입해 LCEL RAG 체인으로 답변을 생성하는 예제를 볼 수 있다

### LangGraph (GRAPH)

- [ ] **GRAPH-01**: 독자는 `TypedDict`/`add_messages` 상태와 노드·엣지로 `StateGraph`를 만드는 예제를 볼 수 있다
- [ ] **GRAPH-02**: 독자는 `add_conditional_edges`와 루프백 엣지로 TOOL-02의 도구 루프를 그래프로 재구성한 예제를 볼 수 있다
- [ ] **GRAPH-03**: 독자는 `InMemorySaver` + `thread_id`로 대화를 기억하는 예제를 볼 수 있다
- [ ] **GRAPH-04**: 독자는 `recursion_limit`으로 무한 루프를 멈추는 예제를 볼 수 있다
- [ ] **GRAPH-05**: 독자는 챕터의 그래프 구조를 mermaid 다이어그램으로 볼 수 있다
- [ ] **GRAPH-06**: 독자는 SQLite 체크포인터로 프로세스를 재시작해도 상태가 유지되는 예제를 볼 수 있다

### LangSmith (TRACE)

- [ ] **TRACE-01**: 독자는 `.env` 플래그로 LangSmith 트레이싱을 켜고 끌 수 있으며, 기본값은 꺼짐이다
- [ ] **TRACE-02**: 독자는 트레이스에서 호출 트리, 지연시간·토큰, tool call 인자·결과를 읽는 법을 볼 수 있다
- [ ] **TRACE-03**: 독자는 LangSmith 트레이스 트리와 LangGraph 노드의 1:1 대응 설명을 볼 수 있다

### 코딩 에이전트 캡스톤 (AGENT)

- [ ] **AGENT-01**: 샌드박스 가드는 `Path.resolve()` 기반으로 `../`와 symlink를 통한 폴더 탈출을 거부하며, 이를 테스트로 확인할 수 있다
- [ ] **AGENT-02**: `list_dir`/`read_file`/`write_file` 도구는 가드를 거치고, 오류는 예외가 아니라 tool 메시지로 모델에 돌려준다
- [ ] **AGENT-03**: `run_shell` 도구는 작업 디렉토리를 샌드박스로 고정하고 타임아웃과 출력 크기 제한을 적용한다
- [ ] **AGENT-04**: `StateGraph`로 직접 만든 코딩 에이전트 루프는 종료 조건과 `recursion_limit`을 갖는다
- [ ] **AGENT-05**: 에이전트는 체크포인터로 여러 턴에 걸친 작업을 이어갈 수 있다
- [ ] **AGENT-06**: 에이전트 실행 중 각 스텝의 도구 이름·인자가 스트리밍으로 출력된다
- [ ] **AGENT-07**: 독자는 같은 에이전트를 `create_agent`로 구현한 버전을 직접 만든 버전과 비교해 볼 수 있다
- [ ] **AGENT-08**: 독자는 에이전트가 버그 있는 스크립트를 읽고·고치고·실행해 검증하는 엔드투엔드 데모와 실제 출력을 볼 수 있다

### 부록 (APPX)

- [ ] **APPX-01**: 독자는 Ollama 등 로컬 LLM을 새로 설치하고 `.env`만 바꿔 예제를 실행하는 방법을 볼 수 있다
- [ ] **APPX-02**: 독자는 uv로 Python 환경을 만들고 의존성을 고정(`uv.lock`)하는 방법을 볼 수 있다
- [ ] **APPX-03**: 독자는 `deepagents`로 같은 코딩 에이전트를 짧게 구현한 소개를 볼 수 있다

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### 책 인프라

- **INFRA-V2-01**: `.out` 파일에 소스 해시를 기록하고 CI에서 코드-출력 불일치를 검출한다 (출력 신선도 체크)
- **INFRA-V2-02**: 배포 사이트에서 한국어 키워드 검색을 점검하고 보완한다

### 기초·도구·RAG

- **TOOL-V2-01**: 도구 챕터에서 수동 루프를 `create_agent`로 다시 구현해 대비한다 (v1에서는 캡스톤 AGENT-07에서 다룸)
- **RAG-V2-01**: 같은 한국어 질의로 `bge-small-en`과 `bge-m3`의 검색 결과를 실측 비교한다
- **RAG-V2-02**: PDF 문서를 RAG 입력으로 로딩한다 (`pypdf`)
- **RAG-V2-03**: RAG 품질 평가 (ragas 등)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| `LLMChain`, `SimpleSequentialChain` 등 레거시 체인 | `langchain-classic`으로 격리된 폐기 API — LCEL로 대체 |
| `AgentExecutor` / `initialize_agent` / `langgraph.prebuilt.create_react_agent` | 폐기 API — `create_agent` 또는 직접 만든 LangGraph 루프 사용 |
| `ConversationBufferMemory` 등 구 메모리 클래스 | 폐기 API — LangGraph 체크포인터로 대체 |
| `langchain-community` 의존 | 2026-05 지원 종료 — `pathlib` + `Document`, `langchain-chroma`/`langchain-huggingface` 사용 |
| `with_structured_output` 기본값(`json_schema`) | 로컬 엔드포인트에서 speculative decoding 500 에러 — `function_calling` 사용 |
| TypeScript/LangChain.js | Python 하나에 집중 |
| 클라우드 LLM(OpenAI/Anthropic) 기준 예제 | 로컬 서비스 기준 — `.env`로 바꿀 수 있다는 점만 언급 |
| 본문에서 LLM 서비스 설치 설명 | 이미 돌고 있는 서비스 활용, 설치는 부록(APPX-01) |
| 코딩 에이전트 human-in-the-loop 승인 흐름 | 샌드박스 폴더 제한 + 승인 없이 실행하기로 결정 |
| Jupyter 노트북 형식 | 책 + `.py` 예제로 통일 |
| 퀴즈·과제 등 교육 커리큘럼 요소 | 개인 학습 기록이 목적 |
| 출력 파서 백과사전식 나열 | `with_structured_output`이 표준, quick depth와 맞지 않음 |
| 클라우드 벡터 DB 운영 (Pinecone 등) | 로컬 임베디드 Chroma로 충분 |
| 에이전트 프레임워크 전수 비교 (CrewAI, AutoGen 등) | LangChain/LangGraph 집중 |
| LangSmith 평가·데이터셋·협업 기능 | 트레이싱까지만 다룸 |
| CI에서 예제 실행 | CI는 로컬 LLM에 접근 불가 — 출력은 로컬에서 캡처해 커밋 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 1 | Complete |
| INFRA-03 | Phase 1 | Complete |
| INFRA-04 | Phase 1 | Complete |
| INFRA-05 | Phase 1 | Complete |
| INFRA-06 | Phase 1 | Complete |
| INFRA-07 | Phase 1 | Complete |
| INFRA-08 | Phase 1 | Complete |
| BASIC-01 | Phase 1 | Complete |
| BASIC-02 | Phase 1 | Complete |
| BASIC-03 | Phase 1 | Complete |
| BASIC-04 | Phase 1 | Complete |
| BASIC-05 | Phase 1 | Complete |
| TOOL-01 | Phase 2 | Pending |
| TOOL-02 | Phase 2 | Pending |
| RAG-01 | Phase 3 | Pending |
| RAG-02 | Phase 3 | Pending |
| RAG-03 | Phase 3 | Pending |
| RAG-04 | Phase 3 | Pending |
| GRAPH-01 | Phase 4 | Pending |
| GRAPH-02 | Phase 4 | Pending |
| GRAPH-03 | Phase 4 | Pending |
| GRAPH-04 | Phase 4 | Pending |
| GRAPH-05 | Phase 4 | Pending |
| GRAPH-06 | Phase 4 | Pending |
| TRACE-01 | Phase 4 | Pending |
| TRACE-02 | Phase 4 | Pending |
| TRACE-03 | Phase 4 | Pending |
| AGENT-01 | Phase 5 | Pending |
| AGENT-02 | Phase 5 | Pending |
| AGENT-03 | Phase 5 | Pending |
| AGENT-04 | Phase 5 | Pending |
| AGENT-05 | Phase 5 | Pending |
| AGENT-06 | Phase 5 | Pending |
| AGENT-07 | Phase 5 | Pending |
| AGENT-08 | Phase 5 | Pending |
| APPX-01 | Phase 5 | Pending |
| APPX-02 | Phase 5 | Pending |
| APPX-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-11*
*Last updated: 2026-09-11 after Phase 1 completion (13/39 complete)*
