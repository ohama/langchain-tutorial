---
phase: 04-langgraph-langsmith
plan: 02
subsystem: docs
tags: [langgraph, stategraph, messagesstate, add_messages, tools_condition, toolnode, draw_mermaid, mdbook-mermaid]

# Dependency graph
requires:
  - phase: 04-langgraph-langsmith (plan 01)
    provides: "langgraph/langgraph-checkpoint-sqlite/langsmith deps, include-only mermaid fence gate, sha256-pinned mdbook-mermaid rendering pipeline"
  - phase: 02-tool-calling (plan 01)
    provides: "examples/shared/tools.py (add/multiply/lookup_stock/ALL_TOOLS), the exact Phase 2 baseline question/answer/message-flow to reproduce"
provides:
  - "examples/ch04_langgraph/01_state_graph.py: build_graph() (MessagesState + ToolNode(handle_tool_errors=True) + tools_condition + tools->model loop-back), the stable graph shape 04-03 reuses"
  - "Proof, asserted as a printed boolean in the capture, that the graph reproduces the Phase 2 manual-loop baseline exactly"
  - "examples/ch04_langgraph/02_graph_mermaid.py + outputs/ch04_langgraph/02_graph_mermaid.out: byte-reproducible draw_mermaid() source, LLM-free"
  - "Chapter 4-1 (book/src/ch04_langgraph/01_state_graph.md) live under a new # 4부 LangGraph, with a real rendered <pre class=\"mermaid\"> diagram"
