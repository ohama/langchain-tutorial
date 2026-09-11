#!/usr/bin/env python3
"""파일/디렉터리/stdin에서 비밀 값·토큰·홈 경로 누출을 스캔하는 CLI.

사용법:
    check_leaks.py [--secrets-only] PATH [PATH ...]

PATH는 파일, 디렉터리(재귀적으로 순회, .git/.venv/__pycache__/node_modules와
정확히 이름이 ".env"인 파일은 건너뜀), 또는 stdin을 뜻하는 "-" 중 하나다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from masking import collect_secrets, find_leaks, mask_text  # noqa: E402

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
MAX_BYTES = 20 * 1024 * 1024  # 20 MB


def _load_secrets() -> list[str]:
    try:
        from shared.config import load_settings  # type: ignore

        load_settings()
    except Exception:
        pass
    return collect_secrets()


def _iter_files(path: Path):
    if path.is_file():
        yield path
        return
    if path.is_dir():
        for child in sorted(path.rglob("*")):
            if not child.is_file():
                continue
            if child.name == ".env":
                continue
            if any(part in SKIP_DIRS for part in child.parts):
                continue
            yield child


def _read_text(path: Path) -> str | None:
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > MAX_BYTES:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return data.decode("utf-8", errors="replace")


def _scan_text(label: str, text: str, secrets: list[str], home: str, secrets_only: bool) -> list[str]:
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        kinds = find_leaks(line, secrets, home=home)
        if secrets_only:
            kinds = [k for k in kinds if k == "literal-secret"]
        for kind in kinds:
            safe_label = mask_text(label, secrets, home=home)
            findings.append(f"{safe_label}:{lineno}: {kind}")
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Scan files/dirs/stdin for secret leaks.")
    parser.add_argument("--secrets-only", action="store_true",
                         help="Only report literal-secret findings (for tracked docs/history).")
    parser.add_argument("paths", nargs="+", metavar="PATH")
    args = parser.parse_args(argv)

    secrets = _load_secrets()
    home = str(Path.home())
    cwd = Path.cwd()

    all_findings: list[str] = []

    for raw_path in args.paths:
        if raw_path == "-":
            text = sys.stdin.read()
            all_findings.extend(_scan_text("<stdin>", text, secrets, home, args.secrets_only))
            continue

        p = Path(raw_path)
        for file_path in _iter_files(p):
            text = _read_text(file_path)
            if text is None:
                continue
            try:
                rel = file_path.resolve().relative_to(cwd.resolve())
            except ValueError:
                rel = file_path
            all_findings.extend(_scan_text(str(rel), text, secrets, home, args.secrets_only))

    if not all_findings:
        print("CLEAN")
        return 0

    for line in all_findings:
        print(line)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
