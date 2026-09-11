# Phase 1: Book Infra + Basics - Research

**Researched:** 2026-09-11
**Domain:** mdBook 0.5.3 저작/배포 파이프라인 + LangChain 1.x 기초 예제 (로컬 LiteLLM 엔드포인트)
**Confidence:** HIGH — 아래 대부분은 이 세션에서 직접 실행/재현했다: mdBook 0.5.3으로 실제 프로젝트를 만들어 `{{#include}}` 경로 해석을 검증했고, 로컬 LiteLLM 엔드포인트(`http://127.0.0.1:4000/v1`, `flashnext`)에 대해 invoke/multi-turn/few-shot/RunnableParallel·batch/streaming/`temperature=0`/`with_structured_output(function_calling, strict=False)`를 모두 라이브로 재검증했다. GitHub 쪽은 `gh api`로 Pages 생성 스펙을 확인했고, 리포지토리는 아직 생성되지 않은 상태임을 확인했다.

이 문서는 프로젝트 레벨 연구(`.planning/research/{STACK,ARCHITECTURE,PITFALLS,SUMMARY}.md`)를 재검증·구체화한 것이며, 거기서 이미 HIGH confidence로 확정된 내용(패키지 버전, `with_structured_output` 500 에러 원인, `langchain-community` 배제 등)은 반복하지 않고 **이 phase를 계획하는 데 필요한 새로운/구체적 사실**만 다룬다.

## Summary

책 저작 파이프라인은 세 개의 최상위 트리(`book/`, `examples/`, `outputs/`)로 나누고, mdBook의 `{{#include}}`는 파일시스템 상대경로를 그대로 따라가므로 `book/src/` 바깥의 `examples/`·`outputs/`도 문제없이 include할 수 있음을 실측으로 확인했다(`mdbook v0.5.3`, 0.5.x의 include 동작은 0.4.x와 동일). GitHub Pages 배포는 리포지토리 자체가 아직 없으므로(`gh repo view` 404 확인, 실제 GitHub 로그인 계정은 `ohama`, 이메일 `ohama100@gmail.com`과는 다름) `gh repo create` → Pages를 `build_type: "workflow"`로 활성화(`gh api -X POST /repos/ohama/<repo>/pages`) → 공식 Actions(`checkout`/`configure-pages`/`upload-pages-artifact`/`deploy-pages`)로 배포하는 순서가 필요하다.

`shared/config.py`를 모든 예제가 아무 실행 방식으로든 import할 수 있게 하려면 `examples/`를 `uv init`(app 템플릿) 그대로 두지 말고 `[build-system]`(hatchling) + `[tool.hatch.build.targets.wheel] packages = ["shared"]`를 추가해 **설치형 패키지**로 만들어야 한다. 이렇게 하면 `uv sync` 후 `python foo.py`를 어떤 작업 디렉토리에서 실행하든(`uv run python ch01_basics/01_chat.py`, 심지어 `.venv/bin/python`을 직접 절대경로로 호출해도) `from shared.config import ...`가 그대로 동작함을 실측으로 확인했다. `uv init` 기본값(app, `packages=[]` 없음)으로는 `python ch01_basics/01_chat.py`가 `ModuleNotFoundError: No module named 'shared'`로 실패한다 — 이것이 이 phase에서 반드시 피해야 할 실패 패턴이다.

로컬 LLM 라이브 재검증 결과 이 phase의 모든 BASIC 요구사항이 기술적으로 문제없이 동작함을 확인했다: multi-turn 메시지, few-shot `ChatPromptTemplate`(`FewShotChatMessagePromptTemplate`), `RunnableParallel`/`batch`, 스트리밍(`AIMessageChunk` 누적), `temperature=0`에서 동일 프롬프트 2회 호출 시 완전히 동일한 텍스트 재현(결정론적), `with_structured_output(Schema, method="function_calling", strict=False)` 정상 동작, `<think>` 등 리즈닝 누출 없음. 유일한 새 발견은 **웜업 소요 시간이 이번 세션에서는 8.5초**로(PROJECT.md에 기록된 콜드 63초보다 짧지만 즉시 응답은 아님) 실행 스크립트의 타임아웃/워밍업 설계가 여전히 필요하다는 점이다.

**Primary recommendation:** `book/`(mdBook, `src="src"` 기본값 유지) + `examples/`(installable uv package, `shared/` 패키지 포함) + `outputs/`(캡처 결과, 3트리 병렬 구조)로 리포지토리를 구성하고, GitHub Pages는 공식 `actions/{checkout,configure-pages,upload-pages-artifact,deploy-pages}` 워크플로로 배포한다(사용자의 범용 `/pages` 커맨드가 기본으로 쓰는 `peaceiris/actions-mdbook` + 빌드 산출물 커밋 방식과는 의도적으로 다름 — 근거는 아래 "GitHub Pages 배포 방식: 두 관례의 충돌과 결정" 참고).

## Standard Stack

### Core (책 인프라 전용, LangChain 스택은 STACK.md 참고)

