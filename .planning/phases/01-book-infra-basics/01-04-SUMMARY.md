---
phase: 01-book-infra-basics
plan: 04
subsystem: docs
tags: [langchain-core, lcel, runnables, structured-output, pydantic, mdbook, github-actions, github-pages]

# Dependency graph
requires:
  - phase: 01-book-infra-basics (plan 01-01)
    provides: "examples/shared/config.py chat-model factory (get_chat_model/get_structured_model), scripts/run_examples.py capture runner, scripts/check_leaks.py leak scanner"
  - phase: 01-book-infra-basics (plan 01-02)
    provides: "mdBook skeleton with final Phase 1 TOC, GitHub Actions deploy.yml, live GitHub Pages site"
  - phase: 01-book-infra-basics (plan 01-03)
    provides: "scripts/check_book.py chapter-format gate, chapters 1-3, proven authoring pipeline (example .py -> run_examples.py -> {{#include}}-only .md -> check_book.py)"
provides:
  - "Chapter 4 (LCEL로 체인 만들기): pipe composition, RunnableLambda, RunnableParallel, batch, stream with real captured output"
  - "Chapter 5 (구조화 출력): get_structured_model typed Pydantic result plus a truthful captured 500-error demo of the default with_structured_output method, with root-cause/fix prose"
  - "Whole-phase gate proven end to end: format check x5, three leak scans (full + tracked secrets-only + full git history secrets-only), git hygiene, model-factory invariant, push, successful Actions run, live verification of all 5 chapter pages + index + 404"
