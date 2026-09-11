---
phase: 01-book-infra-basics
plan: 02
subsystem: infra
tags: [mdbook, github-pages, github-actions, ci-cd]

# Dependency graph
requires:
  - phase: 01-book-infra-basics (plan 01-01, parallel)
    provides: root .gitignore, examples/ uv package skeleton (not consumed directly by this plan)
provides:
  - Public GitHub repo ohama/langchain-tutorial with GitHub Pages live
  - mdBook skeleton with final Phase 1 TOC (intro, 1부 기초 x5, 부록)
  - .github/workflows/deploy.yml: LLM-free, Python-free CI build+deploy pipeline
  - README.md with reader/author/leak-scan/preview instructions
affects: [01-03, 01-04, book-content-phases]

# Tech tracking
tech-stack:
  added: [mdBook 0.5.3 (pinned in CI), actions/checkout@v7, actions/configure-pages@v6, actions/upload-pages-artifact@v5, actions/deploy-pages@v5]
  patterns: ["Official OIDC Pages deploy (no committed build output, no third-party actions)", "mdBook build-dir output uploaded directly as Pages artifact"]

key-files:
  created: [book/book.toml, book/src/SUMMARY.md, book/src/introduction.md, book/src/ch01_basics/01_chat_model.md, book/src/ch01_basics/02_messages.md, book/src/ch01_basics/03_prompt_templates.md, book/src/ch01_basics/04_lcel_runnables.md, book/src/ch01_basics/05_structured_output.md, book/src/appendix/about.md, README.md, .github/workflows/deploy.yml]
  modified: []

key-decisions:
  - "Created ohama/langchain-tutorial as a public GitHub repo and pushed to it, as explicitly authorized by the user"
  - "Pages build_type=workflow enabled via a single POST (no 409/422 encountered, no PUT fallback needed)"
  - "mdBook 0.5.3 pinned in CI to match local version exactly"

patterns-established:
  - "SUMMARY.md is final for Phase 1 chapter structure — later plans (01-03, 01-04) only replace stub content, never touch the TOC"
  - "CI fails the build step explicitly on any 'ERROR' string in the mdbook build log, since mdbook itself exits 0 even when an {{#include}} target is missing"

# Metrics
duration: ~20min
completed: 2026-09-11
---

# Phase 1 Plan 02: mdBook Infra + GitHub Pages Deploy Summary

**Public mdBook site live at https://ohama.github.io/langchain-tutorial/ with final Phase 1 TOC, deployed via official GitHub Actions OIDC pipeline (no Python/uv/LLM in CI)**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-09-11
- **Tasks:** 2/2
- **Files modified:** 11 created

## Accomplishments

- mdBook skeleton with the final Phase 1 table of contents: 소개 (intro), 1부 기초 (5 chapters), 부록
- Korean introduction.md covering the book's promise (every code block/output is real and captured from a local LLM), chapter format, repo layout, and prerequisites
- README.md with book link, repo layout, and reader/author/leak-scan/preview commands
- `.github/workflows/deploy.yml`: pins mdBook 0.5.3, builds `book/`, fails explicitly on any `ERROR` in the build log (mdBook itself exits 0 on missing `{{#include}}` targets), deploys via official `configure-pages`/`upload-pages-artifact`/`deploy-pages`
- Created the public GitHub repo `ohama/langchain-tutorial`, enabled Pages with `build_type=workflow`, set the repo homepage
- Pushed to main; the Actions run succeeded end to end (build 9s, deploy 9s) with no Python/uv/example-execution steps
- Verified the live site: index page, sidebar TOC (via `toc.html`), a chapter sub-path, and a styled 404 page all serve correctly under `/langchain-tutorial/`, and the site's stylesheet resolves with HTTP 200

## Task Commits

Each task was committed atomically:

1. **Task 1: mdBook skeleton with final TOC, Korean introduction, chapter stubs, README** - `b50e6d4` (feat)
2. **Task 2: Deploy workflow** - `d4f8ff0` (feat) — repo creation, Pages enablement, and push are GitHub-side/git-remote operations, not local file commits

