---
phase: 01-book-infra-basics
plan: 01
subsystem: infra
tags: [uv, hatchling, langchain-openai, python-dotenv, pytest, secret-masking]

# Dependency graph
requires: []
provides:
  - "Installable `examples/` uv package (hatchling, packages=[\"shared\"]) importable from any cwd or execution mode"
  - "examples/shared/config.py: single chat-model factory (load_settings, get_chat_model, get_structured_model) with ANCHOR regions for book includes"
  - "examples/.env.example template (LLM_BASE_URL, LLM_MODEL, LLM_API_KEY) and author's local examples/.env (git-ignored, key value never on disk as literal)"
  - "scripts/masking.py: collect_secrets, mask_text, find_leaks (stdlib only)"
  - "scripts/check_leaks.py: CLI leak scanner for files/dirs/stdin"
  - "scripts/run_examples.py: warm-up + run + mask + .out capture runner"
  - "Root .gitignore covering secrets, venvs, build output, .claude/"
affects: [01-03, 01-04, phase-2, phase-3, phase-4, phase-5]

# Tech tracking
tech-stack:
  added: [langchain, langchain-core, langchain-openai, langgraph (transitive), langsmith (transitive), python-dotenv, pydantic, pytest]
  patterns:
    - "examples/ is a hatchling-built installable package (packages=[\"shared\"]) instead of sys.path hacks"
    - "shared/config.py is the single point where a chat model is constructed; chapters include it only via ANCHOR regions"
    - "get_structured_model always pins with_structured_output(method=\"function_calling\", strict=False) for the local server"
    - "Every terminal print in run_examples.py passes through mask_text before it reaches stdout/stderr"
    - "Secrets are masked by literal value first (collect_secrets), then by regex fallback (sk-, Bearer), then home path"

key-files:
  created:
    - .gitignore
    - examples/pyproject.toml
    - examples/uv.lock
    - examples/.python-version
    - examples/.env.example
    - examples/shared/__init__.py
    - examples/shared/config.py
    - scripts/masking.py
    - scripts/test_masking.py
    - scripts/check_leaks.py
    - scripts/run_examples.py
  modified: []

key-decisions:
  - "examples/.env is created locally (git-ignored) with the literal text LLM_API_KEY=${LITELLM_API_KEY}; python-dotenv expands ${VAR} from the environment at load time, so the real key value is never written to disk"
  - "masking.py's generic path regexes require a word-char immediately after /Users/ and /home/ (not just any non-slash char), so scanning masking.py's own pattern definitions and comments doesn't self-trigger a false leak finding"

patterns-established:
  - "Runner CLI: uv run --project examples python scripts/run_examples.py [TARGET ...] [--outputs-dir DIR] [--timeout SEC] [--no-warmup], writing examples/<rel>/<stem>.py -> <outputs-dir>/<rel>/<stem>.out with a `# source-sha256: <hex>` header"
  - "Leak scanner CLI: uv run --project examples python scripts/check_leaks.py [--secrets-only] PATH [PATH ...], prints CLEAN and exits 0, or prints relative/path:LINE: kind findings and exits 1"

# Metrics
duration: 7min
completed: 2026-09-11
---

# Phase 1 Plan 1: Book Infra Basics Summary

**Installable `examples/` uv package with a single `shared/config.py` chat-model factory, plus a warm-up/run/mask/capture runner and a stdlib-only secret-masking library, all proven against the live local flashnext endpoint.**

## Performance

- **Duration:** ~7 min (commit span 15:51:39 → 15:58:24 KST)
- **Tasks:** 3/3
- **Files modified:** 11 created (.gitignore, 6 examples/ files, 4 scripts/ files)

## Accomplishments

- `examples/` is a real installable uv package (hatchling, `packages=["shared"]`): `from shared.config import ...` works identically whether invoked via `uv run --project examples python ...` from the repo root or by calling `examples/.venv/bin/python` directly from an unrelated directory
- `shared/config.py` matches the interface contract exactly, including the three ANCHOR regions (`settings`, `chat_model`, `structured`) that later chapters will include verbatim
- `get_chat_model()` made a live call to the local flashnext endpoint and got a real Korean response; editing `LLM_MODEL` in `.env` changed the model returned by `get_chat_model().model_name` with no code change
- `scripts/masking.py` (stdlib only) was built test-first: 15 pytest cases written and confirmed failing (`ModuleNotFoundError`) before any implementation existed, then implemented until all 15 passed
- `scripts/check_leaks.py` scans files, directories, and stdin, defaults to reporting all leak kinds, and supports `--secrets-only` for tracked docs/git history
- `scripts/run_examples.py` performs warm-up, per-example subprocess execution with timeout, masking of every printed line, leak-blocking before any `.out` write, and `# source-sha256: <hex>` headers
- End-to-end leak probe (temporary `ch00_probe/`, deleted afterward) proved masking of the real API key, a `Bearer` token, an `sk-` token, and the home path, plus correct non-zero exit and no `.out` for a deliberately failing example

## Task Commits

Each task was committed atomically:

