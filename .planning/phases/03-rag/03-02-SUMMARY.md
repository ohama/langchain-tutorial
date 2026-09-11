---
phase: 03-rag
plan: 02
subsystem: rag
tags: [lcel, rag, runnable-parallel, runnable-passthrough, chroma, str-output-parser, whole-phase-gate]

# Dependency graph
requires:
  - phase: 03-rag (plan 03-01)
    provides: "get_embeddings() factory, three frozen Korean sample documents (including the company handbook with 재택근무 주 2일 and no parking mention), chunk_size=300/chunk_overlap=50/add_start_index=True chunking, ephemeral Chroma pattern"
  - phase: 02-tool-calling (plan 02-01)
    provides: "Whole-phase release gate pattern (reproducibility rerun, format, masking, 3 leak scans, hygiene, invariants, push, Actions watch, live verification)"
provides:
  - "examples/ch03_rag/03_rag_chain.py: retriever + format_docs + LCEL RAG chain ({'context': retriever | format_docs, 'question': RunnablePassthrough()} | PROMPT | get_chat_model() | StrOutputParser()) answering from retrieved documents and correctly refusing an out-of-scope question"
  - "Chapter 3-3 (LCEL RAG 체인): real capture of retrieved chunks, the rendered prompt with injected document text, a grounded Korean answer, and a 'not in the documents' answer for an unrelated question"
  - "3부 RAG complete in SUMMARY.md; journey pointers from introduction.md and ch02_tools/02_tool_loop.md"
  - "Phase 3 fully published: whole-phase gate passed (reproducibility, ch01/ch02 regression, format, masking, 3 leak scans, git hygiene, invariants), pushed to main, Actions succeeded, all 10 chapter pages live"
affects: [phase-4-langgraph]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "LCEL RAG chain: dict-in-pipe becomes RunnableParallel; retriever | format_docs collapses retrieved Documents into one context string; RunnablePassthrough forwards the raw question to the other branch"
    - "Retriever always returns k results regardless of relevance; grounding relies on an explicit prompt instruction ('문서에서 찾을 수 없습니다'), not on retrieval filtering"

key-files:
  created:
    - examples/ch03_rag/03_rag_chain.py
    - outputs/ch03_rag/03_rag_chain.out
    - book/src/ch03_rag/03_rag_chain.md
  modified:
    - book/src/SUMMARY.md
    - book/src/introduction.md
    - book/src/ch02_tools/02_tool_loop.md

key-decisions:
  - "No rule-8 query revisions needed — both the grounded question (재택근무) and the out-of-scope question (주차 요금) produced correct, on-spec answers on the first capture"
  - "No rule-9 fallback needed — the ch03 scratch rerun was byte-identical (not just wording-only) for all three files"

# Metrics
duration: ~20min
completed: 2026-09-11
---

# Phase 3 Plan 02: LCEL RAG Chain + Whole-Phase Release Gate Summary

**LCEL RAG chain (`{"context": retriever | format_docs, "question": RunnablePassthrough()} | PROMPT | get_chat_model() | StrOutputParser()`) grounds a real Korean answer in the retrieved 재택근무 handbook chunk and correctly refuses an out-of-scope parking question, published after a full byte-identical reproducibility + regression + leak + hygiene + invariants gate.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-09-11T08:51:32Z
- **Tasks:** 2/2
- **Files modified:** 6 (3 created, 3 modified)

## Accomplishments

- `examples/ch03_rag/03_rag_chain.py` builds a `retriever = vectorstore.as_retriever(search_kwargs={"k": 2})` over the same 17-chunk index from 03-01, a `format_docs` join, a grounding prompt instructing the model to answer only from the supplied documents (or say `문서에서 찾을 수 없습니다`), and the LCEL chain `{"context": retriever | format_docs, "question": RunnablePassthrough()} | PROMPT | get_chat_model() | StrOutputParser()`.
- Real capture: section 2 shows the retriever returning two `03_company_handbook.md` chunks for the 재택근무 question and the fully rendered prompt with both chunks' text (including the 재택근무 sentence) injected. Section 3 shows `체인 타입: RunnableSequence` and a grounded answer. Section 4 shows the retriever still returning its nearest (irrelevant) chunks for an out-of-scope question, and the chain correctly answering that the documents don't cover it.
- Chapter 3-3 (LCEL RAG 체인) published with the standard 4-heading format, ties the chain back to 1부 4장's `RunnableParallel`/`RunnablePassthrough` concepts, and explains why `k` always returns results regardless of relevance.
- 3부 RAG is now complete in `SUMMARY.md` (3 chapters); `introduction.md`'s 여정 line and `ch02_tools/02_tool_loop.md`'s 요점 정리 both link forward to 3부.
- Whole-phase gate: scratch rerun of all 10 examples, all 10× `OK`, all 10 scratch files 0 key-count. The three ch03 files were **byte-identical** against committed (`diff` exit 0, no wording-only or structural divergence — rule 9 not invoked). The 7 ch01/ch02 files were also byte-identical (information only, no re-capture) with matching source-sha256 headers.
- Fresh `mdbook build`: 0 ERROR/WARN. `check_book.py --html` 10× `PASS`. Masking tests: 15 passed. All three `check_leaks.py` invocations (full scan, tracked secrets-only, git-history secrets-only): `CLEAN`. Git hygiene and all invariants (`ChatOpenAI(`/`HuggingFaceEmbeddings(`/`@tool` each in exactly one file, no `langchain_community`, no `persist_directory=`, lazy `torch` import confirmed with `LAZY_OK`, `langchain-community` absent from `uv.lock`) passed.
- Pushed to `main` (`3aa1361`). Actions run `34581170155` (workflow `deploy.yml`) had `headSha` matching local `HEAD` and completed with `conclusion: success` (build 8s + deploy 18s).
- Live-verified all 10 chapter pages, `toc.html` (3부 RAG / 2부 도구 호출 / 1부 기초 / 부록), both journey pointers (`introduction.html`, `ch02_tools/02_tool_loop.html` → `ch03_rag/01_load_split.html`), the ch01 1장 `EMBEDDING_MODEL` note, and a 404 for a nonexistent path.

