---
phase: 04-langgraph-langsmith
plan: 04
subsystem: docs
tags: [langgraph, langsmith, tracing, stream_mode-debug, usage_metadata, mdbook, mermaid, release-gate]

# Dependency graph
requires:
  - phase: 04-langgraph-langsmith (plan 02)
    provides: "build_graph() shape (MessagesState + ToolNode(handle_tool_errors=True) + tools_condition + tools->model loop-back) that this plan's graph copies verbatim"
  - phase: 04-langgraph-langsmith (plan 01)
    provides: "hash-pinned mermaid.min.js/mermaid-init.js vendored assets and the mdbook-mermaid CI step this plan's live check re-verifies"
provides:
  - "examples/ch04_langgraph/05_langsmith_trace.py: real captured proof that the LangSmith tracing switch defaults off, flips on with no API key and no network call, and flips back off, followed by a stream_mode='debug' local reconstruction of the run tree (node order, tool calls/args/results, per-step and total token counts) and a printed proof that every observed trace-tree name is a registered graph node name"
  - "Chapter 4-4 (book/src/ch04_langgraph/04_langsmith.md) — closes 4부 with an honest no-cloud, no-screenshot LangSmith chapter"
  - "book/src/SUMMARY.md now lists all 4 chapters under 4부; journey pointers added in introduction.md, ch03_rag/03_rag_chain.md, ch01_basics/01_chat_model.md"
  - "Whole-phase release gate executed and passed: reproducibility, ch01-ch03 regression, fresh mdbook build, format/include checks, masking+leak tests, 3 leak scans, vendored-asset hash pins, git hygiene, code invariants"
  - "Pushed to origin/main; Actions deploy run succeeded for the pushed SHA; all 14 live chapter pages verified serving their real captures, including a human-confirmed rendered mermaid diagram"
affects: [phase-5-capstone-agent]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "lru_cache-aware env toggle: langsmith.utils.get_env_var is @functools.lru_cache-decorated, so an in-process env-var flip must be followed by utils.get_env_var.cache_clear() before the next tracing_is_enabled() read reflects the change"
    - "stream_mode='debug' run-tree reconstruction: task/task_result event pairs keyed by payload['name'] give node start/end order that is provably a subset of app.get_graph().nodes, without ever printing the volatile payload['id'] or event['timestamp']"

key-files:
  created:
    - examples/ch04_langgraph/05_langsmith_trace.py
    - outputs/ch04_langgraph/05_langsmith_trace.out
    - book/src/ch04_langgraph/04_langsmith.md
  modified:
    - examples/.env.example
    - book/src/SUMMARY.md
    - book/src/introduction.md
    - book/src/ch01_basics/01_chat_model.md
    - book/src/ch03_rag/03_rag_chain.md

key-decisions:
  - "No fixes were needed in Task 2's whole-phase gate — everything passed on the first run, so nothing was auto-fixed and no re-capture rules were invoked."

patterns-established:
  - "Release-gate checklist for future phases: reproducibility with an explicit structural-divergence stop rule, ch0N regression via source-sha256 header comparison, fresh mdbook build with a Warning allowlist, check_book.py --html, masking+leak pytest suite, three-angle leak scan (working tree, tracked files, git history) with a single narrow vendored-asset pathspec exclusion backed by a sha256 pin, then push-and-verify-live only after every prior gate is green."

# Metrics
duration: ~12min
completed: 2026-09-14
---

# Phase 4 Plan 04: LangSmith Tracing + Whole-Phase Release Gate Summary

**Chapter 4-4 proves TRACE-01/02/03 with zero LangSmith cloud traffic — a real capture shows the `.env` tracing switch flipping False→True→False with no API key and no network call, then a local `stream_mode="debug"` reconstruction of the run tree (5-step `model→tools→model→tools→model` sequence, tool calls/args/results, per-step token counts summing to 1,713) and a printed proof that all observed node names are registered graph nodes; the whole-phase gate then passed end to end and the human-verify checkpoint confirmed the ch04-1 graph diagram renders as an actual flowchart on the live site.**

## Performance

- **Duration:** ~12 min
- **Tasks:** 3/3 completed (Task 3 was a human-verify checkpoint, approved)
- **Files modified:** 8 (3 created, 5 modified)

## Accomplishments