1. **chore: root .gitignore** - `e19cd1b` (chore) — committed first so the parallel 01-02 plan benefits early
2. **Task 1: Installable examples package + shared/config.py** - `c7ee573` (feat)
3. **Task 2: Masking library (tests first) + leak scanner CLI** - `6970eea` (feat)
4. **Task 3: Capture runner + end-to-end leak probe (includes a masking.py false-positive fix)** - `102f9d3` (feat)

No separate plan-metadata commit was made for this task list beyond the SUMMARY commit below, per the parallel-execution rules (STATE.md/ROADMAP.md are updated by the orchestrator, not this agent).

## Files Created/Modified

- `.gitignore` — ignores `.env`/`.env.*` (keeps `.env.example`), `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `book/book/`, `.claude/`, `.DS_Store`
- `examples/pyproject.toml` — hatchling build, `packages = ["shared"]`, `requires-python = ">=3.14"`
- `examples/uv.lock`, `examples/.python-version` — locked deps, pinned to 3.14
- `examples/.env.example` — tracked template (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY=` blank)
- `examples/shared/__init__.py`, `examples/shared/config.py` — the single chat-model factory (not committed as `.env`, which stays local/git-ignored)
- `scripts/masking.py` — `collect_secrets`, `mask_text`, `find_leaks`
- `scripts/test_masking.py` — 15 pytest cases (139 lines)
- `scripts/check_leaks.py` — CLI leak scanner
- `scripts/run_examples.py` — capture runner (198 lines)

## Decisions Made

- Local `.env` holds the literal string `LLM_API_KEY=${LITELLM_API_KEY}` rather than a pasted value; `python-dotenv`'s `${VAR}` expansion resolves it from the shell environment at load time, verified via `s.api_key == os.environ['LITELLM_API_KEY']` returning `True` with zero literal-key occurrences in the check output.
- `_USERS_PATH_RE`/`_HOME_DIR_PATH_RE` require a word character immediately after `/Users/` or `/home/` (not just "not slash/quote/whitespace"), because the plan's own verification scans `scripts/masking.py` and expects `CLEAN` — the unconstrained version matched the regex's own source definition and a Korean comment mentioning `/Users/...`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed self-referential false positive in generic path regexes**
- **Found during:** Task 3, running the plan's own overall `<verification>` check (`check_leaks.py examples scripts/run_examples.py scripts/check_leaks.py scripts/masking.py` must print `CLEAN`)
- **Issue:** `_USERS_PATH_RE = re.compile(r"/Users/[^/\s\"'<>]+")` and the equivalent `/home/` pattern matched their own source-code definitions and a comment mentioning `/Users/...`/`/home/...`, producing 3 false `users-path` findings when `scripts/masking.py` scanned itself
- **Fix:** Require an initial word character (`[A-Za-z0-9_]`) right after `/Users/` and `/home/` before the rest of the segment — real paths always start with an alnum/underscore username, while the regex source (`[^`) and the comment ellipsis (`...`) do not
- **Files modified:** `scripts/masking.py`
- **Verification:** All 15 masking unit tests still pass; `check_leaks.py examples scripts/run_examples.py scripts/check_leaks.py scripts/masking.py` now prints `CLEAN`; re-ran the full end-to-end probe (real key, Bearer, sk-, home path all still masked/detected correctly)
- **Committed in:** `102f9d3` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary for the plan's own stated overall verification to pass; no scope creep, no interface/contract changes.

## Issues Encountered

None.

## User Setup Required

None — `examples/.env` was created locally by this agent (git-ignored) using the existing `LITELLM_API_KEY` shell variable; no manual step needed to run examples or the runner.

## Exact Commands Observed (for orchestrator / next plans)

- Run masking tests: `uv run --project examples pytest -p no:cacheprovider -q scripts/test_masking.py` → 15 passed
- Scan for leaks (should print CLEAN): `uv run --project examples python scripts/check_leaks.py examples scripts/run_examples.py scripts/check_leaks.py scripts/masking.py`
- Scan git history for the real key only: `git log -p --all | uv run --project examples python scripts/check_leaks.py --secrets-only -`
- Run examples (default warm-up + all chapters): `uv run --project examples python scripts/run_examples.py [TARGET ...] [--outputs-dir DIR] [--timeout SEC] [--no-warmup]`
- Warm-up timing observed this session: **2.2s** (well under PROJECT.md's worst-case 63s cold-start note; still keep timeout headroom for slower runs)

## Next Phase Readiness

- `examples/shared/config.py` and `scripts/run_examples.py` are ready for 01-03/01-04 (basics chapters) and all later phases — every future example only needs to `from shared.config import get_chat_model` (or `get_structured_model`) and rely on the runner for capture.
- `scripts/check_leaks.py` is ready to be wired into any future pre-commit/CI step for this repo if desired (not done in this plan — out of scope).
- No blockers. The parallel plan 01-02 (mdBook skeleton, GitHub Pages deploy, README) completed independently in the same window (`5b48886`) and touched no files this plan owns.

---
*Phase: 01-book-infra-basics*
*Completed: 2026-09-11*
