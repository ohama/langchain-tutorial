# Phase 3: RAG - Research

**Researched:** 2026-09-11
**Domain:** 한국어/다국어 로컬 RAG 파이프라인 (문서 로딩 → 분할 → `bge-m3` 임베딩(MPS) → Chroma 검색 → LCEL 생성), mdBook 저작 파이프라인 위에서 구현
**Confidence:** HIGH — 이 세션에서 별도 scratch `uv` 프로젝트(Python 3.14)에 실제 스택을 설치하고, 이 프로젝트의 실제 로컬 LLM 엔드포인트(`examples/.env` 설정)와 Apple Silicon MPS 백엔드에 대해 로딩·임베딩·Chroma 색인/검색·LCEL RAG 체인 실행까지 전부 라이브로 검증했다. 메모리·결정성·노이즈 억제 결과는 모두 실측치다.

## Summary

Phase 3는 `.planning/research/STACK.md`가 이미 한 차례 이 스택(langchain-text-splitters, langchain-huggingface, sentence-transformers, langchain-chroma, chromadb, torch, `BAAI/bge-m3`)을 Python 3.14에서 라이브 검증해두었다. 이번 연구는 그 결과를 다시 한번 독립적으로 재현하고, 계획 수립에 필요한 구체적 수치(메모리 증가량, 로딩 시간, 결정성, 노이즈 억제 방법, 샘플 문서 설계, 청킹 파라미터, 챕터/플랜 구조)까지 실측으로 채웠다.

결론부터 말하면 `bge-m3`를 MPS에서 그대로 써도 된다. 로드 후 상주 메모리 증가는 약 1GB 내외이고(이 머신은 로컬 LLM 서버와 여유 있게 공존 가능한 사양), 첫 실행(모델 다운로드 포함)은 약 40~45초, 이후 로컬 캐시에서의 재로딩은 약 8~9초로 `STATE.md`가 우려한 "첫 로드 약 1분"과 부합한다. 임베딩 벡터는 같은 프로세스 재실행 간, 그리고 `mps`/`cpu` 장치 간에도 (검증한 소수점 자리까지는) 완전히 동일했고, Chroma 유사도 검색 순서·점수, LCEL RAG 체인의 최종 한국어 답변까지 두 번의 독립 실행에서 타이밍 텍스트를 제외하고 바이트 단위로 동일했다. 즉 Phase 2가 도입한 "스크래치 재실행 diff" 결정성 게이트를 Phase 3에도 그대로 적용할 수 있다. 유일한 실무 주의점은 `HF_HUB_DISABLE_PROGRESS_BARS`/`TRANSFORMERS_VERBOSITY`/`TOKENIZERS_PARALLELISM`/`ANONYMIZED_TELEMETRY` 환경변수를 **`HuggingFaceEmbeddings`를 import하기 전에** 설정하지 않으면 `tqdm` 진행바("Loading weights: 100%|...")가 캡처 stdout에 섞여 들어간다는 점이다(라이브로 재현·수정 확인함).

