---
phase: 02-tool-calling
verified: 2026-09-11T07:56:49Z
status: passed
score: 6/6 must-haves verified
---

# Phase 2: Tool Calling Verification Report

**Phase Goal:** 독자는 모델이 도구를 호출하고 그 결과를 받아 다시 답을 만드는 전체 루프를 손으로 구현한 예제로 이해한다.
**Verified:** 2026-09-11T07:56:49Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Chapter 2-1 shows `@tool` schemas + real `bind_tools`-generated `AIMessage.tool_calls` for single-tool, multi-tool, and no-tool questions (TOOL-01) | VERIFIED | `outputs/ch02_tools/01_define_tools.out` lines 3-31: auto-generated JSON schemas for `add`/`multiply`/`lookup_stock`; section 2 `finish_reason: tool_calls`, `add({"a": 7, "b": 5})`; section 3 two parallel `lookup_stock` calls; section 4 `finish_reason: stop`, `tool_calls: 0개`. Chapter prose (`book/src/ch02_tools/01_define_tools.md`) accurately describes each section. Live page confirmed to render this exact content. |
| 2 | Chapter 2-2 shows a hand-written model to tool_calls to `tool.invoke(full tool_call)` to `ToolMessage` to re-invoke loop reaching a real final answer (TOOL-02) | VERIFIED | `outputs/ch02_tools/02_tool_loop.out` lines 9-18: 3 model calls, step 1 two parallel `lookup_stock` calls, step 2 `multiply(a=12, b=5) = 60`, step 3 final answer `사과 재고 12개 x 바나나 재고 5개 = **60**입니다.`; message flow line shows full `HumanMessage -> AIMessage -> ToolMessage -> ToolMessage -> AIMessage -> ToolMessage -> AIMessage` sequence. `run_tool_call` in `examples/ch02_tools/02_tool_loop.py` calls `tool.invoke(tc)` with the full dict inside try/except. Live page confirmed. |
| 3 | Unknown tool name and a raising tool both come back as `ToolMessage` (no crash/Traceback), loop bounded by `MAX_ITERS` | VERIFIED | `.out` lines 21-22: `알 수 없는 도구: subtract`, `도구 실행 오류: ValueError: 재고 목록에 없는 품목: 수박`; zero `Traceback` occurrences in either `.out` (grep count 0). `MAX_ITERS = 5` defined and used as `range(1, MAX_ITERS + 1)` with a `for...else` guard printing `최대 반복(...) 도달`. |
| 4 | Tools exist exactly once in `examples/shared/tools.py`, pure/deterministic, chapters use only named-anchor includes | VERIFIED | `git grep -n "@tool" -- examples ':!examples/.venv'` matches only 3 decorator lines in `examples/shared/tools.py`. No `datetime`/`random`/`requests`/`httpx`/`urllib`/`time.` in the file. 4 ANCHOR regions (`add`, `multiply`, `lookup_stock`, `all_tools`). Both chapter `.md` files include only via `{{#include ../../../examples/shared/tools.py:<anchor>}}`. |
| 5 | Captured `.out` files contain no ids/timings/paths; a second capture into scratchpad differs only in model text if at all | VERIFIED | Reran `run_examples.py` for `ch02_tools` into `<scratchpad>/verify02`; `diff` against committed `.out` files was byte-identical (exit 0, zero output) for both files. `git status --porcelain` stayed clean after rerun. Key-count grep against both scratch outputs returned 0. |
| 6 | `check_book.py` passes for all 7 chapters, leak scans CLEAN, Actions run for HEAD succeeded, both ch02_tools pages live with captured output | VERIFIED | `check_book.py --html book/book` -> 7x PASS (5 ch01_basics + 2 ch02_tools), exit 0. `check_leaks.py` full scan, tracked-files secrets-only, and full-history secrets-only all `CLEAN`. `gh run list` shows latest `deploy.yml` run (`34576553477`) `conclusion: success` for `headSha faa6738a...` = current local `HEAD`. Live fetch of both ch02_tools pages plus all 5 ch01_basics pages found each page's distinctive `.out` line, no raw `{{#include`, no stub marker. `toc.html` contains `2부 도구 호출`, `1부 기초`, `부록`. `introduction.html` and `ch01_basics/05_structured_output.html` both link to `ch02_tools/01_define_tools.html`. Nonexistent path returns HTTP 404. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `examples/shared/tools.py` | Shared deterministic `@tool` defs (add, multiply, lookup_stock, ALL_TOOLS) | VERIFIED | Exists, 4 anchors, pure functions, no network/clock/randomness, exported `ALL_TOOLS` used by both examples |
| `examples/ch02_tools/01_define_tools.py` | TOOL-01 example: schema inspection + bind_tools + tool_calls | VERIFIED | `bind_tools` present, imports tools from `shared.tools`, no `@tool` decorator use, exits 0 |
| `examples/ch02_tools/02_tool_loop.py` | TOOL-02 example: manual loop, MAX_ITERS, error-to-ToolMessage | VERIFIED | `MAX_ITERS` present, `run_tool_call`/`run_loop` implement full loop with try/except and unknown-tool branch |
| `outputs/ch02_tools/01_define_tools.out` | Captured real output | VERIFIED | Present, key-count 0, no Traceback, source-sha256 header matches current `.py` |
| `outputs/ch02_tools/02_tool_loop.out` | Captured real output | VERIFIED | Present, key-count 0, no Traceback, source-sha256 header matches current `.py` |
| `book/src/ch02_tools/01_define_tools.md` | Chapter 2-1 | VERIFIED | Correct 4-heading template, include of `.out:2:`, prose matches captured output |
| `book/src/ch02_tools/02_tool_loop.md` | Chapter 2-2 | VERIFIED | Correct 4-heading template, include of `.out:2:`, prose matches captured output |
| `book/src/SUMMARY.md` | New part between 1부 and 부록 | VERIFIED | `# 2부 도구 호출` section with both chapter links, correctly positioned before `# 부록` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `examples/ch02_tools/*.py` | `examples/shared/tools.py` | `from shared.tools import ...` | WIRED | Both example files import `ALL_TOOLS`/`add`/`lookup_stock` from `shared.tools`; no `@tool` redefined in chapter examples |
| `examples/ch02_tools/02_tool_loop.py` | `langchain_core ToolMessage` | `tool.invoke(tc)` with full dict inside try/except | WIRED | `run_tool_call` calls `tool.invoke(tc)` (full tool_call dict) inside a try block, catches `Exception` and returns a `ToolMessage` with `status="error"` |
| `book/src/ch02_tools/*.md` | `examples/shared/tools.py` | named-anchor includes | WIRED | Both chapters include only `:add`, `:lookup_stock`, `:all_tools` anchors, never the whole file |
| `git push origin main` | live ch02_tools pages | `deploy.yml` Actions run | WIRED | Latest run `34576553477` succeeded for HEAD `faa6738`; both pages confirmed live with correct content |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|-----------------|
| TOOL-01 | SATISFIED | None — real `@tool` schemas and `bind_tools`-produced `tool_calls` captured and shown live |
| TOOL-02 | SATISFIED | None — full model to tool_call to ToolMessage to re-invoke loop reaches a genuine final answer (60), captured and shown live |

### Anti-Patterns Found

None. No TODO/FIXME/placeholder patterns, no empty handlers, no stub returns in any phase-2 file.

### Phase 1 Regression Check

All 7 chapters (5 ch01_basics + 2 ch02_tools) pass `check_book.py --html`. All 5 ch01_basics live pages confirmed reachable with correct captured content (`LIVE_OK` for each). `toc.html`, `introduction.html` navigation, and internal cross-links intact. No regression detected.

### Human Verification Required

None. All must-haves were verified programmatically against the codebase, the local rebuilt book, the live GitHub Pages site, and the GitHub Actions run for current HEAD.

### Gaps Summary

No gaps found. All 6 must-have truths, all 8 required artifacts, and all 4 key links verified. Reproducibility rerun into the scratchpad was byte-identical to the committed captures. Leak scans (content + tracked-files secrets + full git-history secrets) all CLEAN. `git status --porcelain` remained empty throughout verification (no accidental modifications). GitHub Actions run for current HEAD succeeded, and the live site was independently confirmed via `curl` to serve both ch02_tools chapters and all ch01_basics chapters with real content (no `{{#include}}` markers, no stub text).

---

*Verified: 2026-09-11T07:56:49Z*
*Verifier: Claude (gsd-verifier)*
