---
phase: 04-langgraph-langsmith
plan: 01
subsystem: infra
tags: [langgraph, langgraph-checkpoint-sqlite, langsmith, mdbook-mermaid, mermaid, check-leaks, check-book, ci]

# Dependency graph
requires:
  - phase: 01-book-infra-basics
    provides: "check_book.py format gate, check_leaks.py + masking.py leak scanner, pinned mdBook 0.5.3 CI deploy workflow"
provides:
  - "langgraph, langgraph-checkpoint-sqlite, langsmith declared directly in examples/pyproject.toml and locked on Python 3.14"
  - "examples/ch04_langgraph/*.db(-wal|-shm) gitignored for the SQLite checkpointer demo"
  - "check_book.py: mermaid fences are now include-only gated, same as python/text/ini"
  - "check_leaks.py: repeatable, path-scoped --exclude GLOB (tested), for vendored third-party assets only"
  - "book/book.toml wired to mdbook-mermaid 0.17.0 (additional-js + [preprocessor.mermaid]); two sha256-pinned vendored assets committed"
  - "deploy.yml installs the same pinned mdbook-mermaid release binary via curl/tar before the build step"
affects: [04-02-langgraph-chapters, 04-03-langgraph-chapters, 04-04-whole-phase-gate]

# Tech tracking
tech-stack:
  added: [langgraph, langgraph-checkpoint-sqlite, langsmith, mdbook-mermaid]
  patterns:
    - "Vendored third-party build assets (mermaid.min.js) are sha256-pinned in the plan/summary and excluded from the leak scanner by exact path, never by weakening collect_secrets/find_leaks"
    - "check_leaks.py --exclude is opt-in per invocation and path-scoped; masking.py stays the single source of truth for what counts as a secret"

key-files:
  created:
    - book/mermaid.min.js
    - book/mermaid-init.js
    - scripts/test_check_leaks.py
  modified:
    - examples/pyproject.toml
    - examples/uv.lock
    - .gitignore
    - scripts/check_book.py
    - scripts/check_leaks.py
    - book/book.toml
    - .github/workflows/deploy.yml

key-decisions:
  - "langgraph and langsmith declared directly even though already transitive, matching this project's existing convention (langchain-core precedent)"
  - "Vendored mermaid.min.js false-positive handled via path-scoped --exclude + sha256 pin, not by touching masking.py/collect_secrets"

patterns-established:
  - "Rendering pipeline for diagrams: {{#include}} inside a ```mermaid fence -> mdbook-mermaid preprocessor -> <pre class=\"mermaid\"> in built HTML, with hashed additional-js asset filenames"

# Metrics
duration: ~11min
completed: 2026-09-14
---

# Phase 4 Plan 01: LangGraph/LangSmith Toolchain + Mermaid Rendering Pipeline Summary

**Added langgraph/langgraph-checkpoint-sqlite/langsmith as direct, locked dependencies on Python 3.14; strengthened both gate scripts (mermaid fences are now include-only gated, check_leaks.py gained a tested path-scoped `--exclude`); and stood up a sha256-pinned mdbook-mermaid 0.17.0 rendering pipeline (local book.toml + vendored assets + pinned CI install step) so a real `<pre class="mermaid">` diagram can render starting in 04-02.**

## Performance

- **Duration:** ~11 min
- **Tasks:** 3/3 completed
- **Files modified:** 10 (3 created, 7 modified)

## Accomplishments
- `langgraph`, `langgraph-checkpoint-sqlite`, `langsmith` directly declared in `examples/pyproject.toml`; `uv lock --check` passes; every LangGraph symbol this phase needs imports cleanly on Python 3.14; lazy-import invariant (`torch` not imported by `shared.config`) still holds
- `check_book.py` now enforces the include-only rule on `mermaid` fences (proved with a failing negative control on a hand-typed diagram); `check_leaks.py` gained a repeatable, path-scoped `--exclude GLOB`, covered by 3 new tests, without touching `masking.py`
- `mdbook-mermaid 0.17.0` wired into `book/book.toml` and vendored as two sha256-pinned assets; a fresh `mdbook build book` renders a `{{#include}}`-driven mermaid fence into `<pre class="mermaid">` with zero ERROR lines and exactly the one known benign preprocessor warning; `deploy.yml` installs the same pinned binary via curl/tar only