**Primary recommendation:** `examples/shared/config.py`에 `get_embeddings()`를 새 ANCHOR로 추가하되, `torch`/`langchain_huggingface` import와 노이즈 억제 환경변수 설정을 함수 내부에서 지연 수행한다(모듈 최상단 import 금지 — 그래야 ch01/ch02가 `shared.config`를 로드할 때마다 불필요하게 torch를 끌어오지 않는다). Chroma는 `persist_directory` 없이 매 예제 스크립트가 처음부터 색인을 다시 만드는 ephemeral 방식을 쓴다(색인이 1초 미만이라 영속화 이득이 없고, 커밋 대상 디렉터리 문제도 원천 차단됨). `RecursiveCharacterTextSplitter`는 `langchain_text_splitters`에서 그대로 가져온다.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain-text-splitters | 1.1.2 | `RecursiveCharacterTextSplitter` | `langchain-community` 밖의 독립 유지보수 패키지. `examples/pyproject.toml`에 아직 없음 — 신규 추가 필요. RAG-01 요구사항이 명시적으로 지정. |
| langchain-huggingface | 1.2.2 | `HuggingFaceEmbeddings` | 로컬 `sentence-transformers` 모델을 LangChain `Embeddings` 인터페이스로 노출하는 공식 파트너 패키지. 라이브 검증: `model_name="BAAI/bge-m3", model_kwargs={"device": "mps"}, encode_kwargs={"normalize_embeddings": True}` API가 현재도 그대로 유효. |
| sentence-transformers | 6.0.1 | 임베딩 로딩/추론 엔진 | `langchain-huggingface`의 필수 하위 의존성. `torch.backends.mps.is_available() == True` 확인. |
| torch | 2.14.0 (macOS arm64) | MPS 백엔드 | `sentence-transformers`가 내부적으로 사용. 이번 설치에서 `.venv` 내 용량 563MB로 가장 큰 의존성. |
| langchain-chroma | 1.1.0 | `Chroma` 벡터스토어 래퍼 | `Chroma.from_documents(docs, embedding=..., persist_directory=None)`(ephemeral) + `similarity_search`/`similarity_search_with_score`를 라이브로 재검증. |
| chromadb | 1.5.9 | Chroma 임베디드 엔진 | `langchain-chroma`의 의존성으로 자동 설치. 서버 프로세스 불필요. |
| BAAI/bge-m3 (HF 모델) | 모델 카드 기준 최신 | 다국어(한국어 포함) 임베딩, 1024차원 | RAG-02 요구사항이 명시. 라이브 재검증: 다운로드 포함 첫 로드 ~40~45초, 캐시 재사용 시 ~8~9초, 로드 후 상주 메모리 증가 약 1GB, MPS/CPU 간 임베딩 값이 소수점 6자리까지 동일. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain-core | 1.6.2 (이미 설치됨) | `Document`, `RunnablePassthrough`, `StrOutputParser`, `ChatPromptTemplate` | RAG 체인 조립에 전부 필요. 신규 설치 불필요, 이미 `examples/pyproject.toml`에 있음. |
| pathlib (표준 라이브러리) | — | 텍스트/마크다운 파일 → `Document` | `langchain-community` 로더 대신 사용 (PITFALLS.md에서 이미 "죽은 경로"로 확정). |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `BAAI/bge-m3` | `intfloat/multilingual-e5-small` | 실측 결과 `bge-m3`가 메모리(~1GB)·로딩 시간(~8~45초) 모두 이 머신에서 전혀 문제되지 않음이 확인됐으므로 **다운그레이드 불필요**. 코드 변경은 `EMBEDDING_MODEL` 환경변수 한 줄이면 되므로, 다른(더 제약된) 환경의 독자를 위한 각주로만 언급. |
| `persist_directory` 지정 Chroma | ephemeral(인자 생략) Chroma | 영속화하면 재시작 없이 인덱스 재사용 가능하지만, 이 책의 예제는 매 실행이 독립 프로세스이고 색인이 1초 미만이라 이득이 없고, `.gitignore` 관리·디스크 잔여물 문제만 생김. |
| `Chroma` | `langchain_core.vectorstores.InMemoryVectorStore` | STACK.md가 "첫 RAG 개념" 도입용으로 언급했지만, 이번 페이즈 요구사항(RAG-03)이 Chroma를 명시했으므로 이 페이즈에서는 Chroma로 통일. |

**Installation (planner가 실제 execute 단계에서 `examples/`에 대해 실행):**
```bash
cd examples
uv add langchain-text-splitters langchain-chroma langchain-huggingface sentence-transformers
```
이 4개만 명시적으로 추가하면 `torch`/`chromadb`는 전이 의존성으로 함께 잠긴다. Scratch 검증 기준 `uv.lock`에 약 145개 패키지, `.venv` 총 용량 약 1.2GB(그중 `torch`가 563MB)가 추가된다. 설치 자체는 실패 없이 수 분 내 끝난다(대부분 사전 빌드된 `cp314`/`abi3` 휠). **CI는 영향 없음** — `deploy.yml`은 `mdbook build book`만 실행하고 `examples/`를 전혀 설치·실행하지 않으므로(라이브 확인: `.github/workflows/deploy.yml`에 Python/uv 스텝 없음, STACK.md에 기록된 CI 워크플로 그대로), 이 추가로 인해 CI 시간이나 동작이 전혀 달라지지 않는다.

`BAAI/bge-m3` 모델 가중치는 Hugging Face Hub 캐시(`~/.cache/huggingface/hub`)에 약 4.3GB로 저장된다(실측). 저장소에는 들어가지 않고, 최초 실행 시 1회만 네트워크가 필요하다(이후 실행은 로컬 캐시만 사용, 실측 재로딩 8~9초).

## Architecture Patterns

### Recommended Project Structure

```
examples/
├── shared/
│   └── config.py            # get_chat_model, get_structured_model에 이어 get_embeddings() 추가 (신규 ANCHOR)
├── data/
│   └── ch03_rag/            # 신규: 원본 한국어 샘플 문서 3개 (마크다운)
│       ├── 01_langchain_intro.md
│       ├── 02_rag_guide.md
│       └── 03_company_handbook.md
└── ch03_rag/
    ├── 01_load_split.py     # RAG-01
    ├── 02_embed_search.py   # RAG-02 + RAG-03
    └── 03_rag_chain.py      # RAG-04

outputs/ch03_rag/{01_load_split,02_embed_search,03_rag_chain}.out
book/src/ch03_rag/{01_load_split,02_embed_search,03_rag_chain}.md
```

### Pattern 1: `get_embeddings()`를 config.py에 지연 import로 추가

