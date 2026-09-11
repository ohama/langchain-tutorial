# Stack Research

**Domain:** 실행 가능한 예제를 포함하는 mdBook 기반 한국어 LangChain/LangGraph 튜토리얼 (로컬 LiteLLM 엔드포인트, Apple Silicon)
**Researched:** 2026-09-11
**Confidence:** HIGH — 아래 대부분의 항목은 PyPI 메타데이터 조회, 공식 문서 WebFetch, 그리고 **이 프로젝트의 실제 LiteLLM 엔드포인트(`http://127.0.0.1:4000/v1`, 모델 `flashnext`)에 대한 라이브 코드 실행**으로 직접 검증했다(이 세션에서 `uv --python 3.14`로 임시 프로젝트를 만들어 설치·임포트·호출까지 실행). langsmith/GitHub Actions 버전은 공식 릴리스 API로 확인(HIGH). Korean 임베딩 생태계 순위는 WebSearch 기반(MEDIUM)이나, 최종 추천 모델(BAAI/bge-m3)은 실제 Apple Silicon에서 로드·인코딩까지 실행해 성능/정확도를 확인했다(HIGH).

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | **3.14.7** (이미 설치됨, Homebrew) | 런타임 | `langchain`/`langchain-core`/`langchain-openai`/`langgraph`가 명시하는 `requires-python`은 `>=3.10,<4.0`으로 3.14를 배제하지 않는다. 더 중요하게는, C-extension 의존 패키지(torch, numpy, onnxruntime, pydantic-core)가 **이미 macOS arm64용 `cp314` 휠을 배포 중**이고(2026-09 기준), `tokenizers`/`chromadb`/`faiss-cpu`는 `abi3` 휠이라 애초에 파이썬 버전에 구애받지 않는다. 실제로 `uv --python 3.14`로 `langchain 1.4.0`+`langgraph 1.2.11`+`langchain-openai 1.6.2`+`torch 2.14.0`+`chromadb`+`sentence-transformers`+`langchain-chroma`+`langchain-huggingface`를 설치하고 임포트·실행까지 성공했다(빌드 실패 0건). **3.13으로 다운그레이드할 필요 없음.** |
| uv | 0.11.14 (이미 설치됨) | 패키지/venv 관리, 스크립트 실행 | 이미 설치돼 있고 프로젝트 요구사항. `uv add`/`uv run`/`uv sync`로 예제 전용 프로젝트(`examples/`)의 의존성과 lockfile(`uv.lock`)을 재현 가능하게 고정. `uv run --env-file .env`로 python-dotenv 없이도 `.env`를 로드할 수 있다(공식 지원, HIGH). |
| langchain | **1.4.0** | 최상위 편의 API. 이 버전대의 핵심은 `langchain.agents.create_agent` | 2025-10 LangChain v1.0 재설계 이후 표준. `langchain.agents.create_agent`가 LangGraph 런타임 위에서 동작하는 신규 표준 에이전트 생성자임을 실제 임포트로 확인(`middleware`, `checkpointer`, `store`, `response_format` 파라미터 존재). |
| langchain-core | **1.6.2** | 메시지, Runnable/LCEL, Document, VectorStore 등 기반 추상화 | `langchain`/`langchain-openai`/`langgraph`가 공통 의존. `InMemoryVectorStore`, `Document` 등 RAG에 필요한 최소 구성요소가 여기 있어 `langchain-community` 없이도 RAG 파이프라인을 구성할 수 있음(아래 "What NOT to Use" 참고). |
| langchain-openai | **1.6.2** | `ChatOpenAI` — 로컬 LiteLLM 엔드포인트 연동 | 로컬 서버가 OpenAI 호환 API이므로 `langchain-ollama`가 아니라 이 패키지의 `ChatOpenAI(base_url=..., api_key=..., model=...)`를 사용. **라이브 검증:** 기본 invoke, `bind_tools`를 통한 도구 호출, 스트리밍 모두 정상 동작(`finish_reason: tool_calls` 정확히 반환). 단, `with_structured_output`의 **기본값(`method="json_schema"`)은 이 서버에서 500 에러**로 실패함 — 아래 "구조화 출력" 절 참고. |
| langgraph | **1.2.11** | StateGraph, 체크포인터, 조건부 엣지, 캡스톤 에이전트 루프 | `StateGraph`/`add_conditional_edges`/`InMemorySaver`/`langgraph.checkpoint.sqlite.SqliteSaver` 모두 임포트·동작 확인. `langgraph.prebuilt.create_react_agent`는 여전히 임포트는 되지만 공식 마이그레이션 가이드에서 폐기 경로로 안내하므로 신규 코드에는 쓰지 않는다(PITFALLS.md Pitfall 1과 교차 확인). |
| langsmith | **0.12.4** | LangSmith 트레이싱 클라이언트 | `langchain-core`가 내부적으로 사용. 최신 환경변수는 **`LANGSMITH_TRACING=true` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT`**임을 공식 Observability Quickstart로 확인(구 `LANGCHAIN_TRACING_V2`도 하위호환으로 계속 동작하지만 새 문서의 1차 표기는 `LANGSMITH_*`). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain-text-splitters | **1.1.2** | `RecursiveCharacterTextSplitter` | RAG 챕터의 청킹. `langchain-community`가 아니라 독립 패키지에서 임포트(`from langchain_text_splitters import RecursiveCharacterTextSplitter`) — 폐기 경로 아님, 계속 유지보수됨. |
| langchain-huggingface | **1.2.2** | `HuggingFaceEmbeddings` — 로컬 sentence-transformers 모델 래퍼 | 다국어(한국어) 임베딩을 LangChain의 `Embeddings` 인터페이스로 노출. **라이브 검증:** `HuggingFaceEmbeddings(model_name="BAAI/bge-m3", model_kwargs={"device":"mps"}, encode_kwargs={"normalize_embeddings": True})`로 로드·쿼리 임베딩까지 정상 동작. |
| sentence-transformers | **6.0.1** | 임베딩 모델 로딩/추론 엔진 | `langchain-huggingface`의 내부 의존성이자 단독으로도 임베딩 실험에 유용. Apple Silicon MPS 백엔드 사용 가능(`torch.backends.mps.is_available() == True` 확인). |
| BAAI/bge-m3 (HF 모델, 라이브러리 아님) | 모델 카드 기준 최신 | 한국어 포함 다국어(100+ 언어) 임베딩 | **라이브 검증(Apple Silicon, MPS):** 로드 후 인코딩은 3문장 기준 0.92초로 빠름(최초 로드/다운로드에만 약 63초 소요, 이후 프로세스 내 재사용 시 즉시). 한국어-영어 동의 문장 코사인 유사도 0.83 vs 무관 문장 0.29로 명확한 판별력 확인. 1024차원, 8192 토큰 컨텍스트로 긴 한국어 문서도 처리 가능. |
| langchain-chroma | **1.1.0** | `Chroma` 벡터스토어 래퍼 | **라이브 검증:** `Chroma.from_documents(docs, embedding=..., persist_directory=...)` + `similarity_search`까지 한국어 질의로 정상 동작(정답 문서 정확히 검색됨). |
| chromadb | **1.5.9** | Chroma의 임베디드 벡터 DB 엔진 | 서버 프로세스 불필요, 로컬 디렉터리에 영속화. `cp39-abi3` 휠이라 Python 3.14와도 호환. |
| langgraph-checkpoint-sqlite | **3.1.1** | `SqliteSaver` — 파일 기반 영속 체크포인터 | LangGraph/캡스톤 챕터에서 "재시작해도 대화가 이어진다"를 보여줄 때. 기본은 `langgraph.checkpoint.memory.InMemorySaver`(별도 패키지 불필요, `langgraph` 코어에 포함)로 충분하며, 영속성이 필요한 순간에만 도입. |
| python-dotenv | **1.2.3** | `.env` 로딩(코드 내부에서) | 예제 스크립트를 `python foo.py`로 직접 실행할 때 `.env`를 읽기 위함. `uv run --env-file .env python foo.py`로 대체 가능하므로 둘 중 하나만 채택해도 됨 — 이 책은 초심자 대상이므로 코드 안에서 명시적으로 보이는 `load_dotenv()` 쪽을 권장(무엇이 설정을 읽는지 코드로 드러남). |
| pydantic | 2.13.5 (langchain 의존성으로 자동 설치) | `with_structured_output`용 스키마 정의, 캡스톤 상태 모델 | 별도로 버전을 지정할 필요 없음 — langchain-core/langchain-openai가 요구하는 버전이 자동으로 맞춰짐. `pydantic-core`도 `cp314` 네이티브 휠 존재. |
| ruff | 0.16.7 | 예제 코드 린트/포맷 | 책에 실리는 모든 `.py`가 일관된 스타일을 갖도록. CI에서 `ruff check`만 돌려도 "실행은 안 하지만 문법·스타일은 검증"할 수 있어 CI가 LLM 없이도 할 수 있는 최소한의 품질 게이트가 된다. |
| pytest | 9.1.1 | 캡스톤 에이전트의 샌드박스 가드(경로 탈출 방지) 단위 테스트 | LLM 호출 없이도 검증 가능한 부분(경로 정규화, 심볼릭 링크 차단, 위험 명령 블록리스트)은 pytest로 커버 — CI에서 안전하게 실행 가능. |
| pypdf | 6.18.0 | PDF 텍스트 추출(선택) | RAG 챕터에서 PDF 예제를 포함하기로 한다면 `langchain-community.PyPDFLoader` 대신 `pypdf`를 직접 사용해 `Document`를 만들 것(아래 "What NOT to Use" 참고). 이 프로젝트 범위(개인 학습, 한국어 텍스트 중심)라면 아예 마크다운/텍스트 파일 예제로 충분할 수 있음 — FEATURES.md 판단에 위임. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| mdBook | 0.5.4 (로컬엔 0.5.3 설치됨, 최신은 0.5.4) | 책 렌더링 | Python 코드 블록 하이라이팅이 기본 내장(40+ 언어에 python 포함, 별도 설정 불필요). CI에서는 GitHub 릴리스 바이너리를 받아 쓰고, 로컬 버전과 맞추기 위해 CI에서도 태그를 **고정**할 것을 권장(아래 "CI" 절 — "latest" 대신 특정 버전). |
| mdBook 네이티브 `{{#include}}` / `{{#include file.py:anchor}}` | 예제 소스와 캡처된 출력을 챕터에 삽입 | **플러그인(mdbook-cmdrun 등) 불필요.** CI가 로컬 LLM에 접근할 수 없으므로, "빌드 시점에 명령을 실행해 출력을 만드는" 방식(`mdbook-cmdrun`)은 애초에 성립하지 않는다. 대신 로컬에서 예제를 실행해 만든 `.txt`/`.out` 결과 파일을 **커밋**하고, `{{#include}}`로 코드와 결과를 각각 정적으로 삽입하는 방식이 유일하게 타당한 설계. mdBook 공식 기능만으로 충분하므로 서드파티 preprocessor 의존성 자체를 없앨 수 있음. |
| GitHub Actions | CI 빌드·배포 | 아래 "Installation/CI" 절 참고. `actions/checkout@v7`, `actions/configure-pages@v6`, `actions/upload-pages-artifact@v5`, `actions/deploy-pages@v5`(2026-09 기준 최신 릴리스로 확인). |

## Structured Output — 이 프로젝트에서 반드시 알아야 할 라이브 검증 결과

`langchain-openai` 1.6.2의 `ChatOpenAI.with_structured_output()`은 기본값이 `method="json_schema"`다(시그니처로 확인: `method: Literal['function_calling', 'json_mode', 'json_schema'] = 'json_schema'`). 이 프로젝트의 실제 엔드포인트(`http://127.0.0.1:4000/v1`, 모델 `flashnext`, 및 다른 모든 별칭 `flashnext-codex`/`-plan`/`-act`/`-reach-xhigh`)에 대해 세 가지 method를 모두 라이브로 테스트한 결과:

| method | 결과 |
|--------|------|
| `json_schema` (기본값) | **실패.** `500 - Structured response_format is not supported with speculative decoding.` |
| `json_mode` | **실패.** 동일 에러. |
| `function_calling` (기본 strict) | **실패.** 동일 에러 — strict 모드의 tool schema도 내부적으로 제약 디코딩을 타는 것으로 보임. |
| `function_calling` + **`strict=False`** | **성공.** `llm.with_structured_output(Schema, method="function_calling", strict=False)` |
| 순수 `bind_tools([Schema])` + 수동 파싱 | **성공.** tool_calls가 정확한 인자로 반환됨(`tool_choice`로 강제 지정도 가능). |

원인은 이 서버(LiteLLM → MLX)가 **speculative decoding(멀티토큰예측)** 을 켠 상태이며, 이 모드에서는 문법 제약 디코딩(grammar-constrained decoding, `response_format`은 물론 strict function-calling의 내부 구현도 포함)을 지원하지 않기 때문이다.

**권장 패턴(이 프로젝트 전용):** 책의 모든 "구조화 출력" 예제는 `with_structured_output(Schema, method="function_calling", strict=False)`로 통일한다. 다른 로컬 LLM 서버(예: Ollama, 부록에서 다루는 신규 설치)에서는 이 제약이 없을 수 있으므로, 부록에 "당신의 서버가 이 에러를 내지 않는다면 기본값(`method` 생략)을 써도 된다"는 각주를 남긴다. 이 에러 메시지 자체를 트러블슈팅 박스로 책에 실으면 검색 유입 가치도 있다.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Python 버전 | 3.14.7 (그대로 사용) | 3.12/3.13으로 다운그레이드 | 실제로 필요 없음 — 모든 핵심 의존성이 3.14 네이티브 휠 또는 abi3 휠을 이미 배포 중임을 직접 설치로 확인. 괜히 버전을 내리면 "최신 Python 기준"이라는 책의 신뢰성만 낮아짐. |
| 벡터스토어 | Chroma (`langchain-chroma`) | FAISS (`faiss-cpu`) | FAISS는 순수 벡터 인덱스라 메타데이터 필터링·영속화 API가 더 저수준이라 튜토리얼 코드가 길어짐. Chroma는 `persist_directory`만 지정하면 영속화가 되고, 메타데이터 필터가 API에 내장돼 있어 RAG 개념 설명에 더 적합. FAISS는 "이런 대안도 있다" 정도로 각주 처리. |
| 벡터스토어(입문용) | `langchain_core.vectorstores.InMemoryVectorStore` (첫 RAG 예제) | 처음부터 Chroma | 첫 RAG 개념 설명은 인프라(디스크 경로, 클라이언트 초기화) 없이 "임베딩 넣고 유사도 검색"이라는 개념만 보여주는 게 낫다. `InMemoryVectorStore`는 `langchain-core`에 이미 포함돼 있어 추가 설치가 전혀 필요 없음(라이브 확인). 이후 "영속화가 필요해지는 순간"에 Chroma로 전환하는 서사가 교육적으로 자연스럽다. |
| 다국어 임베딩 | BAAI/bge-m3 | intfloat/multilingual-e5-small/base | e5-small(118M, 384차원)은 훨씬 가볍고 빠르지만, bge-m3(568M, 1024차원, 8192 컨텍스트)가 한국어를 포함한 다국어 검색 품질에서 현재(2026) 가장 폭넓게 검증된 오픈소스 기본값이다. 이 프로젝트는 대용량 메모리 Apple Silicon 머신라는 여유가 있고 실제로 로드해본 결과 문제없이 동작했으므로 bge-m3를 기본으로 권장하되, "LLM 서버와 메모리 경쟁" 우려가 실제로 문제가 되면(PITFALLS.md 참고) e5-small로 다운그레이드하는 대안을 부록에 명시. |
| 다국어 임베딩(대안 언급) | — | Qwen3-Embedding, Kanana-Nano-2.1B-Embedding(Kakao) | Qwen3-Embedding은 성능은 좋으나 임베딩 모델치고 크고(8B 옵션은 과함, 작은 옵션도 상대적으로 무거움) 이 튜토리얼의 "가볍게 로컬에서 돌린다"는 취지와 맞지 않음. Kanana는 한국어 특화·경량이라 매력적이지만 다국어 검증 폭이 bge-m3보다 좁고, 이 프로젝트가 한국어-only가 아니라 "다국어 지원"을 요구사항으로 명시했으므로 bge-m3가 더 안전한 기본값. 둘 다 "국산/경량 대안" 각주로 언급할 가치는 있음. |
| 에이전트 구축 방식 | 직접 `StateGraph` 구성 → `langchain.agents.create_agent`로 대비 | `langgraph.prebuilt.create_react_agent`만 사용 | `create_react_agent`(langgraph.prebuilt)는 공식 마이그레이션 가이드상 폐기 경로. 신규 표준은 `langchain.agents.create_agent`(LangGraph 런타임 기반, 미들웨어/체크포인터/구조화출력 내장). ARCHITECTURE.md/FEATURES.md와 일치. |
| LangSmith 환경변수 | `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` | `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` | 구 변수명도 계속 동작하지만(하위호환), 공식 Observability Quickstart의 1차 표기가 `LANGSMITH_*`로 바뀌었으므로 신규 자료는 신규 이름을 기준으로 삼는다. |
| mdBook 출력 캡처 | 로컬 실행 → 커밋된 `.txt` 파일 → `{{#include}}` | `mdbook-cmdrun` 프리프로세서로 빌드 시점에 명령 실행 | CI(GitHub Actions)는 로컬 LLM(`127.0.0.1:4000`)에 네트워크로 접근할 수 없다. `cmdrun`은 "빌드할 때마다 명령을 실행"하는 방식이라 CI 빌드에서는 그 명령이 실패하거나(로컬 전용 preprocessor 설정을 CI에서 끄는 추가 복잡도 필요), 애초에 "저자가 실제로 확인한 출력"이라는 이 책의 핵심 가치와도 맞지 않는다(자동 재실행 결과를 검토 없이 배포하게 됨). 캡처-커밋-include 방식은 mdBook 네이티브 기능만으로 되고 CI 의존성이 없다. |
| GitHub Pages 배포 | 공식 `actions/{checkout,configure-pages,upload-pages-artifact,deploy-pages}` 조합 | `peaceiris/actions-gh-pages` 등 서드파티 액션 | 공식 액션 조합이 GitHub가 직접 유지보수하며, `permissions: pages: write, id-token: write` 기반의 OIDC 배포로 별도 배포 토큰/브랜치 관리가 불필요. 서드파티 액션은 여전히 널리 쓰이지만 이 프로젝트처럼 단순 정적 사이트 배포에는 공식 액션이 더 적은 이동 부품으로 동일한 결과를 낸다. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `langchain-community` (문서 로더, 벡터스토어 등) | **2026-05-22부로 sunset 발표, 2026-06-19에 저장소 archive(read-only)됨.** 이 세션에서 `from langchain_community... import ...`를 실행하면 실제로 `DeprecationWarning: langchain-community is being sunset and is no longer actively maintained`가 출력됨(라이브 확인). 새로 쓰는 튜토리얼 코드에 이걸 쓰면 출간 시점에 이미 "죽은 경로"를 가르치는 꼴이 됨. 게다가 이 경고 자체가 책에 캡처될 출력에 섞여 나와 지저분해짐. | 텍스트/마크다운 소스는 `pathlib.Path.read_text()`로 직접 읽어 `langchain_core.documents.Document(page_content=..., metadata=...)`로 감싼다(라이브 확인 — 추가 의존성 전혀 불필요). 벡터스토어는 `langchain-chroma`, 임베딩은 `langchain-huggingface`처럼 유지보수되는 전용 파트너 패키지 사용. PDF가 꼭 필요하면 `pypdf`를 직접 써서 `Document`로 변환. |
| `langchain.chains.LLMChain`, `SimpleSequentialChain` 등 구 Chain 클래스 | LangChain v1.0에서 `langchain-classic`(레거시 호환 패키지)으로 격리됨. 신규 학습 자료가 폐기 API로 시작하면 안 됨. | LCEL(`prompt | llm | parser`)로 동일한 구성을 표현. |
| `AgentExecutor`, `initialize_agent` | 마찬가지로 `langchain-classic`으로 이동, 유지보수 모드(2026-12까지)만 남음. 인터넷의 옛 튜토리얼 대다수가 아직 이 API 기준이라 검색 시 특히 주의. | `langchain.agents.create_agent`(신규 표준) 또는 직접 짠 LangGraph `StateGraph` 루프. |
| `langgraph.prebuilt.create_react_agent`를 "최신 권장"으로 소개 | 공식 마이그레이션 가이드가 폐기 예정으로 안내(`langchain.agents.create_agent`로 대체). 여전히 임포트는 되지만(1.2.11 기준) 새 코드의 기준으로 삼으면 안 됨. | `langchain.agents.create_agent` — import 경로와 시그니처를 이 세션에서 직접 확인(`model, tools, system_prompt, middleware, response_format, checkpointer, store` 등). |
| `ConversationBufferMemory` 등 구 메모리 클래스 | `langchain-classic`으로 이동. | `langgraph.checkpoint.memory.InMemorySaver` + `thread_id`(라이브 확인, 코어에 포함되어 추가 설치 불필요). |
| `with_structured_output(Schema)` 를 method 지정 없이 그대로 사용 | 기본값 `method="json_schema"`가 **이 프로젝트의 실제 서버에서 500 에러**로 실패함(위 "Structured Output" 절 라이브 검증 결과). 책의 모든 코드가 실제로 돌아야 한다는 핵심 가치를 정면으로 위배. | `with_structured_output(Schema, method="function_calling", strict=False)`로 명시. |
| `LANGCHAIN_TRACING_V2`를 전역 `.env`에 상시 켜두기 | LangSmith 챕터가 아닌 다른 챕터를 실행할 때도 모든 요청이 클라우드로 전송됨(PROJECT.md 제약 위반, PITFALLS.md와 일치). | `LANGSMITH_TRACING`을 해당 챕터 전용 설정(`.env.langsmith` 또는 스크립트 내부 한정)으로 분리. |
| Python 3.14 회피(3.11/3.12로 다운그레이드) | 불필요한 보수적 선택 — 실제로 3.14에서 전체 스택이 빌드/설치/실행됨을 이 세션에서 검증했음. | 3.14.7 그대로 사용, `uv python pin 3.14`로 고정. |
| `mdbook-cmdrun` 등 빌드타임 명령 실행 프리프로세서를 CI 파이프라인에 사용 | CI가 로컬 LLM에 접근 불가하므로 빌드가 깨지거나, 조건부로 껐다 켰다 하는 복잡한 설정이 필요해짐. | 로컬에서 실행·캡처한 정적 출력 파일을 커밋 + mdBook 네이티브 `{{#include}}`. |

## Stack Patterns by Variant

**만약 독자가 부록을 따라 Ollama 등 다른 로컬 LLM으로 바꾼다면:**
- `ChatOpenAI(base_url=...)` 대신 `langchain_ollama.ChatOllama(model=...)`로 교체하거나, Ollama도 OpenAI 호환 엔드포인트(`http://localhost:11434/v1`)를 제공하므로 `ChatOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")`로 코드 변경을 최소화할 수 있음(부록에서 후자를 권장 — 본문 코드와 최대한 동일한 API 표면 유지).
- speculative decoding 제약은 서버 구현에 따라 다르므로, `with_structured_output` 기본값(`method` 생략)이 그 환경에서는 성공할 수도 있음 — 부록에 "당신의 서버에서 기본값이 실패하면 이 프로젝트가 쓴 `function_calling, strict=False`로 바꿔보라"는 트러블슈팅 각주 필수.

**만약 임베딩 모델 메모리 경쟁이 실제로 문제가 된다면(LLM 서버가 이미 RAM 대부분 사용 중):**
- `BAAI/bge-m3` 대신 `intfloat/multilingual-e5-small`(118M, 384차원)로 교체. `HuggingFaceEmbeddings(model_name=...)`의 `model_name` 문자열 하나만 바꾸면 되므로 코드 변경 최소.
- 임베딩 계산을 "문서 인덱싱 스크립트"와 "질의응답 스크립트"로 분리해, 인덱싱이 끝나면 프로세스를 종료해 메모리를 반환(ARCHITECTURE.md 패턴과 일치).

**만약 향후 PDF/HTML 등 복잡한 문서 로더가 필요해진다면:**
- `langchain-community`로 회귀하지 말고, 필요한 최소 라이브러리(`pypdf`, `beautifulsoup4` 등)를 직접 써서 `Document`를 만드는 얇은 로더 함수를 `examples/shared/`에 추가. 유지보수되는 전용 패키지가 있다면(`langchain-docling` 등) 그쪽을 우선 검토.

## Installation

```bash
# uv로 examples/ 프로젝트 초기화 (Python 3.14 고정)
cd examples
uv init --no-workspace --python 3.14
uv python pin 3.14

# 핵심
uv add langchain langchain-core langchain-openai langgraph langsmith

# RAG용
uv add langchain-text-splitters langchain-chroma langchain-huggingface sentence-transformers

# LangGraph 영속 체크포인터(선택, 필요해질 때)
uv add langgraph-checkpoint-sqlite

# 설정/보조
uv add python-dotenv pydantic

# PDF가 꼭 필요할 때만(선택)
uv add pypdf

# 개발 도구
uv add --dev ruff pytest
```

```bash
# 예제 실행 (uv run이 venv를 자동으로 맞춤)
uv run --env-file .env python ch01_basics/01_chat_model.py

# 다국어 임베딩 모델은 최초 실행 시 Hugging Face Hub에서 자동 다운로드됨(수 GB, 최초 1회)
# device="mps"로 Apple Silicon GPU 가속 사용 (torch.backends.mps.is_available() == True 확인됨)
```

```bash
# mdBook (이미 설치됨, 최신으로 갱신하고 싶다면)
mdbook --version   # 로컬 확인된 버전: v0.5.3 (최신 릴리스: v0.5.4, 2026-07-06)
```

### CI: GitHub Pages 배포 워크플로 (`.github/workflows/deploy.yml`)

```yaml
name: Deploy mdBook to GitHub Pages
on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      MDBOOK_VERSION: "0.5.4"   # 로컬 버전과 맞춰 고정 — "latest"로 두면 로컬/CI 렌더링이 미묘하게 어긋날 수 있음
    steps:
      - uses: actions/checkout@v7
      - name: Install mdbook (pinned version)
        run: |
          mkdir mdbook
          curl -sSL "https://github.com/rust-lang/mdBook/releases/download/v${MDBOOK_VERSION}/mdbook-v${MDBOOK_VERSION}-x86_64-unknown-linux-gnu.tar.gz" \
            | tar -xz --directory=./mdbook
          echo "$(pwd)/mdbook" >> "$GITHUB_PATH"
      - name: Build book
        run: mdbook build book
        # 이 단계는 .py 파일을 실행하지 않는다 — {{#include}}는 텍스트 삽입일 뿐,
        # LLM 호출도 uv/langchain 설치도 CI에는 필요 없음.
      - uses: actions/configure-pages@v6
      - uses: actions/upload-pages-artifact@v5
        with:
          path: book/book   # mdbook의 기본 출력 디렉터리(book.toml의 build.build-dir)

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
```

**리포지토리 설정 전제조건:** Settings → Pages → Source를 "GitHub Actions"로 지정해야 위 워크플로가 동작함(공식 문서/위키 확인).

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Python 3.14.7 | langchain 1.4.0, langchain-core 1.6.2, langchain-openai 1.6.2, langgraph 1.2.11, chromadb 1.5.9, faiss-cpu 1.15.0, sentence-transformers 6.0.1, torch 2.14.0 | 전부 이 세션에서 `uv --python 3.14` 가상환경에 설치·임포트·실행 성공(빌드 실패 없음). `tokenizers`/`chromadb`/`faiss-cpu`는 abi3 휠이라 버전 무관하게 항상 호환. |
| torch 2.14.0 (macOS arm64) | MPS 백엔드 | `torch.backends.mps.is_available() == True`를 Apple Silicon에서 직접 확인 — `sentence-transformers`가 `device="mps"`로 bge-m3를 문제없이 로드·추론함. |
| langchain-openai 1.6.2 `with_structured_output` | 이 프로젝트의 LiteLLM(`flashnext` 및 다른 모든 별칭) 엔드포인트 | 기본 `method="json_schema"`/`"json_mode"`/기본 strict `"function_calling"` 모두 500 에러. **`method="function_calling", strict=False`만 성공** — 반드시 이 조합으로 통일. |
| langgraph 1.2.11 | langgraph-checkpoint 4.2.0, langgraph-checkpoint-sqlite 3.1.1 | `InMemorySaver`(코어 포함)와 `SqliteSaver`(별도 패키지) 모두 임포트 확인. |
| langchain-huggingface 1.2.2 | sentence-transformers 6.0.1, BAAI/bge-m3 | `HuggingFaceEmbeddings` + `Chroma.from_documents` 조합으로 한국어 질의 검색까지 end-to-end 확인. |
| mdBook 0.5.x | GitHub Actions `ubuntu-latest` 러너 | 공식 릴리스 tarball(`mdbook-v{ver}-x86_64-unknown-linux-gnu.tar.gz`)로 설치, Rust 툴체인 설치 불필요(prebuilt 바이너리). |

## Sources

- PyPI JSON API (직접 조회, 이 세션에서 실행) — `langchain` 1.4.0, `langchain-core` 1.6.2, `langchain-openai` 1.6.2, `langgraph` 1.2.11, `langsmith` 0.12.4, `langchain-text-splitters` 1.1.2, `langchain-community` 0.4.2(archived), `langchain-chroma` 1.1.0, `langchain-huggingface` 1.2.2, `chromadb` 1.5.9, `faiss-cpu` 1.15.0, `sentence-transformers` 6.0.1, `langgraph-checkpoint` 4.2.0, `langgraph-checkpoint-sqlite` 3.1.1, `torch` 2.14.0, `numpy` 2.5.3, `onnxruntime` 1.30.0, `pydantic-core` 2.49.0, `pypdf` 6.18.0, `ruff` 0.16.7, `pytest` 9.1.1의 최신 버전·`requires_python`·macOS arm64 휠 태그 확인 (HIGH)
- 라이브 실행 검증 (이 세션에서 직접 수행, 2026-09-11): `uv init --python 3.14` 임시 프로젝트에 위 패키지 설치 → `ChatOpenAI(base_url="http://127.0.0.1:4000/v1", model="flashnext")`로 invoke/bind_tools/stream/with_structured_output(3가지 method + strict 옵션) 테스트, `HuggingFaceEmbeddings(model_name="BAAI/bge-m3", device="mps")` 로드·인코딩, `Chroma.from_documents` + `similarity_search` end-to-end 테스트, `langchain.agents.create_agent` 시그니처 확인 (HIGH — 이 프로젝트의 실제 엔드포인트/하드웨어에 대한 1차 증거)
- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) — `create_agent` 표준화, `langchain-classic` 격리 대상 확인 (HIGH)
- [langchain-community sunset 공지 (issue #674)](https://github.com/langchain-ai/langchain-community/issues/674) — 2026-05-22 sunset, 2026-06-19 저장소 archive 확인 (HIGH, 공식 이슈 + 라이브 DeprecationWarning으로 교차 확인)
- [LangSmith Observability Quickstart](https://docs.langchain.com/langsmith/observability-quickstart) — `LANGSMITH_TRACING`/`LANGSMITH_API_KEY`/`LANGSMITH_PROJECT` 현재 표준 환경변수명 확인 (HIGH)
- [mdBook Syntax Highlighting 공식 문서](https://rust-lang.github.io/mdBook/format/theme/syntax-highlighting.html) — Python 기본 지원 확인 (HIGH)
- [mdBook Continuous Integration 공식 문서](https://rust-lang.github.io/mdBook/continuous-integration.html) / [mdBook Wiki: Automated Deployment - GitHub Actions](https://github.com/rust-lang/mdBook/wiki/Automated-Deployment:-GitHub-Actions) — GitHub Actions Pages 배포 워크플로 원형 확인 (HIGH, 공식 위키)
- GitHub Releases API (직접 조회) — `rust-lang/mdBook` v0.5.4, `actions/checkout` v7.0.1, `actions/configure-pages` v6.0.0, `actions/upload-pages-artifact` v5.0.0, `actions/deploy-pages` v5.0.1 최신 버전 확인 (HIGH, 2026-09-11 조회 시점)
- WebSearch: "best open source multilingual embedding model Korean retrieval 2026" — BAAI/bge-m3, Qwen3-Embedding, Kanana-Nano-2.1B-Embedding(Kakao) 등 후보 확인 (MEDIUM, WebSearch 요약 기반이나 최종 선택 모델은 라이브 검증으로 HIGH까지 보강)
- 프로젝트 자체 자료: `.planning/PROJECT.md`, `.planning/research/PITFALLS.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/FEATURES.md` (병렬 연구 결과 교차 확인 — `create_agent` 표준화, `{{#include}}` 채택, 임베딩 메모리 경쟁 우려 등이 일치함)

---
*Stack research for: 한국어 LangChain/LangGraph 튜토리얼 (mdBook, 로컬 LLM, Apple Silicon)*
*Researched: 2026-09-11*
