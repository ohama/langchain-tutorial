"""4부 2장: 체크포인터로 대화를 기억하고, recursion_limit으로 무한 루프를 멈춘다."""
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from shared.config import get_chat_model
from shared.tools import ALL_TOOLS

INTRO = "내 이름은 영희야. 기억해줘."
RECALL = "내 이름이 뭐라고 했지?"


def build_graph_builder() -> StateGraph:
    # 1장의 build_graph()와 노드/엣지가 의도적으로 동일하다 — 컴파일만 이 파일에서
    # 두 번(체크포인터 없이 한 번, 있이 한 번) 따로 한다.
    model_with_tools = get_chat_model().bind_tools(ALL_TOOLS)

    def call_model(state: MessagesState) -> dict:
        return {"messages": [model_with_tools.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(ALL_TOOLS, handle_tool_errors=True))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "model")
    return graph


def last_answer(result) -> str:
    return result["messages"][-1].content


print("=== 1. 체크포인터가 없으면 기억하지 못한다 ===")
app = build_graph_builder().compile()
result = app.invoke({"messages": [HumanMessage(INTRO)]})
print(f"1턴 질문: {INTRO}")
print(f"1턴 답변: {last_answer(result)}")
result = app.invoke({"messages": [HumanMessage(RECALL)]})
print(f"2턴 질문: {RECALL}")
print(f"2턴 답변: {last_answer(result)}")
print(f"두 번째 호출이 받은 메시지 수: {len(result['messages'])}")
print("각 호출이 빈 상태에서 시작한다 — 체크포인터가 없으면 이전 턴이 남지 않는다")

print()
print("=== 2. InMemorySaver + thread_id로 기억하기 ===")
app = build_graph_builder().compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "chat-1"}}
result = app.invoke({"messages": [HumanMessage(INTRO)]}, config=config)
print(f"1턴 질문: {INTRO}")
print(f"1턴 답변: {last_answer(result)}")
result = app.invoke({"messages": [HumanMessage(RECALL)]}, config=config)
answer = last_answer(result)
print(f"2턴 질문: {RECALL}")
print(f"2턴 답변: {answer}")
print(f"thread_id=chat-1에 쌓인 메시지 수: {len(app.get_state(config).values['messages'])}")
print(f"답변에 '영희'가 들어있나: {'영희' in answer}")

print()
print("=== 3. thread_id가 다르면 기억도 다르다 ===")
other = {"configurable": {"thread_id": "chat-2"}}
result = app.invoke({"messages": [HumanMessage(RECALL)]}, config=other)
other_answer = last_answer(result)
print(f"질문: {RECALL}")
print(f"답변: {other_answer}")
print(f"답변에 '영희'가 들어있나: {'영희' in other_answer}")
print(f"thread_id=chat-2에 쌓인 메시지 수: {len(app.get_state(other).values['messages'])}")

print()
print("=== 4. recursion_limit으로 무한 루프 멈추기 ===")


class CountState(TypedDict):
    count: int


def bump(state: CountState) -> dict:
    return {"count": state["count"] + 1}


def always_bump(state: CountState) -> str:
    return "bump"  # END로 가는 길이 없다 — 일부러 만든 무한 루프


counter = StateGraph(CountState)
counter.add_node("bump", bump)
counter.add_edge(START, "bump")
counter.add_conditional_edges("bump", always_bump, {"bump": "bump"})
counter_app = counter.compile()

print("기본 recursion_limit은 25이고, 여기서는 5로 줄여서 빠르게 확인한다")
try:
    counter_app.invoke({"count": 0}, config={"recursion_limit": 5})
except GraphRecursionError as e:
    print(f"{type(e).__name__}")
    print(f"{e}")
print("2부의 MAX_ITERS 가드가 여기서는 recursion_limit이라는 config 값이다")