- `examples/ch04_langgraph/05_langsmith_trace.py` captured, in one real run: the tracing switch reading `False` with no env vars set, `True` immediately after `LANGSMITH_TRACING=true` with no API key present (and no network call — confirmed by inspection that only `utils.tracing_is_enabled()`/`utils.get_env_var.cache_clear()` are called, never a LangSmith `Client`), and `False` again after unsetting it — the `lru_cache` pitfall on `get_env_var` was handled correctly on the first capture (no re-fix needed).
- The same capture's `stream_mode="debug"` section shows the exact node-start/node-end sequence `model → tools → model → tools → model`, the tool calls `lookup_stock({"item": "사과"})`, `lookup_stock({"item": "바나나"})`, `multiply({"a": 12, "b": 5})`, their results (`사과 재고: 12개`, `바나나 재고: 5개`, `60`), per-step token counts (505 / 582 / 626), and a final proof line `관찰된 이름이 모두 등록된 노드인가: True` comparing the observed names against `app.get_graph().nodes` (`['model', 'tools']`).
- Chapter 4-4 published honestly: states plainly that nothing was sent to LangSmith, that no screenshot or UI capture exists, and describes (marked as "공식 문서 기준") what the LangSmith UI additionally shows on top of this reconstruction, including per-step latency, which this book never captures.
- `.env.example` now documents `LANGSMITH_TRACING=false` (default off) and an empty `LANGSMITH_API_KEY`; 1부 1장 gained one explanatory sentence pointing readers to chapter 4-4; `book/src/SUMMARY.md`, `introduction.md`, and `ch03_rag/03_rag_chain.md` all link into 4부.
- Whole-phase release gate (Task 2) passed on the first attempt with zero fixes required, and the human-verify checkpoint (Task 3) confirmed the rendered mermaid diagram on the live site.

## Task Commits

Each task was committed atomically:

1. **Task 1: `05_langsmith_trace.py` + `.env.example` + chapter 4-4 + pointers** - `26d9308` (feat)
2. **Task 2: Whole-phase gate (reproducibility, regression, format, tests, leaks, hygiene, invariants, push, live verification)** - verification-only; no code/content changes were needed, so no separate commit exists for this task
3. **Task 3: Human-verify checkpoint (rendered diagram)** - no commit (approval only)

**Plan metadata:** this SUMMARY commit

## Files Created/Modified

- `examples/ch04_langgraph/05_langsmith_trace.py` — tracing-switch demo + `stream_mode="debug"` local run-tree reconstruction + node-name correspondence proof + token totals
- `examples/.env.example` — appended `LANGSMITH_TRACING=false` / `LANGSMITH_API_KEY=` block
- `outputs/ch04_langgraph/05_langsmith_trace.out` — real capture via `scripts/run_examples.py`
- `book/src/ch04_langgraph/04_langsmith.md` — chapter 4-4, 4-heading template, include-only code/text blocks
- `book/src/SUMMARY.md` — fourth 4부 link added
- `book/src/introduction.md` — `LangGraph·LangSmith` linked to `ch04_langgraph/01_state_graph.md`
- `book/src/ch01_basics/01_chat_model.md` — one sentence added pointing to chapter 4-4
- `book/src/ch03_rag/03_rag_chain.md` — closing sentence turned into a link to `ch04_langgraph/01_state_graph.md`

## Decisions Made

- None beyond what the plan specified — followed the plan as written; the `lru_cache`-clearing mechanism worked correctly on the first capture attempt, so no rule-10 retry was needed.

## Deviations from Plan

None - plan executed exactly as written. No rule 1/2/3 auto-fixes were required in either task, and no rule-11 structural divergence occurred during the reproducibility gate.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. `LANGSMITH_TRACING` defaults to `false` and no LangSmith account or API key is needed to run any example in this book.

## Gate Results (Task 2, whole-phase release gate)

