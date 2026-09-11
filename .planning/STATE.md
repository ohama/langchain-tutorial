# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** 책을 순서대로 따라가면, 실제로 돌아가는 코드와 실제 출력으로 LangChain/LangGraph를 이해하고 마지막에 스스로 코딩 에이전트를 구현할 수 있어야 한다.
**Current focus:** Phase 3 - RAG

## Current Position

Phase: 3 of 5 (RAG)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-09-11 — Phase 2 (Tool Calling) 완료·검증 통과 (6/6), 2부 도구 호출 챕터 2개 라이브 배포

Progress: [████░░░░░░] 40%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: ~7 min
- Total execution time: ~0.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Book Infra + Basics | 4 | ~27 min | ~7 min |
| 2. Tool Calling | 1 | ~8 min | ~8 min |

**Recent Trend:**
- Last 5 plans: 01-01 (~9m), 01-02 (~5m), 01-03 (~7m), 01-04 (~6m), 02-01 (~8m)
- Trend: stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Tool Calling → RAG → LangGraph+LangSmith → Capstone+Appendix 순서로 5개 페이즈 확정
- Phase 1: `.env` 변수는 공급자 중립 이름 `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY`. `.env`는 `examples/`에 있고 `LLM_API_KEY=${LITELLM_API_KEY}` 참조만 담음 (키 값은 디스크에 없음)
- Phase 1: `examples/`는 hatchling 설치형 uv 패키지. 예제는 `from shared.config import get_chat_model`만 사용, `ChatOpenAI(`는 `shared/config.py`에만 존재
- Phase 1: 구조화 출력은 `get_structured_model` → `with_structured_output(..., method="function_calling", strict=False)`
- Phase 1: `.out` 파일 1행은 `# source-sha256:` 헤더 → 챕터는 `{{#include ...out:2:}}`로 포함. `shared/*.py`는 이름 있는 ANCHOR로만 포함. 해시 헤더는 예제 파일만 덮으므로 `shared/` 모듈을 바꾸면 그 모듈을 쓰는 챕터 출력을 모두 재캡처할 것
- Phase 1: 챕터 헤딩 고정 순서 `개념: 왜 필요한가` / `최소 코드` / `실제 출력` / `요점 정리` — `scripts/check_book.py`가 강제 (새 `ch*` 디렉토리는 SUMMARY.md 링크만 추가하면 자동 인식)
- Phase 1: 배포는 공식 Pages Actions + mdBook 0.5.3 고정. 공개 저장소 https://github.com/ohama/langchain-tutorial , 사이트 https://ohama.github.io/langchain-tutorial/
- Phase 2: 도구는 `examples/shared/tools.py`에 한 번만 정의 (`add`/`multiply`/`lookup_stock`, `ALL_TOOLS`; 순수·결정적, 재고 사과 12/바나나 5/포도 0, 없는 품목은 `ValueError`). `@tool`은 이 파일에만 존재
- Phase 2: 수동 루프는 `tool.invoke(tool_call)`에 전체 dict를 넘겨 `ToolMessage`를 받음 (args만 넘기면 원시 값 반환). 알 수 없는 도구·예외는 `ToolMessage` 오류 내용으로 반환, `MAX_ITERS=5` for/else 가드, tool_call id는 출력하지 않음 (재현성)
- Phase 2: temperature=0에서 `ch02_tools` 재캡처가 바이트 단위로 동일 — 결정성 게이트(스크래치 재실행 diff)를 이후 챕터에도 적용
- **Phase 4 기준선 (GRAPH-02가 재현해야 함):** 질문 `사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘.` → 모델 호출 3회: ① `lookup_stock` 2개 병렬 ② `multiply(a=12, b=5)` ③ 최종 답 `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.` / 메시지 흐름 `Human → AI → Tool → Tool → AI → Tool → AI`

**Authoring commands (재사용):**
- 캡처: `uv run --project examples python scripts/run_examples.py [TARGET ...] [--outputs-dir DIR] [--timeout SEC] [--no-warmup]`
- 형식 게이트: `uv run --project examples python scripts/check_book.py [MD ...] [--html book/book]`
- 누출 스캔: `uv run --project examples python scripts/check_leaks.py <paths...>` / 히스토리: `git log -p --all | uv run --project examples python scripts/check_leaks.py --secrets-only -`
- 마스킹 테스트: `uv run --project examples pytest -p no:cacheprovider -q scripts/test_masking.py`
- 이 셸의 `grep`은 ugrep 래퍼 → `/usr/bin/grep` 또는 `git grep` 사용
- mdBook 0.5.3 사이드바 목차는 `book/book/toc.html`(iframe)에 렌더링됨

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet. (howto 주제 5개는 `documentation/howto/TODO.md`에 대기)

### Blockers/Concerns

- Phase 3: 다국어 임베딩(`bge-m3`)은 LLM 서버와 같은 머신의 메모리를 나눠 씀 — RAG 계획 시 메모리 영향과 로드 시간(첫 로드 약 1분) 확인할 것
- Phase 5: 샌드박스 보안 하드닝(symlink 실경로 검증, 셸 명령 안전장치)은 설계 방향만 있고 구체 구현·침투 테스트 시나리오가 없음 — plan-phase 5에서 반드시 구체화할 것
- `.planning/`은 공개 저장소에 계속 커밋함 (사용자 결정: "민감 정보만 정리"). 문서 작성 시 절대경로·이메일·하드웨어 사양·백엔드 포트는 `~`, `<repo>`, `<scratchpad>`, "Apple Silicon" 등으로 적을 것. 과거 git 히스토리에는 원래 값이 남아 있음 (재작성 안 함)
- `book/src/appendix/about.md` 부록 목록은 "(준비 중)" — Phase 5에서 채움

## Session Continuity

Last session: 2026-09-11
Stopped at: Phase 2 완료 (검증 passed), Phase 3 계획 대기
Resume file: None