**What:** `shared/config.py`의 `get_chat_model` 패턴을 그대로 따르되, 무거운 `torch`/`langchain_huggingface` import와 노이즈 억제 환경변수 설정을 함수 **내부**에서 수행한다.
**When to use:** RAG 챕터 전체가 임베딩 모델을 만드는 유일한 진입점.
**Why lazy import matters (라이브 실측):** `run_examples.py`는 모든 캡처 실행에서 무조건 `from shared.config import get_chat_model, load_settings`를 최상단에서 import한다. 만약 `config.py`가 모듈 최상단에서 `from langchain_huggingface import HuggingFaceEmbeddings`를 한다면, ch01/ch02처럼 임베딩과 무관한 챕터를 캡처할 때도 매번 `torch` import(실측 약 0.4~0.6초)가 강제되고, 더 중요하게는 RAG와 무관한 챕터의 캡처가 `torch`/`transformers` 관련 이슈에 불필요하게 연쇄 실패할 위험이 생긴다. 함수 내부 지연 import로 이 결합을 없앤다(라이브로 지연 import 패턴이 노이즈 억제와 함께 문제없이 동작함을 확인).

**Example (라이브 검증한 동작을 그대로 코드화):**
```python
# Source: 이 세션의 scratch 실행 (langchain-huggingface 1.2.2, sentence-transformers 6.0.1)
# ANCHOR: embeddings
def get_embeddings(**overrides):
    # HuggingFaceEmbeddings를 import하기 "전에" 반드시 설정해야 진행바/로그가 stdout에 섞이지 않는다 (라이브 확인)
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

    from langchain_huggingface import HuggingFaceEmbeddings  # 지연 import
    import torch

    model_name = os.environ.get("EMBEDDING_MODEL", "").strip() or "BAAI/bge-m3"
    device = os.environ.get("EMBEDDING_DEVICE", "").strip()
    if not device:
        device = "mps" if torch.backends.mps.is_available() else "cpu"

    params = dict(
        model_name=model_name,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )
    params.update(overrides)
    return HuggingFaceEmbeddings(**params)
# ANCHOR_END: embeddings
```
`.env.example`에는 선택 항목으로 다음을 추가할 것을 권장(생략 시 기본값 `BAAI/bge-m3` + 자동 device 판별로 그대로 동작):
```
# 임베딩 모델 설정 (3부 RAG, 선택 — 비워두면 BAAI/bge-m3 + 자동 device 판별)
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=mps
```

### Pattern 2: `langchain-community` 없이 마크다운 → `Document`

**What:** `pathlib.Path.read_text()` + `Document(page_content=..., metadata={"source": relative_name})`.
**When to use:** RAG-01. 이미 PITFALLS.md/STACK.md가 확정한 패턴을 그대로 재사용.
**Example (라이브 검증):**
```python
# Source: 이 세션 라이브 실행
from pathlib import Path
from langchain_core.documents import Document

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "ch03_rag"

def load_documents() -> list[Document]:
    docs = []
    for path in sorted(DATA_DIR.glob("*.md")):
        docs.append(Document(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name}))
    return docs
```
`metadata["source"]`는 **파일명만**(`path.name`) 저장한다 — 절대경로(`path`)를 그대로 넣으면 캡처 시 `mask_text`가 `/Users/...`를 `~`로 자동 치환해 누출은 막아주지만(라이브로 `scripts/masking.py`의 `_USERS_PATH_RE` 확인), 애초에 상대적/파일명만 쓰는 편이 재현성·가독성에 낫다.

### Pattern 3: 청킹 (Korean 대상 `RecursiveCharacterTextSplitter`)

**What:** `RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50, add_start_index=True)`.
**Why these numbers:** 라이브 실험에서 `chunk_size=200, chunk_overlap=40`으로 두 개의 ~250자 문단짜리 문서가 문서당 2개, 총 4개 청크로 자연스럽게 갈라졌다(문단 경계에서 분리, 문장이 중간에 잘리지 않음). 이 페이즈에서 권장하는 약 1000~1500자 분량의 문서 3개(아래 "샘플 문서" 참고)에는 `chunk_size=300, chunk_overlap=50`이 문서당 약 4~6개, 총 약 12~18개 청크를 만들어 "청크 수·내용이 실제 출력에 나타난다"(성공 기준 1)를 풍부하게 보여주기 좋다. 한국어는 공백 기준 형태소 분리가 약하지만, `RecursiveCharacterTextSplitter`는 문자 단위 분리(`\n\n`, `\n`, `. `, ` `, `""` 순서의 기본 separator)라 한국어에도 그대로 잘 작동함을 실측으로 확인(문장이 어색하게 안 잘리고 문단 경계에서 갈라짐).
**Example (라이브 실측 출력 그대로):**
```
문서 2개 -> 청크 4개
  [0] len=168 source=langchain.md start_index=0
  [1] len=81 source=langchain.md start_index=160
  [2] len=158 source=rag.md start_index=0
  [3] len=85 source=rag.md start_index=148
```
`add_start_index=True`로 만든 `metadata["start_index"]`도 함께 출력하면 "분할이 원문의 어디를 가리키는지"를 독자가 눈으로 확인할 수 있어 좋은 교육 소재가 된다(라이브 확인, 재현 가능).

### Pattern 4: Ephemeral Chroma (persist 없음) + 매 예제가 처음부터 색인