affects: [04-03-checkpointer-chapters, 04-04-whole-phase-gate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "build_graph() verbatim-copy convention: 02_graph_mermaid.py duplicates 01_state_graph.py's build_graph() rather than importing it, matching 3부's load_documents() precedent"
    - "GRAPH-02 baseline proof is asserted in captured output (final == BASELINE_ANSWER printed as a boolean), not left to prose"

key-files:
  created:
    - examples/ch04_langgraph/01_state_graph.py
    - examples/ch04_langgraph/02_graph_mermaid.py
    - outputs/ch04_langgraph/01_state_graph.out
    - outputs/ch04_langgraph/02_graph_mermaid.out
    - book/src/ch04_langgraph/01_state_graph.md
  modified:
    - book/src/SUMMARY.md

key-decisions:
  - "Section 4's demo question changed from the plan's literal '수박 재고를 확인해줘.' to '노트북 재고를 확인해줘.' after the original produced an unbounded ~60-turn retry loop (see Deviations) — no change to build_graph(), ALL_TOOLS, shared/config.py, or handle_tool_errors"

# Metrics
duration: ~20min
completed: 2026-09-14
---

# Phase 4 Plan 02: StateGraph Reconstruction of the Manual Tool Loop Summary

**`build_graph()` (MessagesState + ToolNode(handle_tool_errors=True) + tools_condition + tools->model loop-back) reproduces the Phase 2 manual tool loop exactly — same parallel `lookup_stock` calls, same `multiply(a=12, b=5)`, same message flow, and a final answer that the capture itself asserts (`True`) is identical to the Phase 2 baseline — and chapter 4-1 renders the compiled graph as a real `<pre class="mermaid">` diagram sourced from a byte-reproducible `draw_mermaid()` capture.**

## Performance

- **Duration:** ~20 min
- **Tasks:** 3/3 completed
- **Files modified:** 6 (5 created, 1 modified)

## Accomplishments

- `01_state_graph.py` shows, in real captured output, `ChatState` (`TypedDict` + `Annotated[list, add_messages]`) and `MessagesState` sharing the same `['messages']` shape, `add_messages` appending (not overwriting) a 1+1 merge into 2 messages, and the compiled graph's nodes/edges including the conditional `model -> tools`/`model -> __end__` edges and the `tools -> model` loop-back.
- Running the exact Phase 2 baseline question through the graph reproduced the baseline exactly: parallel `lookup_stock(item="사과")`/`lookup_stock(item="바나나")`, then `multiply(a=12, b=5)` -> `60`, message flow `HumanMessage → AIMessage → ToolMessage → ToolMessage → AIMessage → ToolMessage → AIMessage`, and a final answer identical (character-for-character) to the Phase 2 baseline — asserted in the capture as a printed `True`.
- A tool-body `ValueError` (unknown inventory item) came back as an error `ToolMessage` instead of killing the graph, because `ToolNode` was built with `handle_tool_errors=True`; the model then answered directly without crashing the run.
- `02_graph_mermaid.py` captures `draw_mermaid()` output with nothing else in stdout; the capture is byte-identical across a scratch re-run and leak-scan CLEAN.
- Chapter 4-1 is live under a new `# 4부 LangGraph` section; a fresh local `mdbook build` renders a genuine `<pre class="mermaid">` diagram (not a literal fence) containing `graph TD;` and `tools --> model`, backed by both pinned hashed asset script tags; `check_book.py --html` passes 11/11.

## Task Commits

Each task was committed atomically:

1. **Task 1: `01_state_graph.py` — state, nodes/edges, Phase 2 baseline reproduction, tool-error handling** - `146348d` (feat)
2. **Task 2: `02_graph_mermaid.py` — capture the diagram source as pure output** - `f9cb8d2` (feat)
3. **Task 3: Chapter 4-1 + `# 4부 LangGraph` in SUMMARY + rendered-diagram verification** - `a71fc08` (feat)

**Plan metadata:** this SUMMARY commit (local only, not pushed — 04-04 pushes after the whole-phase gate)

## Files Created/Modified

- `examples/ch04_langgraph/01_state_graph.py` — `ChatState`, `BASELINE_ANSWER`, `build_graph()`, `describe()`, four numbered sections
- `examples/ch04_langgraph/02_graph_mermaid.py` — verbatim-copied `build_graph()`, prints only `draw_mermaid()` source
- `outputs/ch04_langgraph/01_state_graph.out`, `outputs/ch04_langgraph/02_graph_mermaid.out` — real captures via `scripts/run_examples.py`
- `book/src/ch04_langgraph/01_state_graph.md` — new chapter, 4-heading template, include-only code/text/mermaid blocks
- `book/src/SUMMARY.md` — new `# 4부 LangGraph` section inserted before `# 부록`

## Decisions Made

- Changed the section-4 tool-error demo question from the plan's literal "수박 재고를 확인해줘." to "노트북 재고를 확인해줘." — see Deviations below for the full rationale. No graph, tool, `shared/config.py`, or `handle_tool_errors` code was touched.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Section 4's plan-specified demo question caused an unbounded retry loop, producing an unusable ~230-line capture**

- **Found during:** Task 1, first capture of `01_state_graph.py`
- **Issue:** With the plan's literal question `HumanMessage("수박 재고를 확인해줘.")`, the default `ToolNode(handle_tool_errors=True)` error message (`"Error: ValueError(...)\n Please fix your mistakes."`) prompted the model to keep guessing alternate fruit-item spellings (한글/영문 이름을 번갈아) instead of giving up after one attempt. The first capture ran 5.5 model-turns of section 3 plus **~62 model calls** in section 4 alone (388.8s total), producing a 264-line `.out` dominated by repeated `수박`/`watermelon`/other-fruit guesses. This is real, reproducible model behavior (confirmed with an isolated scratch probe using a low `recursion_limit`, which hit the limit deterministically), not a one-off fluke, and not something rule 9's retry-once allowance was designed for (the error `ToolMessage` *was* produced correctly — the problem was capture size/practicality, not correctness).
- **Fix:** Changed only the example script's section-4 question to `HumanMessage("노트북 재고를 확인해줘.")` — a category that isn't a plausible fruit-name misspelling, so the model recognizes it as out-of-scope after exactly one tool call and answers directly. Re-captured: section 4 is now 1 tool call, 1 error `ToolMessage`, 1 final answer (matching the plan's intended shape). Total capture time dropped from 388.8s to 10.7s. `build_graph()`, `ALL_TOOLS`, `shared/config.py`, and `handle_tool_errors=True` were **not** modified.
- **Files modified:** `examples/ch04_langgraph/01_state_graph.py` (one line: the section-4 question), `outputs/ch04_langgraph/01_state_graph.out` (re-captured)
- **Verification:** Re-capture (`10.7s`) shows exactly: `Human: 노트북 재고를 확인해줘.` → `AI: tool_calls [lookup_stock({"item": "노트북"})]` → `Tool[lookup_stock] (error): Error: ValueError('재고 목록에 없는 품목: 노트북')\n Please fix your mistakes.` → `AI: 노트북은 현재 재고 목록에 없는 품목으로 확인됩니다. ...`. Section 3 (the GRAPH-02 baseline proof) was unaffected and identical across both captures. `check_leaks.py` CLEAN, key count 0, no `Traceback`/`0x`/absolute paths.
- **Committed in:** `146348d` (Task 1 commit — the fix was applied before the first commit, so no separate fix-commit exists)

---

**Total deviations:** 1 auto-fixed (1 bug, example-script wording only; no graph/tool/config code changed)
**Impact on plan:** No scope creep. GRAPH-01/02/05 truths are all still satisfied exactly as specified; only the illustrative wording of one demo question changed, and only because the plan's literal choice triggered impractical (though real) model retry behavior.

## Issues Encountered

None beyond the deviation above.

## User Setup Required

None - no external service configuration required.

## GRAPH-02 Baseline Reproduction (verbatim from the capture)

- **Question (identical to Phase 2):** `사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘.`
- **Step 1 (parallel):** `lookup_stock({"item": "사과"})` -> `사과 재고: 12개`; `lookup_stock({"item": "바나나"})` -> `바나나 재고: 5개`
- **Step 2:** `multiply({"a": 12, "b": 5})` -> `60`
- **Step 3:** no tool calls; final answer `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.`
- **Message flow:** `HumanMessage → AIMessage → ToolMessage → ToolMessage → AIMessage → ToolMessage → AIMessage`
- **Baseline-equality boolean printed in the capture:** `2부 수동 루프의 최종 답과 동일: True` — the graph's final answer matched the Phase 2 baseline character-for-character; **no re-run was needed** (rule 9 was not invoked for this comparison).

## Tool-Error Section (verbatim from the capture)

- **Question:** `노트북 재고를 확인해줘.`
- **Tool call:** `lookup_stock({"item": "노트북"})`
- **Error `ToolMessage`:** status `error`, content `Error: ValueError('재고 목록에 없는 품목: 노트북')` followed by ` Please fix your mistakes.` (the default `handle_tool_errors=True` formatting)
- **Model's follow-up answer (graph did not crash):** `노트북은 현재 재고 목록에 없는 품목으로 확인됩니다.` followed by an offer to check another item.

## Mermaid Capture and Render

- **Captured node lines:** `__start__([<p>__start__</p>]):::first`, `model(model)`, `tools(tools)`, `__end__([<p>__end__</p>]):::last`
- **Captured edge lines:** `__start__ --> model;`, `model -.-> __end__;`, `model -.-> tools;`, `tools --> model;`, plus 3 `classDef` lines
- **Early determinism:** a scratch re-capture of `02_graph_mermaid.out` (LLM-free) diffed byte-identical against the committed file (`diff` exit 0) — no rule-10 classification needed (no difference occurred)
- **Rendered-page confirmation:** fresh local `mdbook build book` produced exactly one `<pre class="mermaid">` block on `book/book/ch04_langgraph/01_state_graph.html`, containing `graph TD;` and (HTML-escaped) `tools --&gt; model;`; the page references both pinned hashed assets (`mermaid-eefea253.min.js`, `mermaid-init-ccf746f1.js`, matching 04-01's sha256 pins); `mermaid-eefea253.min.js` is 2,667,011 bytes (>1,000,000); the page contains zero occurrences of an unrendered `{{#include` marker. (One incidental, harmless match of the literal substring `` ```mermaid `` appears — inside the *included Python source listing*, in a Korean code comment describing the pipeline, not as an actual unrendered Markdown fence; the diagram itself renders correctly as shown above.)
- **Whole build:** `check_book.py --html book/book` -> 11/11 `PASS`; `toc.html` contains `4부 LangGraph`; `check_leaks.py book/src/ch04_langgraph outputs/ch04_langgraph` -> `CLEAN`.

## Next Phase Readiness

- `build_graph()` in `examples/ch04_langgraph/01_state_graph.py` is the stable graph shape 04-03's checkpointer chapters reuse (same `MessagesState`/`ToolNode`/`tools_condition`/loop-back).
- `recursion_limit` (foreshadowed in this chapter's closing line and code comment) is still unintroduced in example code — 04-03 introduces it alongside the checkpointer, as planned.
- Nothing pushed; all three task commits plus this SUMMARY are local on `main`. 04-04 handles the whole-phase gate and push.

---
*Phase: 04-langgraph-langsmith*
*Completed: 2026-09-14*
