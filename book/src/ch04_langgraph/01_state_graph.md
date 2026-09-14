# 도구 루프를 그래프로 다시 만들기

## 개념: 왜 필요한가

2부의 수동 루프는 `for`문과 `if`문으로 "모델 → 도구 → 모델"을 직접 돌렸다. 분기·반복·중단 조건이 늘어날수록 이 루프는 읽기 어려워진다.

LangGraph는 같은 흐름을 **상태(State) + 노드 + 엣지**로 선언한다. 상태는 누적되는 메시지 목록이고, 노드는 상태를 받아 새 메시지를 돌려주는 함수이며, 엣지는 다음에 어느 노드로 갈지를 정한다.

리듀서 `add_messages`가 핵심이다: 노드는 *새로 생긴* 메시지만 돌려주고, 리듀서가 기존 목록에 이어 붙인다. 그래서 노드 함수는 전체 대화를 관리할 필요가 없다.

조건부 엣지(`tools_condition`)가 2부의 `if ai_msg.tool_calls:` 자리를 대신하고, `tools → model` 루프백 엣지가 `for`문의 반복을 대신한다.

이 장의 목표는 새 기능이 아니라 **같은 결과를 다른 구조로** 얻는 것이다 — 2부와 똑같은 질문에 똑같은 최종 답이 나오는지 출력으로 확인한다.

## 최소 코드

### 예제 코드

`examples/ch04_langgraph/01_state_graph.py`

```python
{{#include ../../../examples/ch04_langgraph/01_state_graph.py}}
```

- `TypedDict` + `Annotated[list, add_messages]`로 만든 `ChatState`가 상태의 최소 형태이고, `MessagesState`는 그 모양을 미리 만들어 둔 것이다.
- `ToolNode`가 2부의 `run_tool_call`을 대신하되, **`handle_tool_errors=True`를 반드시 켜야** 도구 함수 안에서 난 예외가 `ToolMessage`로 돌아온다는 점이 다르다 — 기본값에서는 예외가 그대로 올라와 그래프 실행이 멈춘다.
- `tools_condition`이 마지막 `AIMessage`에 `tool_calls`가 있으면 `tools`로, 없으면 `END`로 보낸다.
- `add_edge("tools", "model")` 루프백이 반복을 만든다. 2부의 `MAX_ITERS` 자리에는 `recursion_limit`이 있는데, 이건 다음 장에서 다룬다.
- `compile()`이 실행 가능한 앱을 만든다.

실행 방법 (examples 디렉터리에서):

```bash
uv run python ch04_langgraph/01_state_graph.py
```

### 그래프를 그림으로 그리는 코드

`draw_mermaid()`는 컴파일된 그래프에서 mermaid 소스를 만들어 준다.

```python
{{#include ../../../examples/ch04_langgraph/02_graph_mermaid.py}}
```

이 예제의 출력 전체가 다이어그램 소스이므로 책에 그대로 그림으로 실린다.

```bash
uv run python ch04_langgraph/02_graph_mermaid.py
```

## 실제 출력

아래는 저자가 로컬 `flashnext` 모델로 실제 실행해 캡처한 결과다. LLM 응답이므로 여러분의 결과와 글자 단위로 같지 않을 수 있다.

```text
{{#include ../../../outputs/ch04_langgraph/01_state_graph.out:2:}}
```

`=== 1 ===`에서 `ChatState`와 `MessagesState` 모두 필드가 `['messages']`로 같은 모양임을 보여준다. `add_messages([1개], [1개])`는 2개짜리 목록(`HumanMessage`, `AIMessage`)을 만들었다 — 리듀서가 두 목록을 이어 붙였을 뿐, 어느 쪽도 덮어쓰지 않았다는 뜻이다.

