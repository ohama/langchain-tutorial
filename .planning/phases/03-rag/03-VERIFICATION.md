---
phase: 03-rag
verified: 2026-09-11T08:58:00Z
status: passed
score: 10/10 must-haves verified (1 prose gap closed by orchestrator fix 354a83e)
gaps:
  - truth: "A question the documents do not cover (주차 요금) gets an answer saying it cannot be found in the documents, with the retrieved (irrelevant) sources printed"
    status: closed
    closed_by: "commit 354a83e — section-4 prose corrected to 교육 지원(start_index=664) / 연차 휴가(start_index=164); check_book PASS, mdbook build 0 ERROR, check_leaks CLEAN, Actions run 34581971258 success, live page shows corrected text"
    reason: "The underlying capture (outputs/ch03_rag/03_rag_chain.out) is correct: retrieval returns 03_company_handbook.md chunks at start_index=664 (교육 지원 / education-support section) and start_index=164 (연차 휴가 / annual-leave section), and the chain correctly answers '문서에서 찾을 수 없습니다'. But the published chapter's 실제 출력 interpretation paragraph misnames these two chunks as '업무 장비, 재택근무' (equipment, remote-work), which are different sections (start_index=895 and 436). This is a factual mismatch between chapter prose and the captured .out data, live on the public site."
    artifacts:
      - path: "book/src/ch03_rag/03_rag_chain.md"
        issue: "Section '=== 4 ===' interpretation sentence names the wrong two retrieved chunk topics (업무 장비, 재택근무 instead of 교육 지원, 연차 휴가)"
    missing:
      - "Correct the chunk-topic names in the 실제 출력 prose for section 4 to match outputs/ch03_rag/03_rag_chain.out (start_index=664 → 교육 지원, start_index=164 → 연차 휴가)"
---

# Phase 3: RAG Verification Report

**Phase Goal:** 독자는 한국어 문서를 로딩·분할·다국어 임베딩·검색·생성으로 잇는 RAG 파이프라인 전체를 실제 출력과 함께 따라갈 수 있다.
**Verified:** 2026-09-11T08:58:00Z
**Status:** passed — initial run found 1 prose/capture mismatch; fixed in 354a83e and re-checked
**Re-verification:** Yes — gap-closure re-check by orchestrator (2026-09-11)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Ch3-1 shows real Document loading + RecursiveCharacterTextSplitter chunk count/content (RAG-01) | VERIFIED | `outputs/ch03_rag/01_load_split.out`: `문서 3개 -> 청크 17개` (7/5/5 per doc), per-chunk `start_index`/길이/preview; live page confirms same text |
| 2 | Ch3-2 shows real bge-m3 (mps) embedding run: dim, first values, L2 norm, similar>different (RAG-02) | VERIFIED | `.out`: `차원: 1024`, `'device': 'mps'`, `벡터 길이(L2 노름): 1.0000`, cosine 0.8970 (similar) > 0.3243 (different) |
| 3 | Ch3-2 shows Chroma-indexed Korean-query search with rank-1 = intended doc, distances to 4 decimals (RAG-03) | VERIFIED | All 3 queries' rank-1 source matches intended document; distances printed to 4 decimals (e.g. `0.7067`, `0.7570`, `0.5286`) |
| 4 | Ch3-3 shows retrieved chunks + rendered prompt with injected text (RAG-04) | VERIFIED | `.out` section 2 shows retrieved sources and the full rendered prompt containing the 재택근무 sentence |
| 5 | LCEL RAG chain produces a real Korean answer grounded in the 재택근무 fact (RAG-04) | VERIFIED | `.out` section 3: `체인 타입: RunnableSequence`, `답변: 한 주에 최대 2일까지 할 수 있습니다.` |
| 6 | Out-of-scope (주차) question answered "not found," with retrieved sources printed | VERIFIED (after fix) | `.out`: `답변: 문서에서 찾을 수 없습니다`, sources start_index 664/164; chapter prose corrected in 354a83e to 교육 지원 / 연차 휴가 and confirmed on the live page |
| 7 | Embedding factory is the single, lazy, quiet source of embeddings; captures leak nothing | VERIFIED | `git grep HuggingFaceEmbeddings(` → only `shared/config.py`; `LAZY_OK`; `check_leaks.py` → `CLEAN`; no ids/timings/paths/`0x` in any `.out` |
| 8 | All chapters pass format gate; no Phase 1/2 regression | VERIFIED | `check_book.py --html` → 10× PASS; `mdbook build` → 0 ERROR; all 10 scratch re-captures byte-identical to committed `.out` |
| 9 | Reproducibility gate honored (identical/wording-only pass, structural stop) | VERIFIED | Full scratch rerun of all 10 examples: 10× OK, all byte-identical (including the LLM-driven `03_rag_chain.out`) |
| 10 | Pushed HEAD deployed; all 10 chapter pages + TOC + pointers live | VERIFIED | `gh run view` for HEAD SHA `2d3a520...` → `conclusion: success`; all 10 chapter pages, `toc.html`, `introduction.html`, `ch02_tools/02_tool_loop.html` return 200 with expected content; 404 for nonexistent path |

