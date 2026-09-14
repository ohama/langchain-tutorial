# 체크포인터와 recursion_limit

## 개념: 왜 필요한가

그래프는 한 번의 `invoke`가 끝나면 상태를 버린다 — 멀티턴 대화를 이어가려면 상태를 어딘가에 저장해야 한다. 체크포인터가 각 단계의 상태를 저장하고, `thread_id`가 "어느 대화인지"를 가리킨다. `InMemorySaver`는 프로세스 메모리에만 저장하므로 프로세스가 끝나면 사라진다(다음 장에서 파일로 옮긴다). 폐기된 `ConversationBufferMemory` 대신 이 방식이 표준이다.

그리고 루프백 엣지가 있는 그래프는 원리상 끝나지 않을 수 있으므로 `recursion_limit`이 안전장치가 된다(기본값 25).

## 최소 코드

### 예제 코드

`examples/ch04_langgraph/03_checkpointer.py`

```python
{{#include ../../../examples/ch04_langgraph/03_checkpointer.py}}
```

- `compile(checkpointer=InMemorySaver())`로 컴파일하면 그래프가 각 단계의 상태를 저장한다.
- `config={"configurable": {"thread_id": ...}}`가 "어느 대화인지"를 가리킨다 — 같은 앱이라도 `thread_id`가 다르면 다른 대화가 된다.
- `app.get_state(config)`로 특정 스레드에 쌓인 상태(메시지 수 등)를 확인할 수 있다.
- 4번 섹션의 그래프는 LLM을 전혀 쓰지 않는 순수 파이썬 그래프라 매번 같은 오류를 낸다 — `bump` 노드가 스스로에게 돌아가는 조건부 엣지만 있고 `END`로 가는 길이 없다.

실행 방법 (examples 디렉터리에서):

```bash
uv run python ch04_langgraph/03_checkpointer.py
```

## 실제 출력

아래는 저자가 로컬 `flashnext` 모델로 실제 실행해 캡처한 결과다. LLM 응답이므로 여러분의 결과와 글자 단위로 같지 않을 수 있다.

```text
{{#include ../../../outputs/ch04_langgraph/03_checkpointer.out:2:}}
```

`=== 1 ===`에서는 체크포인터 없이 컴파일한 그래프에 같은 이름("영희")을 알려주고 다음 호출에서 물어봤지만, 모델은 이름을 알려준 적이 없다고 답했다 — 두 번째 호출이 받은 메시지 수가 2(새 질문 하나와 그 답)뿐이라는 점이 이를 뒷받침한다: 각 `invoke` 호출이 빈 상태에서 시작했다는 뜻이다.

`=== 2 ===`에서는 `InMemorySaver`로 컴파일하고 `thread_id="chat-1"`로 같은 두 턴을 반복했다. 이번에는 모델이 "영희라고 하셨어요!"로 답했고(`답변에 '영희'가 들어있나: True`), `thread_id=chat-1`에 쌓인 메시지 수는 6(1턴의 질문·답변, 2턴의 질문·답변에 더해 체크포인터가 관리하는 누적분)으로 늘어나 있었다.

`=== 3 ===`은 같은 앱, 다른 `thread_id="chat-2"`로 "내 이름이 뭐라고 했지?"를 물었다. 답변은 이름을 모른다는 내용이었고(`답변에 '영희'가 들어있나: False`), 이 스레드의 메시지 수는 2로 `chat-1`의 6보다 적었다 — `thread_id`가 다르면 완전히 별개의 대화라는 뜻이다.

`=== 4 ===`는 LLM 없이 순수 파이썬으로 만든, 일부러 끝나지 않는 그래프를 `recursion_limit=5`로 돌렸다. 실제로 `GraphRecursionError`가 났고, 메시지는 "Recursion limit of 5 reached without hitting a stop condition. You can increase the limit by setting the `recursion_limit` config key."였다 — 한도에 도달했고, `recursion_limit`이라는 config 값을 키우면 늘릴 수 있다는 뜻이다.

## 요점 정리

- `compile(checkpointer=InMemorySaver())`가 각 단계의 상태를 저장하고, `config={"configurable": {"thread_id": ...}}`가 어느 대화인지를 가리킨다.
- 체크포인터가 없으면 매 `invoke` 호출이 빈 상태에서 시작한다 — 이번 캡처에서는 이름을 알려준 바로 다음 호출에서도 모델이 기억하지 못했다.
- 같은 앱이라도 `thread_id`가 다르면 상태가 공유되지 않는다 — `chat-1`은 이름을 기억했고 `chat-2`는 기억하지 못했다.
- `InMemorySaver`는 프로세스 메모리에만 저장되므로 프로세스가 끝나면 사라진다.
- 루프백 엣지가 있는 그래프는 끝나지 않을 수 있으므로 `recursion_limit`(기본값 25)이 안전장치가 된다 — 2부의 `MAX_ITERS` 가드와 같은 역할이다.

다음 장에서는 이 기억을 파일에 저장해 프로세스를 재시작해도 남게 만든다.