`=== 2 ===`의 노드 목록은 `['__end__', '__start__', 'model', 'tools']`다. 엣지는 `__start__ -> model`(무조건), `model -> __end__`와 `model -> tools`(둘 다 조건부 — `tools_condition`이 고른다), `tools -> model`(무조건, 루프백)로 네 줄 나온다. 마지막 줄 `tools -> model 루프백 있음: True`는 바로 위 엣지 목록에서 계산한 값이라 항상 그 목록과 일치한다.

`=== 3 ===`은 2부와 똑같은 질문 "사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘."을 그래프에 넣은 결과다. 1단계에서 `lookup_stock({"item": "사과"})`와 `lookup_stock({"item": "바나나"})`를 병렬로 호출해 각각 `사과 재고: 12개`, `바나나 재고: 5개`를 받았고, 2단계에서 `multiply({"a": 12, "b": 5})`를 호출해 `60`을 받았으며, 3단계에서 더 이상 도구를 부르지 않고 `사과 재고 12개 × 바나나 재고 5개 = **60**입니다.`로 답했다. 메시지 흐름은 `HumanMessage → AIMessage → ToolMessage → ToolMessage → AIMessage → ToolMessage → AIMessage`로, 2부 2장의 흐름과 정확히 같다. `2부 수동 루프의 최종 답과 동일: True` — 이 줄이 이 장의 핵심 증거다: 그래프가 낸 최종 답이 2부 2장이 낸 최종 답과 글자까지 같다는 뜻이다.

`=== 4 ===`는 재고 목록에 없는 "노트북"을 물었다. 모델이 `lookup_stock({"item": "노트북"})`을 호출하자 도구 안에서 `ValueError`가 났고, 그 예외는 `Tool[lookup_stock] (error): Error: ValueError('재고 목록에 없는 품목: 노트북')\n Please fix your mistakes.`라는 오류 `ToolMessage`로 돌아왔다. 그래프는 죽지 않고 모델에게 이 메시지를 다시 건넸고, 모델은 도구를 다시 부르지 않고 "노트북은 현재 재고 목록에 없는 품목으로 확인됩니다"로 답을 마쳤다 — `ToolNode(ALL_TOOLS, handle_tool_errors=True)`가 아니었다면 이 `ValueError`가 그대로 올라와 그래프 실행 자체가 멈췄을 것이다.

### 그래프 다이어그램

아래 그림은 위 예제가 출력한 mermaid 소스를 그대로 렌더링한 것이다.

```mermaid
{{#include ../../../outputs/ch04_langgraph/02_graph_mermaid.out:2:}}
```

`__start__`에서 `model`로 들어가고, `model`에서 점선(조건부)으로 `tools` 또는 `__end__`로 갈라지며, `tools`에서 실선으로 `model`로 돌아오는 고리가 보인다.

## 요점 정리

- 상태는 `TypedDict` + `Annotated[list, add_messages]`이고, `MessagesState`는 이미 그 모양으로 만들어져 있다 — 노드는 새로 생긴 메시지만 돌려주면 리듀서가 이어 붙인다.
- `add_conditional_edges(model, tools_condition, ...)` + `add_edge("tools", "model")`이 2부의 `if ai_msg.tool_calls:`와 `for`문 반복을 대신한다.
- 같은 질문으로 그래프를 돌리면 2부 수동 루프와 동일한 도구 호출·메시지 흐름·최종 답이 나온다 — 이 장의 출력에 찍힌 `True`가 그 증거다.
- `ToolNode(..., handle_tool_errors=True)`가 없으면 도구 함수 안 예외가 그래프를 그대로 죽인다 — 반드시 켜야 오류가 `ToolMessage`로 돌아와 모델이 스스로 복구를 시도할 수 있다.
- `draw_mermaid()` 출력을 캡처해 mermaid 펜스에 그대로 include하면 그래프 구조가 실제 그림으로 렌더링된다.

다음 장에서는 이 그래프에 체크포인터를 붙여 대화를 기억시키고 `recursion_limit`으로 무한 루프를 막는다.
