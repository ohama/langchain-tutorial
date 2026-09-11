# LangChain 튜토리얼 (한국어)

로컬 LLM으로 직접 실행하며 배우는 LangChain·LangGraph, 그리고 코딩 에이전트 만들기.

**책 보기:** https://ohama.github.io/langchain-tutorial/

이 책에 실린 모든 코드는 이 저장소 안의 실제 파일이며, 모든 출력은 저자의 로컬 LLM을 실제로 호출해 캡처한 결과다.

## 저장소 구조

- `book/` — 책 원고 (mdBook 소스)
- `examples/` — 실행 가능한 예제 코드 (uv 프로젝트)
- `outputs/` — 예제를 실행해 캡처한 실제 결과
- `scripts/` — 예제 실행·결과 캡처·검사 도구

## 독자로서 예제 실행하기

```bash
cd examples
cp .env.example .env
# .env를 열어 LLM_BASE_URL, LLM_MODEL, LLM_API_KEY를 자신의 엔드포인트에 맞게 수정한다
uv sync
uv run python ch01_basics/01_chat_model.py
```

## 저자로서 출력 캡처하기

```bash
uv run --project examples python scripts/run_examples.py ch01_basics
```

`outputs/ch01_basics/*.out` 파일이 생성된다.

## 키/경로 유출 검사

```bash
uv run --project examples python scripts/check_leaks.py outputs book/src
```

## 책 미리보기

```bash
mdbook serve book
```

## 주의

`.env` 파일은 API 키를 담고 있으므로 절대 커밋하지 않는다 (`.gitignore`에 이미 포함되어 있다).
