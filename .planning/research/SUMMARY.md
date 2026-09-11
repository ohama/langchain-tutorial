# Project Research Summary

**Project:** LangChain Tutorial (한국어)
**Domain:** 실행 가능한 예제를 포함하는 mdBook 기반 한국어 LangChain/LangGraph 튜토리얼 (로컬 LiteLLM 엔드포인트, GitHub Pages 배포, 캡스톤 = 샌드박스 코딩 에이전트)
**Researched:** 2026-09-11
**Confidence:** HIGH — 핵심 결정 대부분이 이 프로젝트의 실제 LiteLLM 엔드포인트(`http://127.0.0.1:4000/v1`, 모델 `flashnext`)에 대한 라이브 코드 실행으로 검증되었다.

## Executive Summary

이 프로젝트는 "개인 학습 기록이자 공개 배포되는 실행형 튜토리얼 책"이다. 전문가들이 이런 자료를 만드는 표준 방식은 (1) 개념 설명은 최소화하고 실제로 돌아가는 코드와 실제 출력을 1:1로 대응시키며, (2) 최신 LangChain 1.0(2025-10 GA) API — LCEL, `langchain.agents.create_agent`, LangGraph `StateGraph` — 만을 표준으로 삼아 이미 `langchain-classic`으로 격리된 폐기 API(`LLMChain`, `AgentExecutor`, `create_react_agent`)를 배제하는 것이다. 4개 연구 파일 모두 독립적으로 이 결론에 수렴했다.

권장 접근은 다음과 같다. 스택은 Python 3.14.7 + `langchain 1.4.0`/`langgraph 1.2.11`/`langchain-openai 1.6.2`를 그대로 사용하고(다운그레이드 불필요, 라이브 검증됨), RAG는 `langchain-chroma` + `HuggingFaceEmbeddings(BAAI/bge-m3)`로 다국어(한국어) 검색을 구성한다. 아키텍처는 "로컬에서 실행·캡처 → 커밋된 `.py`/`.out` 파일 → mdBook `{{#include}}`로 조립 → CI는 빌드만" 이라는 실행/조립 분리 패턴을 전 챕터에 예외 없이 적용해야 한다(핵심 가치인 "코드-출력 무결성"이 이 패턴 하나에 구조적으로 의존한다).

가장 큰 리스크는 세 가지다. 첫째, 이 프로젝트의 로컬 서버가 speculative decoding을 사용해 `with_structured_output`의 기본값(`method="json_schema"`)이 500 에러로 실패한다 — 반드시 `method="function_calling", strict=False`로 통일해야 한다(라이브로 확정됨). 둘째, 폐기 예정 API를 검색으로 베껴 쓸 위험이 매우 크다(인터넷 콘텐츠 절대다수가 구버전 기준). 셋째, 캡스톤 코딩 에이전트는 "승인 없이 실행"하기로 결정했으므로 경로 탈출(symlink, `../`) 방어와 셸 명령 안전장치가 선택이 아니라 필수이며, 얕은 문자열 검증은 실제로 우회당한다. 이 세 리스크 모두 완화 전략이 이미 라이브 테스트로 검증되어 있어 실행 난이도는 낮다.

## Key Findings

### Recommended Stack

Python 3.14.7과 uv를 그대로 사용하고, LangChain 1.0 재설계 이후 표준인 `langchain 1.4.0` + `langchain-core 1.6.2` + `langgraph 1.2.11`을 채택한다. 이 조합은 이 세션에서 실제로 설치·임포트·호출까지 확인되었다(빌드 실패 0건). RAG 스택은 `langchain-chroma`(벡터스토어) + `langchain-huggingface`(`HuggingFaceEmbeddings`) + `BAAI/bge-m3`(다국어 임베딩, Apple Silicon MPS에서 로드·인코딩 검증)로 구성하고, 첫 RAG 예제는 설치가 필요 없는 `langchain_core.vectorstores.InMemoryVectorStore`로 개념만 보여준 뒤 Chroma로 전환하는 서사를 권장한다. 문서 로더는 `langchain-community`(2026-06 archive됨) 대신 `pathlib.Path.read_text()` + `Document`로 직접 구성한다.

