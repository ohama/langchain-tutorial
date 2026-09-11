"""3장: 프롬프트 템플릿 — 변수가 있는 템플릿과 few-shot 예시."""
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from shared.config import get_chat_model

model = get_chat_model()

print("=== 1. 변수가 있는 템플릿 ===")
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 {level} 수준의 학습자를 돕는 튜터다. 두 문장 이내로 답하라."),
        ("human", "{topic}을(를) 설명해줘."),
    ]
)
print("input_variables:", prompt.input_variables)

value = prompt.invoke({"level": "초급", "topic": "재귀 함수"})
for m in value.to_messages():
    print(f"[{type(m).__name__}] {m.content}")

answer = model.invoke(value)
print("답변:", answer.content)

print()
print("=== 2. few-shot 템플릿 ===")
examples = [
    {"input": "행복", "output": "슬픔"},
    {"input": "크다", "output": "작다"},
]
example_prompt = ChatPromptTemplate.from_messages(
    [("human", "{input}"), ("ai", "{output}")]
)
few_shot = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt, examples=examples
)
final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "입력된 단어의 반대말만 한 단어로 답하라."),
        few_shot,
        ("human", "{input}"),
    ]
)

expanded = final_prompt.invoke({"input": "빠르다"})
for m in expanded.to_messages():
    print(f"[{type(m).__name__}] {m.content}")

for word in ["빠르다", "밝다", "무겁다"]:
    result = model.invoke(final_prompt.invoke({"input": word}))
    print(f"{word} -> {result.content}")
