# LCEL로 체인 만들기

## 개념: 왜 필요한가

3장에서는 `prompt.invoke(...)`로 메시지를 먼저 채우고, 그 결과를 다시 `model.invoke(...)`에 직접 넘겼다. 프롬프트, 모델, 출력 파서, 심지어 평범한 파이썬 함수까지 — LangChain의 이 구성요소들은 모두 `Runnable`이라는 공통 인터페이스를 따르며 `invoke`/`batch`/`stream`이라는 동일한 세 메서드를 갖는다. LCEL(LangChain Expression Language)은 이 사실을 이용해 `|` 연산자로 여러 Runnable을 연결한다. `prompt | model | parser`는 "프롬프트를 채운 결과를 모델에 넘기고, 모델의 응답을 파서에 넘긴다"는 뜻이며, 3장에서 손으로 하던 일을 파이프 하나로 표현한 것이다.

파이프로 연결된 체인 자체도 하나의 Runnable이므로, 개별 구성요소처럼 `invoke`/`batch`/`stream`을 그대로 쓸 수 있다. 이번 장에서는 `RunnableLambda`(평범한 함수를 체인에 끼워 넣기), `RunnableParallel`(여러 체인을 동시에 실행해 결과를 딕셔너리로 모으기), 그리고 체인의 `batch`(여러 입력을 한 번에 처리)와 `stream`(파이프 전체를 통과하며 조각조각 응답받기)을 다룬다.

## 최소 코드

`examples/ch01_basics/04_lcel_runnables.py`

```python
{{#include ../../../examples/ch01_basics/04_lcel_runnables.py}}
```

### 1. 파이프로 연결

`chain = prompt | model | StrOutputParser()`는 세 Runnable을 연결한 `RunnableSequence`다. `StrOutputParser()`는 모델이 반환하는 `AIMessage`에서 텍스트만 뽑아내므로, `chain.invoke(...)`의 결과는 `AIMessage`가 아니라 문자열이다.

### 2. RunnableLambda

`RunnableLambda(to_input)`은 평범한 함수 `to_input`을 체인의 일부로 만든다. `RunnableLambda(to_input) | prompt | model | StrOutputParser()`에 문자열 하나를 바로 넣으면, 먼저 `to_input`이 그 문자열을 프롬프트가 기대하는 `{"topic": ...}` 딕셔너리로 바꾼 뒤 나머지 파이프로 흘려보낸다.

### 3. RunnableParallel

`RunnableParallel(summary=..., keywords=...)`은 같은 입력을 두 개의 서로 다른 체인(`summary_prompt | model | StrOutputParser()`와 `keyword_prompt | model | StrOutputParser()`)에 동시에 흘려보내고, 결과를 `{"summary": ..., "keywords": ...}` 형태의 딕셔너리로 모아준다.

### 4. batch

`chain.batch([...])`는 여러 입력을 리스트로 한 번에 넘기고, 입력 순서와 동일한 순서의 결과 리스트를 돌려받는다.

### 5. stream

`chain.stream({...})`은 체인 전체를 통과하는 응답을 조각(chunk) 단위로 순회한다. `StrOutputParser()`가 파이프의 마지막에 있으므로 각 조각은 문자열이다.

실행 방법 (examples 디렉터리에서):

```bash
uv run python ch01_basics/04_lcel_runnables.py
```

## 실제 출력

아래는 저자가 로컬 `flashnext` 모델로 실제 실행해 캡처한 결과다. LLM 응답이므로 여러분의 결과와 글자 단위로 같지 않을 수 있다.

```text
{{#include ../../../outputs/ch01_basics/04_lcel_runnables.out:2:}}
```

`=== 1 ===`에서 체인 타입은 예상대로 `RunnableSequence`다. 결과 타입은 `TextAccessor`로 찍히는데, 이건 이 버전의 `langchain-core`가 내부적으로 쓰는 `str`의 서브클래스일 뿐이다 — `isinstance(result, str)`은 `True`이고 다른 문자열처럼 그대로 출력·연결·슬라이싱할 수 있다. 핵심은 `AIMessage` 객체가 아니라 문자열(호환 타입)이 나온다는 점이다.

`=== 3 ===`에서는 `키: ['keywords', 'summary']`로 두 체인이 병렬로 실행된 결과가 하나의 딕셔너리에 모였음을 확인할 수 있고, `summary`/`keywords` 각각 실제 모델 응답이 들어 있다. `=== 4 ===`의 세 줄(`임베딩 -> ...`, `토큰 -> ...`, `프롬프트 -> ...`)은 `batch`가 입력 순서를 그대로 보존한다는 것을 보여준다. `=== 5 ===`의 청크 타입도 마찬가지로 `TextAccessor`이며, 청크 개수(`26`)는 하나의 응답이 여러 조각으로 나뉘어 왔음을 뜻한다.

## 요점 정리

- `prompt | model | parser`처럼 `Runnable`들을 `|`로 연결하면 `RunnableSequence`가 만들어지고, 체인 자체도 `invoke`/`batch`/`stream`을 갖는 Runnable이다.
- `RunnableLambda`로 평범한 함수를 체인에 끼워 넣어 입력 형태를 바꿀 수 있다.
- `RunnableParallel`은 여러 체인을 동시에 실행해 결과를 하나의 딕셔너리로 모은다.
- `chain.batch([...])`는 입력 순서를 보존한 결과 리스트를, `chain.stream(...)`은 조각(chunk) 단위 응답을 돌려준다.
- `StrOutputParser()`를 거친 결과는 `AIMessage`가 아니라 문자열(또는 그 호환 서브클래스)이다.