**What:** `Chroma.from_documents(chunks, embedding=get_embeddings(), collection_name="...")` — `persist_directory` 인자를 아예 주지 않는다.
**When to use:** 이 페이즈의 모든 RAG 예제. 라이브 확인: `persist_directory`를 생략하면 프로세스 종료 후 현재 디렉터리에 어떤 파일도 남지 않는다(`os.listdir(".")`로 확인, Chroma가 완전히 인메모리로 동작).
**Why not persist:** (1) 색인 시간이 실측 1초 미만(문서 몇 개 규모)이라 영속화 이득이 없음. (2) `run_examples.py`는 각 `.py`를 **독립 서브프로세스**로 실행하므로, 한 챕터에서 만든 영속 디렉터리를 다음 챕터가 그대로 재사용하는 구조는 애초에 안 맞음(각 스크립트가 매번 `sys.executable py_file`로 새로 뜸). (3) 영속 디렉터리를 쓰면 리포에 커밋하면 안 되는 산출물이 생겨 `.gitignore`/hygiene 체크가 늘어난다. **결론: 3개 챕터 모두 "문서 로드 → 분할 → 임베딩 → 색인"을 각자 처음부터 반복**(단순함·재현성 우선, Phase 2가 `MAX_ITERS`처럼 매번 명시적으로 전체를 보여주는 스타일과 일관됨).
**텔레메트리:** `ANONYMIZED_TELEMETRY=False`를 설정해도(라이브 확인) 이미 로컬 실행에서는 chromadb가 별다른 네트워크 요청/stderr 노이즈를 내지 않았지만, 명시적으로 꺼두는 것이 안전하고 문서화 가치도 있다(`Chroma.from_documents` 호출 전 `os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")`).

### Pattern 5: LCEL RAG 체인

**What:** `{"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt | get_chat_model() | StrOutputParser()`.
**Example (라이브로 실제 한국어 답변까지 검증):**
```python
# Source: 이 세션 라이브 실행 (examples/.env의 로컬 LLM 엔드포인트 대상)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

def format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
prompt = ChatPromptTemplate.from_template(
    "다음 문서를 참고해서 질문에 한국어로 간단히 답하세요.\n\n문서:\n{context}\n\n질문: {question}"
)
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | get_chat_model()
    | StrOutputParser()
)
answer = chain.invoke("RAG는 무엇을 하는 기법이야?")
# 실측 답변: "RAG는 검색으로 찾은 문서를 프롬프트에 넣어 LLM이 그 내용을 바탕으로 답변을 생성하게 하는 기법입니다."
```
Phase 1이 확인한 `StrOutputParser` 반환값이 `str` 서브클래스 `TextAccessor`라는 사실이 이 체인에서도 그대로 재현됨(라이브 확인: `type(answer).__name__ == 'TextAccessor'`, `isinstance(answer, str) is True`). 챕터 프로즈에서 "`str`처럼 다루면 된다"고 설명하되, 이전 챕터(1부 4장 LCEL)와 같은 표현으로 일관성 있게 언급.

### Anti-Patterns to Avoid

- **`config.py` 최상단에서 `torch`/`langchain_huggingface` import:** ch01/ch02 캡처마다 불필요한 무거운 import를 강제함(Pattern 1 참고). 반드시 `get_embeddings()` 함수 내부에서 지연 import.
- **`HuggingFaceEmbeddings` import 후에 노이즈 억제 환경변수 설정:** 이미 늦다 — `tqdm` 진행바가 새더라도 그때는 못 막는다(라이브로 순서 실패 재현: env 설정 없이 실행하면 `Loading weights: 100%|...` 줄이 stdout/stderr에 그대로 찍힘). 반드시 import **직전**에 `os.environ`을 설정.
- **Chroma `persist_directory`를 리포 경로(`examples/...`)로 지정:** 커밋되면 안 되는 SQLite/바이너리 산출물이 생기고 `.gitignore` 관리 부담이 생김. Pattern 4처럼 아예 생략.
- **`similarity_search`에 원시 `float`를 그대로 print:** 부동소수점 표현 차이로 재현성 diff가 흔들릴 수 있으니(이번 실측에서는 문제없었지만) `round(score, 4)`처럼 반올림해서 출력.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 텍스트를 의미 단위로 자르기 | 직접 정규식/문장 분리 로직 | `RecursiveCharacterTextSplitter` | 문단→줄→문장→공백 순으로 재귀적으로 시도하는 알고리즘이 이미 있고, `add_start_index`로 원문 위치까지 추적해줌. 한국어에도 문자 단위라 그대로 잘 동작함을 실측 확인. |
| 임베딩 벡터 정규화·차원 확인 | 직접 L2 정규화 코드 | `encode_kwargs={"normalize_embeddings": True}` | `HuggingFaceEmbeddings`가 이미 지원. 직접 구현하면 코사인 유사도 계산과 미묘하게 어긋날 위험. |
| 벡터 유사도 검색 + 메타데이터 필터 | 직접 코사인 유사도 루프 | `Chroma.similarity_search`/`similarity_search_with_score` | Chroma가 인덱싱·거리 계산·정렬을 전부 처리. 직접 구현은 문서 수가 늘면 O(n) 선형 스캔 코드를 재발명하는 것과 같음. |
| HF Hub 다운로드 진행바/로그 끄기 | stdout을 파싱해서 필터링 | `HF_HUB_DISABLE_PROGRESS_BARS`/`TRANSFORMERS_VERBOSITY` 환경변수 | 라이브러리가 공식으로 지원하는 끔 스위치가 있는데 출력을 사후 필터링하면 깨지기 쉽고 유지보수 비용만 늘어남. |

