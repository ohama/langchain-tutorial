"""2장: 메시지와 멀티턴 대화 — 대화 기록이 곧 모델의 기억이다."""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from shared.config import get_chat_model

model = get_chat_model()

print("=== 1. 대화 기록과 함께 ===")
messages = [
    SystemMessage("너는 간결하게 한국어로 답하는 비서다."),
    HumanMessage("안녕! 내 이름은 민수고, 파이썬을 배우고 있어."),
]
ai = model.invoke(messages)
messages.append(ai)
messages.append(HumanMessage("내 이름이 뭐였고, 무엇을 배우고 있다고 했지?"))
ai2 = model.invoke(messages)
messages.append(ai2)

for m in messages:
    print(f"[{type(m).__name__}] {m.content}")
print(f"최종 답변: {ai2.content}")

print()
print("=== 2. 대화 기록 없이 같은 질문 ===")
no_history_answer = model.invoke(
    [HumanMessage("내 이름이 뭐였고, 무엇을 배우고 있다고 했지?")]
)
print(no_history_answer.content)

print()
print("=== 3. 직접 만든 AIMessage ===")
custom_history = [
    HumanMessage("가장 좋아하는 프로그래밍 언어가 뭐야?"),
    AIMessage("저는 파이썬을 가장 좋아합니다."),
    HumanMessage("방금 뭐라고 답했는지 한 문장으로 요약해줘."),
]
summary = model.invoke(custom_history)
print(summary.content)
