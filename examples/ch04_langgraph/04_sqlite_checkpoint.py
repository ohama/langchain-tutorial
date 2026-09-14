"""4부 3장: 프로세스를 두 번 띄워 SQLite 체크포인터가 재시작을 견디는지 확인한다."""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / ".checkpoint_demo.db"  # 생성물임을 표시 — 실행마다 지운다
SIDECARS = [DB_PATH, Path(str(DB_PATH) + "-wal"), Path(str(DB_PATH) + "-shm")]
WORKER = HERE / "sqlite_worker.py"
THREAD_ID = "restart-demo"


def clean() -> None:
    for p in SIDECARS:
        p.unlink(missing_ok=True)


def db_exists() -> bool:
    return DB_PATH.exists()


def run_worker(label: str) -> None:
    # 표준 출력을 그대로 물려받게 해서(capture하지 않고) 워커의 출력이 캡처에
    # 그대로 남게 한다. 부모 프로세스의 print()는 파이프로 나갈 때 블록
    # 버퍼링되므로, 자식이 먼저 flush(종료 시)해 순서가 뒤바뀌지 않도록
    # 호출 직전에 부모 stdout을 강제로 비운다.
    sys.stdout.flush()
    subprocess.run(
        [sys.executable, str(WORKER), label, str(DB_PATH), THREAD_ID, str(os.getpid())],
        check=True,
    )


print("=== 1. 깨끗한 상태에서 시작 ===", flush=True)
clean()
print(f"시작 전 DB 파일 존재: {db_exists()}", flush=True)
print("SqliteSaver는 WAL 모드를 쓰므로 실행하면 -wal/-shm 사이드카 파일도 함께 생긴다", flush=True)
print("(경로는 출력하지 않는다)", flush=True)

try:
    print(flush=True)
    print("=== 2. 첫 번째 프로세스 ===", flush=True)
    run_worker("run1")
    print(f"실행 후 DB 파일 존재: {db_exists()}", flush=True)

    print(flush=True)
    print("=== 3. 두 번째 프로세스 (완전히 새 파이썬 프로세스) ===", flush=True)
    run_worker("run2")
    print(f"같은 thread_id로 이어서 대화했다: {THREAD_ID}", flush=True)
finally:
    print(flush=True)
    print("=== 4. 정리 ===", flush=True)
    clean()
    print(f"정리 후 DB 파일 존재: {db_exists()}", flush=True)
    print("예제는 실행할 때마다 깨끗한 상태에서 시작한다", flush=True)