**Key insight:** 이 페이즈에서 "새로 만들어야 하는 코드"는 사실상 `shared/config.py`의 `get_embeddings()` 하나뿐이고, 나머지는 전부 검증된 라이브러리 조합을 그대로 쓰면 된다.

## Common Pitfalls

### Pitfall 1: 임베딩 모델 로딩 시 stdout/stderr 오염 (진행바·로그)

**What goes wrong:** 환경변수 없이 `HuggingFaceEmbeddings(model_name="BAAI/bge-m3", ...)`를 처음 호출하면 `Loading weights: 100%|██████████| 391/391 [...]` 같은 `tqdm` 진행바 줄이 stdout 또는 stderr에 그대로 출력된다(라이브로 재현 확인).
**Why it happens:** `transformers`/`safetensors`가 가중치 로딩 시 기본적으로 `tqdm` 진행바를 그리고, `huggingface_hub`도 다운로드 시 별도 진행바를 그린다. 이 두 종류 모두 기본값은 "켜짐"이다.
**How to avoid:** `HF_HUB_DISABLE_PROGRESS_BARS=1`, `TRANSFORMERS_VERBOSITY=error`, `TOKENIZERS_PARALLELISM=false`를 `HuggingFaceEmbeddings`를 import하기 **이전** 코드 경로에서 설정한다(Pattern 1). 라이브로 이 조합이 stdout·stderr 모두를 완전히 비움을 두 가지 시나리오(무관한 import가 먼저 일어난 뒤 지연 설정하는 경우 포함)에서 확인했다.
**Warning signs:** `.out` 캡처에 `it/s]` 또는 `Loading weights` 문자열이 보이면 이 설정이 빠진 것.

### Pitfall 2: `run_examples.py`의 공통 import가 전체 챕터에 무거운 의존성을 강제

**What goes wrong:** `run_examples.py`는 모든 실행에서 무조건 `shared.config`를 import한다. `get_embeddings()`용 `torch`/`langchain_huggingface` import를 `config.py` 최상단에 두면, ch01/ch02 챕터 캡처(및 매 `run_examples.py` 실행의 웜업 단계)까지 불필요하게 이 무거운 모듈들을 로드하게 된다.
**Why it happens:** "설정은 한 곳에" 원칙을 지키려다 import 위치까지 안 가리는 경우 흔히 발생.
**How to avoid:** Pattern 1의 지연 import. 실측 오버헤드는 약 0.4~0.6초로 크지는 않지만, 그보다 더 중요한 건 RAG와 무관한 챕터가 `torch` 관련 문제에 연쇄적으로 영향받지 않도록 결합을 끊는 것.
**Warning signs:** ch01/ch02 캡처 로그의 웜업 단계가 이전보다 눈에 띄게 느려지거나, `torch`/`transformers` 관련 경고가 RAG와 무관한 챕터 실행에 섞여 나옴.

### Pitfall 3: 절대경로가 메타데이터·출력에 섞여 들어감

**What goes wrong:** `Document(metadata={"source": str(path)})`처럼 절대경로 객체를 그대로 문자열화하면 캡처된 `.out`에 `/Users/...` 경로가 남는다.
**Why it happens:** `pathlib.Path`를 그대로 쓰다 보면 무심코 절대경로가 흘러들어가기 쉽다.
**How to avoid:** `metadata={"source": path.name}`처럼 항상 파일명(또는 리포 루트 기준 상대경로 문자열)만 저장한다. `mask_text`가 `/Users/...`를 `~`로 자동 치환해주긴 하지만(안전망), 애초에 상대경로만 쓰는 게 원칙에 맞고 재현성도 더 좋다(마스킹된 값이 독자 환경에서 그대로 재현되지 않기 때문).
**Warning signs:** `git grep -n "/Users/" outputs/ch03_rag` 또는 `check_leaks.py`가 `users-path`를 검출.

### Pitfall 4: Chroma `similarity_search` 결과를 결정성 없이 그대로 출력

**What goes wrong:** `tool_call_id`처럼 매 실행 무작위인 값은 없지만, 부동소수점 거리 점수를 반올림 없이 그대로 출력하면 아주 드물게 마지막 자리가 흔들릴 수 있다(이번 실측 두 번의 완전 독립 실행에서는 소수점 4자리까지 완전히 동일했지만, 안전하게 반올림 규칙을 명시하는 편이 좋다).
**How to avoid:** 점수는 `round(score, 4)`로, 임베딩 값 예시는 `round(x, 6)`로 고정 자리수 반올림 후 출력. 청크 수·문서 소스·검색 순위처럼 "구조"를 보여주는 값을 우선하고, 원시 실수는 반올림해서 보조적으로만 보여준다.

