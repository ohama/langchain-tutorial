---
phase: 03-rag
plan: 01
subsystem: rag
tags: [langchain-text-splitters, langchain-chroma, langchain-huggingface, sentence-transformers, bge-m3, chroma, embeddings]

# Dependency graph
requires:
  - phase: 01-book-infra-basics (plan 01-01)
    provides: "examples/shared/config.py chat-model factory pattern (lazy ANCHOR regions, dotenv loading), scripts/run_examples.py capture runner, scripts/check_book.py format gate, scripts/check_leaks.py leak scanner"
  - phase: 02-tool-calling (plan 02-01)
    provides: "Proven single-plan whole-phase pattern, reproducibility-rerun gate style, shared-module ANCHOR convention"
provides:
  - "examples/shared/config.py get_embeddings(): single lazy factory for BAAI/bge-m3 (langchain_huggingface.HuggingFaceEmbeddings), device auto-detect (mps/cpu), normalize_embeddings=True, noise-suppression env vars set before import"
  - "examples/data/ch03_rag/*.md: three original Korean documents (LangChain concepts, RAG guide, fictional company handbook) with fixed handbook facts (연차 15일, 재택근무 주 2일, 교육비 100만원, 노트북 3년) for 03-02's RAG chain to reuse"
  - "Chapter 3-1 (문서 로딩과 분할): real Document loading + RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50, add_start_index=True) capture"
  - "Chapter 3-2 (임베딩과 벡터스토어 검색): real bge-m3 embeddings (1024-dim, mps) + ephemeral Chroma index + 3 Korean-query similarity_search_with_score capture"
  - "Chunk parameters, sample documents and get_embeddings() are frozen stable inputs for 03-02's LCEL RAG chain"
affects: [phase-3-plan-02]

# Tech tracking
tech-stack:
  added: [langchain-text-splitters 1.1.2, langchain-chroma 1.1.0, langchain-huggingface 1.2.2, sentence-transformers 6.0.1, torch 2.14.0 (transitive), chromadb 1.5.9 (transitive)]
  patterns:
    - "get_embeddings() mirrors get_chat_model(): single factory, dataclass-free, **overrides passthrough, function-local heavy imports so ch01/ch02 never load torch"
    - "Ephemeral Chroma: Chroma.from_documents(chunks, embedding=..., collection_name=...) with no persist_directory, rebuilt from scratch by every example script"

key-files:
  created:
    - examples/data/ch03_rag/01_langchain_intro.md
    - examples/data/ch03_rag/02_rag_guide.md
    - examples/data/ch03_rag/03_company_handbook.md
    - examples/ch03_rag/01_load_split.py
    - examples/ch03_rag/02_embed_search.py
    - outputs/ch03_rag/01_load_split.out
    - outputs/ch03_rag/02_embed_search.out
    - book/src/ch03_rag/01_load_split.md
    - book/src/ch03_rag/02_embed_search.md
  modified:
    - examples/pyproject.toml
    - examples/uv.lock
    - examples/shared/config.py
    - examples/.env.example
    - book/src/SUMMARY.md
    - book/src/ch01_basics/01_chat_model.md

key-decisions:
  - "get_embeddings() calls load_dotenv(ENV_PATH, override=False) itself (per plan's correction to research Pattern 1), so EMBEDDING_* values in examples/.env are honored even when the caller never touched shared.config's load_settings()"
  - "Kept the plan-specified import order in 02_embed_search.py (langchain_chroma before shared.config) after empirically disproving the plan's noise-contingency hypothesis — see Deviations"

# Metrics
duration: ~35min
completed: 2026-09-11
---

# Phase 3 Plan 01: RAG Retrieval Foundation (Loading, Splitting, Embedding, Search) Summary

**`get_embeddings()` factory for local BAAI/bge-m3 on MPS, three original Korean sample documents, and two real-captured chapters covering document loading/chunking and embedding/Chroma search — all three Korean test queries retrieve their intended source document.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-09-11T08:05:00Z (approx, context load)
- **Completed:** 2026-09-11T08:42:00Z
- **Tasks:** 3/3
- **Files modified:** 15 (9 created, 6 modified)

## Accomplishments

