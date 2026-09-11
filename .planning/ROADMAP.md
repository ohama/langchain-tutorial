# Roadmap: LangChain Tutorial (한국어)

## Overview

책 저작 파이프라인(mdBook + `{{#include}}` + 캡처 스크립트 + CI/Pages 배포)을 가장 먼저 끝까지 완성해 검증한 뒤, 그 위에서 기초 → 도구 호출 → RAG → LangGraph/LangSmith 챕터를 순서대로 쌓는다. 마지막 페이즈에서 지금까지 배운 도구·그래프·체크포인터·트레이싱을 모두 합쳐 샌드박스 코딩 에이전트 캡스톤을 완성하고 부록(로컬 LLM 설치, uv 환경)을 덧붙인다.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Book Infra + Basics** - 저작 파이프라인 전체(로컬 실행→캡처→`{{#include}}`→CI 빌드→Pages 배포)를 끝까지 증명하고, 그 위에서 기초 챕터를 완성한다
- [ ] **Phase 2: Tool Calling** - 모델의 tool call과 수동 재호출 루프를 직접 구현한 예제로 익힌다
- [ ] **Phase 3: RAG** - 한국어 문서를 로딩·분할·다국어 임베딩·검색·생성까지 잇는 RAG 파이프라인을 완성한다
- [ ] **Phase 4: LangGraph + LangSmith** - 도구 루프를 상태 그래프로 재구성하고, 체크포인터로 기억시키며, 트레이싱으로 내부 동작을 들여다본다
- [ ] **Phase 5: Capstone + Appendix** - 샌드박스 코딩 에이전트를 완성하고 로컬 LLM 설치·uv 환경 부록을 마무리한다

## Phase Details

### Phase 1: Book Infra + Basics
**Goal**: 독자는 GitHub Pages에 배포된 한국어 mdBook에서, 저자가 실제로 실행하고 캡처한 출력이 실린 기초 챕터(채팅 모델 호출~구조화 출력)를 읽을 수 있다. 이 페이즈에서 챕터 저작 파이프라인 전체가 한 번 끝까지 검증되어야 이후 모든 챕터가 같은 그릇을 재사용할 수 있다.
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07, INFRA-08, BASIC-01, BASIC-02, BASIC-03, BASIC-04, BASIC-05
**Success Criteria** (what must be TRUE):
  1. GitHub Pages URL에 접속하면 목차·챕터·부록 구조를 갖춘 한국어 mdBook 사이트가 뜬다 (INFRA-01)
  2. main에 push하면 GitHub Actions가 LLM을 호출하지 않고 mdBook을 빌드해 Pages에 자동 배포한 로그를 확인할 수 있다 (INFRA-02)
  3. 독자가 `.env.example`을 복사해 base_url/모델명/API 키만 바꾸면 `shared/config.py`를 경유하는 모든 예제가 자신의 환경에서 그대로 실행된다 (INFRA-03, INFRA-04)
  4. 저자가 명령 한 번으로 예제를 실행하면 `.out` 파일이 생성되고, 그 안의 API 키와 로컬 절대경로가 자동으로 마스킹되어 있다 (INFRA-05, INFRA-06)
  5. 기초 챕터(채팅 호출/스트림, 멀티턴 메시지, 프롬프트 템플릿, LCEL 체인, `function_calling` 구조화 출력) 각각이 `{{#include}}`로만 코드·출력을 불러오고 개념→코드→출력→요점 형식을 따른다 (INFRA-07, INFRA-08, BASIC-01, BASIC-02, BASIC-03, BASIC-04, BASIC-05)
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Python 실행 인프라: examples uv 패키지 + shared/config.py + .env.example, 마스킹·누출 스캐너, warm-up 캡처 러너 (Wave 1)
- [x] 01-02-PLAN.md — mdBook 골격(최종 목차·소개·부록), 공개 리포 생성, Pages(workflow) 활성화, CI 첫 배포 라이브 검증 (Wave 1)
- [x] 01-03-PLAN.md — check_book.py 형식 게이트 + 기초 챕터 1~3(채팅 호출/스트림·.env 설정, 메시지, 프롬프트 템플릿) (Wave 2)
- [x] 01-04-PLAN.md — 기초 챕터 4~5(LCEL, 구조화 출력·500 에러) + 전체 형식·누출 스캔·push·라이브 검증 (Wave 3)

### Phase 2: Tool Calling
**Goal**: 독자는 모델이 도구를 호출하고 그 결과를 받아 다시 답을 만드는 전체 루프를 손으로 구현한 예제로 이해한다.
**Depends on**: Phase 1 (책 저작 파이프라인, `shared/config.py`)
**Requirements**: TOOL-01, TOOL-02
**Success Criteria** (what must be TRUE):
  1. `@tool`로 정의한 도구와 `bind_tools`로 모델이 만든 `tool_calls`가 실제 출력에서 확인된다 (TOOL-01)
  2. 모델→tool call→`ToolMessage`→재호출 루프 예제가 실제로 최종 답을 만들어내는 실행 결과를 보여준다 (TOOL-02)
**Plans**: TBD

Plans:
- [ ] 02-01: TBD

