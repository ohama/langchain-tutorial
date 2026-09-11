---
phase: 01-book-infra-basics
plan: 03
subsystem: docs
tags: [langchain, langchain-core, langchain-openai, mdbook, prompt-templates, few-shot]

# Dependency graph
requires:
  - phase: 01-book-infra-basics (plan 01-01)
    provides: "examples/shared/config.py chat-model factory, scripts/run_examples.py capture runner, scripts/check_leaks.py leak scanner"
  - phase: 01-book-infra-basics (plan 01-02)
    provides: "mdBook skeleton with final Phase 1 TOC and chapter stubs (book/src/ch01_basics/0{1,2,3}_*.md)"
provides:
  - "scripts/check_book.py: stdlib chapter-format gate (exact ## headings, include-only code blocks, :2: output range, ANCHOR suffix rule, no-stub rule, rendered-HTML cross-check)"
  - "Chapter 1 (채팅 모델 호출하기): reader .env setup walkthrough + real invoke/stream capture with visible stream chunk boundaries"
  - "Chapter 2 (메시지와 멀티턴 대화): real multi-turn System/Human/AI message history contrasted with a history-less call"
  - "Chapter 3 (프롬프트 템플릿): ChatPromptTemplate variable substitution and FewShotChatMessagePromptTemplate expansion with real model answers"
  - "Reference chapter authoring pattern (example .py -> runner capture -> {{#include}}-only .md) proven end to end for 01-04 and all later content phases"
affects: [01-04, phase-2, phase-3, phase-4, phase-5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "scripts/check_book.py is the mechanical gate for chapter format; every future chapter plan should run it (with default --html book/book) before committing"
    - "Examples never construct ChatOpenAI directly, never print timings/paths/keys, and print short === 섹션 === headers so static .out files stay readable without ANCHOR markers"
    - "Chapter .md files include shared/config.py only via its settings/chat_model/structured ANCHOR regions, never as a whole-file include"

key-files:
  created:
    - scripts/check_book.py
    - examples/ch01_basics/01_chat_model.py
    - examples/ch01_basics/02_messages.py
    - examples/ch01_basics/03_prompt_templates.py
    - outputs/ch01_basics/01_chat_model.out
    - outputs/ch01_basics/02_messages.out
    - outputs/ch01_basics/03_prompt_templates.out
  modified:
    - book/src/ch01_basics/01_chat_model.md
    - book/src/ch01_basics/02_messages.md
    - book/src/ch01_basics/03_prompt_templates.md

key-decisions:
  - "check_book.py validates the raw .md source (exact heading list, single-line include-only fenced blocks) and, when book/book exists, cross-checks the rendered HTML for leftover {{#include}}/ANCHOR/source-sha256 strings — catching both authoring mistakes and silent mdBook include failures"
  - "01_chat_model.py prints stream chunk count plus repr() of the first 5 chunks so a static captured .out file still proves streaming happened in multiple pieces, not just one blob"

patterns-established:
  - "Chapter authoring pipeline: write examples/chNN/0N_name.py (import model only via shared.config) -> capture with scripts/run_examples.py -> write book/.../0N_name.md with only {{#include}} lines in code fences -> gate with scripts/check_book.py"

# Metrics
duration: ~10min
completed: 2026-09-11
---

# Phase 1 Plan 03: Book Infra + Basics Chapters 1-3 Summary

**Three real LangChain basics chapters (chat model invoke/stream, multi-turn messages, prompt templates + few-shot) authored end to end through the capture pipeline, gated by a new stdlib `scripts/check_book.py` chapter-format checker.**

## Performance

- **Duration:** ~10 min (commit span 16:03:45 → 16:05:43 KST for the three task commits; research reading and per-example capture/verification loops extended total wall time beyond the commit span)
- **Tasks:** 3/3
- **Files modified:** 10 (1 created script, 3 created examples, 3 created captured outputs, 3 replaced chapter stubs)

## Accomplishments

- `scripts/check_book.py` (171 lines, stdlib only) enforces: exact `## ` heading list and order, every `python`/`text`/`ini` fenced block is a single `{{#include ...}}` line whose target resolves, `outputs/*.out` includes always use `:2:`, files containing `ANCHOR:` markers must be included by anchor name, no chapter may still contain the stub placeholder text, and (when `book/book` exists) the rendered HTML must not leak `{{#include`, `ANCHOR`, or `source-sha256` strings. Defaults to discovering all `ch*/` pages from `book/src/SUMMARY.md` when called with no arguments.
- Chapter 1 walks the reader through copying `.env.example` to `.env`, includes the real `.env.example` and `shared/config.py`'s `settings`/`chat_model` ANCHOR regions, then shows a real `invoke` call and a real `stream` call whose captured output visibly shows 70 separate chunks (`repr()` of the first five) proving streaming is not just one printed blob.
- Chapter 2 captures a real two-turn conversation where the model correctly recalls the user's name ("민수") and topic from a `SystemMessage`/`HumanMessage`/`AIMessage` history, directly contrasted with the identical follow-up question sent with no history (model explicitly says it can't know), plus a third section showing a hand-built `AIMessage` is treated identically to a real model response.
- Chapter 3 captures `ChatPromptTemplate` variable substitution — printing `input_variables` and the formatted messages before ever calling the model — and a `FewShotChatMessagePromptTemplate` expansion where two example pairs become real `Human`/`AI` messages in the prompt; the model then answers three new words in the exact one-word opposite format the few-shot examples taught it (빠르다→느리다, 밝다→어둡다, 무겁다→가볍다), with no LCEL `|` operator used yet.
- All three chapters pass `check_book.py` individually, together, and via `SUMMARY.md`-driven auto-discovery; `mdbook build book` produces zero `ERROR` lines each time; `check_leaks.py` reports `CLEAN` across all three `.out` files, the three chapter `.md` sources, the built HTML, and `check_book.py` itself.

