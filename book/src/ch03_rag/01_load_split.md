# 문서 로딩과 분할

## 개념: 왜 필요한가

모델은 한 번도 보지 못한 문서(사내 규정, 개인 메모 같은 것들)의 내용을 알지 못한다. RAG(검색 증강 생성)는 질문과 관련 있는 문서 조각을 미리 찾아서 프롬프트에 넣어 주는 방식으로 이 문제를 푼다. 3부는 이 과정을 세 장에 나눠 다룬다. 이번 장은 문서를 읽어 들이고 조각으로 나누고, 다음 장은 그 조각을 임베딩해서 벡터스토어에 저장하고 검색하며, 마지막 장은 검색된 조각을 근거로 LCEL 체인이 실제 답을 생성한다.

문서를 조각으로 나누는 이유는 두 가지다. 프롬프트에는 길이 제한이 있어서 문서 전체를 통째로 넣을 수 없고, 작고 주제가 분명한 조각일수록 질문과 관련된 부분만 정확하게 찾아낼 수 있다.

LangChain에서 문서는 `Document`라는 값으로 다룬다. `Document`는 실제 텍스트를 담은 `page_content`와, 출처 같은 부가 정보를 담은 `metadata` 두 가지로 이루어진다. 이 책은 파일을 읽어 들일 때 표준 라이브러리 `pathlib`로 직접 읽어서 `Document`를 만든다 — `langchain-community` 패키지의 로더들도 있지만 지원이 종료되었으므로 쓰지 않는다.

## 최소 코드

### 샘플 문서

이번 장부터는 세 개의 원본 한국어 문서를 예제 데이터로 쓴다. 모두 이 책을 위해 새로 쓴 글이다.

- `01_langchain_intro.md` — LangChain의 핵심 개념(Runnable, 파이프 연산자, 프롬프트 템플릿) 노트
- `02_rag_guide.md` — RAG가 무엇이고 왜 필요한지, 전체 단계를 설명하는 안내문
- `03_company_handbook.md` — 이 책을 위해 지어낸 가상 회사의 근무 규정(연차, 재택근무 등). 실존하는 회사와는 무관하다.

가상 회사 근무 규정 문서는 다음 장, 다음다음 장에서도 검색·질의응답 대상으로 계속 쓰인다.

```text
{{#include ../../../examples/data/ch03_rag/03_company_handbook.md}}
```

### 예제 코드

`examples/ch03_rag/01_load_split.py`

```python
{{#include ../../../examples/ch03_rag/01_load_split.py}}
```

- `load_documents()`는 각 파일의 `metadata["source"]`에 저장소 기준 **상대경로**(예: `examples/data/ch03_rag/01_langchain_intro.md`)를 저장한다. 절대경로를 그대로 쓰면 실행한 사람의 컴퓨터 경로가 출력에 그대로 남아 재현성이 떨어진다.
- `chunk_size`와 `chunk_overlap`은 모두 **문자 수** 기준이다(토큰이 아니다).
- `add_start_index=True`를 주면 각 조각의 `metadata["start_index"]`에 원문에서 그 조각이 시작하는 위치가 기록되어, 분할 결과가 원문 어디를 가리키는지 눈으로 확인할 수 있다.
- `RecursiveCharacterTextSplitter()`의 기본 구분자 순서는 `['\n\n', '\n', ' ', '']`다 — 문단 경계(빈 줄) → 줄바꿈 → 공백 → 글자 순으로 자를 위치를 찾는다.

실행 방법 (examples 디렉터리에서):

```bash
uv run python ch03_rag/01_load_split.py
```

## 실제 출력

이 장의 예제는 LLM을 전혀 호출하지 않는다. 같은 샘플 문서와 같은 라이브러리 버전이면 누가 실행해도 같은 결과가 나와야 한다.

```text
{{#include ../../../outputs/ch03_rag/01_load_split.out:2:}}
```

이번 캡처에서는 문서 3개(각각 1290자, 1211자, 1105자)가 총 청크 17개로 나뉘었다(`01_langchain_intro.md` 7개, `02_rag_guide.md` 5개, `03_company_handbook.md` 5개). `chunk_size=300`을 넘는 조각은 하나도 없고(가장 긴 조각이 295자), 대부분의 경계가 `##` 소제목이나 빈 줄 같은 문단 경계에서 갈라져 문장이 중간에 잘리는 경우는 보이지 않는다.

3번 구간에서 청크 0과 청크 1 사이의 겹친 글자 수는 0이다. `chunk_overlap=50`은 "겹치도록 시도하는 목표 값"이지, 항상 정확히 그만큼 겹치라는 뜻은 아니다 — 이번 캡처에서는 청크 0이 끝나는 지점(204) 바로 뒤에 다음 소제목(`## Runnable 인터페이스`)이 시작되는 자연스러운 문단 경계가 있었고, 분할기가 그 경계에서 그대로 나누면서 별도로 앞부분을 끌어와 겹칠 필요가 없었다.

## 요점 정리

- `Document`는 `page_content`(본문)와 `metadata`(부가 정보)로 이루어진다. 이 책은 `pathlib`로 파일을 읽어 직접 `Document`를 만든다.
- `metadata["source"]`에는 절대경로 대신 저장소 기준 상대경로를 저장해 재현성을 지킨다.
- `RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50, add_start_index=True)`는 문단 → 줄 → 공백 → 글자 순으로 자를 위치를 찾고, `start_index`로 원문 위치를 함께 기록한다.
- `chunk_overlap`은 목표 값일 뿐, 자연스러운 문단 경계에서 나뉘면 실제 겹침이 0이 될 수도 있다.
- 다음 장은 이 조각들을 임베딩하고 벡터스토어에 저장해 한국어 질의로 검색한다.
