# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** 책을 순서대로 따라가면, 실제로 돌아가는 코드와 실제 출력으로 LangChain/LangGraph를 이해하고 마지막에 스스로 코딩 에이전트를 구현할 수 있어야 한다.
**Current focus:** Phase 2 - Tool Calling

## Current Position

Phase: 2 of 5 (Tool Calling)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-09-11 — Phase 1 (Book Infra + Basics) 완료·검증 통과 (5/5), 기초 챕터 5개 라이브 배포

Progress: [██░░░░░░░░] 20%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: ~7 min
- Total execution time: ~0.45 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Book Infra + Basics | 4 | ~27 min | ~7 min |

**Recent Trend:**
- Last 5 plans: 01-01 (~9m), 01-02 (~5m), 01-03 (~7m), 01-04 (~6m)
- Trend: stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Book Infra + Basics를 Phase 1로 묶어 저작 파이프라인을 가장 먼저 끝까지 증명 — 완료
- Roadmap: Tool Calling → RAG → LangGraph+LangSmith → Capstone+Appendix 순서로 5개 페이즈 확정
- Phase 1: `.env` 변수는 공급자 중립 이름 `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY`. `.env`는 `examples/`에 있고 `LLM_API_KEY=${LITELLM_API_KEY}` 참조만 담음 (키 값은 디스크에 없음)
- Phase 1: `examples/`는 hatchling 설치형 uv 패키지 (plain `uv init`은 `shared` import 실패). 예제는 `from shared.config import get_chat_model`만 사용, `ChatOpenAI(`는 `shared/config.py`에만 존재
- Phase 1: 구조화 출력은 `get_structured_model` → `with_structured_output(..., method="function_calling", strict=False)`
- Phase 1: `.out` 파일 1행은 `# source-sha256:` 헤더 → 챕터는 `{{#include ...out:2:}}`로 포함. `config.py`는 이름 있는 ANCHOR로만 포함
- Phase 1: 챕터 헤딩 고정 순서 `개념: 왜 필요한가` / `최소 코드` / `실제 출력` / `요점 정리` — `scripts/check_book.py`가 강제
- Phase 1: 배포는 공식 `configure-pages`/`upload-pages-artifact`/`deploy-pages` + mdBook 0.5.3 고정 (사용자 `/pages` 스킬의 peaceiris 방식과 의도적으로 다름). mdBook은 include 누락에도 exit 0이므로 CI가 `ERROR` 로그로 실패 처리
- Phase 1: 공개 저장소 https://github.com/ohama/langchain-tutorial , 사이트 https://ohama.github.io/langchain-tutorial/

**Authoring commands (재사용):**
- 캡처: `uv run --project examples python scripts/run_examples.py [TARGET ...] [--outputs-dir DIR] [--timeout SEC] [--no-warmup]`
- 형식 게이트: `uv run --project examples python scripts/check_book.py [MD ...] [--html book/book]`
- 누출 스캔: `uv run --project examples python scripts/check_leaks.py <paths...>` / 히스토리: `git log -p --all | uv run --project examples python scripts/check_leaks.py --secrets-only -`
- 마스킹 테스트: `uv run --project examples pytest -p no:cacheprovider -q scripts/test_masking.py`
- 이 셸의 `grep`은 ugrep 래퍼 → `/usr/bin/grep` 또는 `git grep` 사용
- mdBook 0.5.3 사이드바 목차는 `book/book/toc.html`(iframe)에 렌더링됨

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

- Phase 5: 샌드박스 보안 하드닝(symlink 실경로 검증, 셸 명령 안전장치)은 설계 방향만 있고 구체 구현·침투 테스트 시나리오가 없음 — plan-phase 5에서 반드시 구체화할 것
- `.planning/`은 공개 저장소에 계속 커밋함 (사용자 결정: "민감 정보만 정리"). 이메일·홈 절대경로·스크래치 경로·하드웨어 사양·백엔드 포트를 일반 표현으로 치환 완료. 이후 문서 작성 시에도 이런 값은 `~`, `<repo>`, `<scratchpad>`, "Apple Silicon" 등으로 적을 것. 과거 git 히스토리에는 원래 값이 남아 있음 (히스토리 재작성은 하지 않음)
- `book/src/appendix/about.md` 부록 목록은 "(준비 중)" — Phase 5에서 채움

## Session Continuity

Last session: 2026-09-11
Stopped at: Phase 1 완료 (검증 passed), Phase 2 계획 대기
Resume file: None
