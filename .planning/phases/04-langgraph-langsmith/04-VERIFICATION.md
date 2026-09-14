---
phase: 04-langgraph-langsmith
verified: 2026-09-14T05:33:45Z
status: passed
score: 5/5 must-haves verified
---

# Phase 4: LangGraph + LangSmith Verification Report

**Phase Goal:** 독자는 도구 루프를 상태 그래프로 재구성하고, 체크포인터로 대화를 여러 턴 이어가며, LangSmith 트레이스로 에이전트 내부 동작을 들여다볼 수 있다.
**Verified:** 2026-09-14T05:33:45Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `TypedDict`/`add_messages` 상태 + `StateGraph`(노드·엣지) + mermaid 다이어그램 (GRAPH-01, GRAPH-05) | VERIFIED | `examples/ch04_langgraph/01_state_graph.py` defines `ChatState(TypedDict)` with `Annotated[list, add_messages]`, compares it to `MessagesState`; captured output shows both fields `['messages']` and `add_messages` appending (2→ merged). Graph nodes/edges printed: `__start__ -> model`, `model -> tools/__end__` (conditional), `tools -> model` loop-back. `02_graph_mermaid.py` emits `draw_mermaid()` source, included verbatim into `book/src/ch04_langgraph/01_state_graph.md` as a ` ```mermaid ` fence. Built HTML (`book/book/ch04_langgraph/01_state_graph.html`) contains one `<pre class="mermaid">` block whose script tags point at the vendored, sha256-pinned assets (see Artifacts). Human-verify checkpoint for the rendered diagram was already approved by the user (per task context) — not re-raised here. |
| 2 | 그래프 도구 루프가 Phase 2 수동 루프와 동일한 최종 답 (GRAPH-02) | VERIFIED | Re-ran `01_state_graph.py`; captured `outputs/ch04_langgraph/01_state_graph.out` shows question `사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘.`, message flow `HumanMessage → AIMessage → ToolMessage → ToolMessage → AIMessage → ToolMessage → AIMessage`, final answer `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.`, and printed `2부 수동 루프의 최종 답과 동일: True`. Matches the Phase 2 baseline recorded in STATE.md exactly (question, answer, message-type sequence). |
| 3 | `InMemorySaver` + `thread_id` 대화 이어가기, `recursion_limit`으로 무한 루프 정지 (GRAPH-03, GRAPH-04) | VERIFIED | `outputs/ch04_langgraph/03_checkpointer.out`: without a checkpointer, second call doesn't recall the name (2 messages, fresh state each call); with `InMemorySaver()` + `thread_id="chat-1"`, second turn answers "영희라고 하셨어요!" (`답변에 '영희'가 들어있나: True`, 6 accumulated messages); a different `thread_id="chat-2"` does not share memory (`False`, 2 messages). Section 4 runs a deliberately non-terminating pure-Python graph with `recursion_limit=5` and captures the real `GraphRecursionError` message, no LLM involved. |
| 4 | SQLite 체크포인터로 프로세스 재시작 후에도 상태 유지 (GRAPH-06) | VERIFIED | `04_sqlite_checkpoint.py` launches `sqlite_worker.py` twice via `subprocess.run` (genuinely separate OS processes, each prints `부모 프로세스와 동일: False`). Captured output: run1 (`철수`) writes state; run2, a brand-new interpreter process, reads it back and answers "당신의 이름은 **철수**라고 하셨어요!" with message count growing 4→6. DB + WAL sidecars (`.checkpoint_demo.db`, `-wal`, `-shm`) are deleted at start and end; no path or pid printed. Re-ran into scratchpad: byte-identical output, no leftover `.checkpoint_demo.db*` files afterward, `git status --porcelain` empty. `sqlite_worker.py` (non-digit-prefixed filename) is correctly excluded from `scripts/run_examples.py`'s batch collector (`_example_files_in_dir` filters `p.name[:1].isdigit()`), so it only ever runs as a subprocess. |
| 5 | `.env` 플래그로 LangSmith on/off(기본 꺼짐), 트레이스 호출 트리·토큰·tool call 인자/결과, 트레이스↔노드 1:1 대응, 클라우드 미전송 (TRACE-01..03) | VERIFIED | `examples/.env.example` documents `LANGSMITH_TRACING=false` (default off) and empty `LANGSMITH_API_KEY`; `book/src/ch01_basics/01_chat_model.md` explains the new lines. `05_langsmith_trace.py` toggles `LANGSMITH_TRACING` and calls `langsmith.utils.tracing_is_enabled()` (env-only lookup, no network) — capture shows `False → True → False`. `stream_mode="debug"` reconstructs the call tree locally: per-step node start/end, tool call names+args, tool results, and `usage_metadata` token counts per model call, plus a token-sum section. Section 3 compares observed event names against `app.get_graph().nodes` and prints `True`. Chapter prose is honest: explicitly states no data was sent to LangSmith, explains what the LangSmith UI additionally shows (collapsible tree, latency, side-by-side comparison), and states no screenshot/trace-link is included — matching the user-locked no-cloud-account/no-data-sent decision. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `examples/pyproject.toml` | Direct `langgraph`/`langgraph-checkpoint-sqlite`/`langsmith` deps | VERIFIED | Lines 13-15 present; `uv lock --check` (examples/) resolves 151 packages, no drift. |
| `book/book.toml` | `[preprocessor.mermaid]` + `additional-js` | VERIFIED | Both present, wired to `mdbook-mermaid` binary and the two vendored JS files. |
| `book/mermaid.min.js`, `book/mermaid-init.js` | sha256-pinned mdbook-mermaid 0.17.0 assets | VERIFIED | Recomputed sha256 matches plan/summary exactly: `eefea253...` (2,667,011 bytes) and `ccf746f1...` (1,262 bytes). Live site serves the same content-hashed filenames (`mermaid-eefea253.min.js`, `mermaid-init-ccf746f1.js`), HTTP 200. |
| `scripts/check_leaks.py` --exclude | Path-scoped, repeatable, tested | VERIFIED | `_is_excluded()` + repeatable `--exclude`, applied only in the directory-walk branch; `scripts/test_check_leaks.py` (3 tests) all pass; not applied to `outputs/`, `book/src/`, or in CI (`deploy.yml` never invokes `check_leaks.py`). |
| `.github/workflows/deploy.yml` | Pinned `mdbook-mermaid` via curl/tar only | VERIFIED | `MDBOOK_MERMAID_VERSION: "0.17.0"` installed via `curl \| tar -xz`, no python/uv step added — CI-stays-mdBook-only invariant holds. |
| `examples/ch04_langgraph/01_state_graph.py` | GRAPH-01/02 example | VERIFIED | `handle_tool_errors=True` present; matches Phase 2 baseline exactly. |
| `examples/ch04_langgraph/02_graph_mermaid.py` | GRAPH-05 mermaid source | VERIFIED | Entire stdout is `draw_mermaid()` output; re-capture into scratchpad is byte-identical to the committed `.out`. |
| `examples/ch04_langgraph/03_checkpointer.py` | GRAPH-03/04 | VERIFIED | `InMemorySaver`, `thread_id`, deterministic `recursion_limit=5` trip. |
| `examples/ch04_langgraph/04_sqlite_checkpoint.py`, `sqlite_worker.py` | GRAPH-06 | VERIFIED | Two-process subprocess design; `SqliteSaver.from_conn_string`; DB/WAL cleanup verified via scratchpad re-run. |
| `examples/ch04_langgraph/05_langsmith_trace.py` | TRACE-01/02/03 | VERIFIED | `stream_mode="debug"`, `tracing_is_enabled()`, node-name correspondence check. |
| `book/src/ch04_langgraph/{01..04}.md` + `SUMMARY.md` | Four chapters, 4부 wired into TOC | VERIFIED | All four chapters exist, all pass `check_book.py --html`, `SUMMARY.md` lists all four under `# 4부 LangGraph`. |
| `book/src/introduction.md`, `ch01_basics/01_chat_model.md`, `ch03_rag/03_rag_chain.md` | Journey pointers | VERIFIED | Introduction lists 4부 in the reading path; ch01 explains the new `LANGSMITH_*` env lines; ch03 points forward into 4부. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `book/book.toml` | mdbook-mermaid binary | `[preprocessor.mermaid] command` | WIRED | `mdbook build book` produces zero ERROR lines, one expected benign version-mismatch WARN, and a real `<pre class="mermaid">` block in the built HTML. |
| `book/book.toml` | vendored JS assets | `additional-js` | WIRED | Live site serves content-hashed filenames matching local sha256 prefixes exactly. |
| `01_state_graph.py` | `shared/tools.ALL_TOOLS`, `shared/config.get_chat_model` | imports | WIRED | Both imported, no `ChatOpenAI(` outside `config.py`. |
| model node → tools node | conditional + loop-back | `add_conditional_edges` + `add_edge("tools","model")` | WIRED | Confirmed by both source and the printed edge list in the capture. |
| `03_checkpointer.py` | compiled graph w/ memory | `compile(checkpointer=InMemorySaver())` + `thread_id` | WIRED | Confirmed via capture (memory differs per thread_id). |
| `04_sqlite_checkpoint.py` | `sqlite_worker.py` | `subprocess.run([sys.executable, ...])` | WIRED | Two genuinely separate OS processes (`부모 프로세스와 동일: False` both times), reproduced in scratchpad re-run. |
| `sqlite_worker.py` | shared SQLite file | `SqliteSaver.from_conn_string` | WIRED | run2 reads run1's state after full process restart. |
| `05_langsmith_trace.py` | `langsmith.utils.tracing_is_enabled` | env flip + `get_env_var.cache_clear()` | WIRED | Capture shows the toggle actually flipping (`False→True→False`) after the cache-clear workaround. |
| `05_langsmith_trace.py` | compiled graph node names | `stream_mode="debug"` event `name` vs `app.get_graph().nodes` | WIRED | Printed `관찰된 이름이 모두 등록된 노드인가: True`. |
| `git push origin main` | live GitHub Pages (all 4 chapters) | `deploy.yml` Actions run | WIRED | HEAD `79f1836` (and code commit `26d9308`) both show `status: completed / conclusion: success`; all four `ch04_langgraph/*.html` pages return HTTP 200; hashed mermaid asset URLs return HTTP 200. |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|-----------------|
| GRAPH-01 | SATISFIED | none |
| GRAPH-02 | SATISFIED | none |
| GRAPH-03 | SATISFIED | none |
| GRAPH-04 | SATISFIED | none |
| GRAPH-05 | SATISFIED | none (human-verify of rendered diagram already approved) |
| GRAPH-06 | SATISFIED | none |
| TRACE-01 | SATISFIED | none |
| TRACE-02 | SATISFIED | none |
| TRACE-03 | SATISFIED | none |

