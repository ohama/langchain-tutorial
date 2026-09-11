---
phase: 02-tool-calling
plan: 01
subsystem: docs
tags: [langchain-core, tool-calling, bind_tools, tool-message, langchain-openai]

# Dependency graph
requires:
  - phase: 01-book-infra-basics (plan 01-01)
    provides: "examples/shared/config.py chat-model factory, scripts/run_examples.py capture runner, scripts/check_leaks.py leak scanner"
  - phase: 01-book-infra-basics (plan 01-04)
    provides: "Proven whole-phase release gate (format x5, 3 leak scans, git hygiene, push, Actions, live verification), full basics part (chapters 1-5)"
provides:
  - "examples/shared/tools.py: pure deterministic @tool definitions (add, multiply, lookup_stock, ALL_TOOLS) reused by future LangGraph chapters"
  - "Chapter 2-1 (도구 정의와 bind_tools): @tool schemas, bind_tools, real AIMessage.tool_calls for single/multi/no-tool questions"
  - "Chapter 2-2 (수동 도구 실행 루프): hand-written model -> tool_call -> ToolMessage -> re-invoke loop with MAX_ITERS guard, unknown-tool and exception handling, reaching a real final answer"
  - "LangGraph baseline: exact loop question, step sequence and final answer recorded below for Phase 4 to reproduce"
affects: [phase-4-langgraph, capstone]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shared deterministic tool module (examples/shared/tools.py) with named ANCHOR regions, same role as shared/config.py, reused across chapters and future phases"
    - "Manual tool-call loop: messages list grows via HumanMessage -> AIMessage -> ToolMessage* -> ... -> AIMessage(no tool_calls); tool.invoke(full tool_call dict) produces ToolMessage directly; exceptions caught at the loop layer, not inside tools"

key-files:
  created:
    - examples/shared/tools.py
    - examples/ch02_tools/01_define_tools.py
    - examples/ch02_tools/02_tool_loop.py
    - outputs/ch02_tools/01_define_tools.out
    - outputs/ch02_tools/02_tool_loop.out
    - book/src/ch02_tools/01_define_tools.md
    - book/src/ch02_tools/02_tool_loop.md
  modified:
    - book/src/SUMMARY.md
    - book/src/introduction.md
    - book/src/ch01_basics/05_structured_output.md

key-decisions:
  - "lookup_stock raises ValueError (not a friendly string) for unknown items, so chapter 2-2's loop-layer try/except has something real to catch"
  - "Reworded 01_define_tools.py's docstring/section-1 header to avoid the literal substring '@tool' so this plan's own invariant grep (@tool matches only shared/tools.py) holds without weakening the check"

# Metrics
duration: ~25min
completed: 2026-09-11
---

# Phase 2 Plan 01: Tool Definition and Manual Tool-Call Loop Summary

**Two tool-calling chapters (`@tool`/`bind_tools`/`tool_calls` inspection, then a hand-written model -> ToolMessage -> re-invoke loop reaching a real final answer of 60) built on a new shared deterministic tools module, published live with a fully reproducible byte-identical rerun.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-09-11T07:44:00Z (approx, context load)
- **Completed:** 2026-09-11T07:52:46Z
- **Tasks:** 3/3
- **Files modified:** 10 (3 examples created, 2 outputs created, 2 chapters created, 3 existing files modified: SUMMARY.md, introduction.md, ch01_basics/05_structured_output.md)

## Accomplishments

- `examples/shared/tools.py` defines three pure, deterministic `@tool` functions (`add`, `multiply`, `lookup_stock` over a fixed Korean-keyed inventory dict) with four named ANCHOR regions (`add`, `multiply`, `lookup_stock`, `all_tools`), no network/clock/randomness.
- Chapter 2-1 captures real tool schemas (auto-generated JSON Schema from type hints) and real `AIMessage.tool_calls` from `bind_tools` for a single-tool question (`add`), a two-tool parallel question (`lookup_stock` x2), and a question needing no tool at all (model returned `tool_calls: 0개`, `finish_reason: stop`).
- Chapter 2-2 implements the full manual loop (`run_tool_call`, `run_loop` with `MAX_ITERS=5`) and captures it reaching a genuine final answer via two tool-execution steps, plus a full-dict-vs-args-only `invoke` contrast and two deterministic + one live error-handling scenario (unknown tool name, and a real `ValueError` from `lookup_stock` recovered from ToolMessage feedback).
- Both `.out` captures contain zero occurrences of the real API key and no raw `tool_call` ids (only `bool(...)` existence checks or `==` comparisons), verified by grep before and after every capture.
- Whole-phase gate passed clean on the first attempt (after one inline fix, see Deviations): fresh `mdbook build` (0 ERROR/WARN), `check_book.py --html` 7x PASS, three `check_leaks.py` invocations all CLEAN (full scan, tracked-files secrets-only, full git-history secrets-only), git hygiene clean, `ChatOpenAI(`/`@tool` invariants each matching exactly one file, and a **byte-identical** reproducibility rerun (not just text-only — the scratch rerun's `.out` files diffed to zero lines against the committed ones, since only the model's own captured text and no volatile fields are printed).
- Pushed to `main` (`9d7be55`), confirmed the triggered Actions run's `headSha` matched local `HEAD` before watching, and the run (`34576379480`) completed with `conclusion: success` in ~17s (build 9s + deploy 8s).
- Live-verified all 7 chapter pages (5 basics + 2 tool-calling) at `https://ohama.github.io/langchain-tutorial/`: each page's `html.unescape`d HTML contains a distinctive line from its own `.out` and neither `{{#include` nor the stub marker; `toc.html` contains `2부 도구 호출`, `1부 기초`, `부록`; `introduction.html` and `ch01_basics/05_structured_output.html` both link to `ch02_tools/01_define_tools.html`; a nonexistent path returns HTTP 404.