### Phase 3: RAG
**Goal**: 독자는 한국어 문서를 로딩·분할·다국어 임베딩·검색·생성으로 잇는 RAG 파이프라인 전체를 실제 출력과 함께 따라갈 수 있다.
**Depends on**: Phase 1 (책 저작 파이프라인)
**Requirements**: RAG-01, RAG-02, RAG-03, RAG-04
**Success Criteria** (what must be TRUE):
  1. 한국어 텍스트/마크다운 문서가 `Document`로 로딩되고 `RecursiveCharacterTextSplitter`로 분할된 청크 수·내용이 실제 출력에 나타난다 (RAG-01)
  2. `bge-m3` 로컬 임베딩(MPS)으로 문서를 임베딩한 실행 결과(벡터 차원 등)를 볼 수 있다 (RAG-02)
  3. Chroma에 저장한 뒤 한국어 질의로 검색한 실제 결과 문서들이 출력에 나타난다 (RAG-03)
  4. 검색 결과를 프롬프트에 주입한 LCEL RAG 체인이 실제 한국어 답변을 생성한 출력을 보여준다 (RAG-04)
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: LangGraph + LangSmith
**Goal**: 독자는 도구 루프를 상태 그래프로 재구성하고, 체크포인터로 대화를 여러 턴 이어가며, LangSmith 트레이스로 에이전트 내부 동작을 들여다볼 수 있다.
**Depends on**: Phase 1 (책 저작 파이프라인), Phase 2 (재구성 대상인 도구 루프)
**Requirements**: GRAPH-01, GRAPH-02, GRAPH-03, GRAPH-04, GRAPH-05, GRAPH-06, TRACE-01, TRACE-02, TRACE-03
**Success Criteria** (what must be TRUE):
  1. `TypedDict`/`add_messages` 상태와 노드·엣지로 만든 `StateGraph`와 그 mermaid 다이어그램을 볼 수 있다 (GRAPH-01, GRAPH-05)
  2. `add_conditional_edges` + 루프백으로 재구성한 도구 루프 그래프가 Phase 2의 수동 루프와 동일한 최종 답을 실제 출력으로 보여준다 (GRAPH-02)
  3. `InMemorySaver` + `thread_id`로 같은 스레드의 대화가 이어지는 실행 결과와, `recursion_limit`으로 무한 루프가 멈추는 실행 결과를 각각 볼 수 있다 (GRAPH-03, GRAPH-04)
  4. SQLite 체크포인터 예제는 프로세스를 재시작해도 이전 상태가 유지됨을 실제 실행 결과로 보여준다 (GRAPH-06)
  5. `.env` 플래그로 LangSmith를 켜면(기본값 꺼짐) 트레이스에서 호출 트리·지연시간/토큰·tool call 인자/결과를 확인할 수 있고, 트레이스 트리와 그래프 노드의 1:1 대응 설명을 볼 수 있다 (TRACE-01, TRACE-02, TRACE-03)
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

### Phase 5: Capstone + Appendix
**Goal**: 독자는 지정된 작업 폴더 안에서만 파일을 읽고·쓰고 셸 명령을 실행하는 코딩 에이전트를 손수 구현하고, `create_agent`/`deepagents` 버전과 비교하며, 버그를 스스로 고치는 엔드투엔드 데모를 확인한다. 마지막으로 로컬 LLM 설치와 uv 환경 구성 부록을 읽는다.
**Depends on**: Phase 1 (책 저작 파이프라인), Phase 2 (도구 루프), Phase 4 (StateGraph, 체크포인터)
**Requirements**: AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05, AGENT-06, AGENT-07, AGENT-08, APPX-01, APPX-02, APPX-03
**Success Criteria** (what must be TRUE):
  1. 샌드박스 가드 테스트를 실행하면 `Path.resolve()` 기반 검증이 `../` 경로와 symlink를 통한 폴더 탈출 시도를 모두 거부함을 테스트 출력으로 확인할 수 있다 (AGENT-01)
  2. `list_dir`/`read_file`/`write_file` 도구는 가드를 통과한 정상 요청을 수행하고, 위반 시 예외 대신 tool 메시지로 오류가 모델에 전달됨을 실행 결과로 볼 수 있다 (AGENT-02)
  3. `run_shell` 도구가 작업 디렉토리를 샌드박스로 고정한 채 명령을 실행하며, 타임아웃/출력 크기 제한을 넘는 상황에서 제한이 실제로 적용됨을 실행 결과로 볼 수 있다 (AGENT-03)
  4. 손수 만든 `StateGraph` 에이전트가 종료 조건과 `recursion_limit`을 갖고, 체크포인터로 여러 턴에 걸친 작업을 이어가며, 각 스텝의 도구 이름·인자가 스트리밍으로 출력되는 실행 로그를 볼 수 있다 (AGENT-04, AGENT-05, AGENT-06)
  5. 독자는 같은 에이전트의 손수 구현/`create_agent`/`deepagents` 버전을 나란히 비교하고, 에이전트가 버그 있는 스크립트를 읽고·고치고·실행해 검증하는 엔드투엔드 데모의 실제 출력을 확인하며, 부록에서 Ollama 설치와 uv 환경 구성(`uv.lock`) 방법을 볼 수 있다 (AGENT-07, AGENT-08, APPX-01, APPX-02, APPX-03)
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

**Research flag**: 샌드박스 보안 하드닝(AGENT-01, symlink 실경로 검증·셸 명령 안전장치)은 계획 단계에서 구체적 침투 테스트 시나리오를 먼저 설계해야 한다. AGENT-01(가드)이 AGENT-02/AGENT-03(파일·셸 도구)보다 먼저 구현·검증되어야 한다.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Book Infra + Basics | 4/4 | Complete | 2026-09-11 |
| 2. Tool Calling | 0/TBD | Not started | - |
| 3. RAG | 0/TBD | Not started | - |
| 4. LangGraph + LangSmith | 0/TBD | Not started | - |
| 5. Capstone + Appendix | 0/TBD | Not started | - |
