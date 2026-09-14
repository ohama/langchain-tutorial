"""4부 4장: 트레이싱 스위치를 켜고 끄고, 그래프 내부 호출 트리를 로컬에서 들여다본다."""
import json
import os

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langsmith import utils

from shared.config import get_chat_model
from shared.tools import ALL_TOOLS

QUESTION = "사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘."

TRACING_VARS = ("LANGSMITH_TRACING", "LANGSMITH_TRACING_V2",
                "LANGCHAIN_TRACING", "LANGCHAIN_TRACING_V2")


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


def tracing_state() -> bool:
    # get_env_var는 lru_cache가 걸려 있어, 환경변수를 바꾼 뒤에는 캐시를 비워야 한다
    utils.get_env_var.cache_clear()
    return utils.tracing_is_enabled()


print("=== 1. 트레이싱 스위치 (기본값: 꺼짐) ===")
# 캡처 재현성을 위해 저자 환경의 설정을 무시하고, 항상 같은 출발점(아무 설정 없음)에서 시작한다
for var in TRACING_VARS:
    os.environ.pop(var, None)

print(f"기본값(아무 설정 없음): {tracing_state()}")
os.environ["LANGSMITH_TRACING"] = "true"
print(f"LANGSMITH_TRACING=true: {tracing_state()}")
print(f"API 키 없이도 스위치 자체는 켜진다: {tracing_state()} (실제 전송에는 키가 필요하다)")
del os.environ["LANGSMITH_TRACING"]
print(f"다시 끈 뒤: {tracing_state()}")
print("이 함수는 환경변수만 읽고 네트워크에 접속하지 않으므로, 이 장의 어떤 출력도 클라우드로 전송되지 않았다")

print()
print("=== 2. 그래프 내부의 호출 트리 (로컬) ===")
app = build_graph()
seen_nodes = []
totals = {"input": 0, "output": 0}
for event in app.stream({"messages": [HumanMessage(QUESTION)]}, stream_mode="debug"):
    kind, payload, step = event["type"], event["payload"], event["step"]
    name = payload["name"]
    if kind == "task":
        print(f"[{step}] {name} 시작")
    elif kind == "task_result":
        seen_nodes.append(name)
        for msg in payload["result"]["messages"]:
            msg_kind = type(msg).__name__
            if msg_kind == "AIMessage" and msg.tool_calls:
                calls = ", ".join(fmt_call(tc) for tc in msg.tool_calls)
                print(f"[{step}] {name} 끝 → 도구 요청: {calls}")
            elif msg_kind == "AIMessage":
                print(f"[{step}] {name} 끝 → 답변: {msg.content}")
            elif msg_kind == "ToolMessage":
                print(f"[{step}] {name} 끝 → {msg.name} ({msg.status}): {msg.content}")
            usage = getattr(msg, "usage_metadata", None)
            if usage:
                print(f"[{step}] {name} 토큰: 입력 {usage['input_tokens']} / 출력 {usage['output_tokens']} / 합계 {usage['total_tokens']}")
                totals["input"] += usage["input_tokens"]
                totals["output"] += usage["output_tokens"]

print()
print("=== 3. 트레이스 트리의 이름 = 그래프 노드 이름 ===")
registered = sorted(n for n in app.get_graph().nodes if not n.startswith("__"))
print(f"그래프에 등록한 노드: {registered}")
print(f"트레이스에서 관찰된 순서: {' → '.join(seen_nodes)}")
print(f"관찰된 이름이 모두 등록된 노드인가: {set(seen_nodes) <= set(registered)}")

print()
print("=== 4. 토큰 사용량 합계 ===")
print(f"모델 호출 {seen_nodes.count('model')}회")
print(f"입력 토큰 합계 {totals['input']} / 출력 토큰 합계 {totals['output']} / 전체 합계 {totals['input'] + totals['output']}")
print("지연시간은 재현 가능한 값이 아니라 이 책의 캡처에는 넣지 않는다 — LangSmith UI에서는 각 단계 옆에 실제 소요 시간이 함께 표시된다")