**Core technologies:**
- `langchain 1.4.0` / `langchain-core 1.6.2`: 최상위 편의 API·메시지·Runnable — `create_agent`가 이 버전대의 표준 에이전트 생성자
- `langchain-openai 1.6.2`: `ChatOpenAI(base_url=...)`로 로컬 LiteLLM(OpenAI 호환) 연동 — invoke/bind_tools/stream 라이브 검증 완료
- `langgraph 1.2.11`: `StateGraph`, 조건부 엣지, `InMemorySaver`/`SqliteSaver` — 캡스톤 에이전트 루프의 기반
- `langchain-chroma` + `langchain-huggingface`(`BAAI/bge-m3`): 로컬 임베디드 벡터스토어 + 다국어(한국어) 임베딩
- mdBook(0.5.x) + GitHub Actions(공식 `actions/{checkout,configure-pages,upload-pages-artifact,deploy-pages}`): 책 렌더링·Pages 배포, CI는 코드 실행 없이 정적 조립만 수행

### Expected Features

FEATURES.md는 WikiDocs/TeddyNote/LangGraph Academy 등 기존 한국어·영어 튜토리얼과 비교해 table stakes와 차별화 요소를 구분했다. 이 책의 핵심 차별화는 "100% 로컬 LLM 기준"과 "실제 실행 로그를 그대로 수록"이라는 두 가지로, 대부분의 경쟁 자료가 클라우드 API 키 발급을 전제로 시작하는 것과 대비된다.

**Must have (table stakes):**
- Book infra: mdBook 목차 구조 + GitHub Pages CI 배포 + `.env` 설정 분리 + 챕터 포맷(개념→코드→실행결과→요점) 고정
- Basics: 채팅 모델 호출, 메시지 타입, 프롬프트 템플릿, `with_structured_output`, LCEL/Runnable
- Tool calling: `@tool` 정의, 수동 도구 실행 루프, `create_agent` 소개
- RAG: 로딩→분할→다국어 임베딩→벡터스토어→검색·생성 5단계 골격
- LangGraph: `StateGraph`/조건 분기/체크포인터(`InMemorySaver`)
- LangSmith: 트레이싱 on/off + 트레이스 읽는 법
- Capstone: 샌드박스 경로 강제, 파일 도구(list/read/write), shell 실행 도구, 에이전트 루프, 체크포인터 세션 유지, 진행 상황 스트리밍

**Should have (differentiators):**
- "직접 루프 구현 → `create_agent`로 리팩터링" 대비 학습 (프레임워크를 블랙박스로 남기지 않음)
- 한국어 실질 검색 품질 실측 비교(영어 전용 임베딩 vs 다국어 임베딩)
- LangGraph 그래프 시각화(`draw_mermaid_png`), LangSmith 트레이스↔그래프 노드 1:1 매핑 설명
- 캡스톤의 "승인 없는 자율 실행 + 샌드박스 격리" 트레이드오프를 명시적으로 논의

**Defer (v2+):**
- 디스크 영속 체크포인터(SQLite) — `InMemorySaver`로 학습 목적 충분
- `deepagents` 소개, RAG 평가(ragas 등), CI 자동 출력 검증(diff) 파이프라인 — quick depth 범위 밖
- 출력 파서 백과사전식 나열, 클라우드 벡터 DB 심화, 에이전트 프레임워크 전수 비교 — anti-feature로 명시적 배제

### Architecture Approach

핵심은 "로컬 실행(LLM 필요) / 조립(CI, LLM 불필요)"의 물리적 분리다. `examples/`(uv 단일 프로젝트)의 `.py`를 로컬에서 실행해 `outputs/*.out`(소스 sha256 헤더 포함)으로 캡처·커밋하고, `book/src/*.md`는 `{{#include}}`로만 코드와 출력을 끌어온다. GitHub Actions는 `mdbook build`만 수행하며 `.py`를 실행하거나 LLM을 호출하지 않는다 — CI가 로컬 LLM(`127.0.0.1:4000`)에 네트워크로 접근할 수 없다는 제약이 이 아키텍처의 근본 원인이다.

**Major components:**
1. `book/src/chNN_topic/` ↔ `examples/chNN_topic/` ↔ `outputs/chNN_topic/` — 동일 이름·번호 접두사로 3트리 병렬 유지, 경로만 보고 대응 관계 파악 가능
2. `examples/shared/config.py` — `.env` 기반 `base_url`/`model`/`api_key`를 단일 진입점으로 노출, 모든 예제가 이를 경유(엔드포인트 하드코딩 금지)
3. `scripts/check_fresh.py` — `.py` 소스 해시 vs `.out` 헤더 해시 비교로 드리프트 감지, LLM 호출 없이 CI에서도 안전하게 실행 가능
4. `capstone/` — 손수 짠 `StateGraph`(model 노드 + tool 노드 + 조건부 엣지)와 `create_agent` 버전을 나란히 제시, 도구 자체가 샌드박스 경로 검증을 캡슐화

### Critical Pitfalls

