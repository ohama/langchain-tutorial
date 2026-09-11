# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** 책을 순서대로 따라가면, 실제로 돌아가는 코드와 실제 출력으로 LangChain/LangGraph를 이해하고 마지막에 스스로 코딩 에이전트를 구현할 수 있어야 한다.
**Current focus:** Phase 4 - LangGraph + LangSmith

## Current Position

Phase: 4 of 5 (LangGraph + LangSmith)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-09-11 — Phase 3 (RAG) 완료. 검증에서 3-3장 산문 1문장 오류(gap) 발견 → 오케스트레이터가 수정·배포 후 10/10 통과

Progress: [██████░░░░] 60%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: ~9 min
- Total execution time: ~1.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Book Infra + Basics | 4 | ~27 min | ~7 min |
| 2. Tool Calling | 1 | ~8 min | ~8 min |
| 3. RAG | 2 | ~21 min | ~11 min |

**Recent Trend:**
- Last 5 plans: 01-04 (~6m), 02-01 (~8m), 03-01 (~12m), 03-02 (~9m)
- Trend: stable (RAG plans longer due to embedding model load + more chapters)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Phase 1: `.env` 변수는 공급자 중립 이름 `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY`. `.env`는 `examples/`에 있고 `LLM_API_KEY=${LITELLM_API_KEY}` 참조만 담음 (키 값은 디스크에 없음)
- Phase 1: `examples/`는 hatchling 설치형 uv 패키지. 예제는 `shared.config`의 팩토리만 사용, `ChatOpenAI(`는 `shared/config.py`에만 존재
- Phase 1: 구조화 출력은 `get_structured_model` → `with_structured_output(..., method="function_calling", strict=False)`
- Phase 1: `.out` 1행은 `# source-sha256:` 헤더(예제 `.py`만 해시) → 챕터는 `{{#include ...out:2:}}`. `shared/*.py`는 이름 있는 ANCHOR로, 설정 파일 일부는 줄 범위(`:N:`)로 include 가능
- Phase 1: 챕터 헤딩 고정 순서 `개념: 왜 필요한가` / `최소 코드` / `실제 출력` / `요점 정리` — `scripts/check_book.py`가 강제 (새 `ch*` 디렉토리는 SUMMARY.md 링크만 추가하면 자동 인식)
- Phase 1: 배포는 공식 Pages Actions + mdBook 0.5.3. 공개 저장소 https://github.com/ohama/langchain-tutorial , 사이트 https://ohama.github.io/langchain-tutorial/
- Phase 2: 도구는 `examples/shared/tools.py`에 한 번만 정의 (`add`/`multiply`/`lookup_stock`, `ALL_TOOLS`; 재고 사과 12/바나나 5/포도 0, 없는 품목은 `ValueError`). `@tool`은 이 파일에만 존재
- Phase 2: 수동 루프는 `tool.invoke(tool_call)`에 전체 dict → `ToolMessage`. 예외·알 수 없는 도구는 `ToolMessage` 오류화, `MAX_ITERS=5` for/else 가드, tool_call id 비출력
- **Phase 4 기준선 (GRAPH-02가 재현해야 함):** 질문 `사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘.` → 모델 호출 3회: ① `lookup_stock` 2개 병렬 ② `multiply(a=12, b=5)` ③ 최종 답 `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.` / 메시지 흐름 `Human → AI → Tool → Tool → AI → Tool → AI`
- Phase 3: 임베딩은 `shared/config.py`의 `get_embeddings()` 한 곳 (`BAAI/bge-m3`, 지연 import, import 전에 HF/tqdm 노이즈 억제 env 설정, `.env`의 `EMBEDDING_MODEL`/`EMBEDDING_DEVICE`, MPS→CPU 폴백, `normalize_embeddings=True`, 1024차원)
- Phase 3: Chroma는 휘발성(persist 디렉토리 없음, 텔레메트리 off), 예제마다 색인 재구축. 문서 `source` 메타데이터는 저장소 상대경로. 샘플 문서 `examples/data/ch03_rag/` 3개(가상 회사 규정 포함, 주차·식대·급여 내용 없음)
- Phase 3: 분할 `chunk_size=300, chunk_overlap=50, add_start_index=True` → 17청크. 임베딩은 소수 6자리, 점수는 4자리로 출력하면 재실행 바이트 동일
- Phase 3: HF "Loading weights" 진행 표시는 stderr로만 나오며 러너는 stdout만 캡처 → `.out` 오염 없음
- Phase 3 교훈: 검증기가 산문-캡처 불일치(검색된 청크 섹션 이름)를 잡음. 챕터 작성 시 출력에 `start_index` 같은 간접 식별자만 찍히면 산문에서 해석을 틀리기 쉬움 → 가능하면 예제 출력에 사람이 읽는 라벨(섹션명 등)을 함께 찍거나, 산문 작성 후 캡처와 한 번 더 대조할 것

**Authoring commands (재사용):**
- 캡처: `uv run --project examples python scripts/run_examples.py [TARGET ...] [--outputs-dir DIR] [--timeout SEC] [--no-warmup]`
- 형식 게이트: `uv run --project examples python scripts/check_book.py [MD ...] [--html book/book]`
- 누출 스캔: `uv run --project examples python scripts/check_leaks.py <paths...>` / 히스토리: `git log -p --all | uv run --project examples python scripts/check_leaks.py --secrets-only -`
- 마스킹 테스트: `uv run --project examples pytest -p no:cacheprovider -q scripts/test_masking.py`
- 이 셸의 `grep`은 ugrep 래퍼 → `/usr/bin/grep` 또는 `git grep` 사용
- mdBook 0.5.3 사이드바 목차는 `book/book/toc.html`(iframe)에 렌더링됨

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet. (howto 주제 6개는 `documentation/howto/TODO.md`에 대기)

### Blockers/Concerns

- Phase 4: LangSmith 트레이싱은 클라우드 전송 — 챕터에서만 `.env` 플래그로 켜고 기본값 꺼짐. LangSmith API 키가 필요하면 사용자 제공이 필요할 수 있음(키는 절대 커밋·출력 금지). 트레이스 화면/링크는 캡처 출력으로 재현 불가하므로 챕터 서술 방식(스크린샷 여부 등) 계획 시 결정할 것
- Phase 5: 샌드박스 보안 하드닝(symlink 실경로 검증, 셸 명령 안전장치)은 설계 방향만 있고 구체 구현·침투 테스트 시나리오가 없음 — plan-phase 5에서 반드시 구체화할 것
- `.planning/`은 공개 저장소에 계속 커밋함 (사용자 결정: "민감 정보만 정리"). 문서 작성 시 절대경로·이메일·하드웨어 사양·백엔드 포트는 `~`, `<repo>`, `<scratchpad>`, "Apple Silicon" 등으로 적을 것. 과거 git 히스토리에는 원래 값이 남아 있음 (재작성 안 함)
- `book/src/appendix/about.md` 부록 목록은 "(준비 중)" — Phase 5에서 채움

## Session Continuity

Last session: 2026-09-11
Stopped at: Phase 3 완료 (gap 수정 후 검증 통과), Phase 4 계획 대기
Resume file: None
