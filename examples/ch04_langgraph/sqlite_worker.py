"""4부 3장: 별도 프로세스로 실행되어 SQLite 체크포인터에 한 턴을 기록한다."""
# 파일명이 숫자로 시작하지 않으므로 scripts/run_examples.py가 이 파일을 직접
# 수집·실행하지 않는다 — 04_sqlite_checkpoint.py가 subprocess로만 띄운다.
import os
import sys

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from shared.config import get_chat_model
from shared.tools import ALL_TOOLS


def build_graph_builder() -> StateGraph:
    # 1장/2장의 그래프와 노드/엣지가 의도적으로 동일하다.
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


def main() -> None:
    turn_label, db_path, thread_id, parent_pid = sys.argv[1:5]

    question = {
        "run1": "내 이름은 철수야. 기억해줘.",
        "run2": "내 이름이 뭐라고 했지?",
    }[turn_label]

    with SqliteSaver.from_conn_string(db_path) as saver:
        app = build_graph_builder().compile(checkpointer=saver)
        config = {"configurable": {"thread_id": thread_id}}
        result = app.invoke({"messages": [HumanMessage(question)]}, config=config)
        answer = result["messages"][-1].content
        message_count = len(app.get_state(config).values["messages"])

    print(f"[{turn_label}] 부모 프로세스와 동일: {os.getpid() == int(parent_pid)}")
    print(f"[{turn_label}] 질문: {question}")
    print(f"[{turn_label}] 답변: {answer}")
    print(f"[{turn_label}] 이 스레드에 쌓인 메시지 수: {message_count}")


if __name__ == "__main__":
    main()
