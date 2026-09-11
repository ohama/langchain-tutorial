# Howto TODO

| # | 제목 | 파일명 | 근거 |
|---|------|--------|------|
| 1 | 로컬 OpenAI 호환 서버에서 구조화 출력 500 에러 해결 | `debug-structured-output-500-speculative-decoding.md` | MLX/LiteLLM speculative decoding 서버에서 `with_structured_output` 기본값(json_schema)·json_mode·strict가 모두 500 → `method="function_calling", strict=False`로 해결 (라이브 검증) |
| 2 | uv 예제 프로젝트를 설치형 패키지로 만들어 공유 모듈 import 안정화 | `setup-uv-package-for-shared-imports.md` | plain `uv init`은 `No module named 'shared'` → `[build-system]` hatchling + `packages = ["shared"]` + `uv sync`로 실행 위치와 무관하게 import 성공 |
| 3 | mdBook에 실제 실행 출력을 include로 싣기 | `setup-mdbook-include-real-outputs.md` | `src/` 밖 파일 include 가능, `.out` 1행 해시 헤더를 `:2:`로 숨김, 전체 include 시 `ANCHOR` 줄 노출, include 누락에도 mdBook 0.5.3이 exit 0 → CI에서 `ERROR` 로그로 실패 처리 |
| 4 | 캡처 출력의 비밀값 마스킹과 누출 스캔 | `write-output-masking-and-leak-scan.md` | 실제 키 값 → 토큰 패턴 → 홈 경로 순서로 마스킹, 검사는 개수만 출력, 마스킹 정규식이 자기 소스를 오탐하는 문제, git 히스토리 전체 스캔 |
| 5 | mdBook을 공식 Pages Actions로 배포 | `setup-mdbook-pages-deploy-with-actions.md` | `gh api`로 Pages `build_type=workflow` 선활성화, mdBook 버전 고정 설치, 0.5.x 사이드바 목차가 `toc.html`(iframe)로 렌더링되어 검증 대상이 달라짐 |
| 6 | LangChain 수동 도구 루프를 안전하고 재현 가능하게 짜기 | `write-manual-tool-loop.md` | `tool.invoke(tool_call)`에 전체 dict를 넘기면 `ToolMessage`, args만 넘기면 원시 값 반환. 도구 예외는 그대로 전파되므로 `try/except`로 `ToolMessage` 오류화, `MAX_ITERS` for/else 가드, 무작위 tool_call id를 출력하지 않아야 temperature=0 재캡처가 바이트 동일 |

---
총 6개 대기 | 업데이트: 2026-09-11
