"""4부 1장: 같은 그래프의 구조를 mermaid 다이어그램 소스로 출력한다."""
# 이 파일의 전체 표준출력이 곧 mermaid 다이어그램 소스다 — 책의 ```mermaid 펜스에
# 그대로 include되어 그림으로 렌더링되므로, "=== 섹션 ===" 같은 머리말을 절대 찍지 않는다.

from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from shared.config import get_chat_model
from shared.tools import ALL_TOOLS


# 1장의 build_graph()와 의도적으로 동일하다 (3부가 load_documents()에 쓴 것과 같은
# verbatim-copy 관례) — 다른 예제에서 import하지 않는다.
def build_graph():
    model_with_tools = get_chat_model().bind_tools(ALL_TOOLS)

    def call_model(state: MessagesState) -> dict:
        return {"messages": [model_with_tools.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(ALL_TOOLS, handle_tool_errors=True))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "model")
    return graph.compile()


app = build_graph()
print(app.get_graph().draw_mermaid(), end="")