## Task Commits

Each task was committed atomically:

1. **Task 1: LangGraph dependencies + SQLite checkpoint artifact ignore** - `ce6c05a` (chore)
2. **Task 2: Gate scripts — enforce include-only mermaid fences, add path-scoped --exclude to the leak scanner** - `1d49a1f` (feat)
3. **Task 3: Install and pin the mdbook-mermaid rendering pipeline** - `2af7fbc` (build)

**Plan metadata:** (this SUMMARY commit)

## Resolved Dependency Versions

- `langgraph` 1.2.11
- `langgraph-checkpoint` 4.2.0 (transitive, not directly declared)
- `langgraph-checkpoint-sqlite` 3.1.1
- `langsmith` 0.12.4
- `langchain` 1.4.0
- `langchain-core` 1.6.2
- `uv lock --project examples --check`: passed (0 changes needed)

## Vendored Asset SHA256 Pins (re-verified by 04-04's whole-phase gate)

- `book/mermaid.min.js` — sha256 `eefea253bed9655e838eb874ff955c46872f982a8e26290c1dd2982ddc0a4703`, 2,667,011 bytes
- `book/mermaid-init.js` — sha256 `ccf746f10c0a71bd34799867d2f9860dddb5fc6efc6c50d1ea55a1eb1a7bd406`, 1,262 bytes
- Both match the values measured during planning from `mdbook-mermaid 0.17.0` exactly (`shasum -a 256 -c` reported `OK` for both).

## Leak Scanner False Positive (documented justification for --exclude)

- `check_leaks.py book/mermaid.min.js` (no exclude) reports exactly **2** `literal-secret` findings.
- `collect_secrets()` in this environment returns exactly **1** secret, **5 characters**, alphanumeric — it coincidentally occurs inside the 2.6 MB minified bundle. This is the documented false positive; `masking.py` was **not modified** to accommodate it.
- With `--exclude 'book/mermaid.min.js'`, the same scan over the project's real content (`book/src examples outputs scripts .github`) reports `CLEAN`.

## `book/book.toml` Diff Shape

`mdbook-mermaid install book` added, and nothing else:
- `additional-js = ["mermaid.min.js", "mermaid-init.js"]` appended inside the existing `[output.html]` table
- A new empty `[preprocessor]` table
- `[preprocessor.mermaid]` with `command = "mdbook-mermaid"`

Confirmed unchanged: `site-url`, `git-repository-url`, `edit-url-template`, `default-theme`, `preferred-dark-theme`, and the entire `[output.html.search]` table (`enable`/`limit-results`).

## Build Log

- Fresh `mdbook build book`: **0** `ERROR` lines.
- The single expected `Warning` line, verbatim: `Warning: The mdbook-mermaid preprocessor was built against version 0.5.0 of mdbook, but we're being called from version 0.5.3`
- No other `Warning`/`WARN` lines present.
- Hashed assets landed in the build output: exactly one `mermaid-eefea253.min.js` and one `mermaid-init-ccf746f1.js`, the former well over 1,000,000 bytes.
- `check_book.py --html book/book`: 10/10 `PASS` (no reader-visible chapter regressed).

## `masking.py`

Confirmed unmodified: `git diff --stat -- scripts/masking.py` produced no output at any point in this plan.