**Score:** 10/10 truths verified (truth 6 closed after prose fix)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `examples/shared/config.py` `get_embeddings()` | Single lazy factory | VERIFIED | `ANCHOR: embeddings` region present; lazy `torch`/`langchain_huggingface` import confirmed (`LAZY_OK`) |
| `examples/data/ch03_rag/*.md` (3 docs) | Original Korean docs, handbook facts fixed | VERIFIED | Read all 3; original, non-overlapping, fiction disclaimer in handbook, no PII/real-org content, contain 재택근무/연차/교육/노트북 facts |
| `examples/ch03_rag/01_load_split.py` | RAG-01 example | VERIFIED | `RecursiveCharacterTextSplitter` used, repo-relative `source` metadata |
| `examples/ch03_rag/02_embed_search.py` | RAG-02/03 example | VERIFIED | `similarity_search_with_score`, ephemeral `Chroma.from_documents` (no `persist_directory`) |
| `examples/ch03_rag/03_rag_chain.py` | RAG-04 example | VERIFIED | `RunnablePassthrough`, LCEL chain, retriever + format_docs |
| `outputs/ch03_rag/*.out` (3 files) | Captured real output | VERIFIED | Present, key-count 0, no Traceback/`0x`/absolute paths, byte-identical on scratch re-run |
| `book/src/ch03_rag/*.md` (3 chapters) | Chapters with includes | VERIFIED | Correct `{{#include}}` lines, 4-heading format, `check_book.py` PASS |
| `book/src/SUMMARY.md` | 3부 RAG with 3 links | VERIFIED | `# 3부 RAG` present with all 3 chapter links, live in `toc.html` |
| `book/src/introduction.md` | Journey pointer to 3부 | VERIFIED | Links to `ch03_rag/01_load_split.md`, confirmed live |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `02_embed_search.py`/`03_rag_chain.py` | `shared/config.py get_embeddings` | `from shared.config import get_embeddings` | WIRED | Confirmed via grep; only file constructing `HuggingFaceEmbeddings(` is `shared/config.py` |
| `get_embeddings()` | `langchain_huggingface.HuggingFaceEmbeddings` | function-local import after env-var setdefault | WIRED | Confirmed noise-suppression env vars set before import; no progress-bar text in any `.out` |
| `02_embed_search.py`/`03_rag_chain.py` | `langchain_chroma.Chroma` (ephemeral) | `Chroma.from_documents(...)` no `persist_directory` | WIRED | `git grep persist_directory` → only a comment; no Chroma/sqlite artifacts in `git status --porcelain --ignored` |
| `03_rag_chain.py` | Chroma retriever | `retriever \| format_docs` in chain dict | WIRED | `.out` section 2/3 show retrieval→prompt injection→chain answer |
| `git push origin main` | GitHub Pages | `deploy.yml` Actions run for pushed HEAD | WIRED | Run `34581342990` for HEAD `2d3a520...` succeeded; all pages live |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|---|---|---|
| RAG-01 (load/split, real output) | SATISFIED | none |
| RAG-02 (bge-m3 mps embedding, real output) | SATISFIED | none |
| RAG-03 (Chroma Korean-query search, real output) | SATISFIED | none |
| RAG-04 (LCEL RAG chain, real Korean answer) | SATISFIED | none (the section-4 prose mislabel does not affect the chain's actual answer, which is correct and verified) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `book/src/ch03_rag/03_rag_chain.md` | section "=== 4 ===" interpretation paragraph | Prose names wrong retrieved-chunk topics vs. actual `.out` | Warning — RESOLVED in 354a83e | Misleads readers about which document sections the retriever returned for the out-of-scope question; does not affect the model's actual (correct) answer or any code/data artifact |

### Human Verification Required

None. All must-haves in this phase are mechanically verifiable from captured `.out` files, chapter markdown, live HTML, and Actions status — no visual/subjective judgment required beyond the factual cross-check performed above.

### Regression Check (Phase 1 / Phase 2)

- `check_book.py --html book/book` → 10× PASS (5 ch01_basics + 2 ch02_tools + 3 ch03_rag), exit 0.
- Fresh `mdbook build book` → 0 ERROR/WARN.
- Full scratch rerun of all 10 examples (`scripts/run_examples.py`, no targets) → 10× `OK`; every scratch `.out` byte-identical to its committed counterpart (diff exit 0), including all 5 ch01 and both ch02 files.
- All 7 ch01/ch02 live pages (`ch01_basics/01..05`, `ch02_tools/01..02`) return HTTP 200 with real captured content, no `{{#include` leakage, no stub marker.
- `git status --porcelain` remained clean throughout verification; no Chroma/sqlite/parquet artifacts appeared.
- `LITELLM_API_KEY` never printed; all key-count checks on scratch/committed `.out` files returned 0.

### Gate Re-checks

- `scripts/check_leaks.py outputs book/src examples book/book .planning/phases/03-rag` → `CLEAN`
- `scripts/test_masking.py` → 15 passed
- Single-factory invariants: `HuggingFaceEmbeddings(` only in `shared/config.py`; `ChatOpenAI(` only in `shared/config.py`; `@tool` only in `shared/tools.py`; no `persist_directory=` anywhere in `examples`
- `git rev-parse HEAD` == the `headSha` of the latest successful `deploy.yml` Actions run (`34581342990`, conclusion `success`)

## Gaps Summary

Phase 3's RAG pipeline is genuinely working end-to-end and reproducibly: all three chapters' captured `.out` files are accurate, byte-identical on re-run (including the LLM-driven chain answer), correctly wired to the single `get_embeddings()`/`get_chat_model()` factories, leak-free, and live on the deployed site with no regression to Phase 1/2 pages.

One content-accuracy defect was found: in `book/src/ch03_rag/03_rag_chain.md`, the "실제 출력" interpretation of section 4 (the out-of-scope 주차 question) names the two retrieved chunks as "업무 장비, 재택근무" when the actual captured chunks (by `start_index`) are 교육 지원 (664) and 연차 휴가 (164). This is a one-sentence factual correction in the chapter prose — it does not require re-capturing any `.out` file, re-running any example, or touching code/data, since the underlying capture and the chain's actual answer are both correct. Recommended fix: edit the sentence in `book/src/ch03_rag/03_rag_chain.md`'s section-4 interpretation to say "교육 지원, 연차 휴가" instead of "업무 장비, 재택근무", then rebuild/re-check `check_book.py` and re-push.

## Gap Closure (orchestrator, 2026-09-11)

- Cross-checked `outputs/ch03_rag/03_rag_chain.out` section 4 against the handbook section offsets: `start_index=664` begins `## 교육 지원` (chunk body = education support, trailing `## 업무 장비` header only) and `start_index=164` begins `## 연차 휴가`. Confirmed with the same splitter settings (`chunk_size=300, chunk_overlap=50`), no LLM call.
- Edited the one sentence in `book/src/ch03_rag/03_rag_chain.md` to name `start_index=664`의 교육 지원 조각 and `start_index=164`의 연차 휴가 조각. No `.out`, example, or data file changed.
- Re-ran: `mdbook build book` → 0 ERROR/WARN; `check_book.py --html book/book` → PASS; `check_leaks.py outputs book/src examples` → CLEAN; key count in commit → 0.
- Pushed `354a83e`; Actions run `34581971258` → success; live `ch03_rag/03_rag_chain.html` contains the corrected text and no longer contains the old wording.

---

*Verified: 2026-09-11T08:58:00Z*
*Verifier: Claude (gsd-verifier)*
