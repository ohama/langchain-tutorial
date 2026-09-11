"""1장: 채팅 모델 호출하기 — invoke와 stream의 차이를 보여준다."""
from shared.config import get_chat_model

model = get_chat_model()

print("=== invoke ===")
response = model.invoke("LangChain을 한 문장으로 소개해줘.")
print(type(response).__name__)
print(response.content)
print(response.usage_metadata)

print()
print("=== stream ===")
chunks = []
for chunk in model.stream("하늘이 파란 이유를 두 문장으로 설명해줘."):
    print(chunk.content, end="", flush=True)
    chunks.append(chunk)
print()
print(f"청크 개수: {len(chunks)}")
print([repr(c.content) for c in chunks[:5]])