- Added 4 RAG dependencies (`langchain-text-splitters`, `langchain-chroma`, `langchain-huggingface`, `sentence-transformers`) via `uv add`; resolved versions match the phase research exactly: `langchain-core 1.6.2`, `langchain-text-splitters 1.1.2`, `langchain-chroma 1.1.0`, `langchain-huggingface 1.2.2`, `sentence-transformers 6.0.1`, `torch 2.14.0`, `chromadb 1.5.9`. `uv lock --project examples --check` passed (resolved 148 packages).
- `examples/shared/config.py` gained a fourth ANCHOR region, `get_embeddings()`, matching the plan's exact spec: lazy `torch`/`langchain_huggingface` import, noise-suppression env vars set before that import, device auto-detect (`mps` on this machine), `normalize_embeddings=True`. Lazy-import invariant verified live (`import shared.config` does not pull in `torch` or `langchain_huggingface`).
- Wrote three original Korean documents (1105–1290 chars each, all forbidden-substring checks clean): a LangChain concepts note, a RAG guide, and a fictional company handbook with the exact facts 03-02 will need (연차 휴가 15일/2년차부터, 재택근무 주 2일/수요일 예외, 교육비 연 100만원, 노트북 3년 교체) — no mention of parking/meals/gym/salary.
- Chapter 3-1 (문서 로딩과 분할): real capture shows 3 documents → 17 chunks (7/5/5 per document), all ≤ 300 chars, `start_index` tracked per chunk, and a worked overlap example (0 characters of actual overlap at a clean paragraph boundary, explained in prose as a target-not-guarantee of `chunk_overlap`).
- Chapter 3-2 (임베딩과 벡터스토어 검색): real capture shows `BAAI/bge-m3` on `mps`, 1024 dimensions, L2 norm `1.0000`, a similar-meaning sentence pair (cosine `0.8970`) clearly outscoring an unrelated pair (`0.3243`), an ephemeral 17-chunk Chroma index, and all three Korean queries retrieving their intended source document as rank 1 on the first attempt (no rule-8 query revision needed).
- Independently verified that Chroma's `similarity_search_with_score` distance equals `2 − 2×cosine similarity` (squared Euclidean distance between unit vectors) by re-embedding a query and its rank-1 chunk and comparing to the captured score — matched to 4 decimals (`0.5286` both ways). The chapter prose asserts this relationship.
- Early determinism gate (rule 9): a full scratch rerun of both examples via `run_examples.py --outputs-dir $SCRATCH/early` produced byte-identical `.out` files against the committed ones (`diff` exit 0 for both) — no flake, no rule-9 handling needed.
- 9 chapters (5 ch01 + 2 ch02 + 2 ch03) pass `check_book.py --html` and a fresh `mdbook build` produced 0 ERROR lines. `book/src/ch01_basics/01_chat_model.md` now explains the new optional `EMBEDDING_MODEL`/`EMBEDDING_DEVICE` lines.

## Task Commits

Each task was committed atomically:

1. **Task 1: RAG dependencies, get_embeddings() factory, .env.example section, Korean sample documents** - `4b34747` (feat)
2. **Task 2: Chapter 3-1 (문서 로딩과 분할) + 3부 in SUMMARY** - `170e1e1` (feat)
3. **Task 3: Chapter 3-2 (임베딩과 벡터스토어 검색) + 1부 1장 note + early determinism check** - `2041ea0` (feat)

