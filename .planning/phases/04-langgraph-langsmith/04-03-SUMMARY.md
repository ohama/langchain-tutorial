---
phase: 04-langgraph-langsmith
plan: 03
subsystem: docs
tags: [langgraph, checkpointer, inmemorysaver, sqlitesaver, thread_id, recursion_limit, subprocess]

# Dependency graph
requires:
  - phase: 04-langgraph-langsmith (plan 02)
    provides: "build_graph() shape (MessagesState + ToolNode(handle_tool_errors=True) + tools_condition + tools->model loop-back) that this plan's graphs copy verbatim"
provides:
  - "examples/ch04_langgraph/03_checkpointer.py: real captured proof that InMemorySaver + thread_id continues a conversation, a different thread_id does not share it, and a deliberately cyclic LLM-free graph is stopped by recursion_limit with the real GraphRecursionError message"
  - "examples/ch04_langgraph/04_sqlite_checkpoint.py + sqlite_worker.py: two genuinely separate OS processes sharing one SqliteSaver file, proving restart-survival rather than in-process reuse"
  - "Chapters 4-2 and 4-3 (book/src/ch04_langgraph/02_checkpointer.md, 03_sqlite_checkpoint.md), SUMMARY.md now lists 3 chapters under 4부"
affects: [04-04-whole-phase-gate, phase-5-capstone-agent (multi-turn memory + restart survival mechanisms)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "build_graph_builder() convention: 03_checkpointer.py and sqlite_worker.py both copy the same StateGraph builder verbatim rather than importing it, continuing the 04-02 precedent, so the compiled-once-vs-compiled-with-checkpointer split stays in one file"
    - "Volatile-value discipline: process identity is proven via a printed boolean comparison (부모 프로세스와 동일: False) instead of printing a pid; the SQLite path is passed as a CLI arg but never printed"
    - "Parent-stdout flush-before-subprocess pattern: when a child process inherits the parent's stdout fd for a captured run, the parent must flush its own buffered print() calls before spawning the child, or the child's directly-inherited writes land in the capture ahead of the parent's still-buffered text"

key-files:
  created:
    - examples/ch04_langgraph/03_checkpointer.py
    - examples/ch04_langgraph/04_sqlite_checkpoint.py
    - examples/ch04_langgraph/sqlite_worker.py
    - outputs/ch04_langgraph/03_checkpointer.out
    - outputs/ch04_langgraph/04_sqlite_checkpoint.out
    - book/src/ch04_langgraph/02_checkpointer.md
    - book/src/ch04_langgraph/03_sqlite_checkpoint.md
  modified:
    - book/src/SUMMARY.md

key-decisions:
  - "Fixed a stdout-ordering bug (see Deviations) by adding flush=True to every parent print() and an explicit sys.stdout.flush() before each subprocess.run() call in 04_sqlite_checkpoint.py."

# Metrics
duration: ~9min
completed: 2026-09-14
---

# Phase 4 Plan 03: Checkpointer + SQLite Restart-Survival Summary

**`InMemorySaver`/`thread_id` and `recursion_limit` proven in one real capture (chapter 4-2), and `SqliteSaver` proven to survive an actual OS process restart via two `subprocess`-launched Python processes sharing one file (chapter 4-3), with no volatile values or leftover `.db*` artifacts.**

## Performance

- **Duration:** ~9 min
- **Tasks:** 2/2 completed
- **Files modified:** 8 (7 created, 1 modified)

## Accomplishments

- `03_checkpointer.py` shows, in one real capture: a checkpointer-less graph forgetting a name across two separate `invoke` calls (message count 2, meaning each call started from an empty state); the same graph compiled with `InMemorySaver()` remembering the name on `thread_id="chat-1"` (message count 6, answer contains "영희" → `True`); a different `thread_id="chat-2"` not sharing that memory (message count 2, answer does not contain "영희" → `False`); and a deliberately cyclic, LLM-free graph stopped by `recursion_limit=5` with the exact real `GraphRecursionError` message, caught so the script exits 0.
- `04_sqlite_checkpoint.py` + `sqlite_worker.py` launch two genuinely separate Python processes (`subprocess.run([sys.executable, ...])`) sharing one `SqliteSaver` file: the DB file did not exist before, existed after the first process, and was removed again at the end; both processes printed `부모 프로세스와 동일: False` (never a pid); the second process answered "당신의 이름은 **철수**라고 하셨어요!" — the name the first process had stored — and its message count (6) was higher than the first process's (4).
- Chapters 4-2 and 4-3 are live; `book/src/SUMMARY.md` now lists 3 chapters under `4부 LangGraph`; `check_book.py --html` passes 13/13; `check_leaks.py` (with the narrow `book/mermaid.min.js` / `scripts/test_masking.py` excludes) reports `CLEAN`.

## Task Commits

Each task was committed atomically:

1. **Task 1: `03_checkpointer.py` + chapter 4-2 (체크포인터와 recursion_limit)** - `563f9be` (feat)
2. **Task 2: `04_sqlite_checkpoint.py` + `sqlite_worker.py` + chapter 4-3 (프로세스 재시작)** - `7a6f5f3` (feat)

**Plan metadata:** this SUMMARY commit (local only, not pushed — 04-04 pushes after the whole-phase gate)

## Files Created/Modified

- `examples/ch04_langgraph/03_checkpointer.py` — checkpointer-less vs `InMemorySaver`+`thread_id` comparison, then an LLM-free cyclic graph stopped by `recursion_limit`
- `examples/ch04_langgraph/04_sqlite_checkpoint.py` — cleans the DB, launches two worker processes via `subprocess.run`, cleans up again (try/finally)
- `examples/ch04_langgraph/sqlite_worker.py` — one-turn worker run as a separate OS process against the shared `SqliteSaver` file (deliberately not numbered, so `run_examples.py` never collects it standalone)
- `outputs/ch04_langgraph/03_checkpointer.out`, `outputs/ch04_langgraph/04_sqlite_checkpoint.out` — real captures via `scripts/run_examples.py`
- `book/src/ch04_langgraph/02_checkpointer.md`, `book/src/ch04_langgraph/03_sqlite_checkpoint.md` — new chapters, 4-heading template, include-only code/text blocks
- `book/src/SUMMARY.md` — two new links under `4부 LangGraph`

## Decisions Made

- No question/name text revisions were needed (rule 9 not invoked) — both captures showed their intended point on the first run.
- Added `flush=True` to every `print()` in `04_sqlite_checkpoint.py` and an explicit `sys.stdout.flush()` immediately before each `subprocess.run()` call — see Deviations for why.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Parent script's own output landed after both workers' output in the first capture, instead of interleaved in source order**

- **Found during:** Task 2, first capture of `04_sqlite_checkpoint.py`
- **Issue:** The parent script's `print()` calls go to a pipe (not a tty) when run under `scripts/run_examples.py`'s `subprocess.run(capture_output=True)`, so Python block-buffers them and only flushes at process exit. The child worker processes inherit the same stdout file descriptor and write directly to it, flushing at their own (earlier) exit. Net effect in the first capture: both workers' full output appeared first in the `.out` file, followed by all four of the parent's `=== N ===` section lines in their correct relative order — a real ordering bug, not a flake (reproducible, and diagnosable from Python's documented buffering behavior for non-tty streams).
- **Fix:** Added `flush=True` to every parent `print()` call and an explicit `sys.stdout.flush()` right before each `subprocess.run()` invocation in `run_worker()`. Re-captured: the `.out` now shows `=== 1 ===` through `=== 4 ===` interleaved with each worker's lines in the exact order the source code executes them.
- **Files modified:** `examples/ch04_langgraph/04_sqlite_checkpoint.py`, `outputs/ch04_langgraph/04_sqlite_checkpoint.out` (re-captured)
- **Verification:** Re-capture confirms correct interleaving; all other content (DB-existence booleans, `부모 프로세스와 동일` values, run1/run2 answers and message counts) is byte-identical to the pre-fix capture — only ordering changed. `check_leaks.py` CLEAN, key count 0, no `Traceback`/`0x`/`/Users/`/`.db` path string.
- **Committed in:** `7a6f5f3` (Task 2 commit — the fix was applied before the commit, so no separate fix-commit exists)

---

**Total deviations:** 1 auto-fixed (1 bug, output-ordering only; no graph/tool/checkpointer logic changed)
**Impact on plan:** No scope creep. GRAPH-03/04/06 truths are all satisfied exactly as specified; the fix only corrected the temporal ordering of already-correct captured content.

## Issues Encountered

- In the SQLite demo's first worker turn (`run1`, "내 이름은 철수야. 기억해줘."), the model unexpectedly called `lookup_stock(item="test")` before answering, producing a 4-message thread instead of the simpler 2-message exchange seen in chapter 4-2's `InMemorySaver` intro turn. This is real, reproducible model behavior (confirmed identical across the pre-fix and post-fix captures) rather than a code defect — the graph, tools, and checkpointer all behaved correctly, and the chapter's core point (the second process recalls the name the first process stored) is unaffected and clearly shown. The prose in chapter 4-3 describes this turn accurately rather than glossing over it.

## User Setup Required

None - no external service configuration required.

## Memory and Recursion-Limit Outcomes (chapter 4-2, verbatim from the capture)

- **Without a checkpointer:** each `invoke` starts empty; the second call's message count was 2, and the model reported never having been told a name.
- **`InMemorySaver`, `thread_id="chat-1"`:** answer to the recall question contained "영희" (`답변에 '영희'가 들어있나: True`); message count for `chat-1` was 6.
- **`InMemorySaver`, `thread_id="chat-2"` (different thread):** answer did not contain "영희" (`답변에 '영희'가 들어있나: False`); message count for `chat-2` was 2 — lower than `chat-1`'s 6, confirming the threads are isolated.
- **`recursion_limit=5` on a deliberately cyclic, LLM-free graph:** raised `GraphRecursionError` with message exactly: "Recursion limit of 5 reached without hitting a stop condition. You can increase the limit by setting the `recursion_limit` config key." (plus the documentation-URL troubleshooting line). No rule-9 or rule-10 classification was needed — this section is LLM-free and matched the pre-verified deterministic text exactly on first capture.

## SQLite Restart-Survival Outcomes (chapter 4-3, verbatim from the capture)

- **DB-existence booleans:** `시작 전 DB 파일 존재: False` → `실행 후 DB 파일 존재: True` (after `run1`) → `정리 후 DB 파일 존재: False` (after cleanup).
- **`부모 프로세스와 동일`:** printed `False` exactly twice (once per worker), confirming both workers ran as genuinely separate OS processes.
- **`run2`'s verbatim answer:** "당신의 이름은 **철수**라고 하셨어요! 😊" followed by an offer to help further — recalling the name `run1` stored, from a completely separate process.
- **Message counts:** `run1` ended with 4 messages in the thread; `run2` ended with 6 — growth across the process boundary.
- **Rule 9/10:** no question revisions were needed; the point (restart-survival) was shown on the first capture. The only re-capture was the rule-1 ordering fix above, which produced byte-identical content aside from line order (a "printed volatile value" would have required an example-bug fix; this was a pure ordering issue, also fixed as a rule-1 bug per the deviation above).
- **Cleanup confirmed:** no `.db`, `.db-wal`, or `.db-shm` file remained after the run (`ls examples/ch04_langgraph/ | grep -c '\.db'` → `0`; `git status --porcelain --ignored` → `0` matches for those patterns), and `git status --porcelain` was clean except for this plan's own intentionally-tracked new files.

## Next Phase Readiness

- Both `InMemorySaver`+`thread_id` (in-process memory) and `SqliteSaver` (restart-surviving memory) are now demonstrated with real captures — the exact mechanisms Phase 5's capstone agent needs for multi-turn work.
- `recursion_limit` is demonstrated as the loop-termination safety net for graphs with loop-back edges.
- Nothing pushed; both task commits plus this SUMMARY are local on `main`. 04-04 handles the whole-phase gate and push.

---
*Phase: 04-langgraph-langsmith*
*Completed: 2026-09-14*