## Code Examples

### 문서 로딩 + 분할 (RAG-01)
```python
# Source: 이 세션 라이브 실행 결과 그대로
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "ch03_rag"

def load_documents() -> list[Document]:
    return [
        Document(page_content=p.read_text(encoding="utf-8"), metadata={"source": p.name})
        for p in sorted(DATA_DIR.glob("*.md"))
    ]

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50, add_start_index=True)
chunks = splitter.split_documents(load_documents())
print(f"문서 {len(load_documents())}개 -> 청크 {len(chunks)}개")
```

### 임베딩 + 벡터스토어 + 검색 (RAG-02, RAG-03)
```python
# Source: 이 세션 라이브 실행, 실제 결과 반환값 형태 확인
from shared.config import get_embeddings
from langchain_chroma import Chroma

embeddings = get_embeddings()
sample_vec = embeddings.embed_query("테스트 문장입니다.")
print(f"임베딩 차원: {len(sample_vec)}")  # 실측: 1024

vectorstore = Chroma.from_documents(chunks, embedding=embeddings, collection_name="ch03_rag")
for doc, score in vectorstore.similarity_search_with_score("RAG는 무엇을 하는 기법이야?", k=2):
    print(f"  - {doc.metadata['source']}: {round(score, 4)} | {doc.page_content[:40]!r}")
```

### LCEL RAG 체인 (RAG-04)
```python
# Source: 이 세션 라이브 실행, 실제 한국어 답변까지 확인 (Pattern 5 참고)
from shared.config import get_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

def format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
prompt = ChatPromptTemplate.from_template(
    "다음 문서를 참고해서 질문에 한국어로 간단히 답하세요.\n\n문서:\n{context}\n\n질문: {question}"
)
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | get_chat_model() | StrOutputParser()
)
print(chain.invoke("RAG는 무엇을 하는 기법이야?"))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `langchain_community.document_loaders.TextLoader`/`DirectoryLoader` | `pathlib.Path.read_text()` + `Document(...)` 직접 생성 | `langchain-community` 2026-05-22 sunset 공지, 2026-06-19 archive(이미 STACK.md/PITFALLS.md에서 확정) | RAG-01은 처음부터 `langchain-community` 없이 설계해야 함. 별도 설치도 불필요. |
| `langchain_community.vectorstores.Chroma` | `langchain_chroma.Chroma` | 위와 동일한 커뮤니티 분리 흐름 | import 경로만 다르고 API는 유사하지만, 유지보수되는 쪽을 써야 향후 langchain 업그레이드에도 안전. |
| `langchain_community.embeddings.HuggingFaceEmbeddings` | `langchain_huggingface.HuggingFaceEmbeddings` | 동일 | 이번 세션에 라이브로 신규 경로가 정상 동작함을 재확인. |

**Deprecated/outdated:** 위 세 항목 모두 `langchain-community`를 통한 구경로이며, 이 프로젝트는 애초에 `langchain-community`를 의존성에 추가하지 않으므로 혼동의 여지가 없다.

## Open Questions

1. **Chroma의 `similarity_search` 순서·점수가 langchain-chroma/chromadb 패치 버전이 바뀌어도 계속 안정적일지**
   - What we know: 이번 세션에서 완전히 동일한 버전 조합(`langchain-chroma` 1.1.0, `chromadb` 1.5.9)으로 두 번의 독립 실행 결과가 타이밍을 제외하고 바이트 단위로 동일했다.
   - What's unclear: `uv add`가 이 정확한 버전을 다시 고정해줄지(락파일이 없으므로 실행 시점의 최신 호환 버전이 잡힘). 마이너 패치가 코사인 거리 계산 순서를 바꿀 가능성은 낮지만 0은 아니다.
   - Recommendation: 플랜 실행 시 `uv add` 직후 `uv.lock`에 고정된 정확한 버전을 SUMMARY에 기록해두고, 스크래치 재실행 diff 게이트(Phase 2와 동일 패턴)로 매 플랜마다 실제로 재확인한다. 문제가 생기면(점수/순서가 흔들리면) 출력에서 원시 점수를 아예 빼고 "상위 문서 제목/소스"만 보여주는 쪽으로 낮추면 된다.

2. **`EMBEDDING_DEVICE=mps`가 지원되지 않는 독자 환경(Linux/Windows, 구형 macOS)에서 `get_embeddings()`가 어떻게 실패하는지**
   - What we know: `torch.backends.mps.is_available()`가 `False`인 환경에서는 코드상 자동으로 `cpu`로 폴백하도록 설계했다(Pattern 1).
   - What's unclear: 이 폴백 경로 자체를 이번 세션에서 직접 재현하지는 못했다(이 머신은 MPS가 항상 사용 가능). CPU 장치로 명시 지정한 케이스는 검증했지만, "MPS 미탑재 환경에서 자동판별이 cpu로 떨어지는 코드 경로"는 로직 검토로만 확인.
   - Recommendation: 부록(또는 챕터 각주)에 "MPS가 없는 환경에서는 자동으로 CPU를 쓰며 느려질 수 있다"는 문장을 남기고, 실제 자동판별 실패 시나리오까지 계획 단계에서 재현 의무를 지우지 않는다(우선순위 낮음, 이 프로젝트가 Apple Silicon 전용임을 이미 전제).

## Sources

### Primary (HIGH confidence)
- 이 세션의 라이브 실행 (scratch `uv --python 3.14` 프로젝트, `<scratchpad>/rag-experiment`): `langchain` 1.4.0, `langchain-core` 1.6.2, `langchain-openai` 1.6.2, `langchain-text-splitters` 1.1.2, `langchain-chroma` 1.1.0, `langchain-huggingface` 1.2.2, `sentence-transformers` 6.0.1, `torch` 2.14.0, `chromadb` 1.5.9 설치·임포트·실행. `HuggingFaceEmbeddings(model_name="BAAI/bge-m3", device="mps"/"cpu")` 로딩·임베딩, `Chroma.from_documents`(ephemeral) + `similarity_search`/`similarity_search_with_score`, `RecursiveCharacterTextSplitter`(청크/오버랩/`add_start_index`), 이 프로젝트의 실제 로컬 LLM 엔드포인트를 대상으로 한 LCEL RAG 체인 전체(`retriever | format_docs | prompt | model | StrOutputParser`)까지 end-to-end 실행 확인 (2026-09-11)
- 메모리 측정: `resource.getrusage(RUSAGE_SELF).ru_maxrss`로 import 전/모델 로드 후/임베딩 후 RSS 실측 (mps: 로드 후 +약 1GB, cpu: 로드+임베딩 후 +약 2GB)
- 결정성 측정: 동일 스크립트(`rag_test.py`) 2회 완전 독립 실행 → `diff`로 비교, 소요 시간 텍스트를 제외한 모든 줄(청크 분할, 임베딩 기반 검색 순서·점수, LCEL 체인의 실제 한국어 답변) 완전 동일
- 노이즈 억제 측정: `HF_HUB_DISABLE_PROGRESS_BARS`/`TRANSFORMERS_VERBOSITY`/`TOKENIZERS_PARALLELISM` 설정 유무에 따른 stdout/stderr 차이를 직접 재현 (미설정 시 `tqdm` 진행바 누출 확인 → 설정 후 완전히 제거됨 확인, import 순서를 바꿔도(지연 import) 동일하게 동작함을 재확인)
- 이 리포지토리 자체 코드: `examples/pyproject.toml`, `examples/shared/config.py`, `scripts/run_examples.py`, `scripts/check_book.py`, `scripts/check_leaks.py`, `scripts/masking.py`, `book/src/SUMMARY.md`, `book/book.toml`, `.planning/phases/02-tool-calling/02-01-PLAN.md`/`02-01-SUMMARY.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` (직접 읽고 확인)

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md`, `.planning/research/PITFALLS.md` — 같은 날짜(2026-09-11)에 별도 세션이 동일 스택을 이미 라이브 검증해둔 결과. 이번 세션의 독립 재검증과 수치가 일치함(예: bge-m3 1024차원, MPS 사용 가능, `langchain-community` sunset).

