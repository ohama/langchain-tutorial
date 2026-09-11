#!/usr/bin/env python3
"""예제를 웜업 -> 실행 -> 마스킹 -> .out 저장까지 한 번에 처리하는 캡처 러너.

사용법 (리포 루트에서):
    uv run --project examples python scripts/run_examples.py [TARGET ...] \
        [--outputs-dir DIR] [--timeout SEC] [--no-warmup]

TARGET은 챕터 디렉터리(ch01_basics), 파일(ch01_basics/01_chat_model.py),
또는 examples/를 앞에 붙인 동일한 경로다. cwd 기준으로 먼저 풀고,
안 되면 examples/ 기준으로 다시 푼다. 반드시 examples/ 안쪽으로 풀려야 한다
(shared/, .venv/ 등은 거부). TARGET이 없으면 examples/ch*/ 전체를 실행한다.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from masking import collect_secrets, find_leaks, mask_text  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"

sys.path.insert(0, str(EXAMPLES_DIR))

from shared.config import get_chat_model, load_settings  # noqa: E402


class TargetError(Exception):
    pass


def _resolve_target(raw: str) -> Path:
    """단일 TARGET 문자열을 examples/ 안쪽 절대경로로 해석한다."""
    candidates = [Path(raw), EXAMPLES_DIR / raw]
    stripped = raw
    if stripped.startswith("examples/"):
        stripped = stripped[len("examples/"):]
        candidates.append(EXAMPLES_DIR / stripped)

    for candidate in candidates:
        resolved = candidate if candidate.is_absolute() else (Path.cwd() / candidate)
        resolved = resolved.resolve()
        if not resolved.exists():
            continue
        try:
            resolved.relative_to(EXAMPLES_DIR.resolve())
        except ValueError:
            raise TargetError(f"target must resolve inside examples/: {raw}")
        rel = resolved.relative_to(EXAMPLES_DIR.resolve())
        top = rel.parts[0] if rel.parts else ""
        if top in ("shared", ".venv"):
            raise TargetError(f"target must not be shared/ or .venv/: {raw}")
        return resolved

    raise TargetError(f"target not found: {raw}")


def _example_files_in_dir(dir_path: Path) -> list[Path]:
    files = [
        p for p in sorted(dir_path.glob("*.py"))
        if p.name[:1].isdigit()
    ]
    return files


def _collect_examples(targets: list[str]) -> list[Path]:
    if not targets:
        chapter_dirs = sorted(d for d in EXAMPLES_DIR.glob("ch*") if d.is_dir())
        files: list[Path] = []
        for d in chapter_dirs:
            files.extend(_example_files_in_dir(d))
        if not files:
            raise TargetError("no examples found under examples/ch*/")
        return files

    files = []
    for raw in targets:
        resolved = _resolve_target(raw)
        if resolved.is_dir():
            found = _example_files_in_dir(resolved)
            if not found:
                raise TargetError(f"no numbered .py files found in: {raw}")
            files.extend(found)
        elif resolved.is_file():
            files.append(resolved)
        else:
            raise TargetError(f"target is neither file nor directory: {raw}")
    return files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Warm up, run, mask, and capture example outputs.")
    parser.add_argument("targets", nargs="*", metavar="TARGET")
    parser.add_argument("--outputs-dir", default=str(REPO_ROOT / "outputs"))
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--no-warmup", action="store_true")
    args = parser.parse_args(argv)

    outputs_dir = Path(args.outputs_dir)

    try:
        examples = _collect_examples(args.targets)
    except TargetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    settings = load_settings()
    secrets = collect_secrets(extra=[settings.api_key])
    home = str(Path.home())

    def out(msg: str) -> None:
        print(mask_text(msg, secrets, home=home), flush=True)

    def err(msg: str) -> None:
        print(mask_text(msg, secrets, home=home), file=sys.stderr, flush=True)

    if not args.no_warmup:
        start = time.monotonic()
        try:
            get_chat_model(max_tokens=16).invoke("ping")
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - start
            err(f"warm-up failed after {elapsed:.1f}s: {type(exc).__name__}: {exc}")
            return 2
        elapsed = time.monotonic() - start
        err(f"warm-up: {elapsed:.1f}s")

    any_failed = False

    for py in examples:
        rel_to_examples = py.relative_to(EXAMPLES_DIR)
        rel_to_repo = py.relative_to(REPO_ROOT) if REPO_ROOT in py.parents else py

        run_env = dict(os.environ)
        run_env["PYTHONIOENCODING"] = "utf-8"
        run_env["NO_COLOR"] = "1"

        start = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, str(py)],
                cwd=EXAMPLES_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=args.timeout,
                env=run_env,
            )
            elapsed = time.monotonic() - start
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            out(f"FAIL {rel_to_repo} (timeout, {elapsed:.1f}s)")
            any_failed = True
            continue

        if proc.returncode != 0:
            out(f"FAIL {rel_to_repo} (exit {proc.returncode}, {elapsed:.1f}s)")
            stderr_tail = "\n".join(proc.stderr.splitlines()[-30:])
            err(stderr_tail)
            any_failed = True
            continue

        body = mask_text(proc.stdout, secrets, home=home)
        body = body.rstrip("\n") + "\n"

        leaks = find_leaks(body, secrets, home=home)
        if leaks:
            out(f"LEAK-BLOCKED {rel_to_repo}: {', '.join(leaks)}")
            any_failed = True
            continue

        out_path = outputs_dir / rel_to_examples.parent / f"{rel_to_examples.stem}.out"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        source_hash = hashlib.sha256(py.read_bytes()).hexdigest()
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# source-sha256: {source_hash}\n")
            f.write(body)

        rel_out = out_path.relative_to(REPO_ROOT) if REPO_ROOT in out_path.parents else out_path
        out(f"OK {rel_to_repo} -> {rel_out} ({elapsed:.1f}s)")

        if proc.stderr.strip():
            out("stderr (not captured):")
            err(proc.stderr)

    return 1 if any_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