## Task Commits

Each task was committed atomically:

1. **Task 1: Shared tools module + chapter 2-1** - `ff24cd2` (feat)
2. **Task 2: Chapter 2-2 + next-part pointers** - `9d7be55` (feat) — includes the inline `01_define_tools.py` wording fix and its re-capture
3. **Task 3: Whole-phase gate (reproducibility, format, leaks, hygiene, push, Actions, live verification)** - no additional commit; every check passed against the state left by tasks 1-2, `git status --porcelain` was empty throughout

**Plan metadata commit:** this SUMMARY.md, committed and pushed alongside plan completion (STATE.md/ROADMAP.md remain the orchestrator's responsibility)

## Files Created/Modified

- `examples/shared/tools.py` — `add`, `multiply`, `lookup_stock` (`@tool`), `ALL_TOOLS`; pure/deterministic, 4 named ANCHOR regions
- `examples/ch02_tools/01_define_tools.py` — tool schema inspection + `bind_tools` + `tool_calls` for single/multi/no-tool questions
- `examples/ch02_tools/02_tool_loop.py` — `run_tool_call`/`run_loop` manual loop, `MAX_ITERS=5`, full-dict-vs-args-only contrast, unknown-tool and exception handling
- `outputs/ch02_tools/01_define_tools.out`, `outputs/ch02_tools/02_tool_loop.out` — real captures via `scripts/run_examples.py`, each starting with `# source-sha256:`
- `book/src/ch02_tools/01_define_tools.md`, `book/src/ch02_tools/02_tool_loop.md` — new chapters, exact 4-heading template, include-only code blocks
- `book/src/SUMMARY.md` — new `# 2부 도구 호출` section with both chapter links, inserted before `# 부록`
- `book/src/introduction.md` — `도구 호출` now links to chapter 2-1
- `book/src/ch01_basics/05_structured_output.md` — new closing bullet pointing to 2부 도구 호출

## Decisions Made

- `lookup_stock` raises `ValueError` (not a soft "not found" string) for unknown items so chapter 2-2 has a real exception for the loop's `try/except` to demonstrate, matching the plan's explicit "error-to-ToolMessage" requirement.
- Reworded `01_define_tools.py`'s module docstring and section-1 print header (`@tool로 도구를 정의하고...` -> `tool 데코레이터로 정의한 도구를...`, `=== 1. @tool이 만든 도구 ===` -> `=== 1. tool 데코레이터가 만든 도구 ===`) so the plan's own invariant (`git grep -n "@tool" -- examples` matches only `examples/shared/tools.py`) holds without weakening the check itself. Re-captured `outputs/ch02_tools/01_define_tools.out`; only the section-1 header text changed, every other line (schemas, tool_calls, finish_reason) was identical.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `01_define_tools.py` contained the literal string "@tool" outside `shared/tools.py`, breaking this plan's own invariant check**

- **Found during:** Task 2, running Task 2's own `<verify>` step (`git grep -n "@tool" -- examples ':!examples/.venv'` must match only `examples/shared/tools.py`)
- **Issue:** The module docstring and the section-1 print header in `examples/ch02_tools/01_define_tools.py` both contained the literal substring `@tool` (as prose, not a decorator use), which the invariant grep can't distinguish from an actual decorator
- **Fix:** Reworded both strings to describe the same concept ("tool 데코레이터") without the `@tool` substring; no behavior change
- **Files modified:** `examples/ch02_tools/01_define_tools.py`, re-captured `outputs/ch02_tools/01_define_tools.out`
- **Verification:** `git grep -n "@tool" -- examples ':!examples/.venv'` now matches only the three decorator lines in `examples/shared/tools.py`; re-capture diffed identical except the one header line; `check_book.py` still PASS
- **Committed in:** `9d7be55` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug, caught by this plan's own verification step before it could reach Task 3's gate)
**Impact on plan:** Text-only fix inside an example file's prose; no change to tool definitions, loop logic, or captured tool-call/loop behavior. No scope creep.

## Issues Encountered

