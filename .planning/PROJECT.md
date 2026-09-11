# LangChain Tutorial (한국어)

## What This Is

LangChain을 기초부터 LangGraph 에이전트까지 차근차근 익히며 기록하는 한국어 튜토리얼 책이다. mdBook으로 작성해 GitHub Pages에 배포한다. 모든 예제는 로컬에서 이미 돌고 있는 LLM 서비스(LiteLLM 프록시 뒤의 Qwen3.8-Flash-Next)로 실제 실행하고, 그 출력을 책에 그대로 싣는다. 튜토리얼의 끝에서는 지정된 작업 폴더 안에서 파일을 읽고·수정하고 명령을 실행하는 **코딩 에이전트**를 직접 만든다.

주 독자는 저자 자신이다(개인 학습 기록). 다만 공개 배포되므로 다른 사람이 읽고 따라 할 수 있는 수준으로 쓴다.

## Core Value

책을 순서대로 따라가면, 실제로 돌아가는 코드와 실제 출력으로 LangChain/LangGraph를 이해하고 마지막에 스스로 코딩 에이전트를 구현할 수 있어야 한다. 책에 실린 코드는 반드시 실행되고 출력은 실제 결과여야 한다.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] mdBook 기반 한국어 튜토리얼 책 구조 (SUMMARY.md, 챕터, 부록)
- [ ] GitHub Pages로 CI 자동 빌드·배포
- [ ] 기초 챕터: 채팅 모델 호출, 메시지, 프롬프트 템플릿, 출력 파서/구조화 출력, LCEL/Runnable
- [ ] 도구 호출 챕터: 도구 정의, 모델의 tool call, 도구 실행 루프
- [ ] RAG 챕터: 문서 로딩, 분할, 다국어 임베딩(로컬), 벡터스토어, 검색·생성
- [ ] LangGraph 챕터: 상태 그래프, 노드/엣지, 조건 분기, 체크포인트/메모리
- [ ] LangSmith 챕터: 트레이싱으로 에이전트 내부 동작 들여다보기
- [ ] 캡스톤: 지정된 작업 폴더(샌드박스) 안에서 파일 읽기/쓰기, 셸 명령 실행을 승인 없이 수행하는 코딩 에이전트
- [ ] 모든 챕터 예제가 저장소 안의 실행 가능한 Python 파일로 존재하고, 책에 실린 출력은 실제 실행 결과
- [ ] 챕터 형식: 개념(왜 필요한가) → 최소 코드 → 실행 결과 → 요점 정리
- [ ] 부록: 로컬 LLM 서비스를 새로 설치하는 방법(예: Ollama), uv 기반 Python 환경 구성
- [ ] LLM 엔드포인트·모델명·API 키를 .env로 분리해 독자가 자기 환경에 맞게 바꿀 수 있음

### Out of Scope

- TypeScript/LangChain.js — Python 하나에 집중
- OpenAI/Anthropic 등 클라우드 LLM을 기본으로 쓰는 예제 — 로컬 서비스 기준 (설정으로 바꿀 수는 있음)
- 본문에서 LLM 서비스 설치 과정 설명 — 이미 돌고 있는 서비스를 활용하고, 새로 설치하는 방법은 부록으로
- 코딩 에이전트의 human-in-the-loop 승인 흐름 — 작업 폴더로 범위를 제한하고 승인 없이 실행하기로 결정
- Jupyter 노트북 형식 — 책 + .py 예제로 통일
- 팀 교육용 커리큘럼(과제, 퀴즈 등) — 개인 학습 기록이 목적

## Context

**로컬 LLM 환경 (2026-09-11 확인):**
- 하드웨어: Apple Silicon Mac (대용량 통합 메모리)
- LiteLLM 프록시 `http://127.0.0.1:4000/v1` (API 키 필요, 환경변수 `LITELLM_API_KEY`) — 모델 별칭: `flashnext`, `flashnext-codex`, `flashnext-plan`, `flashnext-act`, `flashnext-reach-xhigh`
- 그 뒤의 MLX OpenAI 호환 서버 (LiteLLM 백엔드, 포트 비공개) — `Qwen3.8-Flash-Next-MLX-oQ4`, `BAAI/bge-small-en-v1.5`
- Ollama는 설치되어 있지 않음 → 코드는 `langchain-ollama`가 아니라 OpenAI 호환 클라이언트(`langchain-openai`의 `ChatOpenAI(base_url=...)`) 기준
- 도구 호출 확인 완료: 백엔드 MLX 서버에서 `get_weather(city="Seoul")`를 정확히 호출, 생성 속도 약 42 tok/s
- 첫 요청에서 프롬프트 273토큰 처리에 약 63초 (캐시 콜드 추정) — 예제 실행 시간에 영향이 있을 수 있음
- 기존 임베딩 `bge-small-en-v1.5`는 영어 전용 → RAG는 다국어 임베딩 모델을 로컬에 추가해서 사용

**개발 도구:** Python 3.14.7 (Homebrew), uv 0.11.14, mdbook v0.5.3, gh CLI (github.com 계정 로그인됨)

**동기:** 실제 에이전트를 스스로 설계·구현할 수 있는 수준까지 LangChain/LangGraph를 익히는 것.

## Constraints

- **언어**: 본문은 한국어, 코드는 Python — 개인 학습 기록이자 한국어 자료
- **LLM**: 로컬 LiteLLM 프록시(`flashnext`) 기준 — 이미 돌고 있는 서비스 활용, 비용 없음
- **엔드포인트 설정**: base_url / 모델명 / API 키를 `.env`로 분리, `.env`는 커밋 금지 — 공개 저장소에 키가 새면 안 됨
- **정확성**: 책의 코드와 출력은 실제 실행 결과여야 함 — 핵심 가치
- **API 버전**: 최신 LangChain 1.x / LangGraph API 기준, 폐기된 API(LLMChain 등)를 쓰지 않음
- **Python 버전**: 3.14가 LangChain 생태계와 호환되는지 확인 필요 — 안 되면 uv로 지원 버전을 고정
- **배포**: GitHub Pages, CI 자동 빌드
- **LangSmith**: 트레이싱 데이터가 클라우드로 전송됨 — 해당 챕터에서만 선택적으로 켬

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python 단일 언어 | 자료·생태계가 가장 풍부 | — Pending |
| mdBook + GitHub Pages | 챕터형 책 + 웹 배포 | — Pending |
| 기초 → 도구 → RAG → LangGraph → 코딩 에이전트 순서 | 개념을 차근차근 쌓아 캡스톤에서 합침 | — Pending |
| 로컬 LiteLLM `:4000` `flashnext` 사용 (Ollama 아님) | 이미 돌고 있는 서비스, 짧고 안정적인 별칭 | — Pending |
| `langchain-openai` `ChatOpenAI(base_url=...)` | 서비스가 OpenAI 호환 API | — Pending |
| 다국어 임베딩 모델을 로컬에 추가 | bge-small-en은 한국어 검색 품질이 낮음 | — Pending |
| 모든 예제 실행 + 실제 출력 수록 | 책의 신뢰성이 핵심 가치 | — Pending |
| 코딩 에이전트는 샌드박스 폴더 안에서 승인 없이 실행 | 단순한 구조, 폴더 제한으로 안전 확보 | — Pending |
| LangSmith 챕터 포함 | 에이전트 내부 동작 시각화 | — Pending |
| 새 LLM 설치(Ollama 등)는 부록으로 | 본문은 LangChain에 집중 | — Pending |

---
*Last updated: 2026-09-11 after initialization*