1. **폐기 예정 API로 낡은 책이 됨** — `LLMChain`/`AgentExecutor`/`langgraph.prebuilt.create_react_agent`는 이미 `langchain-classic`으로 격리됨. LCEL + `langchain.agents.create_agent` + 직접 `StateGraph`만 표준으로 채택.
2. **구조화 출력 500 에러** — 이 서버는 speculative decoding 중이라 `with_structured_output`의 기본 method(`json_schema`)가 항상 실패한다. `method="function_calling", strict=False`로 전 챕터 통일(라이브 확정, HIGH).
3. **콜드 스타트 지연(첫 요청 63초)** — 캡처 자동화 스크립트에 워밍업 요청을 선행하고 타임아웃을 120초 이상으로 설정.
4. **키/절대경로/LangSmith 공개 트레이스 노출** — 캡처 자동화에 마스킹 유틸 + 커밋 전 grep 훅 필수, LangSmith 트레이스는 기본 비공개.
5. **캡스톤 샌드박스 탈출** — 문자열 prefix 검증이 아니라 `Path.resolve()` 실경로 비교 필수, `shell=False` + 위험 명령 블록리스트 + `recursion_limit` + 도구 출력 길이 상한.

## Implications for Roadmap

Depth가 "quick"(3-5 phases)이므로 FEATURES.md의 8단계 MVP 순서를 5개 페이즈로 압축한다. 순서는 FEATURES.md의 의존성 그래프(샌드박스 가드 → 도구, Tool calling → LangGraph → Capstone, LangSmith는 LangGraph 이후)를 그대로 따른다.

### Phase 1: Book Infra + Basics
**Rationale:** 이후 모든 챕터가 `{{#include}}` + 해시 헤더 캡처 패턴 위에서 동작하므로, 이 파이프라인(`shared/config.py`, `scripts/run_examples.py`, `scripts/check_fresh.py`, CI 워크플로)을 가장 먼저 만들어야 이후 챕터들이 반복해서 그릇을 재사용할 수 있다. Basics는 이 파이프라인을 검증하는 첫 실사용처이기도 하다.
**Delivers:** mdBook 골격 + GitHub Pages CI 배포 + `.env` 분리 + 챕터 포맷 템플릿 + 채팅 모델/메시지/프롬프트/LCEL/구조화 출력 챕터
**Addresses:** FEATURES.md의 "Book infra" 전체 table stakes, "Basics" table stakes
**Avoids:** Pitfall 1(폐기 API로 시작하지 않도록 버전 고정), Pitfall 2(구조화 출력을 `function_calling, strict=False`로 처음부터 통일), Pitfall 5(캡처 규칙을 인프라 단계에서 확정), Pitfall 6(마스킹/grep 훅을 인프라 단계에서 구축)

### Phase 2: Tool Calling
**Rationale:** 에이전트 루프 개념의 씨앗 — 모델→tool call→ToolMessage→재호출을 손으로 짜본 뒤에야 LangGraph의 조건 분기가 "왜 필요한지" 체감된다. `create_agent`를 여기서 짧게 소개해 캡스톤에서의 대비 학습을 예열한다.
**Delivers:** `@tool` 정의, 수동 도구 실행 루프, `create_agent` 도입부
**Uses:** STACK.md의 `bind_tools`/`ChatOpenAI` 라이브 검증 결과
**Implements:** ARCHITECTURE.md Pattern 3(손수 루프 vs `create_agent` 대비)의 축소판
**Avoids:** Pitfall 3(리즈닝 필드 누출 확인 + 후처리 유틸), 스트리밍/비스트리밍 tool_calls 형식 차이(Moderate Pitfall)

### Phase 3: RAG
**Rationale:** Tool calling과 개념적으로 독립적이지만 PROJECT.md가 순서를 확정했고, 다국어 임베딩 도입이라는 별도 준비(모델 다운로드·로드)가 필요해 한 페이즈로 독립시키는 것이 적절하다.
**Delivers:** 문서 로딩→분할→`BAAI/bge-m3` 임베딩→`Chroma`→검색·생성, 한국어 검색 품질 실측 비교
**Uses:** `langchain-text-splitters`, `langchain-chroma`, `langchain-huggingface`(STACK.md 라이브 검증)
**Avoids:** 다국어 임베딩 모델과 LLM 서버 간 메모리 경쟁(Moderate Pitfall) — 인덱싱/질의 스크립트 분리 권장