**Plan metadata commit:** this SUMMARY.md (committed alongside plan completion; STATE.md/ROADMAP.md remain the orchestrator's responsibility)

Not pushed — this plan commits locally only; 03-02 pushes after the whole-phase gate.

## Files Created/Modified

- `examples/pyproject.toml`, `examples/uv.lock` — 4 new RAG dependencies locked
- `examples/shared/config.py` — new `get_embeddings()` ANCHOR region (additive; docstring updated to mention embeddings)
- `examples/.env.example` — new optional `EMBEDDING_MODEL`/`EMBEDDING_DEVICE` section
- `examples/data/ch03_rag/01_langchain_intro.md`, `02_rag_guide.md`, `03_company_handbook.md` — original Korean sample documents
- `examples/ch03_rag/01_load_split.py` — RAG-01: `pathlib` → `Document` → `RecursiveCharacterTextSplitter`
- `examples/ch03_rag/02_embed_search.py` — RAG-02/RAG-03: `get_embeddings()` → `Chroma.from_documents` (ephemeral) → `similarity_search_with_score`
- `outputs/ch03_rag/01_load_split.out`, `02_embed_search.out` — real captures via `scripts/run_examples.py`
- `book/src/ch03_rag/01_load_split.md`, `02_embed_search.md` — new chapters, exact 4-heading template, include-only code blocks
- `book/src/SUMMARY.md` — new `# 3부 RAG` part with both chapter links, inserted before `# 부록`
- `book/src/ch01_basics/01_chat_model.md` — one new paragraph noting the optional `EMBEDDING_*` `.env` lines

## Decisions Made

- `get_embeddings()` calls `load_dotenv(ENV_PATH, override=False)` itself (the plan's explicit correction to the phase research's Pattern 1 snippet), so `EMBEDDING_*` values in `examples/.env` are read even if the caller never invoked `load_settings()` first.
- Kept the plan's literally-specified import order in `02_embed_search.py` (`langchain_chroma` imported before `shared.config`) rather than applying the plan's suggested "noise contingency" reorder — see Deviations for why the reorder was empirically shown not to change behavior.

## Deviations from Plan

### Investigated, no code change needed

**1. Progress-bar noise on stderr during `Chroma.from_documents`, contingency's proposed fix does not actually work**

- **Found during:** Task 3, capturing `02_embed_search.py`
- **What happened:** The plan's stated trigger ("if the `.out` contains progress-bar text") did not fire — the committed `.out` file has zero occurrences of `it/s]`/`Loading weights`/`%|` (verified by grep, both on the initial capture and the early-determinism rerun). However, `Loading weights: 100%|...` did appear on **stderr** (which `run_examples.py` never writes into `.out`), specifically only when `Chroma.from_documents(...)` was called — not merely from importing `langchain_chroma`, and not from `get_embeddings()`/`embed_query()`/`embed_documents()` alone (isolated scratch tests confirmed zero stderr from those).
- **Root-cause check:** I tested the plan's proposed fix (moving `from shared.config import get_embeddings` above the `langchain_chroma` import) in isolation. It made **no difference** — the same stderr noise appeared regardless of import statement order, because the import statements all execute before any function call regardless of their relative order, and the trigger is specifically the `Chroma.from_documents` call re-touching the embedding pipeline, not import ordering.
- **Decision:** Since the plan's actual required invariant ("captured `.out` files contain no progress bars") already holds without any change, and the plan's suggested fix was empirically shown not to address the real trigger, I did not apply the reorder — it would be a no-op that misrepresents the cause in the code comment. Import order in `02_embed_search.py` matches the plan's literal specification (`math`, `Path`, `Chroma`, `Document`, `RecursiveCharacterTextSplitter`, `get_embeddings`).
- **Files:** none changed as a result (informational only)
- **Verification:** `grep -cE "it/s\]|Loading weights|%\|" outputs/ch03_rag/02_embed_search.out` → `0` (both the committed capture and the early-determinism scratch rerun)

---

**Total deviations:** 0 code changes; 1 investigated non-issue documented above for transparency (the plan's own contingency clause anticipated exactly this class of noise, so this is expected troubleshooting, not scope creep).
**Impact on plan:** None — no files changed beyond the plan's own scope.

## Issues Encountered

None. Both captures were meaningful on the first `run_examples.py` run: chapter 3-1's chunk split produced ≥2 chunks per document and all chunks ≤300 chars on the first try; chapter 3-2's three Korean queries all retrieved their intended document as rank 1 on the first try, and the similar/different sentence-pair contrast was clear on the first try. No rule-8 query or sentence revisions were needed at any point.

## User Setup Required

None — reused the same `examples/.env` (git-ignored) and shell `LITELLM_API_KEY`; the new `EMBEDDING_MODEL`/`EMBEDDING_DEVICE` settings are optional and work correctly when left unset (auto-detected `mps` on this machine). `BAAI/bge-m3` was already present in the local Hugging Face cache, so no first-run download was observed in this session (smoke-test/capture timings reflect a warm cache).

## Reproducibility Result

Both examples in this plan are LLM-free. Early determinism check (rule 9, run during Task 3): `run_examples.py ch03_rag/01_load_split.py ch03_rag/02_embed_search.py --no-warmup --outputs-dir $SCRATCH/early`, then `diff` against the committed `.out` files — **byte-identical** for both (`diff` exit 0, zero output). No flake, no rule-9 fallback needed.

## Detailed Capture Facts (for 03-02)

**Chunking (chapter 3-1):** `chunk_size=300, chunk_overlap=50, add_start_index=True` over the 3 committed sample documents (1290/1211/1105 chars) → **17 chunks total** (`01_langchain_intro.md`: 7, `02_rag_guide.md`: 5, `03_company_handbook.md`: 5). Max chunk length observed: 295 chars. Section 3's worked overlap example (first two chunks of `01_langchain_intro.md`) showed **0 characters of actual overlap** — the splitter found a clean `\n\n` paragraph boundary right at the target cut point, so no extra characters were pulled in from the neighboring chunk even though `chunk_overlap=50` was requested. Verified default separator order for this splitter version: `['\n\n', '\n', ' ', '']` (no `". "` separator in this release, differing slightly from the phase research's guess).

**Embedding (chapter 3-2):** device `mps`, dimension `1024`, L2 norm `1.0000`. Similarity(기준, 비슷한 뜻) = `0.8970`; similarity(기준, 다른 주제) = `0.3243`. Index count = chunk count = `17`.

**Search results (rank-1 per query):**
| Query | Rank-1 source | Distance |
|---|---|---|
| "LCEL에서 파이프 연산자는 어떤 역할을 하나요?" | `01_langchain_intro.md` | `0.7067` |
| "문서를 자를 때 청크를 겹치게 만드는 이유는?" | `02_rag_guide.md` | `0.7570` |
| "연차 휴가는 1년에 며칠 받을 수 있나요?" | `03_company_handbook.md` | `0.5286` |

**Distance formula check:** re-embedded the third query and its rank-1 chunk independently, computed `2 − 2×cosine`, got `0.5286` — matches the captured score to 4 decimals. The chapter prose asserts Chroma's `similarity_search_with_score` distance is squared Euclidean distance between unit-normalized vectors (equivalently `2 − 2×cosine similarity`), smaller is closer.

**Handbook facts frozen for 03-02** (from `examples/data/ch03_rag/03_company_handbook.md`, unchanged since Task 1's commit): 연차 휴가 첫해 개근 월 1일(최대 11일)/2년차부터 15일, 신청은 사용 3일 전까지; 재택근무 주 2일까지, 전날 오후 6시까지 팀 채널 신청, 수요일은 전원 출근; 교육 지원 연 100만원 한도(도서/온라인 강의); 노트북 3년마다 교체. The handbook does **not** mention parking, meals, gyms or salary — 03-02 can safely use a parking question as its "not in the documents" test case.

## Next Phase Readiness

- `get_embeddings()`, the three sample documents, and the chunking parameters (`chunk_size=300, chunk_overlap=50, add_start_index=True`) are stable, committed inputs. 03-02 should reuse `load_documents()`/chunking verbatim (as this plan's `02_embed_search.py` already does, copied from `01_load_split.py`) so its LCEL RAG chain indexes the exact same 17 chunks.
- No blockers. The whole-phase release gate (reproducibility rerun, `check_book.py` 9x PASS, 0 mdbook ERROR, leak scans CLEAN, git hygiene) has already been dry-run at the plan level here; 03-02 should repeat the full 7-step gate from the phase research (adding the new `03_rag_chain` chapter) before pushing.
- One open item carried into 03-02 (not a blocker): the plan's "noise contingency" reorder for `02_embed_search.py` was investigated and found not to change behavior (see Deviations) — 03-02's `03_rag_chain.py` may see the same benign stderr-only `Loading weights` line from its own `Chroma.from_documents` call; this does not affect `.out` captures and needs no fix.

---
*Phase: 03-rag*
*Completed: 2026-09-11*
