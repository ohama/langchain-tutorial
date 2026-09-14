"""4부 1장: 2부의 수동 도구 루프를 StateGraph로 다시 만든다."""
import json
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from shared.config import get_chat_model
from shared.tools import ALL_TOOLS


class ChatState(TypedDict):
    # add_messages는 "덮어쓰기" 대신 "이어 붙이기"로 합치는 리듀서다
    messages: Annotated[list, add_messages]


# 2부 수동 루프가 낸 최종 답 (02-01-SUMMARY.md 기록)
BASELINE_ANSWER = "사과 재고 12개 × 바나나 재고 5개 = **60**입니다."
QUESTION = "사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘."


def fmt_call(tc):
    return f"{tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})"


def build_graph():
    model_with_tools = get_chat_model().bind_tools(ALL_TOOLS)

    def call_model(state: MessagesState) -> dict:
        return {"messages": [model_with_tools.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    # handle_tool_errors=True가 없으면 도구 함수 안에서 난 예외가 그래프를 그대로 죽인다
    graph.add_node("tools", ToolNode(ALL_TOOLS, handle_tool_errors=True))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "model")  # 도구 결과를 들고 모델로 되돌아가는 루프백
    return graph.compile()


def describe(messages):
    for m in messages:
        if isinstance(m, AIMessage):
            if m.tool_calls:
                calls = ", ".join(fmt_call(tc) for tc in m.tool_calls)
                print(f"AI: tool_calls [{calls}]")
            else:
                print(f"AI: {m.content}")
        elif isinstance(m, HumanMessage):
            print(f"Human: {m.content}")
        elif type(m).__name__ == "ToolMessage":
            print(f"Tool[{m.name}] ({m.status}): {m.content}")
        else:
            print(f"{type(m).__name__}: {m.content}")


print("=== 1. 상태(State): TypedDict + add_messages ===")
print(f"ChatState 필드: {list(ChatState.__annotations__)}")
print(f"MessagesState 필드: {list(MessagesState.__annotations__)}")
print("MessagesState는 위 ChatState와 같은 모양을 미리 만들어 둔 것")

old = [HumanMessage("안녕", id="m1")]
new = [AIMessage("반가워", id="m2")]
merged = add_messages(old, new)
print(f"add_messages([1개], [1개]) -> {len(merged)}개: {[type(m).__name__ for m in merged]}")
print("노드는 새로 생긴 메시지만 돌려주고, 리듀서가 기존 목록에 이어 붙인다")

print()
print("=== 2. 노드와 엣지 ===")
app = build_graph()
g = app.get_graph()
print(f"노드: {sorted(g.nodes)}")
edges = sorted((e.source, e.target, bool(e.conditional)) for e in g.edges)
for src, dst, cond in edges:
    print(f"  {src} -> {dst}" + ("  (조건부)" if cond else ""))
print(f"tools -> model 루프백 있음: {('tools', 'model', False) in edges}")

print()
print("=== 3. 2부 도구 루프를 그래프로 재현 ===")
print(f"질문: {QUESTION}")
result = app.invoke({"messages": [HumanMessage(QUESTION)]})
describe(result["messages"])
print("메시지 흐름: " + " → ".join(type(m).__name__ for m in result["messages"]))
final = result["messages"][-1].content
print(f"최종 답: {final}")
print(f"2부 수동 루프의 최종 답과 동일: {final == BASELINE_ANSWER}")

print()
print("=== 4. 도구 안에서 난 예외도 ToolMessage로 ===")
result = app.invoke({"messages": [HumanMessage("노트북 재고를 확인해줘.")]})
describe(result["messages"])
print(f"마지막 답: {result['messages'][-1].content}")
print("ToolNode(ALL_TOOLS, handle_tool_errors=True)이 아니었다면 이 예외가 그래프를 죽였을 것이다")