## Files Created/Modified
- `examples/pyproject.toml`, `examples/uv.lock` — direct langgraph/langgraph-checkpoint-sqlite/langsmith declarations, relocked
- `.gitignore` — three explicit ignore lines for the ch04 SQLite checkpointer demo's `.db`/`.db-wal`/`.db-shm` artifacts
- `scripts/check_book.py` — `"mermaid"` added to `INCLUDE_ONLY_LANGS`
- `scripts/check_leaks.py` — `import fnmatch`, `_is_excluded()` helper, repeatable `--exclude GLOB` argument, applied in the directory-walk branch only (not stdin)
- `scripts/test_check_leaks.py` (new) — 3 tests proving `--exclude` reports without it, skips only the matched file, and doesn't hide findings elsewhere
- `book/book.toml` — `[preprocessor.mermaid]` + `additional-js` registration
- `book/mermaid.min.js`, `book/mermaid-init.js` (new) — vendored, sha256-pinned mdbook-mermaid 0.17.0 assets
- `.github/workflows/deploy.yml` — `MDBOOK_MERMAID_VERSION` env var + a pinned curl/tar install step for `mdbook-mermaid`, placed before the build step

## Decisions Made
- Declared `langgraph` and `langsmith` directly even though already present transitively, per this project's existing convention that any package an example imports directly must be declared directly.
- Kept `--exclude` opt-in and path-scoped; did not touch `masking.py`, `collect_secrets`, `find_leaks`, or the `CLEAN`/findings output format.
- Used the plan's exact CI curl/tar pattern (mirroring the existing pinned mdBook install step) rather than any package manager, preserving the mdBook-only CI invariant.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Task 3's leak-scan verify command needed an additional, pre-existing exclusion to actually reach CLEAN**
- **Found during:** Task 3, running the plan's verify step `check_leaks.py book/src examples outputs scripts .github --exclude 'book/mermaid.min.js'`
- **Issue:** That command alone still reported 15 findings, all in `scripts/test_masking.py` (sk-token/bearer-token/users-path patterns). This is not new: the same findings occur identically on the pre-Phase-4 commit (verified via `git stash` + checking out the prior `scripts/check_leaks.py`/`masking.py`/`test_masking.py`), and Phase 1's own plan (`01-01-PLAN.md`) already documents that `test_masking.py` "is excluded because it contains fake fixtures by design" — every prior whole-phase gate command omitted a bare `scripts` path for the same reason.
- **Fix:** Re-ran the verify with an additional `--exclude 'scripts/test_masking.py'` (on top of the required `--exclude 'book/mermaid.min.js'`) to reach the intended `CLEAN` result. No code was changed for this; it only affected how the verification command was invoked. The new `scripts/test_check_leaks.py` was confirmed to trip nothing on its own.
- **Files modified:** None (verification-only; no commit needed beyond the already-planned Task 3 commit).
- **Verification:** `check_leaks.py book/src examples outputs scripts .github --exclude 'book/mermaid.min.js' --exclude 'scripts/test_masking.py'` → `CLEAN`, exit 0.

---

**Total deviations:** 1 auto-fixed (1 bug, verification-command-only, no source change)
**Impact on plan:** No scope creep; the underlying gate scripts and vendored-asset exclusion behave exactly as specified. 04-04 (whole-phase gate) should carry the same `scripts/test_masking.py` exclusion forward if it also scans a bare `scripts` path, alongside the two mermaid-asset exclusions it already plans to use.

## Issues Encountered
None beyond the deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 04-02 can add a real ```mermaid fence backed by a single `{{#include}}` and have it both format-gated by `check_book.py` and rendered to `<pre class="mermaid">` by the now-committed pipeline.
- The SQLite checkpointer, LangGraph core APIs, and LangSmith package are all installed and importable; no further toolchain work is needed before authoring chapters.
- Carry forward for 04-04: when re-verifying the whole-phase leak scan over a bare `scripts` path, also exclude `scripts/test_masking.py` (pre-existing, by-design fixture false positive), in addition to the two mermaid-asset exclusions already planned.

---
*Phase: 04-langgraph-langsmith*
*Completed: 2026-09-14*
