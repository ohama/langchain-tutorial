"""5장: 구조화 출력 — Pydantic 스키마로 타입이 있는 결과 받기."""
from pydantic import BaseModel, Field

from shared.config import get_chat_model, get_structured_model


class Person(BaseModel):
    """텍스트에서 추출한 인물 정보"""

    name: str = Field(description="이름")
    age: int = Field(description="나이")
    hobbies: list[str] = Field(description="취미 목록")


print("=== 1. function_calling 방식 (이 책의 규약) ===")
structured = get_structured_model(Person)

result = structured.invoke("김철수는 30살이고 등산과 사진 찍기를 좋아한다.")
print("타입:", type(result).__name__)
print("repr:", repr(result))
print("나이 + 1:", result.age + 1)
print(result.model_dump_json(indent=2))

print()
result2 = structured.invoke("이영희(27)는 요즘 요리에 빠져 있다.")
print("repr:", repr(result2))

print()
print("=== 2. 기본값(json_schema)으로 호출하면? ===")
default_structured = get_chat_model().with_structured_output(Person)
try:
    r = default_structured.invoke("박민수는 22살이고 게임과 독서를 즐긴다.")
    print(f"성공: {type(r).__name__}")
except Exception as e:  # noqa: BLE001
    print(f"실패: {type(e).__name__}")
    print(f"status_code={getattr(e, 'status_code', None)}")