_No SUMMARY/STATE metadata commit included here since this plan runs in a parallel wave with 01-01; the orchestrator handles STATE.md/ROADMAP.md updates after the wave._

## Files Created/Modified

- `book/book.toml` - mdBook config: Korean language, site-url `/langchain-tutorial/`, edit-url template, search enabled
- `book/src/SUMMARY.md` - Final Phase 1 TOC (소개, 1부 기초 x5, 부록)
- `book/src/introduction.md` - Korean book introduction (promise, chapter format, repo layout, prerequisites, roadmap)
- `book/src/ch01_basics/{01..05}.md` - Chapter stubs (title + "작성 중" placeholder), replaced by plans 01-03/01-04
- `book/src/appendix/about.md` - Appendix placeholder listing planned appendix topics
- `README.md` - Repo landing page: book URL, layout, reader/author/leak-scan/preview commands
- `.github/workflows/deploy.yml` - CI build+deploy pipeline (pinned mdBook, official Pages actions)

## Decisions Made

- Repo created as public per explicit user authorization; pushed main (including 01-01's concurrent commits) after the pre-push safety gate passed
- Used a single `POST repos/ohama/langchain-tutorial/pages -f build_type=workflow` — it succeeded immediately (repo had at least the `gh repo create` initial state), so the planned PUT-on-409 and push-first-then-retry fallbacks were not needed
- Kept mdBook 0.5.3 pinned in CI to exactly match the local binary version, per the plan's locked decision

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adjusted TOC verification to check `toc.html`, not `index.html`**

- **Found during:** Task 1 local build verification
- **Issue:** The plan's verify step checked for `"1부 기초"` and `"부록 안내"` inside `book/book/index.html`. In mdBook 0.5.3 the sidebar/TOC is rendered into a separate `toc.html` loaded via an `<iframe>`, not inlined into every page — this is an mdBook 0.5.x architecture detail, confirmed by inspecting the actual build output. Checking `index.html` for those strings fails even though the TOC is correctly built.
- **Fix:** Verified TOC content against `book/book/toc.html` (locally) and `https://ohama.github.io/langchain-tutorial/toc.html` (live) instead; both contain `1부 기초` and `부록 안내`. `index.html` was separately confirmed to render the correct introduction page (`<title>소개 - LangChain 튜토리얼 (한국어)</title>`).
- **Files modified:** None — this was a verification-command adjustment, not a content or code change.
- **Verification:** `grep -q "1부 기초" book/book/toc.html && grep -q "부록 안내" book/book/toc.html` → `TOC_OK`; live equivalent → `LIVE_TOC_OK`.
- **Committed in:** N/A (verification-only finding, no file change)

---

**Total deviations:** 1 auto-fixed (1 bug — verification target file corrected)
**Impact on plan:** No impact on shipped content or structure; only the verification command's target file differed from what mdBook 0.5.3 actually produces. All must-have truths and success criteria were independently confirmed against the correct files.

## Issues Encountered

None — both tasks completed on the first attempt with no retries, auth gates, or blocking errors.

## User Setup Required

None - no external service configuration required beyond what this plan itself automated (repo creation and Pages enablement were done via `gh`).

## Next Phase Readiness

- The publish pipeline (INFRA-01, INFRA-02) is proven end-to-end before any real chapter content exists: push to main → LLM-free CI build → live Pages deploy, confirmed via a successful Actions run and live HTTP checks (index, sub-path, 404, stylesheet).
- `book/src/SUMMARY.md` is final for Phase 1; plans 01-03 and 01-04 should only replace the five chapter stub files' content (and add real `{{#include}}` blocks referencing `examples/` and `outputs/`), never edit the TOC structure.
- No blockers. One note for future phases: mdBook 0.5.x's sidebar lives in `toc.html` (iframe), not inline in each page — worth remembering when writing any future verification steps that check "does the sidebar contain X".

---
*Phase: 01-book-infra-basics*
*Completed: 2026-09-11*
