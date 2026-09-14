#!/usr/bin/env python3
"""챕터 형식(정확한 ## 제목, include-only 코드 블록, 렌더링 HTML)을 강제하는 검사기.

사용법 (리포 루트에서):
    uv run --project examples python scripts/check_book.py [MD ...] [--html DIR]

MD 인자가 없으면 book/src/SUMMARY.md에 링크된 ch*/ 아래 모든 페이지를 검사한다
(소개·부록은 제외). 각 챕터에 대해 `PASS <md>` 또는 `FAIL <md>: <reason>`을 출력하고,
하나라도 실패하면 exit 1을 반환한다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK_SRC = (REPO_ROOT / "book" / "src").resolve()
SUMMARY_MD = BOOK_SRC / "SUMMARY.md"

REQUIRED_HEADINGS = ["개념: 왜 필요한가", "최소 코드", "실제 출력", "요점 정리"]

HEADING_RE = re.compile(r"^## (.+)$", re.MULTILINE)
FENCE_RE = re.compile(r"```(\w*)\n(.*?)\n```", re.DOTALL)
INCLUDE_RE = re.compile(r"^\{\{#include (\S+?)(:[A-Za-z_][\w-]*|:\d*:\d*)?\}\}$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")

STUB_MARKER = "이 장은 작성 중입니다"

INCLUDE_ONLY_LANGS = ("python", "text", "ini", "mermaid")


class CheckError(Exception):
    pass


def _discover_chapters() -> list[Path]:
    text = SUMMARY_MD.read_text(encoding="utf-8")
    paths: list[Path] = []
    for m in LINK_RE.finditer(text):
        target = m.group(1)
        if target.startswith("http"):
            continue
        candidate = (BOOK_SRC / target).resolve()
        try:
            rel = candidate.relative_to(BOOK_SRC)
        except ValueError:
            continue
        if rel.parts and rel.parts[0].startswith("ch"):
            paths.append(candidate)
    return paths


def _check_no_stub(text: str) -> None:
    if STUB_MARKER in text:
        raise CheckError("chapter still contains stub placeholder text")


def _check_headings(text: str) -> None:
    headings = HEADING_RE.findall(text)
    if headings != REQUIRED_HEADINGS:
        raise CheckError(f"## headings must be exactly {REQUIRED_HEADINGS!r}, got {headings!r}")


def _check_code_blocks(md_path: Path, text: str) -> None:
    has_examples_include = False
    has_outputs_include = False

    for lang, body in FENCE_RE.findall(text):
        if lang not in INCLUDE_ONLY_LANGS:
            continue

        lines = [ln for ln in body.splitlines() if ln.strip()]
        if len(lines) != 1:
            raise CheckError(
                f"{lang} block must contain exactly one non-blank line (an include), got {len(lines)}"
            )
        line = lines[0].strip()
        m = INCLUDE_RE.match(line)
        if not m:
            raise CheckError(f"{lang} block line must be a single {{#include ...}}: {line!r}")

        target, suffix = m.group(1), m.group(2)
        resolved = (md_path.parent / target).resolve()
        if not resolved.exists():
            raise CheckError(f"include target does not exist: {target}")

        if target.endswith(".py") and "/examples/" in f"/{target}":
            has_examples_include = True
        if target.endswith(".out") and "/outputs/" in f"/{target}":
            has_outputs_include = True
            if suffix != ":2:":
                raise CheckError(f"outputs/*.out include must use the :2: line range: {line!r}")

        if resolved.is_file():
            content = resolved.read_text(encoding="utf-8", errors="replace")
            if "ANCHOR:" in content:
                is_named_anchor = bool(suffix) and re.match(r"^:[A-Za-z_]", suffix)
                if not is_named_anchor:
                    raise CheckError(
                        f"included file has ANCHOR markers; include must use an anchor suffix: {target}"
                    )

    if not has_examples_include:
        raise CheckError("no include block targets examples/**.py")
    if not has_outputs_include:
        raise CheckError("no include block targets outputs/**.out")


def check_chapter(md_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    _check_no_stub(text)
    _check_headings(text)
    _check_code_blocks(md_path, text)


def check_html(md_path: Path, html_dir: Path) -> None:
    rel = md_path.relative_to(BOOK_SRC)
    html_path = html_dir / rel.with_suffix(".html")
    if not html_path.exists():
        raise CheckError(f"rendered HTML not found: {html_path}")
    content = html_path.read_text(encoding="utf-8", errors="replace")
    for bad in ("{{#include", "ANCHOR", "source-sha256"):
        if bad in content:
            raise CheckError(f"rendered HTML still contains {bad!r}")


def _display(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check chapter format and include-only rule.")
    parser.add_argument("md", nargs="*", metavar="MD")
    default_html_dir = REPO_ROOT / "book" / "book"
    parser.add_argument(
        "--html",
        default=str(default_html_dir) if default_html_dir.exists() else None,
        help="Rendered HTML build dir to cross-check (default: book/book if it exists)",
    )
    args = parser.parse_args(argv)

    if args.md:
        chapters = [Path(m).resolve() for m in args.md]
    else:
        chapters = _discover_chapters()

    html_dir = Path(args.html).resolve() if args.html else None

    any_fail = False
    for md_path in chapters:
        display = _display(md_path)
        try:
            check_chapter(md_path)
            if html_dir is not None:
                check_html(md_path, html_dir)
        except CheckError as exc:
            print(f"FAIL {display}: {exc}")
            any_fail = True
            continue
        print(f"PASS {display}")

    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