affects: [phase-2, phase-3, phase-4, phase-5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Chapter authoring pipeline (proven 5/5 times now): example .py (imports only from shared.config) -> scripts/run_examples.py capture -> {{#include}}-only chapter .md -> scripts/check_book.py gate -> scripts/check_leaks.py -> commit"
    - "Whole-phase release gate: fresh mdbook build -> check_book.py --html -> 3x check_leaks.py invocations -> git hygiene greps -> ChatOpenAI( invariant grep -> push -> gh run watch -> live curl + html.unescape content check per chapter -> index/404 check"

key-files:
  created:
    - examples/ch01_basics/04_lcel_runnables.py
    - examples/ch01_basics/05_structured_output.py
    - outputs/ch01_basics/04_lcel_runnables.out
    - outputs/ch01_basics/05_structured_output.out
  modified:
    - book/src/ch01_basics/04_lcel_runnables.md
    - book/src/ch01_basics/05_structured_output.md
    - examples/shared/config.py

key-decisions:
  - "StrOutputParser()'s real captured result type prints as TextAccessor (a str subclass in this langchain-core version), not plain str — chapter 4 documents this truthfully (isinstance(result, str) is True) instead of asserting the plan's assumed 'str' label"
  - "shared/config.py's get_structured_model comment was reworded to avoid the literal substring 'json_schema' (was tripping this plan's own grep invariant that no config.py text should mention the default method by name); the function's actual behavior (function_calling, strict=False) was unchanged"

patterns-established:
  - "Basics part (chapters 1-5) is complete; all 5 pass check_book.py individually and via SUMMARY.md auto-discovery, together forming the reference pattern for every future book-content phase"

# Metrics
duration: ~25min
completed: 2026-09-11
---

# Phase 1 Plan 04: LCEL, Structured Output, and Whole-Phase Release Gate Summary

**Chapters 4 (LCEL pipe/RunnableLambda/RunnableParallel/batch/stream) and 5 (typed Pydantic structured output plus a real, captured HTTP 500 speculative-decoding failure and its fix) complete the basics part; the full release gate (format x5, 3 leak scans, git hygiene, push, successful Actions run, live content verification) passed on the first pass after one comment-wording fix.**

## Performance

- **Duration:** ~25 min (task commits span 16:09:25 → 16:11:03 KST; total wall time includes reading all context files, two live captures, chapter authoring, the full release gate, push, and watching the Actions run to completion)
- **Completed:** 2026-09-11
- **Tasks:** 3/3
- **Files modified:** 7 (2 created examples, 2 created captured outputs, 2 modified chapter stubs, 1 modified shared config)

## Accomplishments

- Chapter 4 captures real output for `prompt | model | StrOutputParser()` (`RunnableSequence`), `RunnableLambda` adapting a bare string into the prompt's dict input, `RunnableParallel` running summary/keyword chains concurrently into one dict (`{'summary': ..., 'keywords': ...}`), `chain.batch([...])` preserving input order across 3 topics, and `chain.stream(...)` yielding 26 chunks — and honestly documents that the parsed result's type prints as `TextAccessor` (a real `str` subclass in this langchain-core version) rather than asserting a plain `str` label that wasn't what the capture showed.
- Chapter 5 captures a real typed `Person` object via `get_structured_model(Person)` for two different Korean sentences, proves `age` is a genuine `int` (`result.age + 1 == 31`), and then captures the deliberate anti-pattern (`with_structured_output(Person)` with no method override) actually failing with `실패: OpenAIAPIError` / `status_code=500` — the chapter's troubleshooting section explains this via speculative decoding (MTP) rejecting schema-constrained decoding, and why `method="function_calling", strict=False` (centralized in `shared/config.py`) avoids it.
- The whole-phase release gate ran end to end: fresh `mdbook build` (zero ERROR/WARN), `check_book.py --html book/book` PASS x5, three separate `check_leaks.py` invocations (full scan over `outputs book/src examples book/book`, tracked-files secrets-only, full git-history secrets-only) all `CLEAN`, git hygiene greps clean (no `.env`/`.venv`/`.claude`/`book/book`/`__pycache__` tracked, no stray `.venv`/`.pytest_cache`/`main.py`, working tree clean, 5 `.out` files each with a `# source-sha256:` header), and the `ChatOpenAI(` construction invariant holding to exactly one line in `examples/shared/config.py`.
- Pushed to `main` (`4a5ba4b`); confirmed the triggered Actions run's `headSha` matched local `HEAD` before watching it; the run (`34573247193`) completed with `conclusion: success` in ~16s (build 7s + deploy 9s).
- Live-verified all 5 chapter pages at `https://ohama.github.io/langchain-tutorial/ch01_basics/<name>.html`: each page's HTML, after `html.unescape`, contains a distinctive line from its own captured `.out` (from line 2 onward) and contains neither `{{#include` nor the stub placeholder text. Also re-confirmed the sidebar (`toc.html`) still contains `1부 기초` and `부록`, and a nonexistent path returns HTTP 404 with a page referencing `/langchain-tutorial/` asset paths.

## Task Commits

Each task was committed atomically:

1. **Task 1: Chapter 4 (LCEL/Runnables)** - `b24036e` (feat)
2. **Task 2: Chapter 5 (structured output + 500 error troubleshooting)** - `4a5ba4b` (feat) — includes the `shared/config.py` comment-wording fix
3. **Task 3: Whole-phase gate (format, leaks, hygiene, push, Actions, live verification)** - no additional commit; every check passed against the state left by tasks 1-2, so there was nothing new to fix or stage (`git status --porcelain` was empty throughout)

**Plan metadata commit:** this SUMMARY.md (committed and pushed alongside this plan's completion, per plan rules — STATE.md/ROADMAP.md remain the orchestrator's responsibility)

## Files Created/Modified

- `examples/ch01_basics/04_lcel_runnables.py` — pipe composition, RunnableLambda, RunnableParallel, batch, stream (imports only `from shared.config import get_chat_model`)
- `examples/ch01_basics/05_structured_output.py` — `Person` Pydantic schema, `get_structured_model` success path (2 inputs) + deliberate default-method failure demo
- `outputs/ch01_basics/04_lcel_runnables.out`, `outputs/ch01_basics/05_structured_output.out` — real captures via `scripts/run_examples.py`, each starting with `# source-sha256: <hex>`
- `book/src/ch01_basics/04_lcel_runnables.md` — replaces stub; follows the exact 4-heading chapter template
- `book/src/ch01_basics/05_structured_output.md` — replaces stub; adds a `### 트러블슈팅: speculative decoding과 500 에러` subsection under 실제 출력
- `examples/shared/config.py` — one-line comment reword in `get_structured_model` (no behavior change)

## Decisions Made

- Documented the real `TextAccessor` result type in Chapter 4 rather than silently normalizing it to "str" in prose — the plan's own rule ("outputs are generated, never hand-edited... never claim [a result] the output does not show") applies just as much to prose claims about types as it does to error demos; `isinstance(result, str)` being `True` is the load-bearing fact for readers, not the exact subclass name.
- Reworded `shared/config.py`'s `get_structured_model` comment to drop the literal substring `json_schema` (kept the meaning — "the default/unconstrained decoding method fails here" — via "기본 방식(스키마 강제 디코딩)") so the plan's own `git grep -n "json_schema" -- examples/shared/config.py` invariant (proving the codebase never names the broken default) holds. This is a pre-existing string from plan 01-01 that this plan's own verification step caught; the fix is comment-only, no functional change, and `get_structured_model`'s actual call (`method="function_calling", strict=False`) was already correct before and after.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed a config.py comment that defeated this plan's own "no json_schema mention" grep check**

- **Found during:** Task 2, running the task's own `<verify>` step (`git grep -n "json_schema" -- examples/shared/config.py` must print nothing)
- **Issue:** `examples/shared/config.py` (created in plan 01-01) had a Korean comment explaining the design decision that happened to contain the literal substring `json_schema`: `# 로컬 서버는 기본값(json_schema)에서 500 에러 → function_calling + strict=False로 통일`. This is not a functional bug — `get_structured_model` already always called `with_structured_output(schema, method="function_calling", strict=False)` — but it made this plan's stated verification command fail.
- **Fix:** Reworded the comment to `# 로컬 서버는 기본 방식(스키마 강제 디코딩)에서 500 에러 → function_calling + strict=False로 통일`, preserving the exact same meaning without the literal string.
- **Files modified:** `examples/shared/config.py`
- **Verification:** `git grep -n "json_schema" -- examples/shared/config.py` now prints nothing (exit 1, no match); `git grep -n "with_structured_output" -- examples ':!examples/.venv'` still matches only `examples/shared/config.py` and the one demo line in `05_structured_output.py`; re-ran `scripts/run_examples.py ch01_basics/05_structured_output.py` was not needed since only `config.py`'s comment (not `05_structured_output.py`) changed and the capture was already correct.
- **Committed in:** `4a5ba4b` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — a pre-existing comment from an earlier plan that this plan's own gate caught)
**Impact on plan:** Comment-only change, no functional/behavioral difference to `get_structured_model`. No scope creep.

## Issues Encountered

None beyond the deviation above — all captures were meaningful on the first `run_examples.py` run for both chapters (including the intentional 500-error demo, which failed exactly as STACK.md/PITFALLS.md predicted), and the Actions run succeeded on the first push.

## User Setup Required

None — reused the same `examples/.env` (git-ignored, from plan 01-01) and shell `LITELLM_API_KEY`; no new external service configuration was introduced.

## Structured-Output Demo Result (for traceability, no secret values)

- Section 2 of `outputs/ch01_basics/05_structured_output.out` shows: `실패: OpenAIAPIError` / `status_code=500` — the default (unconstrained) `with_structured_output` method failed exactly as STACK.md's live-tested research predicted, due to the local MLX server's speculative decoding (MTP) rejecting schema-constrained decoding. No traceback text is present in the capture.

## Release Gate Results (for traceability)

- Fresh `mdbook build book`: exit 0, 0 ERROR/WARN lines
- `scripts/check_book.py --html book/book`: `PASS` for all 5 chapters (`01_chat_model`, `02_messages`, `03_prompt_templates`, `04_lcel_runnables`, `05_structured_output`), exit 0
- `scripts/check_leaks.py outputs book/src examples book/book`: `CLEAN` — no false positives encountered, so no exclusions/documentation of vendored-asset hits were needed
- `git ls-files -z | xargs -0 scripts/check_leaks.py --secrets-only`: `CLEAN`
- `git log -p --all | scripts/check_leaks.py --secrets-only -`: `CLEAN`
- Git hygiene: no `.env`/`.venv/`/`.claude/`/`book/book/`/`__pycache__`/`.pytest_cache` tracked; no stray `.venv`, `.pytest_cache`, or `main.py` in the working tree; `git status --porcelain` empty at final check; `git ls-files outputs/ch01_basics | wc -l` = 5, each starting with `# source-sha256:`
- `git grep -n "ChatOpenAI(" -- examples`: exactly one match (`examples/shared/config.py:44`)
- Push: `main` updated `5b48886..4a5ba4b`
- Actions run: `34573247193` (workflow `deploy.yml`, branch `main`), `headSha` confirmed equal to local `HEAD` (`4a5ba4b33f06eda80f5575e67dffe0ef054dbb05`) before watching; `gh run watch --exit-status` completed successfully (build 7s + deploy 9s); `gh run view --json conclusion,headSha` confirmed `{"conclusion":"success","headSha":"4a5ba4b33f06eda80f5575e67dffe0ef054dbb05"}`
- Live verification: all 5 pages under `https://ohama.github.io/langchain-tutorial/ch01_basics/` returned `LIVE_OK` (distinctive line from each `.out`'s line 2+ found in the `html.unescape`d page; neither `{{#include` nor the stub marker present); `toc.html` still contains `1부 기초` and `부록`; a nonexistent path returned HTTP 404 with `/langchain-tutorial/` in the served page

## Next Phase Readiness

- Phase 1 (Book Infra + Basics) is functionally complete: all 5 basics chapters exist, pass the format gate, are leak-free, and are live and verified on GitHub Pages with real captured outputs. The full authoring pipeline and whole-phase release gate are both proven twice now (01-03 and this plan) with zero surprises beyond one comment-wording fix.
- No blockers for Phase 2 (Tool Calling). `examples/shared/config.py` (`get_chat_model`, `get_structured_model`), `scripts/run_examples.py`, `scripts/check_book.py`, and `scripts/check_leaks.py` are all stable, reusable infrastructure — no interface changes were made in this plan beyond the comment reword.
- One thing worth remembering for future chapters that use `with_structured_output`: this project's server fails the default method with HTTP 500 (confirmed live twice now, in STACK.md's original research and again in this plan's Chapter 5 capture); always route through `get_structured_model`.

---
*Phase: 01-book-infra-basics*
*Completed: 2026-09-11*