### Tertiary (LOW confidence)
- 없음 — 이번 연구는 웹 검색 없이 전부 이 프로젝트의 실제 코드와 라이브 실행으로 검증했다.

## Plan & Chapter Structure Recommendation

**챕터 3개, 요구사항 매핑:**
1. `ch03_rag/01_load_split.py` → `book/src/ch03_rag/01_load_split.md` — "문서 로딩과 분할" (RAG-01)
2. `ch03_rag/02_embed_search.py` → `book/src/ch03_rag/02_embed_search.md` — "임베딩과 벡터스토어 검색" (RAG-02 + RAG-03, 임베딩 차원 출력과 Chroma 검색이 자연스럽게 한 챕터)
3. `ch03_rag/03_rag_chain.py` → `book/src/ch03_rag/03_rag_chain.md` — "LCEL RAG 체인" (RAG-04)

`book/src/SUMMARY.md`에 `# 3부 RAG` 파트를 `# 2부 도구 호출` 다음, `# 부록` 앞에 추가.

**샘플 한국어 문서 (`examples/data/ch03_rag/`):** 저작권 문제가 없는 원작 콘텐츠 3개, 각 약 1000~1500자, 서로 뚜렷이 다른 주제로(질의 시 정답 문서가 명확히 구분되도록):
- `01_langchain_intro.md` — LangChain 핵심 개념 노트(Runnable, LCEL, 체인)
- `02_rag_guide.md` — RAG 개념·단계 설명(이번 세션 실측 예제와 동일 소재 확장)
- `03_company_handbook.md` — 가상 회사의 사내 정책(예: 휴가 규정, 재택근무 규정) — 순수 창작, 실존 회사와 무관함을 문서 내 명시

