"""도구 호출(2부)과 이후 LangGraph 장이 공유하는 순수 결정적 도구들.

네트워크, 시계, 난수를 쓰지 않는다 — 같은 입력이면 항상 같은 결과를 내어
캡처가 재현 가능하고, 나중에 LangGraph 버전이 같은 최종 답에 도달했는지
비교할 수 있게 한다.
"""
from langchain_core.tools import tool

# ANCHOR: add
@tool
def add(a: int, b: int) -> int:
    """두 정수를 더한다."""
    return a + b
# ANCHOR_END: add

# ANCHOR: multiply
@tool
def multiply(a: int, b: int) -> int:
    """두 정수를 곱한다."""
    return a * b
# ANCHOR_END: multiply

# ANCHOR: lookup_stock
_INVENTORY = {"사과": 12, "바나나": 5, "포도": 0}

@tool
def lookup_stock(item: str) -> str:
    """창고 재고 시스템에서 품목의 재고 수량을 조회한다. item은 한글 품목명."""
    if item not in _INVENTORY:
        raise ValueError(f"재고 목록에 없는 품목: {item}")
    return f"{item} 재고: {_INVENTORY[item]}개"
# ANCHOR_END: lookup_stock

# ANCHOR: all_tools
ALL_TOOLS = [add, multiply, lookup_stock]
# ANCHOR_END: all_tools