## Task Commits

Each task was committed atomically:

1. **Task 1: Chapter 3-3 (LCEL RAG 체인) + journey pointers** - `3aa1361` (feat)
2. **Task 2: Whole-phase gate** - no additional commit; every check passed against the state left by Task 1, `git status --porcelain` was empty throughout

**Plan metadata commit:** this SUMMARY.md (committed and pushed alongside plan completion; STATE.md/ROADMAP.md remain the orchestrator's responsibility)

## Files Created/Modified

- `examples/ch03_rag/03_rag_chain.py` — retriever + `format_docs` + grounding prompt + LCEL RAG chain; sections 1-4 per plan spec
- `outputs/ch03_rag/03_rag_chain.out` — real capture via `scripts/run_examples.py` (with warm-up)
- `book/src/ch03_rag/03_rag_chain.md` — chapter 3-3, exact 4-heading template, include-only code/output blocks
- `book/src/SUMMARY.md` — third 3부 RAG link added, 3부 now complete
- `book/src/introduction.md` — 여정 line: `RAG` → `[RAG](ch03_rag/01_load_split.md)`
- `book/src/ch02_tools/02_tool_loop.md` — one closing bullet pointing to 3부 RAG

## Decisions Made

- No rule-8 (retry) revisions were needed: the 재택근무 question's answer contained `2일` on the first capture, and the 주차 요금 question's answer contained `찾을 수 없` on the first capture.
- No rule-9 (structural-divergence stop/re-run) fallback was needed: the single scratch rerun of `ch03_rag` was byte-identical to the committed files for all three chapters.

## Deviations from Plan

None — plan executed exactly as written. The known benign `Loading weights` progress-bar text again appeared only on stderr during `Chroma.from_documents` (as documented in 03-01), never reaching `.out`; this required no action, consistent with the prior plan's finding.

## Issues Encountered

None. Both RAG chain questions produced meaningful, on-spec answers on the first `run_examples.py` capture; no retries were needed anywhere in the plan.

## User Setup Required

None — reused the same `examples/.env` (git-ignored) and shell `LITELLM_API_KEY`; no new external service configuration was introduced.

## RAG Chain Questions and Answers (verbatim, from `outputs/ch03_rag/03_rag_chain.out`)

**Question 1 (grounded, in-scope):** `재택근무는 일주일에 며칠까지 할 수 있어?`
- Retrieved sources: `03_company_handbook.md` (start_index=436), `03_company_handbook.md` (start_index=164)
- Rendered prompt: contained both retrieved chunks' full text, including the handbook's 재택근무 sentence (`재택근무는 한 주에 최대 2일까지 할 수 있습니다. ...`)
- Chain type: `RunnableSequence`
- Answer: `한 주에 최대 2일까지 할 수 있습니다.`

**Question 2 (out-of-scope, not in the documents):** `회사 주차 요금은 한 달에 얼마야?`
- Retrieved sources (nearest but irrelevant, retriever always returns `k`): `03_company_handbook.md` (start_index=664), `03_company_handbook.md` (start_index=164)
- Answer: `문서에서 찾을 수 없습니다`

No rule-8 query revisions were made — both questions used exactly the text specified in the plan.

## Reproducibility Result

**ch03 (per-file classification):**
| File | Classification |
|---|---|
| `01_load_split.out` | identical (byte-identical, `diff` exit 0) |
| `02_embed_search.out` | identical (byte-identical, `diff` exit 0) |
| `03_rag_chain.out` | identical (byte-identical, `diff` exit 0) |

No wording-only divergence, no structural divergence, no rule-9 re-run or STOP needed.

**ch01/ch02 regression (information only, no re-capture):**
| File | Classification |
|---|---|
| `ch01_basics/01_chat_model.out` | identical |
| `ch01_basics/02_messages.out` | identical |
| `ch01_basics/03_prompt_templates.out` | identical |
| `ch01_basics/04_lcel_runnables.out` | identical |
| `ch01_basics/05_structured_output.out` | identical |
| `ch02_tools/01_define_tools.out` | identical |
| `ch02_tools/02_tool_loop.out` | identical |

All 7 committed `outputs/ch0[12]_*/*.out` first lines matched `# source-sha256:` of their `.py` files; no `Traceback` in any scratch capture.

## Gate Results (for traceability)

- Scratch rerun: `run_examples.py --outputs-dir <scratch>` (no targets, all 10 examples), 10× `OK`, all 10 scratch `.out` files key-count 0
- Fresh `mdbook build book`: exit 0, 0 ERROR/WARN lines
- `scripts/check_book.py --html book/book`: `PASS` for all 10 chapters (5 ch01_basics + 2 ch02_tools + 3 ch03_rag), exit 0
- `pytest scripts/test_masking.py`: 15 passed
- `scripts/check_leaks.py outputs book/src examples book/book .planning/phases/03-rag`: `CLEAN`
- `git ls-files -z | xargs -0 scripts/check_leaks.py --secrets-only`: `CLEAN`
- `git log -p --all | scripts/check_leaks.py --secrets-only -`: `CLEAN`
- Git hygiene: no `.env`/`.venv/`/`.claude/`/`book/book/`/`__pycache__`/`.pytest_cache` tracked; no stray `.venv`/`.pytest_cache`/`main.py`; `git status --porcelain` empty; `git ls-files outputs` = 10; `git ls-files examples/data/ch03_rag` = 3; all 3 `ch03_rag/*.out` first lines match `shasum -a 256` of their `.py`; no Chroma/sqlite/parquet artifacts in status; `examples/.env.example` has exactly one empty `LLM_API_KEY=` line; `uv lock --project examples --check` exit 0 (148 packages resolved); CI workflow grep for python/uv setup = 0 (mdBook-only)
- Invariants: `ChatOpenAI(` only in `examples/shared/config.py`; `HuggingFaceEmbeddings(` only in `examples/shared/config.py`; `@tool` only in `examples/shared/tools.py`; no `langchain_community` anywhere in `examples`; no `persist_directory=` anywhere in `examples`; `import shared.config` does not pull in `torch` (`LAZY_OK`); `langchain-community` absent from `examples/uv.lock` (count 0)
- Push: `main` updated `da982b0..3aa1361` (via `4b34747`, `170e1e1`, `2041ea0`, `a3507a7` from 03-01, then `3aa1361` from this plan)
- Actions run: `34581170155` (workflow `deploy.yml`, branch `main`); `headSha` confirmed equal to local `HEAD` (`3aa13611aa99ed930cbbc23b9e9c272417382982`) before watching; `gh run watch --exit-status` completed successfully (build 8s + deploy 18s); `gh run view --json conclusion,headSha` confirmed `{"conclusion":"success","headSha":"3aa13611aa99ed930cbbc23b9e9c272417382982"}`
- Live verification: all 10 pages returned `LIVE_OK` (distinctive line from each `.out` found in the `html.unescape`d page, neither `{{#include` nor the stub marker present); `toc.html` contains `3부 RAG`, `2부 도구 호출`, `1부 기초`, `부록`; `introduction.html` and `ch02_tools/02_tool_loop.html` both link to `ch03_rag/01_load_split.html`; `ch01_basics/01_chat_model.html` contains `EMBEDDING_MODEL`; a nonexistent path returned HTTP 404

## Final Pushed SHA and Live URLs Checked

- Pushed SHA: `3aa13611aa99ed930cbbc23b9e9c272417382982`
- Actions run ID: `34581170155` (conclusion: `success`)
- Live base URL: `https://ohama.github.io/langchain-tutorial/`
- Pages checked: all 5 `ch01_basics/*.html`, both `ch02_tools/*.html`, all 3 `ch03_rag/*.html`, `toc.html`, `introduction.html`, plus one nonexistent path (404)

## Next Phase Readiness

- Phase 3 (RAG) is fully complete and live: RAG-01 through RAG-04 all shipped with real captures, 3부 RAG has all 3 chapters, and the whole-phase gate (reproducibility, regression, format, masking, leaks, hygiene, invariants) passed cleanly with zero deviations.
- No blockers for Phase 4 (LangGraph). The LangGraph baseline recorded in `02-01-SUMMARY.md` (exact tool-loop question, 3-step trace, final answer `60`) remains the reference Phase 4 must reproduce as a graph; this plan did not touch that code path.
- The authoring pipeline and whole-phase release gate are proven for a fourth time (01-04, 02-01, 03-01's dry run, and this plan) with zero code fixes required at gate time.

---
*Phase: 03-rag*
*Completed: 2026-09-11*