`chunk_size=300, chunk_overlap=50`이면 문서당 약 4~6청크, 총 약 12~18청크로 "청크 수·내용" 성공 기준(1)을 풍부하게 보여줄 수 있다(이번 세션 소형 샘플로 실측 검증한 비율 기준 추정).

**상태 공유 없음, 매번 재구성:** Chroma는 ephemeral로 매 스크립트가 로드→분할→임베딩→색인을 처음부터 반복(Pattern 4). 색인 자체가 1초 미만이라 비용이 거의 없고, `run_examples.py`가 각 파일을 독립 서브프로세스로 실행하는 구조와도 맞다.

**`run_examples.py` 변경 불필요:** 기본 `--timeout`이 600초라 첫 실행(모델 다운로드 포함 최대 약 45초) + 색인(1초 미만) + LLM 호출(실측 5~21초)을 합쳐도 여유가 크다. 웜업 단계(`get_chat_model(max_tokens=16).invoke("ping")`)는 임베딩 모델을 예열하지 않지만, 임베딩 모델 자체의 콜드 로드(최초 1회, ~45초)는 각 예제 스크립트 안에서 자연스럽게 발생하고 이후 캐시로 빨라지므로 스크립트나 러너 수정 없이 그대로 동작한다.

**릴리스 게이트 (Phase 2의 `02-01-PLAN.md` Task 3를 그대로 미러링):**
1. 스크래치 재실행 diff — `run_examples.py ch03_rag --outputs-dir $SCRATCH/rerun` 후 `diff`. 타이밍 텍스트를 제외하면 완전 동일해야 함(이번 세션 실측 근거로 기대 가능). 다르면(원시 점수 등) 반올림 규칙 강화 후 재캡처.
2. `check_book.py` (전체 10챕터: ch01 5 + ch02 2 + ch03 3) → 전부 PASS.
3. `mdbook build` → 0 ERROR/WARN.
4. 3종 leak scan CLEAN (전체 파일, 추적 파일 secrets-only, git 히스토리 secrets-only) — 특히 `examples/data/ch03_rag/*.md`와 `outputs/ch03_rag/*.out`에 절대경로가 없는지 확인.
5. Git hygiene — `examples/pyproject.toml`/`examples/uv.lock` 변경 diff를 리뷰(신규 의존성만 추가됐는지), HF 캐시(`~/.cache/huggingface`)는 리포 밖이라 애초에 커밋 대상이 아님.
6. push → Actions 확인 (CI는 `examples/`를 설치·실행하지 않으므로 이번 페이즈로 인해 CI 동작이 달라지지 않을 것을 재확인).
7. 라이브 검증: 3부 3챕터 + Phase 1(5) + Phase 2(2) 전체 10페이지 회귀 확인, `toc.html`에 `3부 RAG` 포함 확인.

**플랜 개수:** Phase 2(요구사항 2개, 1플랜, ~25분)와 비교해 Phase 3는 요구사항 4개·챕터 3개·신규 의존성 4개가 늘었지만, 각 단계가 이미 이번 연구로 라이브 검증되어 있어 추가 탐색 리스크가 낮다. **1개 플랜(quick depth), 단일 wave, 4개 태스크**를 권장:
- Task 1: `examples/pyproject.toml`에 의존성 추가(`uv add`) + `shared/config.py`에 `get_embeddings()` ANCHOR 추가 + `.env.example` 갱신 + 샘플 문서 3개 작성 + 챕터 3-1(로딩·분할)
- Task 2: 챕터 3-2(임베딩·벡터스토어·검색)
- Task 3: 챕터 3-3(LCEL RAG 체인) + `SUMMARY.md`/`introduction.md` 3부 포인터 추가
- Task 4: 전체 페이즈 게이트(위 7단계)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 이 세션에서 Python 3.14 + Apple Silicon MPS에 실제로 설치·로드·추론까지 재현했고, 별도 세션(STACK.md)의 독립 검증과도 수치가 일치.
- Architecture (get_embeddings 지연 import, ephemeral Chroma, 청킹 파라미터): HIGH — 전부 라이브 실행으로 직접 확인, 리포 자체의 `run_examples.py`/`check_book.py` 소스를 읽고 제약을 반영.
- Pitfalls (노이즈 억제, 절대경로, 결정성): HIGH — 전부 이번 세션에서 실패 상태와 수정 후 상태를 모두 재현.
- 메모리/타이밍 절대 수치: MEDIUM — 이 머신 1대에서 측정한 값이며, 다른 Apple Silicon 사양에서는 달라질 수 있음(상대적 규모 — "약 1GB 증가", "첫 로드 수십 초, 재로딩 한 자릿수 초" — 로 해석할 것을 권장).

**Research date:** 2026-09-11
**Valid until:** 약 30일 (라이브러리 버전 자체는 안정적이나, `langchain`/`chromadb`/`torch` 생태계가 빠르게 릴리스되므로 플랜 실행 시점에 `uv add`로 다시 잠기는 버전이 이 문서의 버전과 다를 수 있음 — 다르면 SUMMARY에 실제 버전을 기록)
