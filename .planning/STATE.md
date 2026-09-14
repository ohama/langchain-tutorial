# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** 책을 순서대로 따라가면, 실제로 돌아가는 코드와 실제 출력으로 LangChain/LangGraph를 이해하고 마지막에 스스로 코딩 에이전트를 구현할 수 있어야 한다.
**Current focus:** Phase 5 - Capstone + Appendix

## Current Position

Phase: 5 of 5 (Capstone + Appendix)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-09-14 — Phase 4 (LangGraph + LangSmith) 완료·검증 통과 (5/5), 4부 챕터 4개 라이브 배포

Progress: [████████░░] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 11
- Average duration: ~10 min
- Total execution time: ~1.9 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Book Infra + Basics | 4 | ~27 min | ~7 min |
| 2. Tool Calling | 1 | ~8 min | ~8 min |
| 3. RAG | 2 | ~21 min | ~11 min |
| 4. LangGraph + LangSmith | 4 | ~55 min | ~14 min |

**Recent Trend:**
- Last 5 plans: 03-01 (~12m), 03-02 (~9m), 04-01 (~7m), 04-02 (~23m, 중간에 한 번 멈춰 재개), 04-03 (~7m), 04-04 (~11m + 승인 후 마무리 2m)
- Trend: 페이즈가 커질수록 플랜당 시간 증가. 04-02는 에이전트가 "다른 작업 대기"로 오인해 멈춘 사례 — 실행 프롬프트에 "너가 직접 끝까지 실행하고, 막히면 기다리지 말고 보고" 문구를 넣을 것

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Phase 1: `.env` 변수는 공급자 중립 이름 `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY`. `.env`는 `examples/`에 있고 셸 변수 참조만 담음 (키 값은 디스크에 없음)
- Phase 1: `examples/`는 hatchling 설치형 uv 패키지. 예제는 `shared.config`의 팩토리만 사용, `ChatOpenAI(`는 `shared/config.py`에만 존재
- Phase 1: `.out` 1행은 `# source-sha256:` 헤더(예제 `.py`만 해시) → 챕터는 `{{#include ...out:2:}}`. `shared/*.py`는 이름 있는 ANCHOR로, 설정 파일 일부는 줄 범위(`:N:`)로 include
- Phase 1: 챕터 헤딩 고정 순서 `개념: 왜 필요한가` / `최소 코드` / `실제 출력` / `요점 정리` — `check_book.py`가 강제 (새 `ch*` 디렉토리는 SUMMARY.md 링크만 추가하면 자동 인식)
- Phase 1: 공개 저장소 https://github.com/ohama/langchain-tutorial , 사이트 https://ohama.github.io/langchain-tutorial/
- Phase 2: 도구는 `examples/shared/tools.py`에 한 번만 정의 (`add`/`multiply`/`lookup_stock`, `ALL_TOOLS`; 재고 사과 12/바나나 5/포도 0, 없는 품목은 `ValueError`). `@tool`은 이 파일에만 존재
- Phase 2: 수동 루프는 `tool.invoke(tool_call)`에 전체 dict → `ToolMessage`. 예외·알 수 없는 도구는 `ToolMessage` 오류화, `MAX_ITERS` for/else 가드, tool_call id 비출력
- Phase 3: 임베딩은 `shared/config.py`의 `get_embeddings()` 한 곳 (`BAAI/bge-m3`, 지연 import, import 전에 노이즈 억제 env 설정, MPS→CPU 폴백, 1024차원). Chroma는 휘발성, 문서 `source`는 저장소 상대경로
- Phase 3: 분할 `chunk_size=300, chunk_overlap=50` → 17청크. 임베딩 소수 6자리·점수 4자리로 출력하면 재실행 바이트 동일
- **Phase 4: 그래프 재구성이 2부 최종 답을 그대로 재현함** — `build_graph()`(`StateGraph` + `ToolNode(ALL_TOOLS, handle_tool_errors=True)` + `tools_condition`)가 2부와 동일한 도구 호출·메시지 흐름·최종 답 `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.`를 냄. 캡스톤 에이전트도 이 구조를 재사용
- **Phase 4: `ToolNode`는 `handle_tool_errors=True`가 필수** — 기본값은 호출 형태 오류만 `ToolMessage`로 바꾸고, 도구 본문에서 난 예외는 그래프를 죽임
- Phase 4: 체크포인터는 `InMemorySaver` + `thread_id`(스레드별 격리 확인), 영속은 `SqliteSaver`. db 파일은 gitignore(`*.db`, `-wal`, `-shm`)하고 캡처는 깨끗한 db에서 시작
- Phase 4: 무한 루프 예제는 LLM 없이 순수 파이썬 2노드 순환 → `GraphRecursionError` 결정적 재현
- Phase 4: mermaid는 `mdbook-mermaid` 0.17.0으로 실제 렌더링. 자산 `book/mermaid.min.js`(sha256 eefea253…)·`book/mermaid-init.js`(ccf746f1…)를 커밋하고 해시 고정. `check_book.py`는 ```mermaid 블록도 include-only로 검사
- Phase 4: 누출 스캔은 경로 한정 예외 2개가 필요 — `book/mermaid.min.js`(벤더 번들), `scripts/test_masking.py`(의도된 가짜 값). 절대 넓히지 말 것. 히스토리 스캔도 번들 경로만 pathspec 제외
- Phase 4: LangSmith는 클라우드 전송 없이 처리 (사용자 결정). 토글은 env만 보는 `tracing_is_enabled()`(기본 꺼짐, `get_env_var`가 lru_cache라 `cache_clear()` 필요), 호출 트리·토큰·tool call은 `stream_mode="debug"` 로컬 캡처로 보여주고 UI 대응은 설명으로만. 스크린샷·트레이스 링크가 있다고 주장하지 않음

**환경 주의:** 셸 환경변수 `LITELLM_API_KEY` 값이 5글자라, 큰 텍스트(예: 2.6MB mermaid 번들)에서 우연히 73회 겹침 → 누출 검사 오경보와 과잉 마스킹의 원인. 실제 유출은 없음(번들 외 히스토리 일치 0건). 사용자에게 더 긴 무작위 키로 교체를 권고함

**Authoring commands (재사용):**
- 캡처: `uv run --project examples python scripts/run_examples.py [TARGET ...] [--outputs-dir DIR] [--timeout SEC] [--no-warmup]`
- 형식 게이트: `uv run --project examples python scripts/check_book.py [MD ...] [--html book/book]`
- 누출 스캔: `uv run --project examples python scripts/check_leaks.py <paths...> --exclude 'book/mermaid.min.js' --exclude 'scripts/test_masking.py'`
- 테스트: `uv run --project examples pytest -p no:cacheprovider -q scripts/test_masking.py scripts/test_check_leaks.py` (18개)
- 이 셸의 `grep`은 ugrep 래퍼 → `/usr/bin/grep` 또는 `git grep` 사용
- `mdbook build book`은 mermaid 프리프로세서의 양성 경고 1줄이 정상

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet. (howto 주제 6개는 `documentation/howto/TODO.md`에 대기)

### Blockers/Concerns

- **Phase 5 (다음): 샌드박스 보안 하드닝**이 가장 큰 미해결 항목 — `Path.resolve()` 기반 검증으로 `../`와 symlink 탈출을 모두 막고, 셸 도구에는 타임아웃·출력 크기 제한을 걸어야 함. 침투 테스트 시나리오(경로 탈출 시도 목록)를 계획 단계에서 먼저 설계할 것. AGENT-01(가드)이 AGENT-02/03(파일·셸 도구)보다 먼저 구현·검증되어야 함
- Phase 5: 에이전트가 파일을 쓰고 셸을 실행하는 예제라, 캡처가 저장소를 오염시키지 않도록 샌드박스 디렉토리를 gitignore하고 매 실행 전 초기화할 것. 캡처에 절대경로·pid·타임스탬프가 섞이기 쉬움
- `.planning/`은 공개 저장소에 계속 커밋함 (사용자 결정: "민감 정보만 정리"). 문서 작성 시 절대경로·이메일·하드웨어 사양·백엔드 포트는 `~`, `<repo>`, `<scratchpad>`, "Apple Silicon" 등으로 적을 것
- `book/src/appendix/about.md` 부록 목록은 "(준비 중)" — Phase 5에서 채움 (APPX-01~03)

## Session Continuity

Last session: 2026-09-14
Stopped at: Phase 4 완료 (검증 passed), Phase 5 계획 대기
Resume file: None