None beyond the deviation above. Both example captures were meaningful and matched all plan expectations on the first `run_examples.py` run (section 2's loop reached the expected final answer of 60 on the first try; no rule-8 prompt adjustments were needed). The reproducibility rerun (Task 3, step 1) produced byte-identical `.out` files against the committed ones — no divergence to investigate, so the plan checker's structural-vs-wording clarification did not need to be applied.

## User Setup Required

None — reused the same `examples/.env` (git-ignored) and shell `LITELLM_API_KEY`; no new external service configuration was introduced.

## LangGraph Baseline (for Phase 4)

Recorded from `outputs/ch02_tools/02_tool_loop.out`, section 2, no secret values or absolute paths:

- **Loop question (exact):** `사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘.`
- **Model calls:** 3
  - Step 1: `tool_calls` = 2 (parallel) — `lookup_stock(item="사과")` -> `사과 재고: 12개`, `lookup_stock(item="바나나")` -> `바나나 재고: 5개`
  - Step 2: `tool_calls` = 1 — `multiply(a=12, b=5)` -> `60`
  - Step 3: no `tool_calls` — final answer
- **Final answer (exact):** `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.`
- **Message flow:** `HumanMessage -> AIMessage -> ToolMessage -> ToolMessage -> AIMessage -> ToolMessage -> AIMessage`
- **`content` on tool-call turns:** empty in this capture (steps 1-2 had no explanatory text; only the final step had content) — for contrast, chapter 2-1's tool-call turns (section 2-1) did have non-empty `content` alongside the tool call, confirming this varies by prompt/turn as research predicted, not a fixed rule.
- **Behavior after the 수박 (watermelon) error:** the model called `lookup_stock(item="수박")`, received the loop's error `ToolMessage` (`도구 실행 오류: ValueError: 재고 목록에 없는 품목: 수박`), did not retry, and answered in step 2 with `수박은 현재 창고 재고 목록에 없는 품목입니다. 다른 품목의 재고를 확인하시거나, 재고 목록에 수박을 추가하는 작업이 필요하시면 알려주세요.` — no crash, no further tool calls.

## Reproducibility Result

Byte-identical: `diff outputs/ch02_tools/01_define_tools.out <scratch-rerun>` and `diff outputs/ch02_tools/02_tool_loop.out <scratch-rerun>` both produced zero output (exit 0). No id/timing/path fields are printed by either example, so nothing needed to differ between runs; this went beyond "text-only" — model text, tool results, and structure all matched exactly. No rule-8 prompt adjustments were needed at any point in this plan.

## Release Gate Results (for traceability)

- Fresh `mdbook build book`: exit 0, 0 ERROR/WARN lines
- `scripts/check_book.py --html book/book`: `PASS` for all 7 chapters (5 `ch01_basics` + 2 `ch02_tools`), exit 0
- `scripts/check_leaks.py outputs book/src examples book/book`: `CLEAN`
- `git ls-files -z | xargs -0 scripts/check_leaks.py --secrets-only`: `CLEAN`
- `git log -p --all | scripts/check_leaks.py --secrets-only -`: `CLEAN`
- Git hygiene: no `.env`/`.venv/`/`.claude/`/`book/book/`/`__pycache__`/`.pytest_cache` tracked; no stray `.venv`/`.pytest_cache`/`main.py`; `git status --porcelain` empty; `git ls-files outputs | wc -l` = 7; both `ch02_tools/*.out` first lines match `shasum -a 256` of their source `.py`
- Invariants: `git grep -n "ChatOpenAI(" -- examples` matches only `examples/shared/config.py`; `git grep -n "@tool" -- examples ':!examples/.venv'` matches only `examples/shared/tools.py` (after the Task 2 deviation fix)
- Push: `main` updated `ae1734d..9d7be55` (via `ff24cd2` then `9d7be55`)
- Actions run: `34576379480` (workflow `deploy.yml`, branch `main`); `headSha` confirmed equal to local `HEAD` (`9d7be55ac449622a732e2b338f4c51626c2ce2a6`) before watching; `gh run watch --exit-status` completed successfully (build 9s + deploy 8s); `gh run view --json conclusion,headSha` confirmed `{"conclusion":"success","headSha":"9d7be55ac449622a732e2b338f4c51626c2ce2a6"}`
- Live verification: all 7 pages returned `LIVE_OK` (distinctive line from each `.out` found in the `html.unescape`d page, neither `{{#include` nor the stub marker present); `toc.html` contains `2부 도구 호출`, `1부 기초`, `부록`; `introduction.html` and `ch01_basics/05_structured_output.html` both link to `ch02_tools/01_define_tools.html`; a nonexistent path returned HTTP 404

## Next Phase Readiness

- `examples/shared/tools.py` is a stable, pure, deterministic tool interface (`add`, `multiply`, `lookup_stock`, `ALL_TOOLS`) ready for Phase 4 (LangGraph) to import directly or reuse as a pattern.
- The LangGraph baseline above (exact question, 3-step trace, final answer `60`) is the reference Phase 4 must reproduce when rebuilding this loop as a graph.
- No blockers for Phase 3 (RAG) or Phase 4 (LangGraph). The authoring pipeline and whole-phase release gate are proven for a third time (01-03, 01-04, and this plan) with only one small text-only self-inflicted invariant fix, caught by the plan's own verification step before ever reaching the final gate.

---
*Phase: 02-tool-calling*
*Completed: 2026-09-11*