| Library/Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mdBook | 0.5.3 (로컬 설치됨) | 책 렌더링 | 이미 설치된 버전을 그대로 사용. 0.5.4가 최신이지만, 로컬/CI 버전을 반드시 일치시키는 것이 더 중요하므로 **0.5.3으로 CI도 고정**(로컬을 0.5.4로 올리지 않는 이상). |
| uv | 0.11.14 (설치됨) | `examples/` 패키지·venv·lockfile 관리 | 이미 설치, 프로젝트 표준. `[build-system]` 추가로 editable 패키지화 필요(아래 참고). |
| hatchling | 최신 (uv가 자동 선택) | `examples` 패키지의 build backend | `pyproject.toml`에 `[build-system]`을 추가하는 가장 가벼운 선택지 — 별도 설정 없이 `packages = [...]`만 지정하면 됨. |
| GitHub CLI (`gh`) | 2.91.0 (설치·로그인됨) | 리포지토리 생성 + Pages 활성화 | 로그인 계정 `ohama` (scopes: `gist`, `read:org`, `repo`, `workflow` — Pages API에 충분). |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `actions/checkout` | v7 | 체크아웃 | CI 워크플로 첫 스텝 (2026-09-11 기준 최신, STACK.md에서 이미 확인) |
| `actions/configure-pages` | v6 | Pages 메타데이터 설정 | build job |
| `actions/upload-pages-artifact` | v5 | 빌드 산출물 업로드 | build job 마지막 스텝, `path: book/book` |
| `actions/deploy-pages` | v5 | 실제 배포 | deploy job (OIDC, `id-token: write` 필요) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| 공식 Pages Actions(OIDC 배포) | `peaceiris/actions-mdbook` + git commit으로 `docs/` 반영 (사용자의 `/pages` 커맨드 기본값) | 서드파티 액션 의존, 매 빌드마다 `docs/` HTML을 리포지토리 히스토리에 커밋(diff 노이즈, 리포 크기 증가), `contents: write` 권한과 봇 커밋 설정 필요. 반면 이 프로젝트는 이미 `examples/*.py` + `outputs/*.out`을 커밋하는 것만으로 "실제 출력" 요구를 충족하므로, 빌드된 HTML까지 커밋할 이유가 없음 — 공식 OIDC 배포가 더 적은 이동 부품 |
| `examples/`를 installable 패키지로(hatchling) | 각 스크립트 상단에 `sys.path.insert(0, ...)` 수동 조작 | 스크립트마다 boilerplate가 섞여 책에 노출하기 지저분함(anchor로 잘라내야 함). 패키지화하면 `shared` import가 항상 깨끗하게 한 줄로 남음 |
| `examples/`를 installable 패키지로 | `uv run python -m ch01_basics.01_chat` (모듈 실행) | 실측으로 동작은 확인했으나(`01_chat`처럼 숫자로 시작하는 모듈명도 `-m`으로는 동작), "항상 `-m`으로만 실행해야 한다"는 제약이 붙고 mdBook에 실행 커맨드를 보여줄 때도 부자연스러움. 패키지화가 더 견고하고 자연스러움 |
| mdBook 0.5.3 그대로 | 0.5.4로 업그레이드 | 최신이지만 로컬에 이미 0.5.3이 있고, 0.5→0.5.4 사이엔 book 저자 대상 breaking change가 없음(아래 참고) — 업그레이드는 선택사항, 이번 phase 필수 아님 |

