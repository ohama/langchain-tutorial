---
phase: 01-book-infra-basics
verified: 2026-09-11T07:18:10Z
status: passed
score: 5/5 must-haves verified
---

# Phase 1: Book Infra + Basics Verification Report

**Phase Goal:** 독자는 GitHub Pages에 배포된 한국어 mdBook에서, 저자가 실제로 실행하고 캡처한 출력이 실린 기초 챕터(채팅 모델 호출~구조화 출력)를 읽을 수 있다. 이 페이즈에서 챕터 저작 파이프라인 전체가 한 번 끝까지 검증되어야 이후 모든 챕터가 같은 그릇을 재사용할 수 있다.

**Verified:** 2026-09-11T07:18:10Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GitHub Pages URL에 목차·챕터·부록 구조를 갖춘 한국어 mdBook 사이트가 뜬다 (INFRA-01) | VERIFIED | `curl https://ohama.github.io/langchain-tutorial/` -> 200; `toc.html` contains `1부 기초` and `부록`; all 5 chapter pages + `introduction.html` + `appendix/about.html` return 200; sidebar structure matches `book/src/SUMMARY.md` |
| 2 | main push -> GitHub Actions builds mdBook (no LLM call) and deploys to Pages (INFRA-02) | VERIFIED | `.github/workflows/deploy.yml` only installs pinned `mdbook v0.5.3` and runs `mdbook build book`; no python/uv/LLM step. `gh run list` shows 4/4 recent runs `completed success`; latest run headSha (`ba8dfe8...`) matches local+remote `main` HEAD. Workflow greps build log for `ERROR` and exits 1 if found — verified by re-running `mdbook build book` locally: 0 ERROR/WARN lines |
| 3 | `.env.example`만 바꾸면 `shared/config.py`를 경유하는 모든 예제가 그대로 실행된다 (INFRA-03/04) | VERIFIED | `examples/pyproject.toml` is an installable hatchling package (`packages=["shared"]`); `import shared.config` succeeds from a directory outside the repo via `examples/.venv/bin/python` (no sys.path hacks). `get_chat_model`/`get_structured_model` read only `LLM_BASE_URL/LLM_MODEL/LLM_API_KEY` via `load_dotenv(ENV_PATH)`. `get_structured_model` always calls `with_structured_output(schema, method="function_calling", strict=False)` (code-read confirmed, and Chapter 5's captured `.out` shows the default method failing with HTTP 500 while `function_calling` succeeds) |
| 4 | 명령 한 번으로 예제를 실행하면 `.out`이 생성되고 API 키/로컬 절대경로가 자동 마스킹된다 (INFRA-05/06) | VERIFIED | Ran `scripts/run_examples.py ch01_basics/01_chat_model.py --outputs-dir <scratch>` end-to-end (warm-up + live LLM call): produced `.out` byte-identical to the tracked capture (temperature=0), starting with `# source-sha256:` matching `shasum -a256` of the source `.py`. Built and ran a deliberate leak-probe example printing the real API key, a `Bearer <key>` string, an `sk-...` token and a home-relative path: masked output had zero key occurrences (`***MASKED_API_KEY***`, `sk-***MASKED***`) and home path rewritten to `~/...`. Built a deliberate failing example: runner exited 1, wrote no `.out`, and did not print the pre-exception stdout (so no key literal reached the terminal). Cleaned up scratch files; `git status --porcelain` empty afterward |
| 5 | 기초 챕터 5개가 `{{#include}}`로만 코드·출력을 불러오고 개념→코드→출력→요점 형식을 따른다 (INFRA-07/08, BASIC-01..05) | VERIFIED | `scripts/check_book.py --html book/book`: `PASS` x5 (headings in exact order, every python/text/ini code fence is a single `{{#include ...}}` line, `.out` includes use `:2:`, no stub marker, rendered HTML has no leftover `{{#include`). Manually re-verified `## ` heading order in all 5 `.md` files. Content spot-checked against captured `.out` for chapters 1, 2, 4, 5 — prose accurately describes genuinely LLM-shaped output (token counts, stream chunk counts, multi-turn memory contrast, real `HTTP 500` for the deliberate structured-output anti-pattern in ch.5) |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `examples/pyproject.toml` | installable uv project, `packages=["shared"]` | VERIFIED | hatchling build-backend, `[tool.hatch.build.targets.wheel] packages = ["shared"]` present |
| `examples/shared/config.py` | model factory (settings/chat_model/structured ANCHORs) | VERIFIED | 51 lines, all 3 ANCHOR regions present, `function_calling` present, no stub patterns, imported by all 5 chapter examples |
| `examples/.env.example` | reader config template | VERIFIED | tracked, `LLM_API_KEY=` blank, `LLM_BASE_URL=http://127.0.0.1:4000/v1` present |
| `scripts/masking.py` | collect_secrets/mask_text/find_leaks | VERIFIED | imported and exercised live via probe example; 15/15 unit tests pass |
| `scripts/test_masking.py` | pytest unit tests | VERIFIED | `pytest scripts/test_masking.py` -> 15 passed |
| `scripts/check_leaks.py` | CLI leak scanner | VERIFIED | ran against `outputs book/src examples`, tracked files (`--secrets-only`), and full git history (`git log -p --all | ... -`) — all `CLEAN` |
| `scripts/run_examples.py` | warm-up+run+mask+capture runner | VERIFIED | 190 lines; live end-to-end run reproduced a tracked `.out` byte-for-byte; leak-probe and failure-probe scenarios both behaved correctly |
| `.gitignore` | ignores secrets/venv/build/tooling | VERIFIED | `.env`, `.venv/`, `book/book/`, `.claude/` all present; `git ls-files` confirms none of these paths are tracked |
| `book/book.toml` | mdBook config, ko, site-url | VERIFIED | `language = "ko"`, `create-missing = false`, `site-url = "/langchain-tutorial/"` |
| `book/src/SUMMARY.md` | final TOC (intro, 1부 기초 x5, 부록) | VERIFIED | matches live `toc.html` exactly |
| `book/src/introduction.md` | Korean intro | VERIFIED | 36 lines (>= 25 min) |
| `.github/workflows/deploy.yml` | Pages build+deploy workflow | VERIFIED | `actions/deploy-pages@v5`, `mdbook build book`, no Python/uv/LLM steps; 4/4 recent runs green |
| `README.md` | repo landing doc | VERIFIED | book URL, layout, run/capture/leak-check/preview commands all present and accurate |
| `scripts/check_book.py` | chapter structure + include-only + HTML gate | VERIFIED | 60+ lines, non-trivial regex-based checker (headings, include-only fences, anchor rules, stub marker, HTML sanity); ran independently, all 5 chapters PASS |
| `examples/ch01_basics/0{1..5}_*.py` | BASIC-01..05 examples | VERIFIED | all import only `from shared.config import get_chat_model`/`get_structured_model`; contain the required API usage (`SystemMessage`, `FewShotChatMessagePromptTemplate`, `RunnableParallel`, `get_structured_model`) |
| `outputs/ch01_basics/0{1..5}_*.out` | captured real output | VERIFIED | all 5 start with `# source-sha256:` matching current source hash (proves outputs are tied to committed code and not hand-edited); content reads as genuine LLM output (token usage dicts, chunk counts, real error status codes) |
| `book/src/ch01_basics/0{1..5}_*.md` | 5 chapters | VERIFIED | each replaces the stub, passes `check_book.py`, live and matches `.out` content |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `shared/config.py` | `examples/.env` | `load_dotenv(ENV_PATH)` from `__file__` | WIRED | Confirmed by code read; `ENV_PATH = EXAMPLES_DIR / ".env"`, independent of cwd |
| `run_examples.py` | `masking.py` | `mask_text`/`find_leaks` before write/print | WIRED | Live-verified via leak-probe and failure-probe runs above |
| `run_examples.py` | `shared/config.py` | warm-up via `get_chat_model()` | WIRED | Live warm-up ("warm-up: 2.1s") observed in scratch run |
| `check_leaks.py` | `masking.py` | reuses `collect_secrets`/`find_leaks` | WIRED | `CLEAN` results across 3 independent invocations |
| `deploy.yml` | `book/` | `mdbook build book` + `upload-pages-artifact path book/book` | WIRED | Confirmed in workflow file and by successful live deploys |
| `book.toml` | live Pages URL | `site-url = "/langchain-tutorial/"` | WIRED | CSS assets resolve with 200 under `/langchain-tutorial/` on both chapter pages (relative `../css/`) and the 404 page (relative `css/`) |
| GitHub repo settings | `deploy.yml` | Pages `build_type=workflow` | WIRED | `gh api repos/ohama/langchain-tutorial/pages` -> `"build_type": "workflow"`, `public: true` |
| `book/src/ch01_basics/0N_*.md` | `examples/...py` + `outputs/...out` | `{{#include}}` only | WIRED | `check_book.py` PASS x5; manual grep of `## ` headings confirms exact order |
| `examples/ch01_basics/*.py` | `examples/shared/config.py` | `from shared.config import get_chat_model` | WIRED | `git grep "ChatOpenAI("` in `examples` (excluding `.venv`) returns exactly one hit, inside `shared/config.py` — no example bypasses the factory |
| `outputs/ch01_basics/*.out` | `run_examples.py` | sha256 header line 1 | WIRED | All 5 `.out` files' header hash matches `shasum -a256` of their corresponding `.py` (proves generation-by-runner, not hand-editing) |
| `05_structured_output.py` | `shared/config.py` | `get_structured_model(Person)` | WIRED | Captured output shows both the `function_calling` success path and the default-method HTTP 500 failure, matching chapter prose exactly |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|-----------------|
| INFRA-01 | SATISFIED | — |
| INFRA-02 | SATISFIED | — |
| INFRA-03 | SATISFIED | — |
| INFRA-04 | SATISFIED | — |
| INFRA-05 | SATISFIED | — |
| INFRA-06 | SATISFIED | — |
| INFRA-07 | SATISFIED | — |
| INFRA-08 | SATISFIED | — |
| BASIC-01 | SATISFIED | — |
| BASIC-02 | SATISFIED | — |
| BASIC-03 | SATISFIED | — |
| BASIC-04 | SATISFIED | — |
| BASIC-05 | SATISFIED | — |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `book/src/appendix/about.md` | 3 | `(준비 중)` — appendix content is a stated placeholder for future topics (Ollama setup, uv env) | ℹ️ Info | Not a blocker: Phase 1's success criteria only require the appendix *section* to exist in the TOC and load (INFRA-01, verified — page returns 200 and appears in sidebar). Full appendix content is out of Phase 1's scope (BASIC-01..05 cover chapters only); this is an intentional forward-reference, not a stub masquerading as complete content |

No blocker or warning-level anti-patterns found in any file touched by this phase's `must_haves` (examples/, scripts/, book/src/ch01_basics/, .github/). No TODO/FIXME/HACK comments anywhere in scope.

### Human Verification Required

None. All must-haves were verifiable programmatically: unit tests, static analysis (grep/hash/structure checks), a real end-to-end LLM call through the pipeline into a scratch directory, live HTTP checks against the deployed GitHub Pages site, and `gh` API/CLI checks against the live repo and Actions history.

### Gaps Summary

No gaps. All 5 derived observable truths (mapped 1:1 to the phase's 5 stated success criteria) are verified against the live codebase, the live GitHub Pages site, and the live GitHub repo — not just SUMMARY claims. Independently reproduced evidence for every must-have across all 4 plans (01-01 through 01-04):

- Ran the actual test suites and leak scanners rather than trusting reported results (`pytest` 15/15, `check_leaks.py` CLEAN x3 including full git history, `check_book.py` PASS x5, fresh `mdbook build` 0 errors).
- Performed a live LLM round-trip through `scripts/run_examples.py` into a scratch outputs directory, confirming byte-identical reproducibility against the committed `.out` (temperature=0) and confirming the sha256 provenance header ties every tracked `.out` to its current source file.
- Constructed and ran two adversarial probe examples (real-key/Bearer/sk-token/home-path leak, and a hard failure) to confirm masking and non-write-on-failure behavior described in the must-haves actually holds, not just that the code looks like it should.
- Verified the live site structurally (sidebar TOC, sub-path CSS resolution, 404 handling) and content-wise (each chapter page contains `html.unescape`d text from its own `.out`, no leftover `{{#include` or stub markers).
- Verified GitHub-side state directly via `gh api`/`gh run list`: Pages `build_type=workflow`, all 4 relevant Actions runs `completed`/`success`, latest run's `headSha` equals local `main` HEAD.
- Cleaned up all scratch/probe artifacts; `git status --porcelain` was empty both before and after verification — no working-tree changes were introduced.

---

*Verified: 2026-09-11T07:18:10Z*
*Verifier: Claude (gsd-verifier)*
