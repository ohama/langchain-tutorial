# Feature Landscape

**Domain:** LangChain/LangGraph 한국어 튜토리얼 책 (mdBook, 개인 학습 기록 + 공개 배포, Python, 캡스톤 = 코딩 에이전트)
**Researched:** 2026-09-11
**Confidence:** MEDIUM-HIGH (공식 문서·레퍼런스로 API 현황 확인, 한국어 튜토리얼 2종 목차 확인. 다만 "flashnext" 로컬 모델의 tool-calling/구조화 출력 신뢰도는 실제 코드 실행으로만 검증 가능하므로 챕터별 실행 시점에 재확인 필요)

카테고리 = 책의 파트: **Book infra / Basics / Tool calling / RAG / LangGraph / Observability(LangSmith) / Capstone agent / Appendix**

---

## Table Stakes

이게 없으면 "LangChain 튜토리얼"이라고 부르기 민망한 것들. WikiDocs의 `<랭체인 노트>`, TeddyNote `langchain-kr`/패스트캠퍼스 강의, LangChain 공식 docs, LangGraph Academy가 공통으로 다루는 항목.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **[Book infra] mdBook 목차·챕터 구조 + GitHub Pages CI 배포** | 프로젝트 형식 자체의 전제조건 | LOW | mdbook v0.5.3 확인됨. GitHub Actions로 `mdbook build` → Pages. |
| **[Book infra] .env 기반 설정 분리 (base_url/모델명/API 키)** | 독자가 자신의 LLM 환경으로 바꿔 따라할 수 있어야 함; 공개 저장소에 키 노출 방지 | LOW | `.env.example` 제공, `.env`는 `.gitignore`. |
| **[Book infra] 챕터 포맷 고정: 개념→최소 코드→실제 실행 결과→요점 정리** | PROJECT.md의 핵심 가치("모든 코드는 실제로 돈다"); 모든 인기 LangChain 튜토리얼(WikiDocs, TeddyNote, 공식 docs)의 공통 패턴 | LOW | 템플릿화해서 반복 적용. |
| **[Basics] 채팅 모델 호출 (`ChatOpenAI(base_url=...)`, `invoke`/`stream`)** | 모든 LangChain 학습의 진입점 | LOW | 로컬 OpenAI 호환 서버 기준이라 `langchain-openai`만으로 충분, `langchain-ollama` 불필요. |
| **[Basics] 메시지 타입 (`SystemMessage`/`HumanMessage`/`AIMessage`/`ToolMessage`)과 멀티턴 대화** | LCEL·에이전트·그래프 상태(`add_messages`)의 기반 개념 | LOW | 이후 모든 챕터(RAG, LangGraph, capstone)가 이 개념 위에 쌓임. |
| **[Basics] 프롬프트 템플릿 (`ChatPromptTemplate`, few-shot)** | WikiDocs CH02, 공식 docs 공통 | LOW | |
| **[Basics] 구조화된 출력 (`with_structured_output`, Pydantic 모델)** | LangChain 1.x에서 `PydanticOutputParser` 등 텍스트 파싱형 출력 파서보다 표준이 된 방식; `create_agent`의 `response_format=`과도 직결 | MEDIUM | 로컬 모델(`flashnext`)이 tool-calling 기반 구조화 출력을 지원하는지 실제 실행으로 검증 필요 — 안 되면 JSON 모드/파서 fallback 필요. |
| **[Basics] LCEL / Runnable 인터페이스 (`\|` 파이프, `RunnableParallel`, `RunnableLambda`, `.batch`/`.stream`)** | LangChain의 조합 문법 자체가 LCEL이며, 1.0 이후에도 유지되는 핵심 추상화(에이전트 전용 API와는 별개로 계속 표준) | MEDIUM | 공식 문서·모든 한국어 튜토리얼(WikiDocs CH01, TeddyNote Part2-3,7)이 필수로 다룸. |
| **[Tool calling] `@tool` 데코레이터로 도구 정의 + 모델의 tool call 파싱** | 에이전트의 최소 단위 개념 | LOW | 로컬 모델의 tool-calling 정확도를 실행으로 확인해야 함(PROJECT.md에 이미 1회 검증 기록 있음: `get_weather` 성공). |
| **[Tool calling] 수동 도구 실행 루프 (모델→tool call→ToolMessage→재호출)** | `create_agent`로 넘어가기 전에 "에이전트 루프"가 실제로 무엇인지 체감시키는 것이 이 책의 교육적 핵심 | MEDIUM | 이 루프를 손으로 한 번 짜보는 것이 LangGraph 챕터의 예열이 됨. |
| **[Tool calling] `langchain.agents.create_agent` (LangGraph 기반 harness) 소개** | LangChain 1.0(2025-10-22 GA) 이후 공식 권장 진입점. `langgraph.prebuilt.create_react_agent`도 deprecated, 구 `AgentExecutor`/`initialize_agent`는 `langchain-classic`으로 이동 | MEDIUM | "직접 만든 루프" → "`create_agent`로 같은 것을 몇 줄로" 대비가 좋은 교육 장치. |
| **[RAG] 문서 로딩 → 텍스트 분할(`RecursiveCharacterTextSplitter` 등) → 임베딩 → 벡터스토어 → 검색 → 생성** | RAG의 표준 5단계, 모든 RAG 튜토리얼의 공통 골격 | MEDIUM | |
| **[RAG] 로컬 다국어 임베딩 모델 사용 (한국어 검색 포함)** | PROJECT.md에서 `bge-small-en-v1.5`는 영어 전용이라 명시적으로 다국어 모델 도입을 결정함 | MEDIUM | `bge-m3`, `multilingual-e5` 계열 등이 후보(STACK.md 영역). 한국어 청크 크기/토크나이저 특성상 chunk 사이즈 튜닝 필요할 수 있음. |
| **[RAG] 로컬 벡터스토어 (`Chroma` 등 임베디드형)** | 별도 서버 없이 로컬 실습에 적합 | LOW | 외부 클라우드 벡터 DB는 이 프로젝트 범위 밖. |
| **[LangGraph] `StateGraph`, `TypedDict`/`Annotated` 상태, 노드/엣지 정의** | LangGraph의 최소 문법, LangGraph Academy 1장("From Chains to Graphs")과 동일 순서 | MEDIUM | |
| **[LangGraph] 조건 분기(`add_conditional_edges`)와 반복(루프백 엣지)** | 에이전트 패턴(도구 호출 반복, 재시도)의 기반 | MEDIUM | LangGraph Academy 2장과 동일 개념. |
| **[LangGraph] 체크포인터/메모리 (`InMemorySaver`, `thread_id` 기반 대화 지속)** | 멀티턴 상태 유지 없이는 "에이전트가 기억한다"는 느낌을 줄 수 없음; capstone 에이전트가 여러 턴에 걸쳐 작업하려면 필수 | MEDIUM | 디스크 영속 체크포인터(SQLite 등)는 옵션(차별화 요소로 격상 가능). |
| **[Observability] LangSmith 트레이싱 켜고 끄기 (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`)** | "에이전트 내부 동작을 들여다본다"는 이 챕터의 목적 자체 | LOW | PROJECT.md 제약: 클라우드 전송이므로 해당 챕터에서만 선택적으로 켠다 — `.env`의 플래그 하나로 on/off. |
| **[Observability] 트레이스 읽는 법 (호출 트리, 토큰/지연시간, tool call 인자·결과 확인)** | 트레이싱을 "켜기만" 하고 안 읽으면 챕터의 의미가 없음 | LOW | LangGraph 노드별로 트레이스가 어떻게 쪼개지는지 캡스톤 에이전트 디버깅과 연결. |
| **[Capstone] 샌드박스 루트 강제 (경로 정규화 + prefix 검사, symlink 방지)** | 코딩 에이전트가 "승인 없이" 자유롭게 도는 것이 이 프로젝트의 핵심 위험 지점; 2026년 상반기 LangChain/LangGraph 경로 탈출 취약점(CVE-2026-34070 등)이 실제로 보고됨 | MEDIUM | 모든 파일 도구(read/write/list/edit)와 shell 실행에 공통 적용되는 단일 가드 함수로 구현 — 이 책에서 가장 중요한 보안 학습 포인트. |
| **[Capstone] 기본 파일 도구: `list_dir`, `read_file`, `write_file`(또는 `edit_file`)** | `deepagents`의 기본 도구 세트(`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`)와 동일 계열이 사실상 업계 표준 최소 세트 | MEDIUM | 직접 구현해서 LangGraph tool로 등록 — "왜 이 도구가 필요한가"를 손으로 배우는 것이 목적. |
| **[Capstone] shell 명령 실행 도구 (`run_shell`, 작업 디렉토리 고정)** | "파일만 고치는" 에이전트가 아니라 "코드를 돌려보는" 에이전트가 되려면 필수 | MEDIUM | `cwd`를 샌드박스 루트로 고정, 타임아웃 필수(무한 루프/장기 실행 명령 방지). |
| **[Capstone] 에이전트 루프 (모델↔도구 반복, 종료 조건)** | LangGraph 챕터에서 배운 조건 분기·루프백을 그대로 응용하는 지점 | MEDIUM | `create_agent`를 바로 쓸 수도 있지만, LangGraph로 직접 구성해 "안이 어떻게 생겼는지" 보여주는 쪽이 이 책의 교육 목적에 더 맞음(공식 문서도 `create_agent`가 LangGraph 위에 구성된 것이라 설명). |
| **[Capstone] 체크포인터로 세션/작업 상태 유지** | 여러 턴에 걸친 코딩 작업(파일 여러 개 순차 수정)을 지원하려면 필요 | LOW | LangGraph 챕터에서 배운 것 재사용. |
| **[Capstone] 진행 상황 스트리밍 (`stream_mode="updates"` 또는 `"messages"`)** | 승인 없이 자유롭게 도는 에이전트일수록 "지금 뭘 하고 있는지" 실시간으로 보여주는 것이 안전감·디버깅 양쪽에 중요 | MEDIUM | 최소한 "어떤 도구를 어떤 인자로 호출했는지"를 매 스텝 콘솔에 출력. |
| **[Appendix] 로컬 LLM 새로 설치 (예: Ollama) 안내** | 본문은 이미 떠 있는 서비스를 전제로 하므로, 처음부터 따라오는 독자를 위한 진입 경로가 부록에 필요 | LOW | |
| **[Appendix] uv 기반 Python 환경/의존성 고정** | 재현성(이 책의 핵심 가치)의 실행 기반 | LOW | Python 3.14가 LangChain 생태계와 호환되는지 확인 필요 — 안 되면 `uv python pin`으로 지원 버전 고정. |

---

## Differentiators

이 책을 "그냥 또 하나의 LangChain 튜토리얼"이 아니게 만드는 요소들. PROJECT.md의 Core Value(모든 코드·출력이 실제 결과)와 직결되는 것 위주로 골랐다.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **[Book infra] 100% 로컬 LLM 기준 튜토리얼** | 대부분의 한국어/영어 LangChain 튜토리얼은 OpenAI API 키 발급을 전제로 시작함(WikiDocs CH01가 "OpenAI API 키 발급"부터 시작하는 것이 대표적). 클라우드 비용·키 없이 완주 가능한 한국어 자료는 드묾 | LOW(이미 환경 있음) | 차별화 포인트를 SUMMARY/README에서 명시적으로 강조할 가치 있음. |
| **[Book infra] 실제 실행 로그를 그대로 수록 (재현 가능한 .py 스크립트 동반)** | 대부분의 튜토리얼은 "예상 출력"을 손으로 써넣거나 캡처 없이 설명만 함; 이 책은 저장소의 `.py`가 곧 책의 소스 오브 트루스 | MEDIUM | CI에서 예제를 실제로 실행해 출력을 검증하는 스크립트가 있으면 신뢰성이 한 단계 더 올라감(선택 사항, quick depth에서는 후순위). |
| **[Tool calling→Capstone] "직접 루프 구현 → create_agent로 리팩터링" 대비 학습** | 대부분의 튜토리얼은 `create_agent`/`AgentExecutor`만 보여주고 내부를 블랙박스로 남김; 손으로 짠 뒤 프레임워크로 갈아타는 순서는 이해도를 크게 높임 | MEDIUM | LangGraph Academy도 유사한 "체인→그래프" 점진적 전개를 채택. |
| **[RAG] 한국어 실질 검색 품질 검증 (다국어 임베딩 실측 비교)** | "다국어 임베딩을 쓴다"고 말만 하는 대신, `bge-small-en` vs 다국어 모델로 같은 한국어 질의를 실제로 돌려 검색 결과 차이를 보여줌 | MEDIUM | 실행 결과 비교 표 하나만으로도 큰 설득력. |
| **[LangGraph] 그래프 시각화 (`get_graph().draw_mermaid_png()` 등)** | 상태 그래프의 구조를 다이어그램으로 보여주면 개념 이해가 빨라짐; 한국어 자료에서 자주 생략됨 | LOW | mdBook에 이미지로 삽입. |
| **[Observability] LangSmith 트레이스와 LangGraph 노드를 나란히 대응시켜 설명** | "트레이싱 켜는 법"만 다루는 자료는 많지만, 그래프 구조↔트레이스 트리를 1:1로 매핑해 설명하는 자료는 드묾 | LOW | Observability 챕터의 실질적 가치 지점. |
| **[Capstone] 승인 없는 자율 실행 + 샌드박스 격리라는 명시적 트레이드오프 설명** | 대부분의 프로덕션 지향 자료(`deepagents` 문서 포함)는 human-in-the-loop 승인을 기본값으로 권장함; 이 책은 "왜 굳이 승인 없이 가는가, 대신 무엇으로 안전을 확보하는가(경로 강제, 타임아웃, 별도 폴더)"를 명시적으로 논의 | LOW | PROJECT.md의 의도적 결정을 챕터 내러티브로 드러내면 단순 튜토리얼이 아니라 "설계 판단"을 보여주는 글이 됨. |
| **[Capstone] 실제 코딩 태스크로 마무리 데모** (예: 버그가 있는 작은 스크립트를 에이전트가 읽고 고치고 실행해서 검증) | 추상적인 "파일을 읽고 씁니다" 데모보다 "실제로 버그를 고쳤다"는 엔드투엔드 스토리가 임팩트가 큼 | MEDIUM | 캡스톤 챕터의 하이라이트. |
| **[Appendix] `deepagents`/`create_deep_agent` 간단 소개 (선택 심화)** | 캡스톤을 손으로 만든 뒤, "같은 걸 batteries-included 패키지로 하면 몇 줄이면 된다"는 것을 짧게 보여주면 생태계 지형을 넓혀줌 | LOW | 본문 필수는 아니고 부록/후기 수준의 짧은 소개로 충분(quick depth 고려). |

---

## Anti-Features

겉보기엔 자연스러워 보이지만 넣으면 안 되거나, 시대에 뒤처졌거나, PROJECT.md의 스코프를 벗어나는 것들.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **`LLMChain`, `SimpleSequentialChain` 등 레거시 체인** | LangChain 1.0에서 `langchain-classic`으로 격리됨. 폐기 예정(2026-12까지 유지보수 모드) API를 새 학습 자료에 넣으면 바로 낡은 자료가 됨 — PROJECT.md 제약(최신 1.x API, 폐기 API 배제)에 정면으로 위배 | LCEL(`\|` 파이프)로 동일한 체인 구성을 표현 |
| **`AgentExecutor` / `initialize_agent`** | 마찬가지로 `langchain-classic`으로 이동, deprecated. 여전히 웹의 많은 튜토리얼(2025년 이전 자료)이 이걸 기본으로 가르치고 있어 혼란의 근원 | `langchain.agents.create_agent` 또는 직접 짠 LangGraph 루프 |
| **`langgraph.prebuilt.create_react_agent`를 "최신"으로 소개** | 이것도 deprecated 되어 `langchain.agents.create_agent`로 대체됨(임포트 경로와 이름이 모두 바뀜) | `langchain.agents.create_agent` 사용, 필요시 "예전엔 이렇게 불렸다" 정도만 각주 처리 |
| **`ConversationBufferMemory` 등 구 메모리 클래스** | `langchain-classic`으로 이동. LangGraph 체크포인터가 표준 대체재 | `InMemorySaver` + `thread_id`, 필요시 메시지 트리밍/요약 미들웨어 |
| **OpenAI/Anthropic 등 클라우드 LLM 키 발급을 본문에서 전제** | PROJECT.md에서 명시적으로 아웃오브스코프(로컬 서비스 기준) | `.env`의 `base_url`만 바꾸면 클라우드로도 전환 가능하다는 점을 각주로만 언급 |
| **Jupyter 노트북 포맷** | PROJECT.md에서 명시적으로 배제(책 + 실행 가능한 `.py`로 통일) | mdBook 코드 블록 + 저장소의 `.py` 스크립트, 실제 실행 로그를 캡처해 삽입 |
| **코딩 에이전트에 human-in-the-loop 승인/인터럽트 흐름 추가** | PROJECT.md에서 명시적으로 배제(샌드박스 격리로 안전 확보, 승인 없이 실행하기로 결정). LangGraph Academy나 `deepagents` 문서는 프로덕션 관점에서 승인 흐름을 강하게 권장하지만, 이 프로젝트의 스코프와 맞지 않음 | 샌드박스 경로 강제 + 실행 타임아웃 + 진행 상황 스트리밍으로 안전성/가시성 확보. HITL은 "이런 선택지도 있다" 각주로만 언급 |
| **팀 교육용 커리큘럼 요소 (퀴즈, 과제, 체크포인트 시험)** | PROJECT.md에서 배제(개인 학습 기록이 목적) | 챕터 끝의 "요점 정리"로 충분 |
| **모든 출력 파서(`PydanticOutputParser`, `CommaSeparatedListOutputParser`, `PandasDataFrameOutputParser`, `DatetimeOutputParser` 등)를 백과사전식으로 나열** | WikiDocs CH03처럼 파서 종류를 전부 훑는 방식은 "quick depth"(3–5 phases) 목표와 맞지 않고, `with_structured_output`이 사실상 표준이 된 지금 학습 가치가 낮음 | `with_structured_output` + Pydantic 모델 하나로 구조화 출력 개념을 가르치고, 텍스트 파서는 "필요하면 이런 것도 있다" 한 줄 언급 |
| **범용 벡터 DB 인프라 심화 (Pinecone/Weaviate 등 클라우드 벡터스토어 운영, 샤딩·스케일링)** | 개인 학습·로컬 실습 스코프를 벗어나는 프로덕션 인프라 주제 | 로컬 임베디드 벡터스토어(`Chroma` 등) 하나로 RAG 개념만 완성 |
| **에이전트 프레임워크 전수 비교 (AutoGPT, CrewAI, AutoGen 등과의 다각 비교 챕터)** | 이 책은 LangChain/LangGraph에 집중하는 것이 목적이지 에이전트 프레임워크 시장 조사가 아님 | 필요하면 부록/후기에 한두 줄 언급 정도로 제한 |
| **LangSmith의 평가(Evaluation)·데이터셋·SaaS 협업 기능까지 확장** | "에이전트 내부를 들여다본다"는 챕터 목적을 넘어서는 팀/프로덕션 기능(자동 평가자는 Cloud 전용 기능이 많아 로컬 우선 원칙과도 어긋남) | 트레이싱(호출 트리, 지연시간, tool call 확인)까지만 다루고 멈춤 |

---

## Feature Dependencies

```
[Book infra: mdBook + CI]
    └──requires nothing (foundation)

[Basics: 채팅 모델 호출 + 메시지]
    └──requires──> [Book infra]

[Basics: 프롬프트 템플릿]
    └──requires──> [Basics: 채팅 모델 호출]

[Basics: LCEL/Runnable]
    └──requires──> [Basics: 채팅 모델 호출 + 프롬프트]

[Basics: 구조화된 출력 (with_structured_output)]
    └──requires──> [Basics: LCEL]
    └──enhances──> [Capstone: 구조화된 도구 응답이 필요할 때]

[Tool calling: @tool 정의]
    └──requires──> [Basics: 채팅 모델 호출]

[Tool calling: 수동 도구 실행 루프]
    └──requires──> [Tool calling: @tool 정의]
    └──enhances──> [LangGraph: 조건 분기/루프] (같은 개념을 그래프로 재구성)

[Tool calling: create_agent 소개]
    └──requires──> [Tool calling: 수동 도구 실행 루프]  (먼저 손으로 짜본 뒤 대비)

[RAG: 문서 로딩→분할→임베딩→벡터스토어→검색·생성]
    └──requires──> [Basics: LCEL]
    └──requires──> [Basics: 프롬프트 템플릿] (검색 결과를 프롬프트에 주입)
    └──independent of──> [Tool calling] (병렬 진행 가능하지만, PROJECT.md 순서상 Tool calling 다음)

[LangGraph: StateGraph/노드/엣지]
    └──requires──> [Tool calling: 수동 도구 실행 루프] (도구 호출 개념을 그래프 노드로 옮김)

[LangGraph: 조건 분기 + 루프백]
    └──requires──> [LangGraph: StateGraph 기본]

[LangGraph: 체크포인터/메모리]
    └──requires──> [LangGraph: StateGraph 기본]
    └──requires for──> [Capstone: 세션 상태 유지]

[Observability: LangSmith 트레이싱]
    └──requires──> [LangGraph: StateGraph] (그래프 노드가 있어야 트레이스 구조가 의미 있음)
    └──enhances──> [Capstone: 디버깅]

[Capstone: 샌드박스 경로 강제]
    └──requires nothing new, but MUST precede──> [Capstone: 모든 파일/shell 도구]
      (도구를 먼저 만들고 나중에 가드를 붙이면 안 됨 — 가드가 먼저)

[Capstone: 파일 도구 (list/read/write)]
    └──requires──> [Tool calling: @tool 정의]
    └──requires──> [Capstone: 샌드박스 경로 강제]

[Capstone: shell 실행 도구]
    └──requires──> [Capstone: 샌드박스 경로 강제]
    └──requires──> [Capstone: 파일 도구] (같은 가드 재사용)

[Capstone: 에이전트 루프]
    └──requires──> [LangGraph: 조건 분기 + 루프백]
    └──requires──> [Capstone: 파일/shell 도구]

[Capstone: 체크포인터 기반 세션 유지]
    └──requires──> [LangGraph: 체크포인터/메모리]
    └──requires──> [Capstone: 에이전트 루프]

[Capstone: 진행 상황 스트리밍]
    └──requires──> [Capstone: 에이전트 루프]
    └──enhances──> [Observability: 실시간 가시성 보완]

[Appendix: 로컬 LLM 새로 설치 / uv 환경]
    └──independent, can be written any time (참조되지만 본문 순서에 끼지 않음)
```

### Dependency Notes

- **샌드박스 경로 강제가 파일/shell 도구보다 먼저:** 도구를 만들고 나서 보안을 덧붙이는 순서로 가르치면, 독자가 "가드 없는 버전"을 그대로 복사해 쓸 위험이 있다. 챕터 내에서도 "가드 함수 → 그 위에 도구" 순서를 지킬 것.
- **Tool calling(수동 루프) → LangGraph → create_agent 소개** 순서가 이 책의 핵심 학습 곡선이다. 처음부터 `create_agent`만 보여주면 캡스톤에서 LangGraph를 손으로 다루는 이유가 약해진다.
- **RAG는 Tool calling/LangGraph와 개념적으로 독립적**이지만 PROJECT.md가 이미 순서를 기초→도구→RAG→LangGraph로 확정했으므로 그 순서를 따른다(로드맵에서 재조정 여지는 낮음).
- **LangSmith는 LangGraph 이후에 와야** 트레이스에서 노드 단위 구조를 보여줄 수 있어 교육적 효과가 크다.

---

## MVP Recommendation

Depth = quick (3–5 phases)이므로, 아래를 "반드시 있어야 완결된 책"의 최소선으로 본다.

1. Book infra (mdBook 구조 + CI 배포 + .env 분리 + 챕터 포맷) — 다른 모든 챕터의 그릇
2. Basics (채팅 모델·메시지·프롬프트·LCEL·구조화 출력) — 이후 모든 챕터의 문법 기반
3. Tool calling (도구 정의 + 수동 루프 + create_agent 소개) — 에이전트 개념의 씨앗
4. RAG (로딩→분할→다국어 임베딩→벡터스토어→검색·생성) — 표준 RAG 골격 1회 완주
5. LangGraph (StateGraph·조건분기·체크포인터) — 캡스톤의 직접 전제
6. LangSmith (트레이싱 on/off + 트레이스 읽기) — "내부를 들여다본다"는 스토리 완성
7. Capstone (샌드박스 강제 + 파일/shell 도구 + 에이전트 루프 + 체크포인터 + 스트리밍) — 책의 클라이맥스
8. Appendix (로컬 LLM 설치, uv 환경) — 신규 독자 진입 경로

Defer / 선택 사항 (없어도 "완결된 책"이라는 인상에 지장 없음):
- **디스크 영속 체크포인터(SQLite 등):** `InMemorySaver`로도 학습 목적은 충분히 달성됨. 이후 버전에서 "실전에서는 이렇게" 절로 추가 가능.
- **그래프 시각화 이미지:** 있으면 좋지만 없어도 텍스트 설명으로 대체 가능(차별화 요소이지 table stake는 아님).
- **`deepagents` 소개:** 부록/후기 수준의 짧은 언급으로 충분, 별도 챕터 불필요.
- **RAG 평가(정확도 측정, ragas 등):** TeddyNote 강의에는 있지만("RAG 평가&개선" 파트) 이 프로젝트의 quick depth와 개인 학습 목적을 고려하면 과도함 — 다음 마일스톤 후보.
- **CI에서 예제 실행 결과를 자동 검증(출력 diff)하는 파이프라인:** 이상적이지만 인프라 비용이 커서 이번 마일스톤에서는 "수동 실행 후 출력 붙여넣기"로 시작하고, 이후 자동화는 별도 개선 과제로 미룸.

---

## Sources

- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) — `AgentExecutor`/`create_react_agent`(langgraph.prebuilt)/`LLMChain`/`ConversationBufferMemory` 등이 `langchain-classic`으로 이동, `langchain.agents.create_agent`가 신규 표준, `prompt`→`system_prompt` 파라미터 변경 확인
- [Agents - Docs by LangChain](https://docs.langchain.com/oss/python/langchain/agents) — `create_agent` 시그니처, `response_format`, 체크포인터(`InMemorySaver`)·`thread_id`, `stream_events`, LangGraph 기반 구조 확인
- [Is AgentExecutor Deprecated in LangChain? (BSWEN, 2026-06)](https://docs.bswen.com/blog/2026-06-16-is-agentexecutor-deprecated-langchain/) — AgentExecutor 유지보수 모드(2026-12까지) 확인
- [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) / [Sandboxes - Docs by LangChain](https://docs.langchain.com/oss/python/deepagents/sandboxes) — 기본 도구 세트(`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute`), 샌드박스 격리 개념, "시크릿을 샌드박스에 넣지 말 것" 경고
- [deepagents GitHub](https://github.com/langchain-ai/deepagents) / [filesystem middleware 소스](https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/middleware/filesystem.py) — 파일시스템 권한/백엔드 구조
- [LangChain/LangGraph 경로 탈출 취약점 — CSO Online](https://www.csoonline.com/article/4151814/langchain-path-traversal-bug-adds-to-input-validation-woes-in-ai-pipelines.html), [CSA Research Note](https://labs.cloudsecurityalliance.org/research/csa-research-note-langchain-langgraph-vulnerabilities-202603/), [The Hacker News](https://thehackernews.com/2026/03/langchain-langgraph-flaws-expose-files.html) — CVE-2026-34070 등 경로 검증 미흡 사례, 샌드박스 가드가 필수인 근거
- [Streaming - Docs by LangChain](https://docs.langchain.com/oss/python/langchain/streaming/overview) — `stream_mode="updates"`/`"messages"`, 에이전트 진행 상황 스트리밍 방식
- [LangGraph Academy 커리큘럼 (Educative 등 정리)](https://www.educative.io/courses/langgraph-from-langchain-user-to-agent-builder/introduction-to-the-course) — 4장 구성(체인→그래프, 제어 흐름/에이전트 패턴, 신뢰성/메모리/체크포인트, 캡스톤) 확인, 이 책의 LangGraph→Capstone 순서와 정합
- [LangSmith 로컬/온프레미스 트레이싱 관련 자료 종합](https://medium.com/@aviadr1/langsmith-tracing-deep-dive-beyond-the-docs-75016c91f747) — `LANGCHAIN_TRACING_V2="local"` 등 로컬 전용 모드 존재, self-hosted 옵션 및 Cloud 전용 기능(Hub, 자동 평가자) 확인
- [WikiDocs `<랭체인LangChain 노트>`](https://wikidocs.net/book/14314) — 한국어 튜토리얼 목차(CH01 시작하기/LCEL, CH02 프롬프트, CH03 출력 파서 다수) 확인, "출력 파서 전수 나열"이 anti-feature 판단의 근거
- [teddylee777/langchain-kr GitHub](https://github.com/teddylee777/langchain-kr), [TeddyNote RAG 비법노트 (FastCampus)](https://fastcampus.co.kr/data_online_teddy) — Part 구성(LCEL 고급, RAG 평가&개선, Agent, LangGraph, 서비스 배포)에서 이 프로젝트 스코프에 포함/제외할 항목 판단
- 참고: `flashnext` 로컬 모델의 구조화 출력·tool calling 신뢰도는 문서 조사만으로는 확정할 수 없음 — Basics/Tool calling 챕터 작성 시 실제 코드 실행으로 재검증 필요(LOW confidence 항목)

---
*Feature research for: LangChain/LangGraph 한국어 튜토리얼 (mdBook, 개인 학습 기록)*
*Researched: 2026-09-11*
