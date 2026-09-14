# 채팅 모델 호출하기

## 개념: 왜 필요한가

LangChain은 OpenAI, Anthropic, 로컬 서버 등 서로 다른 LLM 제공자를 같은 인터페이스로 다루게 해준다. 어떤 모델을 쓰든 `invoke`(응답을 한 번에 받는 방식)와 `stream`(응답이 만들어지는 대로 조각조각 받는 방식)이라는 동일한 두 메서드로 호출한다.

이 책은 `ChatOpenAI(base_url=...)`를 OpenAI 호환 로컬 서버(LiteLLM 프록시, `flashnext` 별칭)에 연결해서 쓴다. 서버 종류가 바뀌어도 코드는 거의 그대로 재사용할 수 있다.

`invoke`는 모델이 답변을 모두 완성할 때까지 기다렸다가 결과를 한 번에 반환하고, `stream`은 토큰(또는 몇 글자) 단위로 생성되는 즉시 하나씩 넘겨준다. 채팅 UI처럼 타이핑되는 느낌을 주려면 `stream`을, 응답 전체를 한 번에 후처리해야 한다면 `invoke`를 쓴다.

로컬 서버는 첫 요청에서 모델을 메모리에 올리느라 수십 초가 걸릴 수 있다(콜드 스타트). 이후 요청은 훨씬 빠르다.

## 최소 코드

### 준비: .env 설정

`examples` 디렉터리에서 `.env.example`을 `.env`로 복사하고 의존성을 설치한다.

```bash
cd examples
cp .env.example .env
uv sync
```

`.env.example`의 내용은 다음과 같다.

```ini
{{#include ../../../examples/.env.example}}
```

독자가 실제로 바꿔야 할 값은 세 가지뿐이다.

- `LLM_BASE_URL` — OpenAI 호환 API 주소. LiteLLM, Ollama의 `/v1`, vLLM 등 사용 중인 서버 주소로 바꾼다.
- `LLM_MODEL` — 사용할 모델 이름(별칭).
- `LLM_API_KEY` — 인증이 필요 없는 로컬 서버라면 비워 둔다. 셸 환경변수를 참조하려면 `LLM_API_KEY=${MY_KEY_ENV}`처럼 쓸 수 있다.

파일 끝의 `EMBEDDING_MODEL`/`EMBEDDING_DEVICE`는 [3부 RAG](../ch03_rag/02_embed_search.md)에서 쓰는 선택 설정이라 지금은 그대로 두면 된다. 그 아래의 `LANGSMITH_*`는 [4부 LangSmith 트레이싱](../ch04_langgraph/04_langsmith.md)에서 쓰는 선택 설정이고 기본값은 꺼짐이라 지금은 그대로 두면 된다.

### 설정을 읽는 곳: shared/config.py

이 책의 모든 예제는 채팅 모델을 오직 이 파일을 통해서만 만든다.

```python
{{#include ../../../examples/shared/config.py:settings}}
```

```python
{{#include ../../../examples/shared/config.py:chat_model}}
```

`get_chat_model()`은 `.env`를 읽어 `ChatOpenAI`를 만든다. 캡처 결과의 재현성을 위해 `temperature=0`을 기본값으로 쓰고, 콜드 스타트에 대비해 `timeout=120`(초)을 준다.

### 예제 코드

`examples/ch01_basics/01_chat_model.py`

```python
{{#include ../../../examples/ch01_basics/01_chat_model.py}}
```

`get_chat_model()`로 모델을 하나 만들어 `invoke`와 `stream`을 차례로 호출한다. `stream` 구간에서는 받은 청크를 모두 리스트에 모아 두었다가, 몇 개의 조각으로 나뉘어 왔는지와 앞부분 조각들의 실제 내용(`repr`)을 함께 출력해서 스트리밍이 실제로 여러 조각으로 오는지 정적인 출력만으로도 확인할 수 있게 했다.

실행 방법 (examples 디렉터리에서):

```bash
uv run python ch01_basics/01_chat_model.py
```

## 실제 출력

아래는 저자가 로컬 `flashnext` 모델로 실제 실행해 캡처한 결과다. LLM 응답이므로 여러분의 결과와 글자 단위로 같지 않을 수 있다.

```text
{{#include ../../../outputs/ch01_basics/01_chat_model.out:2:}}
```

`invoke` 구간은 완성된 응답 전체가 한 번에 출력되지만, `stream` 구간은 청크 개수(70개)와 앞부분 조각들이 `'태'`, `'양'`, `'광'`처럼 짧은 문자열로 잘게 나뉘어 있는 것을 `repr` 출력에서 확인할 수 있다.

## 요점 정리

- `get_chat_model()`은 `.env` 설정을 읽어 `ChatOpenAI` 인스턴스를 만드는 이 책의 유일한 통로다.
- `invoke`는 완성된 응답 전체를, `stream`은 생성되는 대로 조각(chunk)을 반환한다.
- 어떤 OpenAI 호환 서버를 쓰든 `invoke`/`stream` 인터페이스는 동일하다.
- 로컬 서버의 첫 요청은 콜드 스타트로 느릴 수 있으니 `timeout`을 넉넉히 준다.
