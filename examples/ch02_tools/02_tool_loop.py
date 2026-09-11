"""2부 2장: 모델 → tool call → ToolMessage → 재호출 루프를 손으로 구현한다."""
import json

from langchain_core.messages import HumanMessage, ToolMessage

from shared.config import get_chat_model
from shared.tools import ALL_TOOLS, lookup_stock

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}
MAX_ITERS = 5


def fmt_call(tc):
    return f"{tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})"


def run_tool_call(tc) -> ToolMessage:
    tool = TOOLS_BY_NAME.get(tc["name"])
    if tool is None:
        return ToolMessage(
            content=f"알 수 없는 도구: {tc['name']}",
            tool_call_id=tc["id"],
            name=tc["name"],
            status="error",
        )
    try:
        # 전체 tool_call dict를 넘기면 langchain이 ToolMessage를 직접 만들어 준다.
        return tool.invoke(tc)
    except Exception as e:
        return ToolMessage(
            content=f"도구 실행 오류: {type(e).__name__}: {e}",
            tool_call_id=tc["id"],
            name=tc["name"],
            status="error",
        )


def run_loop(model_with_tools, question):
    messages = [HumanMessage(question)]
    print(f"질문: {question}")
    for step in range(1, MAX_ITERS + 1):
        ai_msg = model_with_tools.invoke(messages)
        messages.append(ai_msg)
        if not ai_msg.tool_calls:
            print(f"[{step}] 모델 응답: 도구 호출 없음 → 최종 답")
            print(f"최종 답: {ai_msg.content}")
            break
        print(f"[{step}] 모델 응답: tool_calls {len(ai_msg.tool_calls)}개")
        if ai_msg.content:
            print(f"    content: {ai_msg.content}")
        for tc in ai_msg.tool_calls:
            tm = run_tool_call(tc)
            messages.append(tm)
            print(f"    → {fmt_call(tc)} = {tm.content}")
    else:
        print(f"최대 반복({MAX_ITERS}회) 도달 — 최종 답을 얻지 못함")
    print("메시지 흐름: " + " → ".join(type(m).__name__ for m in messages))
    return messages


print("=== 1. tool_call 하나를 손으로 실행하기 ===")
tc = {"name": "lookup_stock", "args": {"item": "사과"}, "id": "call_demo_1", "type": "tool_call"}
full = lookup_stock.invoke(tc)
print(f"전체 dict → {type(full).__name__}")
print(f"content: {full.content}")
print(f"name: {full.name}")
print(f"tool_call_id 일치: {full.tool_call_id == tc['id']}")
raw = lookup_stock.invoke(tc["args"])
print(f"args만 → {type(raw).__name__}: {raw}")

print()
print("=== 2. 수동 도구 실행 루프 ===")
model_with_tools = get_chat_model().bind_tools(ALL_TOOLS)
run_loop(model_with_tools, "사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘.")

print()
print("=== 3. 오류도 ToolMessage로 돌려준다 ===")
for tc in [
    {"name": "subtract", "args": {"a": 3, "b": 1}, "id": "call_demo_2", "type": "tool_call"},
    {"name": "lookup_stock", "args": {"item": "수박"}, "id": "call_demo_3", "type": "tool_call"},
]:
    tm = run_tool_call(tc)
    print(f"{fmt_call(tc)} → [{tm.status}] {tm.content}")

print()
run_loop(model_with_tools, "수박 재고를 확인해줘.")