## Task Commits

Each task was committed atomically:

1. **Task 1: check_book.py gate + Chapter 1 (chat model invoke/stream)** - `de5316c` (feat)
2. **Task 2: Chapter 2 (messages and multi-turn conversation)** - `1708bb7` (feat)
3. **Task 3: Chapter 3 (prompt templates and few-shot)** - `1d8db95` (feat)

## Files Created/Modified

- `scripts/check_book.py` — stdlib chapter-format + include-only + rendered-HTML checker; CLI: `uv run --project examples python scripts/check_book.py [MD ...] [--html DIR]`
- `examples/ch01_basics/01_chat_model.py` — `get_chat_model()` invoke + stream, prints chunk count and first-5 `repr()`
- `examples/ch01_basics/02_messages.py` — System/Human/AI history with follow-up recall, no-history contrast, hand-built AIMessage
- `examples/ch01_basics/03_prompt_templates.py` — variable template substitution shown pre-invoke, few-shot expansion + 3 real answers
- `outputs/ch01_basics/{01_chat_model,02_messages,03_prompt_templates}.out` — real captures via `scripts/run_examples.py`, each starting with `# source-sha256: <hex>`
- `book/src/ch01_basics/{01_chat_model,02_messages,03_prompt_templates}.md` — replace stubs, follow `<chapter_template>` exactly (`개념: 왜 필요한가` / `최소 코드` / `실제 출력` / `요점 정리`)

## Decisions Made

- `check_book.py`'s anchor-suffix rule treats any suffix matching `:[A-Za-z_]...` (e.g. `:settings`, `:chat_model`) as a valid named anchor, and any `:\d*:\d*` suffix (e.g. `:2:`) as a line-range suffix; a file containing `ANCHOR:` markers requires the former, `outputs/*.out` requires the latter — this single regex distinction (from the plan spec) cleanly separates the two include styles without extra flags.
- Chapter 1's stream example intentionally prints both the chunk count and `repr()` of the first five chunks, per the plan's own research note that a plain stream capture can look identical to an invoke capture in a static file; the captured `.out` confirms 70 chunks like `"'태'", "'양'", "'광'"`.
- No prompt or example changes were needed to get meaningful output — every capture succeeded and was usable on the first `run_examples.py` run (see Deviations).

## Deviations from Plan

None — plan executed exactly as written. No bugs found, no missing critical functionality, no blocking issues, and no architectural changes were needed. Every example's first capture was already meaningful (Chapter 2's section 2 did not accidentally guess the name/topic, so no prompt adjustment/re-capture was required).

## Issues Encountered

None — all three tasks completed on the first attempt with no retries, auth gates, or blocking errors. `LITELLM_API_KEY` was already set in the shell environment from plan 01-01's setup, so no authentication gate was hit.

## User Setup Required

None — the same `examples/.env` (git-ignored, created in 01-01) and shell `LITELLM_API_KEY` were reused; no new external service configuration was introduced.

## Runtimes Observed (for orchestrator / 01-04)

- Warm-up: 2.1–2.2s each run (matches 01-01's cold-start note; well under timeout headroom)
- `01_chat_model.py`: 4.8s (invoke + 70-chunk stream)
- `02_messages.py`: 6.7s (three model calls)
- `03_prompt_templates.py`: 4.5s (one template-fill call + three few-shot calls)
- `mdbook build book`: sub-second, zero `ERROR` lines each of the three times it was run in this plan

## Style Conventions 01-04 Must Copy

- Exact `## ` heading order: `개념: 왜 필요한가` / `최소 코드` / `실제 출력` / `요점 정리`, no others, no reordering.
- Every `python`/`text`/`ini` fenced block contains exactly one `{{#include ...}}` line — never re-typed code or output.
- `outputs/*.out` includes always end in `:2:` to hide the hash header line.
- `shared/config.py` is only included via its ANCHOR regions (`:settings`, `:chat_model`, `:structured`), never as a whole-file include.
- Examples: `from shared.config import get_chat_model` only, no `ChatOpenAI(` construction, no `load_dotenv`, no `sys.path` hacks, no `# ANCHOR` markers in example files, short `=== 섹션 ===` print headers, no timings/paths/keys printed, exit 0 (catch and print only `type(e).__name__` if an error is the lesson).
- Run `uv run --project examples python scripts/check_book.py <chapter.md ...>` (or with no args to check every discovered chapter) plus `scripts/check_leaks.py` on the new `.out`/`.md`/built-HTML paths before committing each task.

## Next Phase Readiness

- `scripts/check_book.py` is ready to gate every remaining chapter in this and future phases (01-04's Chapter 4 LCEL and Chapter 5 structured output, and all book-content phases through Phase 5).
- The full authoring pipeline (example `.py` → `run_examples.py` capture → `{{#include}}`-only `.md` → `check_book.py` gate) is proven three times over on real content, not just infra.
- No blockers. One thing to remember for 01-04: Chapter 3 deliberately avoided the LCEL `|` operator and said so in its prose ("다음 장에서 `|` 연산자로 연결하는 법을 배운다") — Chapter 4 should honor that promise and introduce `|` there.

---
*Phase: 01-book-infra-basics*
*Completed: 2026-09-11*