### Phase 4: LangGraph + LangSmith
**Rationale:** `StateGraph`/조건 분기/체크포인터가 캡스톤의 직접 전제이며, LangSmith는 그래프 노드 구조가 있어야 트레이스가 교육적으로 의미 있으므로 LangGraph 다음에 온다. 두 주제를 한 페이즈로 묶어 quick depth의 5페이즈 목표를 지킨다.
**Delivers:** `StateGraph`/노드·엣지/조건 분기/`InMemorySaver` 체크포인터, LangSmith 트레이싱 on/off(챕터 국소적) + 트레이스 읽기
**Implements:** ARCHITECTURE.md의 캡스톤 런타임 흐름 중 그래프·체크포인터 부분
**Avoids:** Pitfall 7의 일부(`recursion_limit` 명시, `GraphRecursionError` 처리를 여기서 먼저 학습), LangSmith 전역 상시 활성화(Moderate Pitfall)

### Phase 5: Capstone + Appendix
**Rationale:** 지금까지 배운 도구 정의·에이전트 루프·상태 그래프·체크포인터·트레이싱을 전부 합치는 클라이맥스. 부록(Ollama 설치, uv 환경)은 본문 순서에 끼지 않으므로 마지막에 함께 배치해도 무리 없다.
**Delivers:** 샌드박스 경로 강제(realpath 검증) + 파일/shell 도구 + 손수 `StateGraph` 에이전트 루프 + `create_agent` 대비 버전 + 세션 체크포인터 + 진행 상황 스트리밍, 실제 버그 수정 데모, 부록(Ollama/uv)
**Avoids:** Pitfall 7(샌드박스 탈출) 전체, 배포 단계 pitfalls(mdBook `site-url` 하위경로 설정, 한국어 검색 한계, CI 로컬 LLM 접근 불가 문서화)

### Phase Ordering Rationale

- 인프라(Phase 1)가 먼저인 이유: `{{#include}}` + 해시 캡처 패턴을 나중에 도입하면 이미 쓴 챕터를 전부 리팩터링해야 한다(ARCHITECTURE.md Anti-Pattern 1과 직결).
- Tool calling → RAG → LangGraph → Capstone 순서는 FEATURES.md의 Feature Dependencies 그래프를 그대로 반영한다: 샌드박스 가드가 파일/shell 도구보다 먼저, LangGraph가 Capstone보다 먼저, LangSmith가 LangGraph 이후.
- LangGraph와 LangSmith를 한 페이즈로 묶은 것은 quick depth(3-5 phases) 제약 때문 — 두 주제 모두 캡스톤의 "직접 전제"이자 상대적으로 코드량이 적어 병합해도 페이즈가 비대해지지 않는다.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (Capstone):** 샌드박스 보안 하드닝(symlink 실경로 검증, 셸 명령 블록리스트, 도구 출력 길이 상한, `recursion_limit` 조합)은 ARCHITECTURE.md/PITFALLS.md가 설계 방향은 제시했으나(MEDIUM confidence — "이 프로젝트를 위해 종합한 설계 제안") 구체적 구현·자체 침투 테스트 시나리오는 계획 단계에서 검증 필요.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Book Infra + Basics):** mdBook include/앵커 문법, GitHub Actions Pages 배포, `ChatOpenAI`/LCEL 사용법 모두 공식 문서 + 라이브 검증으로 HIGH confidence 확보.
- **Phase 2 (Tool Calling):** `@tool`/`bind_tools`/`create_agent` API 표면이 공식 문서와 라이브 테스트로 이미 확정됨.
- **Phase 3 (RAG):** 벡터스토어·임베딩 조합(`Chroma` + `bge-m3`)이 end-to-end 라이브 검증 완료.
- **Phase 4 (LangGraph + LangSmith):** `StateGraph`/체크포인터/트레이싱 환경변수 모두 공식 문서로 확인됨.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | PyPI 메타데이터 + 이 프로젝트의 실제 엔드포인트/하드웨어에 대한 라이브 설치·실행 검증(uv --python 3.14 임시 프로젝트) |
| Features | MEDIUM-HIGH | 공식 문서 + 한국어 튜토리얼 2종(WikiDocs, TeddyNote) 목차 비교로 확인. 다만 `flashnext` 모델의 tool-calling/구조화 출력 세부 신뢰도는 챕터 작성 시점 재확인 필요 항목으로 명시됨 |
| Architecture | HIGH(핵심 패턴) / MEDIUM(해시 검증 스크립트 설계) | mdBook include·GitHub Actions·`create_agent`/`StateGraph` 패턴은 공식 문서 검증. 드리프트 방지용 해시 체크 스크립트는 이 프로젝트를 위해 종합한 제안으로 구현 세부는 재검토 필요 |
| Pitfalls | MEDIUM-HIGH | LangChain API 격변·mdBook 이슈는 공식 문서/GitHub 이슈로 교차 검증. 로컬 서버 특유 quirk(구조화 출력 500 에러, 콜드 스타트, 스트리밍 tool_calls 형식)는 이 세션에서 직접 재현해 HIGH로 보강됨 |