Note: `.planning/REQUIREMENTS.md` checkboxes for GRAPH-*/TRACE-* still show `[ ]`/`Pending` at time of verification — this is a bookkeeping item for the orchestrator to flip post-verification, not a code/content gap (the same pattern was used for prior phases, e.g. TOOL-01/02 were flipped to `[x]`/`Complete` only after their phase verification passed).

### Anti-Patterns Found

None. No `TODO`/`FIXME`/`placeholder`/stub patterns in any phase-4 example or chapter file. The one instance of an "odd" model behavior (run1 of the SQLite demo hallucinating a `lookup_stock("test")` call instead of directly answering) is real captured output, not a stub, and the chapter prose explicitly explains it (Phase 3 lesson: prose matches captures honestly) rather than glossing over it.

### Anti-Regression Check (Phases 1-3)

- `mdbook build book`: zero ERROR lines, only the expected benign mermaid version-mismatch WARN.
- `scripts/check_book.py --html book/book`: all 14 chapters (Phase 1-4) PASS.
- `scripts/check_leaks.py outputs book/src examples --exclude 'book/mermaid.min.js' --exclude 'scripts/test_masking.py'`: CLEAN.
- `pytest scripts/test_masking.py scripts/test_check_leaks.py`: 18 passed.
- Live site spot-checks for ch01/ch02/ch03 pages: HTTP 200.
- `git status --porcelain`: empty (no modified tracked files, no leftover `.db`/`-wal`/`-shm` artifacts) after re-running examples into the scratchpad.

### Human Verification Required

None outstanding. The one item that would normally require human eyes — the mermaid diagram actually painting in a browser — was already checked and approved by the user per task context, and is corroborated here by structural evidence (built HTML contains `<pre class="mermaid">`, live hashed asset URLs return 200).

### Gaps Summary

No gaps found. All five phase-4 success criteria are backed by real, reproduced, byte-verifiable captures; all key wiring (mermaid pipeline, StateGraph loop-back, checkpointer/thread_id, cross-process SQLite persistence, local trace reconstruction) is confirmed both in source and in captured/re-run output; the release gate (build, format check, leak scan, tests, push, live verification) all pass on the current `main` HEAD; and the LangSmith chapter honors the user-locked no-cloud-account/no-data-sent constraint while still teaching the trace-tree-to-node correspondence.

---

*Verified: 2026-09-14T05:33:45Z*
*Verifier: Claude (gsd-verifier)*