- **Reproducibility:** all 15 examples re-ran byte-identical, including ch04's five captures (the LLM-free `02_graph_mermaid` and the recursion-limit section of `03_checkpointer` byte-identical as required).
- **Regression (ch01-ch03, information only):** all 10 captures re-ran with `OK`, no `Traceback`, and each still matches its `# source-sha256:` header — reported here as informational; nothing in this phase touched their code paths.
- **Fresh build:** `mdbook build` — 0 `ERROR` lines, exactly 1 `Warning` line (the known, already-documented mdbook-mermaid `built against version 0.5.0` preprocessor-version notice).
- **Format:** `scripts/check_book.py --html` — 14/14 `PASS`, exit 0.
- **Tests:** `scripts/test_masking.py` + `scripts/test_check_leaks.py` — 18 passed.
- **Leak scans (3 angles):** working-tree scan, tracked-files secrets-only scan, and full git-history secrets-only scan (with the single vendored-blob pathspec exclusion) — all three `CLEAN`, using only the narrow excludes `book/mermaid.min.js` and `scripts/test_masking.py`.
- **Vendored asset integrity:** `sha256` of `book/mermaid.min.js` and `book/mermaid-init.js` re-verified exactly against the pins recorded in 04-01-SUMMARY.md (`eefea253bed9655e838eb874ff955c46872f982a8e26290c1dd2982ddc0a4703` and `ccf746f10c0a71bd34799867d2f9860dddb5fc6efc6c50d1ea55a1eb1a7bd406`).
- **Git hygiene:** no `.env`/`.venv`/`.claude`/`book/book`/`__pycache__`/`.db*` tracked; no stray `.venv`, `.pytest_cache`, or `main.py`; expected tracked-file counts under `outputs` and `examples/ch04_langgraph` confirmed; `uv lock --check` exits 0; CI workflow stays mdBook-only (no Python setup/uv steps).
- **Invariants:** single chat-model factory, single embedding factory, single `@tool` location, no `langchain_community` imports, no `persist_directory=`, no deprecated `create_react_agent`, no `draw_mermaid_png` remote calls, no absolute home paths in tracked prose/code, and lazy-import check (`torch` not imported at `shared.config` import time) — all passed.
- **Push:** pushed `origin/main` from `197ea7f` to `26d9308`. Actions deploy run (databaseId `34800863434`) for SHA `26d93081261afc0dcf59e91f92fc3e6fd19c12c1` concluded `success`, with `headSha` matching local `HEAD` after the push.
- **Live verification:** all 14 chapter pages returned `LIVE_OK` (each page's `html.unescape`-d body contains its distinctive real-capture line, no `{{#include`, no "이 장은 작성 중입니다"). `toc.html`, pointer links (`introduction.html`, `ch03_rag/03_rag_chain.html` → `ch04_langgraph/01_state_graph.html`; `ch01_basics/01_chat_model.html` → `LANGSMITH_TRACING`), the `.env` line check, and the nonexistent-path 404 check all passed. One known, already-documented false positive: the literal text ```mermaid``` also appears inside the included Python source listing on `ch04_langgraph/01_state_graph.html` (a Korean comment inside `02_graph_mermaid.py`'s embedded listing) — the real rendered diagram is the separate `<pre class="mermaid">` block, confirmed distinct from that source-code fence.
- **Mermaid asset check:** both the hashed `mermaid-<hash>.min.js` (>1,000,000 bytes) and `mermaid-init-<hash>.js` (contains `mermaid.initialize`) URLs returned HTTP 200 on the live site.

## Chapter 4-4 Capture Detail (verbatim from `outputs/ch04_langgraph/05_langsmith_trace.out`)

- **Toggle booleans:** `기본값(아무 설정 없음): False` → `LANGSMITH_TRACING=true: True` → `다시 끈 뒤: False`. No LangSmith API key value was ever set or printed; the switch flips using only `LANGSMITH_TRACING` plus `utils.get_env_var.cache_clear()`.
- **Observed node sequence:** `model → tools → model → tools → model` (5 steps).
- **Tool calls/results per step:** step 1 model requests `lookup_stock({"item": "사과"})` and `lookup_stock({"item": "바나나"})` (tokens: 입력 450 / 출력 55 / 합계 505); step 2 tools return `사과 재고: 12개` and `바나나 재고: 5개`; step 3 model requests `multiply({"a": 12, "b": 5})` (tokens: 입력 545 / 출력 37 / 합계 582); step 4 tools return `60`; step 5 model answers with the final computed result (tokens: 입력 601 / 출력 25 / 합계 626).
- **Totals:** 모델 호출 3회, 입력 토큰 합계 1596 / 출력 토큰 합계 117 / 전체 합계 1713.
- **Correspondence proof:** 그래프에 등록한 노드: `['model', 'tools']`; 관찰된 이름이 모두 등록된 노드인가: `True`.

## Human-Verify Checkpoint Outcome (Task 3)

- **Checkpoint:** confirm the chapter 4-1 graph diagram renders as an actual drawn flowchart (not raw `graph TD;` text) on the live site.
- **Result:** APPROVED. The user opened `https://ohama.github.io/langchain-tutorial/ch04_langgraph/01_state_graph.html` (via the orchestrator) and confirmed the diagram renders as boxes and arrows — a genuine flowchart, not raw mermaid source text.

## Next Phase Readiness

- All of Phase 4's requirements (GRAPH-01..06, TRACE-01..03) are live, gate-verified, and human-confirmed.
- Phase 5's capstone agent can build directly on the `InMemorySaver`/`SqliteSaver` checkpointer mechanisms (04-03) and the `stream_mode="debug"` run-tree introspection pattern (04-04) for its own observability needs.
- No blockers. `origin/main` matches local `HEAD` after this SUMMARY's commit and push.

---
*Phase: 04-langgraph-langsmith*
*Completed: 2026-09-14*
</content>