**Overall confidence:** HIGH

### Gaps to Address

- **리즈닝 필드 누출:** 현재 사용 중인 `flashnext` 별칭에서는 `reasoning` 필드가 `null`로 비어 있어 누출이 없음을 확인했으나, 리즈닝 강화 별칭(`flashnext-reach-xhigh` 등)으로 바꾸면 다를 수 있음 — Tool calling/LangGraph 챕터 작성 시 실제 사용하는 별칭으로 재확인 필요.
- **샌드박스 보안 자체 검증:** symlink 탈출·`../` 경로 조작 시나리오를 실제로 공격해보는 회귀 테스트는 아직 설계만 있고 구현되지 않음 — Capstone 페이즈 계획 시 구체화 필요.
- **mdBook 한국어(CJK) 검색 품질:** 알려진 미해결 이슈(lunr.js 공백 기준 토크나이징)로 완벽한 해결책이 없음 — 배포 단계에서 "베스트에포트"로 문서화하고 목차 내비게이션으로 보완하는 것으로 범위를 낮춤.
- **해시 기반 드리프트 감지 스크립트(`check_fresh.py`)의 구체 구현:** 설계 방향은 명확하나 특정 오픈소스에서 그대로 가져온 패턴이 아니므로, Phase 1 계획 시 실제 스크립트 설계를 한 번 더 검토.

## Sources

### Primary (HIGH confidence)
- 이 세션의 라이브 코드 실행 검증 (2026-09-11): `uv --python 3.14` 환경에 `langchain 1.4.0`/`langgraph 1.2.11`/`langchain-openai 1.6.2`/`chromadb`/`sentence-transformers`/`langchain-chroma`/`langchain-huggingface`/`torch 2.14.0` 설치, `ChatOpenAI(base_url="http://127.0.0.1:4000/v1", model="flashnext")`로 invoke/bind_tools/stream/`with_structured_output`(3 method) 테스트, `HuggingFaceEmbeddings(BAAI/bge-m3, device=mps)` + `Chroma` end-to-end 테스트
- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) — `create_agent` 표준화, `langchain-classic` 격리 대상
- [Agents - Docs by LangChain](https://docs.langchain.com/oss/python/langchain/agents) — `create_agent` 시그니처·체크포인터·스트리밍
- [mdBook-specific features (include, anchors)](https://rust-lang.github.io/mdBook/format/mdbook.html), [GitHub Actions starter workflow: pages/mdbook.yml](https://github.com/actions/starter-workflows/blob/main/pages/mdbook.yml)
- [LangGraph Persistence 공식 문서](https://docs.langchain.com/oss/python/langgraph/persistence), [LangSmith Observability Quickstart](https://docs.langchain.com/langsmith/observability-quickstart)
- PyPI JSON API 직접 조회 — 각 패키지 최신 버전·`requires_python`·macOS arm64 휠 태그 확인

### Secondary (MEDIUM confidence)
- [WikiDocs `<랭체인 노트>`](https://wikidocs.net/book/14314), [teddylee777/langchain-kr](https://github.com/teddylee777/langchain-kr) — 한국어 튜토리얼 목차 비교
- [LangGraph Academy 커리큘럼](https://www.educative.io/courses/langgraph-from-langchain-user-to-agent-builder/introduction-to-the-course) — 체인→그래프→캡스톤 전개 순서 정합성 확인
- [LangChain/LangGraph 경로 탈출 취약점 (CVE-2026-34070 등, CSO Online/CSA Research Note/The Hacker News)](https://www.csoonline.com/article/4151814/langchain-path-traversal-bug-adds-to-input-validation-woes-in-ai-pipelines.html) — 샌드박스 가드 필수 근거
- WebSearch: "best open source multilingual embedding model Korean retrieval 2026" — 최종 선택(`bge-m3`)은 라이브 검증으로 HIGH까지 보강

### Tertiary (LOW confidence)
- 골든 파일/해시 기반 드리프트 감지 스크립트 설계 — 이 프로젝트를 위해 종합한 제안, 특정 오픈소스 그대로 채택 아님(계획 단계 재검토 필요)
- 리즈닝 필드(`reasoning_content`) 처리 — 현재 별칭에서는 미누출 확인했으나 다른 별칭에서는 미검증

---
*Research completed: 2026-09-11*
*Ready for roadmap: yes*
