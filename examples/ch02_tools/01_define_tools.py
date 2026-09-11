"""2부 1장: tool 데코레이터로 정의한 도구를 확인하고 bind_tools로 모델의 tool_calls를 본다."""
import json

from shared.config import get_chat_model
from shared.tools import ALL_TOOLS, add


def show_response(msg):
    print(f"응답 타입: {type(msg).__name__}")
    print(f"finish_reason: {msg.response_metadata.get('finish_reason')}")
    print(f"content: {msg.content!r}")
    print(f"tool_calls: {len(msg.tool_calls)}개")
    for tc in msg.tool_calls:
        args = json.dumps(tc["args"], ensure_ascii=False)
        print(f"  - {tc['name']}({args})  type={tc['type']}  id 있음={bool(tc['id'])}")


print("=== 1. tool 데코레이터가 만든 도구 ===")
print("타입:", type(add).__name__)
for t in ALL_TOOLS:
    print(f"- {t.name}: {t.description}")
    print(f"  args: {json.dumps(t.args, ensure_ascii=False)}")
print("add.invoke({'a': 2, 'b': 3}) =", add.invoke({"a": 2, "b": 3}))

print()
print("=== 2. bind_tools: 도구 하나를 부르는 질문 ===")
model = get_chat_model()
model_with_tools = model.bind_tools(ALL_TOOLS)
show_response(model_with_tools.invoke("7과 5를 더하면?"))

print()
print("=== 3. 한 번에 여러 도구를 부르는 질문 ===")
show_response(model_with_tools.invoke("사과 재고와 바나나 재고를 각각 확인해줘."))

print()
print("=== 4. 도구가 필요 없는 질문 ===")
show_response(model_with_tools.invoke("LangChain에서 도구 호출이 무엇인지 한 문장으로 설명해줘."))