**Installation:**
```bash
# examples/ 를 installable 패키지로 초기화
cd examples
uv init --no-workspace --python 3.14
uv python pin 3.14
# pyproject.toml에 아래 추가 (uv init은 기본적으로 [build-system] 없이 "app" 템플릿을 만듦)
```
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["shared"]
```
```bash
uv add langchain langchain-core langchain-openai langgraph langsmith python-dotenv pydantic
uv sync   # shared 패키지를 .venv에 editable-install
```

## Architecture Patterns

### Recommended Project Structure

```
langchain-tutorial/
├── book/
│   ├── book.toml                  # src = "src" (기본값, 명시 권장)
│   └── src/
│       ├── SUMMARY.md
│       ├── introduction.md
│       ├── ch01_basics/
│       │   ├── 01_chat_model.md
│       │   ├── 02_messages.md
│       │   ├── 03_prompt_templates.md
│       │   ├── 04_lcel_runnables.md
│       │   └── 05_structured_output.md
│       └── appendix/               # 이번 phase에서는 빈 자리표시자만(뒷 phase가 채움)
│
├── examples/
│   ├── pyproject.toml              # [build-system] hatchling, packages=["shared"]
│   ├── .env.example
│   ├── shared/
│   │   ├── __init__.py
│   │   └── config.py                # get_chat_model() 등
│   └── ch01_basics/
│       ├── 01_chat_model.py
│       ├── 02_messages.py
│       ├── 03_prompt_templates.py
│       ├── 04_lcel_runnables.py
│       └── 05_structured_output.py
│
├── outputs/
│   └── ch01_basics/
│       ├── 01_chat_model.out        # 첫 줄: `# source-sha256: <hash>` (마스킹 완료 상태)
│       └── …
│
├── scripts/
│   ├── run_examples.py              # warm-up + 실행 + 캡처 + 마스킹
│   └── (check_fresh.py는 이 phase 범위 밖이면 생략 가능 — 아래 "Open Questions" 참고)
│
├── .github/workflows/deploy.yml
├── .env.example                     # 리포 루트에도 둘지 examples/ 안에만 둘지는 Open Question
├── .gitignore                       # .env, book/book/, examples/.venv/, __pycache__/
└── .planning/…
```

**mdBook include 경로 실측 결과(중요, 이번 세션에서 직접 검증):** `book/src/ch01/01_chat.md`에서 `{{#include ../../../examples/ch01/01_chat.py:setup}}`처럼 `book/src` 바깥으로 3단계(`../../../`)를 거슬러 올라가 `examples/`·`outputs/`를 참조하는 것이 **정상적으로 렌더링됨**을 실제 `mdbook build`로 확인했다(디렉터리 트리와 앵커 포함). mdBook의 include는 “파일 위치 기준 상대경로”일 뿐 `src/` 안으로 제한되지 않는다 — ARCHITECTURE.md가 제안한 3트리 분리 구조를 그대로 채택해도 된다는 뜻이다.

### Pattern 1: `examples/`를 installable 패키지로 만들어 import 문제를 구조적으로 없앤다

**What:** `examples/pyproject.toml`에 `[build-system]`(hatchling) + `[tool.hatch.build.targets.wheel] packages = ["shared"]`를 추가하고 `uv sync`로 `.venv`에 editable 설치한다.

**When to use:** `shared/config.py`를 참조하는 모든 예제. 이 phase에서 확립하면 이후 모든 phase(Tool calling, RAG, LangGraph, Capstone)가 같은 방식을 재사용한다.

**실측 결과:**
- `uv init --no-workspace`의 기본 템플릿(빌드 시스템 없음)으로는 `python ch01_basics/01_chat.py`가 `ModuleNotFoundError: No module named 'shared'`로 실패(스크립트 자기 자신의 디렉터리만 `sys.path`에 들어가고 프로젝트 루트는 안 들어감).
- `[build-system]` + `packages=["shared"]` 추가 후 `uv sync`를 한 번 실행하면, 이후로는 **어떤 방식으로 실행해도**(`uv run python ch01_basics/01_chat.py`, 리포 루트에서 `uv run --project examples python examples/ch01_basics/01_chat.py`, 심지어 `.venv/bin/python`을 절대경로로 직접 호출) `shared` import가 정상 동작함을 확인.

**Example (`examples/pyproject.toml`):**
```toml
[project]
name = "examples"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = ["langchain", "langchain-core", "langchain-openai", "python-dotenv", "pydantic"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["shared"]
```

**Source:** 이 세션의 라이브 검증(스크래치패드 `import_test/`), uv/hatchling 공식 동작 방식과 일치.

### Pattern 2: 캡처 러너 스크립트 — warm-up, 타임아웃, 마스킹

**What:** `scripts/run_examples.py`(단일 진입점, 인자로 특정 파일 또는 전체 지정)가 다음 순서로 동작:
1. `shared.config`로 만든 모델에 짧은 warm-up 요청 1회(결과는 버림) — 콜드 스타트를 실제 캡처 이전에 흡수.
2. 대상 `.py`를 `subprocess.run([venv_python, path], capture_output=True, timeout=180, cwd=examples_root)`로 실행 (실측: warm-up 자체도 8.5초 걸렸으므로, 개별 예제 타임아웃은 최소 120초, 안전하게는 180초 권장 — PITFALLS.md의 63초 콜드 사례까지 감안).
3. stdout(+필요시 stderr)을 마스킹 함수에 통과시킨 뒤 `outputs/<chapter>/<name>.out`에 저장, 첫 줄에 `# source-sha256: <sha256(source)>` 기록.
4. 마스킹 규칙(정규식, 순서 중요 — 구체적 패턴을 먼저 치환):
   - `os.environ["LITELLM_API_KEY"]` **실제 값** 자체를 리터럴 문자열 치환으로 `***MASKED_API_KEY***`로 바꾼다(정규식 패턴 매칭보다 우선 — 로컬 키가 `sk-`로 시작하지 않을 수도 있으므로 "값을 안다"는 사실을 활용하는 게 가장 확실).
   - 보조로 일반적인 키 패턴(`Bearer\s+\S+`, `sk-[A-Za-z0-9]{16,}`)도 정규식으로 한 번 더 스윕(다른 키 별칭/향후 클라우드 키 대비).
   - `str(Path.home())`(즉 `/Users/ohama`) 리터럴 치환 → `~` 또는 `<HOME>`. `re.sub(re.escape(home), "~", text)`가 가장 안전(경로 구분자 이슈 없음).
5. 실행 시간을 stderr 또는 별도 로그에 남겨(PITFALLS.md Pitfall 4) 콜드/웜 여부를 사후에 판단 가능하게 한다.

**스트리밍 캡처:** `model.stream(...)`을 쓰는 예제는 `subprocess`로 감싸 stdout을 그대로 캡처하면 청크가 이미 하나의 텍스트로 합쳐져 저장된다 — 이번 세션 실측(9개 청크, `AIMessageChunk` 누적)에서도 최종 출력은 결국 이어붙인 텍스트이므로, 캡처 방식 자체는 non-streaming과 동일하게 "표준출력 리다이렉트"로 충분하다. 다만 예제 코드 안에서 `print(chunk.content, end="", flush=True)`처럼 청크별로 출력해야 "스트리밍처럼 보이는" `.out` 파일이 만들어진다(개행 없이 이어붙는 모습을 책에 그대로 보여주는 것이 BASIC-01 요구사항의 의도).

**결정론 확인(실측):** `temperature=0`으로 동일 프롬프트를 연속 2회 호출 시 텍스트가 **완전히 동일**했다(글자 단위 일치). 이는 PITFALLS.md Pitfall 5("비결정성이 근본적으로 제거 불가능")보다 낙관적인 결과이지만, 표본이 1개 프롬프트·연속 호출뿐이므로 "이 환경에서는 대체로 안정적이나 100% 보장은 아니다"라는 문구를 부록/캡처 규칙에 남기는 것을 권장(PITFALLS.md 권고 유지).

**Source:** 이 세션 라이브 실행 결과(스크래치패드 `lc_test/test_phase1.py`), PROJECT.md 기존 콜드스타트 기록, PITFALLS.md Pitfall 4/5/6.

### Pattern 3: GitHub 리포지토리·Pages 생성 절차 (아직 리포 없음 — 확인됨)

**What:** `gh repo view ohama/langchain-tutorial`이 404를 반환 — 이 리포지토리는 아직 GitHub에 생성되지 않았다. 로그인 계정은 `ohama`(GitHub 로그인 이름)이며, `.env`/사용자 이메일(`ohama100@gmail.com`)과는 별개다. GitHub Pages 프로젝트 URL은 `https://ohama.github.io/<repo-name>/` 형태가 된다 — `book.toml`의 `output.html.site-url`을 리포 이름에 맞춰 설정해야 한다(PITFALLS.md의 site-url 이슈와 직결).

**절차:**
1. `gh repo create <repo-name> --public --source=. --remote=origin` (또는 먼저 `git remote add`로 기존 로컬 git과 연결) — **사용자 확인 필요 항목**(리포 이름 결정은 저자의 선택).
2. Pages를 `build_type: "workflow"`로 활성화 — REST API로 사전에 켜지 않으면 `deploy-pages` 액션이 "Pages site not found"류로 실패할 수 있음(공식 문서: Pages Source가 없으면 첫 배포가 실패하는 사례가 흔함):
   ```bash
   gh api -X POST /repos/ohama/<repo-name>/pages \
     -f build_type=workflow \
     -f "source[branch]=main" \
     -f "source[path]=/"
   ```
   (POST가 이미 존재하는 Pages 설정에 대해 409를 반환하면 `-X PUT`으로 같은 바디를 보내 업데이트)
3. `.github/workflows/deploy.yml` 커밋 후 push — Actions가 실행되며 실제 배포.
4. 배포 후 `https://ohama.github.io/<repo-name>/`에서 목차·챕터·하위경로·404 페이지를 직접 확인(PITFALLS.md 체크리스트).

**Source:** 이 세션의 `gh api`/`gh repo view` 실행 결과, [GitHub REST API: Create a GitHub Pages site](https://docs.github.com/en/rest/pages/pages#create-a-github-pages-site) (`build_type: "workflow"`, `source.branch`/`source.path` 스키마 확인, HIGH).

### Anti-Patterns to Avoid

- **`uv init`의 기본(비패키지) 템플릿을 그대로 두고 `shared` import를 기대하는 것:** 실제로 `ModuleNotFoundError`로 실패함(위 실측). 반드시 `[build-system]` + `packages=["shared"]` 추가.
- **`mdbook test`를 CI 품질 게이트로 넣는 것:** `mdbook test`는 "Tests that a book's Rust code samples compile"(공식 `--help` 문구 그대로) — **Rust 코드 블록 전용**이며 Python 코드 블록에는 아무 효과가 없다. ARCHITECTURE.md가 "mdbook build 후 mdbook test"를 언급한 부분은 이 프로젝트(Python 전용)에는 적용되지 않으므로 계획에서 제외해야 한다.
- **책의 build 산출물(`book/book/`)을 git에 커밋하는 것:** 공식 Actions(OIDC) 배포를 쓰는 이번 설계에서는 빌드 산출물을 커밋할 필요가 전혀 없다 — `.gitignore`에 반드시 포함.
- **워밍업 없이 바로 캡처:** 이번 세션에서도 최초 요청이 8.5초 걸렸다(웜 상태 재요청은 훨씬 빠름) — 러너 스크립트에 warm-up 단계 누락 시 첫 예제의 캡처 시간이 들쭉날쭉해짐.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 모듈 import 경로 문제 | 스크립트마다 `sys.path.insert()` | `examples/`를 installable 패키지로(hatchling) | 코드가 깨끗해지고, 어떤 실행 방식에서도 견고함 확인됨(실측) |
| API 키/경로 마스킹 | 매번 손으로 출력 확인 후 지우기 | 자동 마스킹 함수(리터럴 치환 우선 + 정규식 보강)를 `scripts/`에 한 번 작성해 모든 캡처가 거치게 함 | PITFALLS.md Pitfall 6 — 손으로 하면 언젠가 반드시 놓침 |
| GitHub Pages 배포 파이프라인 | 커스텀 스크립트로 `gh-pages` 브랜치에 직접 push | 공식 `actions/{configure-pages,upload-pages-artifact,deploy-pages}` | GitHub가 유지보수하는 OIDC 기반 배포, 토큰 관리 불필요 |
| Rust 코드 유효성 검사 도구를 Python 코드에 적용 | `mdbook test`로 Python 코드 블록을 검증하려는 시도 | 별도 없음 — Python 코드의 "실행 가능성"은 애초에 `scripts/run_examples.py`가 실제로 실행해봄으로써만 보장됨(그 결과가 곧 `.out`) | `mdbook test`는 rustdoc 기반이라 Python에는 작동 자체가 안 됨 |

**Key insight:** 이 phase의 인프라 문제 대부분(모듈 경로, Pages 배포, 마스킹)은 "표준 도구를 정확한 설정으로 쓰는 것"이 전부이며, 커스텀 빌드가 필요한 지점은 `scripts/run_examples.py`(warm-up+캡처+마스킹 오케스트레이션) 하나뿐이다. 이 스크립트조차 외부 라이브러리 없이 `subprocess`/`hashlib`/`re`/`pathlib` 표준 라이브러리만으로 충분하다.

## Common Pitfalls

### Pitfall 1: `examples/`가 installable 패키지가 아니어서 `shared` import가 실행 방식에 따라 성공/실패를 오간다

**What goes wrong:** `uv run python ch01_basics/foo.py`(examples 디렉터리 안에서)는 실패하고, `uv run python -m ch01_basics.foo`는 성공하는 등 "어떤 명령으로 실행하느냐"에 따라 결과가 달라져 러너 스크립트와 책의 "실행 방법" 설명이 어긋난다.

**Why it happens:** 일반 `python script.py` 실행은 스크립트 자신의 디렉터리만 `sys.path[0]`에 넣고, 프로젝트 루트나 `shared/`가 있는 위치는 넣지 않는다.

**How to avoid:** `examples/pyproject.toml`에 `[build-system]`(hatchling) + `packages=["shared"]`를 추가하고 `uv sync`로 editable 설치. 이후 어떤 실행 방식이든 동일하게 동작함을 이번 세션에서 확인했다.

**Warning signs:** `ModuleNotFoundError: No module named 'shared'`.

### Pitfall 2: Pages를 미리 활성화하지 않고 `deploy-pages`부터 돌려서 배포가 실패한다

**What goes wrong:** 리포지토리가 갓 생성된 상태에서 `actions/deploy-pages`를 실행하면 Pages 사이트 자체가 없어 배포가 실패할 수 있다(리포에 Pages 설정이 전혀 없는 상태 확인됨 — `gh api .../pages` 404).

**How to avoid:** 워크플로를 push하기 전에(또는 첫 실행 실패 시 바로) `gh api -X POST /repos/ohama/<repo>/pages -f build_type=workflow -f "source[branch]=main" -f "source[path]=/"`로 미리 활성화한다.

**Warning signs:** Actions 로그에서 deploy job이 "Get Pages site failed" 류의 에러로 실패.

### Pitfall 3: `book.toml`의 `site-url`을 리포 이름과 다르게 설정

**What goes wrong:** PITFALLS.md에 이미 기록된 이슈 — 실제 GitHub 로그인 이름이 `ohama`이므로 URL은 `https://ohama.github.io/<repo-name>/`가 된다. 프로젝트명을 `langchain-tutorial`로 정할지 다른 이름으로 할지에 따라 `site-url` 값이 달라짐 — **리포 이름 확정 전에는 이 값을 정확히 채울 수 없다.**

**How to avoid:** 리포 이름을 먼저 정하고(사용자 확인 필요), `book.toml`의 `[output.html] site-url = "/<repo-name>/"`을 그 이름에 맞춰 설정. 배포 후 실제 URL에서 CSS/이미지/404 페이지 확인.

### Pitfall 4: 콜드/웜 워밍업 시간을 과소평가해 러너 타임아웃을 너무 짧게 잡음

**What goes wrong:** 이번 세션 실측으로도 첫 요청이 8.5초 걸렸다(PROJECT.md 기록상 최악의 경우 63초). 타임아웃을 30초 등으로 짧게 잡으면 warm-up 자체가 실패할 수 있다.

**How to avoid:** `ChatOpenAI(..., timeout=120)` 이상, 러너의 `subprocess.run(..., timeout=180)` 이상 권장(PITFALLS.md와 일치, 이번 실측으로 재확인).

## Code Examples

### `shared/config.py` — 단일 진입점

```python
# examples/shared/config.py
import os
from langchain_openai import ChatOpenAI

def get_chat_model(**overrides) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=os.environ["LITELLM_BASE_URL"],
        api_key=os.environ["LITELLM_API_KEY"],
        model=os.environ.get("LITELLM_MODEL", "flashnext"),
        timeout=120,
        **overrides,
    )
```
(`.env`는 `python-dotenv`의 `load_dotenv()`를 각 예제 상단에서 명시적으로 호출하는 방식을 STACK.md가 이미 권장 — 이 phase에서 그대로 채택)

### 구조화 출력 (라이브 검증 통과)

```python
# Source: 이 세션 라이브 검증 (2026-09-11)
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="이름")
    age: int = Field(description="나이")

structured_model = model.with_structured_output(Person, method="function_calling", strict=False)
result = structured_model.invoke("김철수는 30살입니다. 정보를 추출해줘.")
# Person(name='김철수', age=30)
```

### Few-shot `ChatPromptTemplate` (라이브 검증 통과)

```python
# Source: 이 세션 라이브 검증 (2026-09-11)
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

examples = [
    {"input": "행복", "output": "슬픔"},
    {"input": "크다", "output": "작다"},
]
example_prompt = ChatPromptTemplate.from_messages([("human", "{input}"), ("ai", "{output}")])
few_shot = FewShotChatMessagePromptTemplate(example_prompt=example_prompt, examples=examples)
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "입력된 단어의 반대말만 한 단어로 답하라."),
    few_shot,
    ("human", "{input}"),
])
chain = final_prompt | model
chain.invoke({"input": "빠르다"})  # -> '느리다'
```

### RunnableParallel + batch (라이브 검증 통과)

```python
# Source: 이 세션 라이브 검증 (2026-09-11)
from langchain_core.runnables import RunnableParallel, RunnableLambda

par = RunnableParallel(upper=RunnableLambda(str.upper), lower=RunnableLambda(str.lower))
par.invoke("Hello")  # -> {'upper': 'HELLO', 'lower': 'hello'}

model.batch(["한국의 수도는?", "일본의 수도는?"])  # 두 응답 리스트 동시 반환
```

### `{{#include}}` 3-트리 구조 (mdBook 0.5.3 실측 통과)

```markdown
<!-- book/src/ch01_basics/01_chat_model.md -->
### 최소 코드
{{#include ../../../examples/ch01_basics/01_chat_model.py:setup}}

### 실행 결과
{{#include ../../../outputs/ch01_basics/01_chat_model.out:body}}
```
```python
# examples/ch01_basics/01_chat_model.py
# ANCHOR: setup
from shared.config import get_chat_model
model = get_chat_model()
# ANCHOR_END: setup
print(model.invoke("...").content)
```

### GitHub Pages 활성화 (build_type=workflow)

```bash
# Source: GitHub REST API 공식 문서 (docs.github.com/en/rest/pages/pages)
gh api -X POST /repos/ohama/<repo-name>/pages \
  -f build_type=workflow \
  -f "source[branch]=main" \
  -f "source[path]=/"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `peaceiris/actions-mdbook` + 빌드 산출물을 브랜치에 커밋(레거시 Pages "Deploy from branch") | 공식 `configure-pages`/`upload-pages-artifact`/`deploy-pages` + Pages Source="GitHub Actions" | GitHub가 수년 전부터 OIDC 기반 배포를 기본 권장 경로로 전환 | 배포 토큰/브랜치 관리 불필요, 빌드 산출물을 리포지토리 히스토리에 남기지 않음 |
| mdBook 0.4.x 프리프로세서/렌더러 Rust API | mdBook 0.5.x Rust API 재설계(130+ PR) | 2026 mdBook 0.5.0 정식 릴리스 | **이 프로젝트에는 영향 없음** — breaking change는 프리프로세서/렌더러 "개발자"용이며, 이 프로젝트는 서드파티 프리프로세서를 쓰지 않고(architecture 결정) 표준 `book.toml`/`{{#include}}`/검색 설정만 사용하므로 영향권 밖 |

**Deprecated/outdated:**
- `mdbook test`를 "코드 유효성 검사"로 활용하는 발상: 이 프로젝트(Python 코드)에는 애초에 적용 불가(Rust 전용 기능) — 사용하지 않음.

## Suggested Plan Breakdown (quick depth: 1-3 plans)

`config.json`의 `depth: "quick"` + `parallelization: true`를 감안한 제안. Requirements 커버리지: INFRA-01~08, BASIC-01~05 전부 이 3개 플랜 안에 배치.

### Plan 01-01: 저장소 골격 + LLM 연동 인프라 (Wave 1, 순차 — 이후 모든 것의 전제)
- GitHub 리포지토리 생성(`gh repo create`, 이름 확정 필요 — 사용자 확인 체크포인트) + Pages `build_type=workflow` 활성화
- `book/`(book.toml, SUMMARY.md 뼈대) + `examples/`(installable 패키지, `shared/config.py`) + `outputs/` 3트리 생성
- `.env.example`/`.gitignore`/`shared/config.py` 작성
- `.github/workflows/deploy.yml`(공식 Pages 액션 조합) 작성 + push해서 **빈 책이라도 배포되는지 1회 확인**(INFRA-01, INFRA-02 최소 충족을 가장 먼저 증명 — 이후 콘텐츠 추가는 이 위에서 안전하게 반복 가능)
- **이 플랜은 병렬화 불가** — 나머지 모든 작업(콘텐츠, 캡처)이 이 골격 위에서 동작하므로 반드시 먼저 끝나야 함.

### Plan 01-02: 캡처 러너 + BASIC 챕터 5개 (Wave 2 — 01-01 완료 후, 챕터 간 병렬 가능)
- `scripts/run_examples.py`(warm-up, 타임아웃, 마스킹) 작성 — 이 스크립트가 먼저 완성돼야 이후 5개 챕터가 같은 도구로 캡처됨.
- BASIC-01~05 각 챕터의 `.py` 작성 → 러너로 실행·캡처 → `.md`에 `{{#include}}`로 조립:
  - `01_chat_model.py`(BASIC-01: invoke/stream)
  - `02_messages.py`(BASIC-02: 멀티턴)
  - `03_prompt_templates.py`(BASIC-03: few-shot `ChatPromptTemplate`)
  - `04_lcel_runnables.py`(BASIC-04: `|`, `RunnableParallel`/`RunnableLambda`, batch/stream)
  - `05_structured_output.py`(BASIC-05: `with_structured_output(function_calling, strict=False)` + 500 에러 트러블슈팅 박스)
- 5개 챕터의 `.py`+`.out`+`.md` 작성 자체는 서로 독립적이므로 **병렬 실행 가능**(같은 `shared/config.py`와 `run_examples.py`를 공유하되, 파일 간 의존성 없음). 단, `run_examples.py`가 먼저 존재해야 캡처를 시작할 수 있으므로 "러너 작성"은 이 wave의 선행 스텝.

### Plan 01-03: SUMMARY.md 조립 + 전체 사이트 검증 + 배포 확인 (Wave 3, 순차 — 마지막)
- SUMMARY.md에 실제 5개 챕터 등록, `book.toml`의 `site-url`을 확정된 리포 이름으로 최종 반영
- 로컬 `mdbook build`/`mdbook serve`로 목차·include·앵커 렌더링 확인
- git push → Actions 로그 확인(LLM 미호출, 빌드만 수행) → 실제 GitHub Pages URL에서 목차·챕터·하위경로·404 페이지 스모크 체크(PITFALLS.md 체크리스트)
- 커밋 전 `grep -r "Bearer\|/Users/"` 등으로 키/경로 잔존 여부 최종 확인(INFRA-06 검증)

**Parallelization 요약:** Wave 1(01-01)은 반드시 순차 선행. Wave 2(01-02) 안에서는 "러너 스크립트 1개 작성"이 먼저이고, 그 다음 5개 챕터의 코드/캡처/문서 작업은 서로 독립적이라 병렬화 가치가 있음(같은 사람이 순차로 해도 무방하나, 여러 서브에이전트로 나눌 경우 챕터 단위 분할이 자연스러움). Wave 3(01-03)은 전체 조립·검증이므로 순차.

## Open Questions

1. **리포지토리 이름/공개 여부**
   - What we know: GitHub 로그인 계정은 `ohama`, 리포는 아직 생성 안 됨. `.env`의 이메일(`ohama100@gmail.com`)과 GitHub 로그인명은 다름.
   - What's unclear: 정확한 리포 이름(`langchain-tutorial`로 가정했지만 확정 아님), public/private 여부(Pages 무료 티어는 public 리포 또는 GitHub Pro 필요 — public 가정).
   - Recommendation: 플랜 단계에서 `gh repo create <name> --public`을 실행하기 직전에 사용자 확인 체크포인트를 둘 것. `book.toml`의 `site-url`은 이 이름이 정해진 뒤에만 정확히 채울 수 있음.

2. **`.env.example`의 정확한 변수명 확정 (`LITELLM_BASE_URL`/`LITELLM_MODEL`/`LITELLM_API_KEY` vs 다른 이름)**
   - What we know: PROJECT.md는 "base_url/모델명/API 키" 3개만 언급, 정확한 env var 이름은 확정 안 됨. 이 문서에서는 `LITELLM_BASE_URL`/`LITELLM_MODEL`/`LITELLM_API_KEY`로 가정(현재 세션 환경변수 `LITELLM_API_KEY`와 일치시킴).
   - What's unclear: 독자가 Ollama 등으로 바꿀 때 이름이 "LITELLM_"으로 시작하면 어색할 수 있음(예: `OPENAI_COMPAT_BASE_URL` 같은 중립적 이름 후보).
   - Recommendation: 계획 단계에서 변수명을 확정하고 `shared/config.py`·`.env.example`·모든 예제 문서에 일관 적용.

3. **`scripts/check_fresh.py`(해시 드리프트 감지)를 이 phase에 포함할지**
   - What we know: ARCHITECTURE.md가 제안했으나 SUMMARY.md는 "MEDIUM confidence, 계획 단계 재검토 필요"로 명시, REQUIREMENTS.md에는 INFRA-01~08에 해시 검증이 명시적으로 요구되지 않음(v2 백로그 `INFRA-V2-01`로 이미 이연됨).
   - What's unclear: quick depth(3플랜 이하) 목표와 이 스크립트의 우선순위.
   - Recommendation: **이번 phase 범위에서 제외**(v2 요구사항으로 이미 명시적으로 이연됨, REQUIREMENTS.md 참고) — `run_examples.py`의 `.out` 헤더에 해시만 남겨두고, 비교 로직은 만들지 않는 것으로 범위를 좁혀도 INFRA-05/06 요구사항은 충족됨.

4. **`.env` 파일 위치: 리포 루트 vs `examples/` 안**
   - What we know: `shared/config.py`는 `examples/` 패키지 안에 있고, `python-dotenv`의 `load_dotenv()`는 기본적으로 현재 작업 디렉터리 기준으로 `.env`를 탐색(`find_dotenv()`는 상위 디렉터리까지 탐색 가능).
   - What's unclear: 예제를 리포 루트에서 실행할지 `examples/`에서 실행할지에 따라 `.env` 위치가 달라짐.
   - Recommendation: `.env`/`.env.example`을 `examples/` 안에 두고, `load_dotenv()` 대신 `load_dotenv(find_dotenv())` 또는 `Path(__file__).parent.parent / ".env"`로 명시적 경로를 써서 실행 위치와 무관하게 동작하도록 계획.

## Sources

### Primary (HIGH confidence)
- 이 세션의 라이브 실행 검증 (2026-09-11, `/private/tmp/.../scratchpad/lc_test`, `/private/tmp/.../scratchpad/mdbook_test`, `/private/tmp/.../scratchpad/import_test`): mdBook 0.5.3 `{{#include}}` 상대경로 실측(`../../../` 통과), `uv init` 기본 템플릿 vs hatchling 패키지화 import 동작 비교, `ChatOpenAI` invoke/multi-turn/few-shot/RunnableParallel/batch/stream/temperature=0 재현성/`with_structured_output(function_calling, strict=False)`/reasoning 누출 여부 전체 재검증
- `mdbook --version`(v0.5.3), `mdbook test --help`(Rust 전용 확인), `mdbook build --help`(기본 build-dir `./book` 확인) — 로컬 바이너리 직접 실행
- `gh api`, `gh repo view`, `gh auth status` 직접 실행 (2026-09-11): 리포 미생성 확인, 로그인 계정 `ohama` 확인, Pages 엔드포인트 스키마 확인
- [GitHub REST API: Create a GitHub Pages site](https://docs.github.com/en/rest/pages/pages#create-a-github-pages-site) — `build_type: "workflow"` 페이로드 확인 (WebFetch, 2026-09-11)
- `.planning/research/STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md`, `SUMMARY.md` — 프로젝트 레벨 연구(패키지 버전, GitHub Actions 버전, 구조화 출력 500 에러 근본 원인 등 HIGH confidence 항목 재사용)
- `.claude/commands/mdbook.md`, `.claude/commands/pages.md`, `.claude/skills/mdbook-utils.skill.md`, `.claude/skills/mdbook-docs-images.skill.md` — 사용자의 로컬 mdBook/Pages 관례(아래 참고)

### Secondary (MEDIUM confidence)
- [rust-lang/mdBook CHANGELOG](https://github.com/rust-lang/mdBook/blob/main/CHANGELOG.md) (WebSearch 요약) — 0.5.0이 프리프로세서/렌더러 Rust API 대상 breaking change이며 일반 저자에게는 영향 없다는 판단의 근거

### Tertiary (LOW confidence)
- 없음

## GitHub Pages 배포 방식: 두 관례의 충돌과 결정 (planner에게 특히 중요)

이 환경에는 사용자의 범용 `/pages` 슬래시 커맨드와 `mdbook-utils` 스킬이 이미 존재하며, 그 기본 관례는 다음과 같다:
- 별도 `book/` 디렉터리를 만들지 않고 **소스 디렉터리 자체가 mdBook 프로젝트**(`book.toml`의 `src = "."`)가 되는 것을 선호.
- CI는 `peaceiris/actions-mdbook@v2`로 mdBook을 설치하고, 빌드된 `docs/`를 **git commit + push로 리포지토리에 반영**한 뒤, GitHub Pages 저장소 설정을 "Deploy from a branch"(예: `master`/`docs` 폴더)로 사용.

이번 phase에서는 **이 기본 관례를 의도적으로 따르지 않는다.** 이유:
1. 이 프로젝트는 문서 파일 한 벌짜리 단순 사이트가 아니라 `book/`(mdBook 소스) + `examples/`(실행 가능한 코드) + `outputs/`(캡처된 실행 결과)라는 **3개의 독립적인 최상위 트리**를 가진다. "소스 디렉터리 자체가 프로젝트"라는 단순화 전제가 애초에 성립하지 않는다.
2. 빌드 산출물(`docs/` 또는 `book/book/`)을 매번 git에 커밋하면, 이미 `examples/*.py` + `outputs/*.out`를 커밋해 "실제 실행 결과"를 증명하는 이 프로젝트의 핵심 가치와 별개로 **불필요한 대용량 HTML 커밋 노이즈**가 히스토리에 계속 쌓인다.
3. `.planning/research/STACK.md`·`ARCHITECTURE.md`(이 프로젝트 전용, 라이브 검증 포함 HIGH confidence)가 이미 공식 OIDC 배포 방식(`configure-pages`/`upload-pages-artifact`/`deploy-pages`)으로 구체적 워크플로 YAML까지 확정해두었다 — 이 phase 연구는 그 결정을 재확인했을 뿐 뒤집을 근거를 찾지 못했다.

**따라서 planner는 STACK.md의 CI YAML(공식 액션 조합)을 그대로 쓰고, `/pages`/`mdbook-utils` 스킬의 "peaceiris + docs 커밋" 방식은 채택하지 않는다.** 다만 `mdbook-docs-images.skill.md`의 이미지/구조 규칙(이미지는 `src/images/` 하위, 캡션은 이미지 바로 아래 기울임꼴, HTML 태그 금지, admonition 미사용)은 이 phase의 챕터 작성 스타일에도 그대로 적용 가치가 있으므로 채택 권장(이번 phase는 이미지가 필수는 아니지만, 이후 LangGraph 챕터의 mermaid/이미지 삽입 시 이 규칙을 재사용).

## Metadata

**Confidence breakdown:**
- mdBook include 경로 해석 / book.toml 구조: HIGH — 실제 빌드로 재현
- `examples/` 패키지화(import 문제 해결): HIGH — 3가지 실행 방식 모두 실측
- GitHub Pages 활성화 절차: HIGH — 실제 `gh api`/`gh repo view` 실행 + 공식 REST 문서 교차 확인
- LangChain 기초 API(멀티턴/few-shot/LCEL/구조화출력/스트리밍/결정론): HIGH — 이 세션에서 로컬 엔드포인트에 대해 전부 재실행 확인
- 캡처 러너 스크립트의 구체 구현: MEDIUM — 설계 원칙은 확정, 정확한 코드는 계획 단계에서 작성
- `check_fresh.py` 포함 여부: LOW → 이 문서에서 "이번 phase 범위 밖"으로 명확히 권고(v2 요구사항과 일치)

**Research date:** 2026-09-11
**Valid until:** 이 phase의 인프라 부분(mdBook/GitHub Actions/uv 패키징)은 30일 이상 유효(안정적 도구). LangChain API 라이브 검증 부분은 프로젝트 레벨 STACK.md와 동일하게 로컬 LLM 서버 설정이 바뀌면(모델 교체, speculative decoding 설정 변경) 재검증 필요.
