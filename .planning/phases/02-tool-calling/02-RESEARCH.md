# Phase 2: Tool Calling - Research

**Researched:** 2026-09-11
**Domain:** LangChain 도구 정의(`@tool`) + 모델 도구 호출(`bind_tools`) + 수동 tool-call 루프 (langchain-core 1.6.2, langchain-openai 1.6.2, 로컬 LiteLLM 엔드포인트 `flashnext`)
**Confidence:** HIGH — 모든 핵심 주장은 이 세션에서 프로젝트의 실제 `examples/shared/config.py` 경유 라이브 호출로 직접 재현·검증했다 (스크래치 스크립트, 커밋 안 됨).

## Summary

Phase 2는 두 개의 짧은 장으로 끝난다: (1) `@tool`로 도구를 정의하고 `bind_tools`로 모델이 만든 `tool_calls`를 확인하는 장, (2) 모델→tool call→`ToolMessage`→재호출을 손으로 구현해 최종 답을 얻는 장. Phase 1이 이미 만든 저작 파이프라인(`shared/config.py`, `run_examples.py`, `check_book.py`, `check_leaks.py`, SUMMARY.md 자동 발견)은 새 챕터 디렉터리(`ch02_tools`)에 대해 수정 없이 그대로 동작한다 — `SUMMARY.md`에 링크만 추가하면 `check_book.py`가 자동 발견하고, `run_examples.py`는 `examples/ch*` 전체를 글롭하므로 `ch02_tools`도 자동 포함된다.

로컬 엔드포인트(`flashnext`, `temperature=0`)에서 이 세션에 직접 검증한 것: 단일 tool call, 병렬(동시) tool call 2건, `lookup_stock`→`multiply`로 이어지는 2단계 수동 루프가 실제 최종 답(`60`)까지 도달, `tool_choice="add"/"any"/"none"` 모두 정상 동작, `tool.invoke(tool_call)`(전체 dict)가 `ToolMessage`를 직접 반환, 동일 프롬프트 2회 실행 시 `tool_calls`(id 제외)와 `content`가 완전히 동일(결정적), `reasoning`류 필드 누출 없음(`additional_kwargs={'refusal': None}`만 존재). 도구 예외(`ZeroDivisionError`, pydantic `ValidationError`)는 `tool.invoke()`가 그대로 전파하므로 루프 코드가 직접 `try/except`로 잡아 `ToolMessage`로 되돌려야 한다.

**Primary recommendation:** 순수 결정적 도구(사칙연산 + 고정 딕셔너리 재고 조회)를 `examples/shared/tools.py`에 `@tool`로 정의하고, 1장은 정의+`bind_tools`+`tool_calls` 확인, 2장은 같은 도구들을 재사용해 `tool.invoke(tool_call)` 기반 수동 루프(최대 반복 가드 포함)로 최종 답을 만든다. 이 두 장의 프롬프트·도구·최종 답은 Phase 4(GRAPH-02)가 그대로 LangGraph로 재구현할 기준선이므로 그대로 고정한다.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain-core | 1.6.2 (설치 확인됨) | `@tool`, `bind_tools`, `AIMessage.tool_calls`, `ToolMessage` | 이미 Phase 1에서 확정된 버전, 이 프로젝트의 `examples/pyproject.toml`에 `>=1.6.2`로 고정 |
| langchain-openai | 1.6.2 | `ChatOpenAI.bind_tools()` — OpenAI 호환 tool-calling 와이어 포맷으로 직렬화 | 로컬 LiteLLM 엔드포인트가 OpenAI 호환이므로 이 패키지만 필요, `langchain-ollama` 불필요(Phase 1 결정 재사용) |

### Supporting

새 패키지 설치 불필요. `examples/pyproject.toml`의 기존 의존성(`langchain`, `langchain-core`, `langchain-openai`, `pydantic`, `python-dotenv`)만으로 이 페이즈의 모든 기능이 동작함을 라이브로 확인했다.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `langchain_core.tools.tool` | `langchain.tools.tool` (동일 데코레이터 재노출) | 기능은 동일하지만 Phase 1이 일관되게 `langchain_core.*`에서 직접 import했으므로(메시지, 프롬프트, 러너블 모두) 이 관례를 그대로 따른다 |
| `@tool` 데코레이터로 함수를 도구로 승격 | `StructuredTool.from_function(...)` 또는 `BaseTool` 서브클래스 직접 작성 | 이 페이즈는 "손으로 짜는 루프"가 목적이지 커스텀 `BaseTool` 구현이 목적이 아님 — `@tool`이 가장 짧고 표준적인 경로 |
| `tool.invoke(tool_call)`(전체 dict, `ToolMessage` 자동 생성) | `tool.invoke(tool_call["args"])` + `ToolMessage(content=str(result), tool_call_id=tc["id"])` 수동 생성 | 후자는 라이브 테스트로 동작 확인은 되지만(순수 결과값만 반환) `name`/`tool_call_id`를 직접 채워야 하는 중복 코드 — Don't Hand-Roll 참고 |

**Installation:** 불필요 (기존 `examples/` uv 프로젝트 재사용, `uv sync` 이미 완료됨)

## Architecture Patterns

### Recommended Project Structure

```
examples/
├── shared/
│   ├── config.py          # 기존 (변경 없음)
│   └── tools.py            # 신규 — @tool로 정의한 순수 결정적 도구들 (ANCHOR 태그, ch1/ch2/향후 Phase 4가 공유)
└── ch02_tools/
    ├── 01_define_tools.py  # shared.tools import → .args/.name/.description 확인 → bind_tools → tool_calls 출력 (단일+병렬)
    └── 02_tool_loop.py     # shared.tools import → 수동 루프(최대 반복 가드) → 최종 답 출력

book/src/ch02_tools/
    ├── 01_define_tools.md
    └── 02_tool_loop.md

outputs/ch02_tools/
    ├── 01_define_tools.out
    └── 02_tool_loop.out
```

`book/src/SUMMARY.md`에 다음 절만 추가하면 된다 (기존 "# 부록" 절 앞에 삽입):

```markdown
# 2부 도구 호출

- [도구 정의와 bind_tools](ch02_tools/01_define_tools.md)
- [수동 도구 실행 루프](ch02_tools/02_tool_loop.md)
```

**check_book.py / run_examples.py 변경 필요 여부:** 둘 다 변경 불필요.
- `check_book.py`의 `_discover_chapters()`는 `SUMMARY.md`의 링크를 정규식으로 파싱해 `rel.parts[0].startswith("ch")`인 경로만 모으므로, `ch02_tools/*.md` 링크만 추가하면 자동 발견된다.
- `run_examples.py`의 `_collect_examples()`는 인자 없이 실행 시 `EXAMPLES_DIR.glob("ch*")`로 모든 챕터 디렉터리를 스캔하므로 `ch02_tools`도 자동 포함된다. 개별 실행도 `run_examples.py ch02_tools` 형태로 그대로 동작.
- `shared/tools.py`는 `_resolve_target`에서 `shared`/`.venv`는 타깃으로 거부되므로 직접 실행 대상이 아니라 import 전용 모듈로만 쓰인다(= `config.py`와 동일 역할).

### Pattern 1: 도구 정의 — `@tool` + 타입 힌트 + 한 줄 한글 docstring

**What:** 파이썬 함수에 타입 힌트(필수 — 입력 스키마의 근거)와 도구 설명이 되는 docstring을 붙이고 `@tool`을 씌우면 `BaseTool` 인스턴스가 된다.
**When to use:** 이 페이즈의 모든 도구(사칙연산, 재고 조회).
**Example (이 세션에서 라이브 실행 확인):**
```python
# Source: 이 세션 라이브 실행 (langchain_core.tools.tool, langchain-core 1.6.2)
from langchain_core.tools import tool

@tool
def add(a: int, b: int) -> int:
    """두 정수를 더한다."""
    return a + b

print(add.name)          # "add"
print(add.description)   # "두 정수를 더한다."
print(add.args)          # {'a': {'title': 'A', 'type': 'integer'}, 'b': {'title': 'B', 'type': 'integer'}}
print(add.args_schema)   # <class 'langchain_core.utils.pydantic.add'> — 자동 생성된 pydantic 스키마
```
`args_schema`와 `tool_call_schema`는 이 버전에서 동일 객체를 가리킨다(둘 다 접근 가능, 에러 없음).

### Pattern 2: `bind_tools` → `AIMessage.tool_calls` 확인

**What:** `model.bind_tools([...])`로 도구 스키마를 모델에 결합한 새 러너블을 얻고, `invoke()`한 `AIMessage`의 `.tool_calls`(리스트, 0개 이상)를 읽는다.
**When to use:** 1장(TOOL-01)의 핵심 예제.
**Example (라이브 캡처, `flashnext`, `temperature=0`):**
```python
model_with_tools = get_chat_model().bind_tools([add, multiply, lookup_stock])
resp = model_with_tools.invoke("7과 5를 더하면?")
# resp.content == "7 + 5 = **12**"
# resp.tool_calls == [{"name": "add", "args": {"a": 7, "b": 5}, "id": "<uuid>", "type": "tool_call"}]
# resp.response_metadata["finish_reason"] == "tool_calls"
```
병렬 호출(한 번에 2개 이상)도 그대로 리스트에 담겨 온다 — 별도 파싱 불필요:
```python
resp2 = model_with_tools.invoke("사과 재고와 바나나 재고를 각각 확인해줘.")
# len(resp2.tool_calls) == 2, 순서대로 lookup_stock(item="사과"), lookup_stock(item="바나나")
```

### Pattern 3: 도구 실행 → `ToolMessage` — `tool.invoke(tool_call)`을 그대로 쓴다

**What:** `AIMessage.tool_calls`의 각 원소(`{"name", "args", "id", "type"}` 전체 dict)를 해당 `BaseTool.invoke()`에 그대로 넘기면 `content`/`name`/`tool_call_id`가 이미 채워진 `ToolMessage`가 반환된다.
**When to use:** 2장(TOOL-02)의 루프 본문.
**Example (라이브 검증 — 전체 dict vs args-only dict의 차이가 중요한 함정):**
```python
tc = resp2.tool_calls[0]  # {"name": "lookup_stock", "args": {"item": "사과"}, "id": "...", "type": "tool_call"}

result_full = lookup_stock.invoke(tc)          # ToolMessage(content='사과 재고: 12개', name='lookup_stock', tool_call_id='...')
result_args_only = lookup_stock.invoke(tc["args"])  # '사과 재고: 12개' (raw str) — ToolMessage가 아님!
```
루프 코드는 반드시 **전체 `tool_call` dict**를 `invoke`에 넘겨야 `ToolMessage` 생성을 손으로 다시 하지 않는다.

### Pattern 4: 수동 재호출 루프 — 최대 반복 가드 + 미지 도구/예외 처리

**What:** `messages` 리스트를 `[HumanMessage(...)]`로 시작해, 매 반복마다 `model_with_tools.invoke(messages)`로 `AIMessage`를 받아 append하고, `tool_calls`가 있으면 각각 실행해 `ToolMessage`를 append, 없으면 종료.
**When to use:** 2장 전체, 그리고 Phase 4(GRAPH-02)가 LangGraph로 재구현할 기준 로직.
**Example (라이브 실행 — 실제로 2단계를 거쳐 최종 답 `60`에 도달함을 확인):**
```python
# Source: 이 세션 라이브 실행
from langchain_core.messages import HumanMessage, ToolMessage

tools = [add, multiply, lookup_stock]
tool_map = {t.name: t for t in tools}
MAX_ITERS = 5

messages = [HumanMessage("사과 재고와 바나나 재고를 곱하면 몇이야? 재고 조회 후 곱셈 도구로 계산해줘.")]

for i in range(MAX_ITERS):
    ai_msg = model_with_tools.invoke(messages)
    messages.append(ai_msg)
    if not ai_msg.tool_calls:
        print("최종 답:", ai_msg.content)
        break
    for tc in ai_msg.tool_calls:
        name = tc["name"]
        if name not in tool_map:
            tm = ToolMessage(content=f"알 수 없는 도구: {name}", tool_call_id=tc["id"])
        else:
            try:
                tm = tool_map[name].invoke(tc)
            except Exception as e:
                tm = ToolMessage(content=f"도구 실행 오류: {type(e).__name__}: {e}", tool_call_id=tc["id"])
        messages.append(tm)
else:
    print("최대 반복 도달 — 최종 답을 얻지 못함")
```
실제 캡처 결과: iter 0에서 `lookup_stock` 2회(병렬), iter 1에서 `multiply(a=12, b=5)`, iter 2에서 tool_calls 없이 `"사과 재고 12개 × 바나나 재고 5개 = **60**입니다."`로 종료 — 3회 모델 호출로 정확한 최종 답에 도달.

### Anti-Patterns to Avoid

- **`tool_call["args"]`만 꺼내 `tool.invoke()`하고 `ToolMessage`를 손으로 재조립:** `name`/`tool_call_id`를 직접 채워야 해서 실수 여지가 생긴다. 전체 `tool_call` dict를 넘기면 프레임워크가 다 채워준다(Pattern 3).
- **도구 함수 내부에서 예외를 삼켜서 항상 성공 문자열만 반환:** 이 페이즈의 요구사항(로직 안전장치: 미지 도구/예외 처리)을 보여줄 수 없게 된다. 예외는 도구 밖(루프)에서 잡아 `ToolMessage(content="...오류...")`로 모델에 되돌려야 모델이 스스로 복구 시도를 할 수 있다는 교육적 포인트가 산다.
- **`while True` 무한 루프:** 반드시 `MAX_ITERS` 가드를 넣는다 — PITFALLS.md가 이미 "동일 tool_call 인자를 반복하며 진행이 없는" 사례를 경고했다(다른 세션에서 관찰).
- **비결정적 도구(현재 시각, 랜덤값, 실제 네트워크 호출)를 예로 사용:** `.out` 캡처가 재현 불가능해지고 Phase 4의 LangGraph 버전이 "같은 최종 답"에 도달했는지 비교할 수 없게 된다. 순수 함수 + 고정 딕셔너리만 사용(이번 세션에서 결정적임을 실측 확인: 동일 프롬프트 2회 실행 시 `tool_calls`(id 제외)와 `content` 완전 동일).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 도구 입력 스키마(JSON Schema) 생성 | 수동으로 dict/pydantic 스키마 작성 후 모델에 전달 | `@tool` + 타입 힌트 (`add.args_schema`가 자동 생성됨) | 타입 힌트만으로 정확한 스키마가 나옴 — 라이브 확인(`add.args == {'a': {...'type':'integer'}, 'b': {...}}`) |
| tool_call → 함수 실행 → 메시지 변환 | `getattr`/수동 dispatch + `ToolMessage(content=str(result), tool_call_id=...)` 조립 | `tool_map[name].invoke(tool_call)` (전체 dict) | `ToolMessage` 필드(`name`, `tool_call_id`, `content`)를 프레임워크가 정확히 채움(Pattern 3) |
| 병렬 tool_calls 파싱 | 모델 응답 텍스트에서 정규식으로 여러 호출 추출 | `AIMessage.tool_calls`(리스트, 이미 파싱 완료) | 이 엔드포인트에서 병렬 호출이 리스트 형태로 정상 반환됨을 라이브 확인(2건 동시) |
| 스트리밍 tool_call 청크 누적 | 델타를 직접 문자열로 이어붙여 JSON 파싱 | `AIMessageChunk` 덧셈(`chunk1 + chunk2 + ...`) | `tool_call_chunks`가 이미 있고, `+=` 누적이 `tool_calls`를 완성된 형태로 만들어줌(라이브 확인 — 단, 이 엔드포인트는 tool_call이 한 청크에 통째로 옴, PITFALLS.md와 일치) — 이 페이즈는 스트리밍을 요구사항에 포함하지 않으므로 참고용 |

**Key insight:** langchain-core의 도구 계층(`@tool`, `bind_tools`, `AIMessage.tool_calls`, `BaseTool.invoke(tool_call)`)은 스키마 생성·병렬 파싱·메시지 조립까지 이미 다 해결해 둔 문제다. 이 페이즈에서 손으로 짜야 하는 유일한 부분은 "재호출 루프 자체"(model → tool_calls 있으면 실행 → 없으면 종료)이며, 그게 바로 이 페이즈의 교육 목적이다 — 루프 이외의 것을 손으로 만들면 교육 목적이 아니라 재발명이 된다.

## Common Pitfalls

### Pitfall 1: `tool.invoke()`가 예외를 그대로 전파한다 — 루프가 직접 잡아야 함

**What goes wrong:** 도구 함수가 예외를 던지면(`ZeroDivisionError`, 잘못된 인자에 대한 pydantic `ValidationError` 등) `tool.invoke(tool_call)` 호출이 그 예외로 죽는다. 루프에 `try/except`가 없으면 전체 스크립트가 크래시한다.
**Why it happens:** `BaseTool.invoke`는 내부 함수를 그대로 호출하고 예외를 감싸지 않는다(라이브 확인: `divide.invoke({"a":10,"b":0, ...})` → `ZeroDivisionError` 그대로 전파, 필수 인자 누락 시 `pydantic.ValidationError` 전파).
**How to avoid:** 루프의 tool 실행 부분을 `try/except Exception as e: tm = ToolMessage(content=f"도구 실행 오류: {type(e).__name__}: {e}", tool_call_id=tc["id"])`로 감싼다(Pattern 4 예제 그대로).
**Warning signs:** 예제가 `try/except` 없이 `tool.invoke()`를 직접 호출하면서 "실패 예시"를 보여주려 한다면, 실제로는 스크립트가 죽어 `.out`이 생성되지 않는다.

### Pitfall 2: `tool_call["args"]`만 넘기면 `ToolMessage`가 아니라 원시 반환값이 온다

**What goes wrong:** `tool.invoke(tool_call["args"])`처럼 `args`만 꺼내 넘기면 함수의 반환값(예: `int`, `str`)이 그대로 온다. `.content`/`.tool_call_id`가 없으므로 이어서 `messages.append()`하면 `ToolMessage`가 아니라 잘못된 타입이 대화 히스토리에 들어간다.
**Why it happens:** `BaseTool.invoke`는 입력이 `dict`이고 `tool_call` 형태(`name`/`args`/`id`/`type` 키를 가짐)인지 아닌지에 따라 동작이 갈린다 — 전체 tool_call dict를 넘기면 `ToolMessage`로 감싸 반환, 순수 인자 dict를 넘기면 원시 결과를 반환한다(이 세션에서 직접 확인, 위 Pattern 3).
**How to avoid:** 루프에서는 항상 `AIMessage.tool_calls`의 원소(전체 dict)를 그대로 `invoke()`에 전달한다.
**Warning signs:** 재호출 루프에서 `messages.append(result)`한 다음 모델이 "이전 도구 결과를 못 찾겠다"는 식으로 답하면 십중팔구 이 문제다.

### Pitfall 3: 모델이 도구 호출 시 `content`를 빈 문자열로 낸다 — "설명 없이 바로 호출"을 전제로 프롬프트/출력 설계

**What goes wrong:** 이번 세션의 모든 tool-call 턴에서 `AIMessage.content`는 빈 문자열(`''`)이었고, 최종 답 턴에서만 실제 텍스트가 나왔다(PITFALLS.md가 예고한 "비스트리밍은 도구 호출 전 설명 텍스트를 담아 옴"과 달리, 이번 세션·이 프롬프트 조합에서는 설명 텍스트 없이 바로 tool_calls만 나왔다 — 프롬프트에 따라 달라질 수 있음을 시사).
**Why it happens:** 모델별/프롬프트별 동작 차이. 이 페이즈의 예제는 이 사실에 의존하지 말고, `content`가 있든 없든 안전하게 출력하는 루프 로그(예: `content가 있으면 출력, 없으면 생략`)를 짠다.
**How to avoid:** 챕터 프로즈에서 "모델이 도구 호출 시 설명 텍스트를 냈는지 여부는 실제 캡처를 그대로 보여준다"고만 서술하고, 있다/없다를 단정하지 않는다. 출력 포맷팅 코드는 `if ai_msg.content: print(ai_msg.content)` 형태로 방어적으로 작성.
**Warning signs:** 챕터 프로즈가 "모델이 항상 `~하겠습니다`라고 말한 뒤 도구를 호출한다"처럼 단정하면 캡처와 어긋날 수 있다.

### Pitfall 4: 비결정적 도구를 쓰면 `.out` 캡처가 매번 달라져 Phase 4 대조가 깨짐

**What goes wrong:** 현재 시각, `random`, 실제 HTTP 호출 등을 도구에 쓰면 캡처마다 결과가 달라진다. Phase 4(GRAPH-02)는 이 루프를 LangGraph로 재구현해 "같은 최종 답"에 도달해야 하는데, 비결정적 도구는 비교 기준 자체를 무너뜨린다.
**Why it happens:** 요구사항 노트에 명시된 재사용 제약("Phase 4가 이 루프를 재구현하며 같은 최종 답에 도달해야 함")을 간과하면 흔히 생기는 실수.
**How to avoid:** 사칙연산(`add`, `multiply`)과 고정 딕셔너리 기반 조회(`lookup_stock`, 실제 네트워크/DB 없음)만 사용. `temperature=0`은 이미 `get_chat_model()` 기본값(Phase 1 결정, 변경 불필요).
**Warning signs:** 도구 함수 안에 `datetime.now()`, `random.*`, `requests.get(...)` 등이 보이면 즉시 위험 신호.

## Code Examples

### 도구 정의 모듈 스켈레톤 (`examples/shared/tools.py` 후보 — 플래너가 최종 확정)

```python
# Source: 이 세션 라이브 실행으로 검증된 패턴
"""Phase 2(도구 호출)와 Phase 4(LangGraph)가 공유하는 순수 결정적 도구."""
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
        return f"'{item}'은(는) 재고 목록에 없음"
    return f"{item} 재고: {_INVENTORY[item]}개"
# ANCHOR_END: lookup_stock
```
`config.py`와 동일하게 ANCHOR로 태그하면, 1장 프로즈는 `{{#include ../../../examples/shared/tools.py:add}}` 식으로 도구별 정의를 보여줄 수 있고, `check_book.py`의 "ANCHOR 있는 파일은 반드시 anchor suffix로 include" 규칙을 만족한다.

### `tool_choice`로 특정 도구 강제 (라이브 검증 — 참고용, 요구사항에는 없지만 플래너 재량 항목일 수 있음)

```python
# Source: 이 세션 라이브 실행
forced = model.bind_tools(tools, tool_choice="add").invoke("아무 말이나 해줘, 도구는 쓰지 마.")
# forced.tool_calls == [{"name": "add", "args": {"a": 1, "b": 2}, ...}]  # 강제로 add 호출

no_tools = model.bind_tools(tools, tool_choice="none").invoke("7과 5를 더하면?")
# no_tools.tool_calls == []  # 강제로 도구 미사용, content에 텍스트로 직접 답함
```
`tool_choice`는 `"<도구이름>"`(특정 도구 강제), `"any"`(아무 도구나 강제), `"none"`(도구 사용 금지) 모두 이 엔드포인트에서 정상 동작함을 확인했다. TOOL-01/TOOL-02 요구사항에는 필수가 아니므로, 챕터에 넣을지는 플래너 재량(넣으면 "왜 모델이 도구를 쓰기로 했는지" 대조 설명에 유용).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `langchain.agents.AgentExecutor` + `initialize_agent`로 도구 호출 루프를 감춤 | 이 페이즈처럼 루프를 손으로 먼저 보여준 뒤, Phase 5에서 `langchain.agents.create_agent`(LangChain 1.0 GA, 2025-10-22)로 대비 | LangChain 1.0 | `AgentExecutor`류는 `langchain-classic`으로 이동, 새 코드 기준 아님(STACK.md 기존 결론 재확인, 이 페이즈에서 변경 없음) |
| `langgraph.prebuilt.create_react_agent` | `langchain.agents.create_agent`(공식 마이그레이션 가이드가 전자를 폐기 예정으로 안내) | 확인된 시점: STACK.md 리서치(이전 세션) | 이 페이즈에는 영향 없음(둘 다 Phase 2 범위 밖, TOOL-V2-01로 Phase 5 캡스톤에 배정됨) |

**Deprecated/outdated:** 이 페이즈 범위에서는 해당 없음 — `@tool`/`bind_tools`/`AIMessage.tool_calls`/`ToolMessage`는 langchain-core 1.6.2의 안정된 표준 API다.

## Open Questions

1. **모델이 도구 호출 시 `content`에 설명 텍스트를 담는지 여부가 프롬프트에 따라 달라짐**
   - What we know: PITFALLS.md(이전 세션)는 비스트리밍에서 설명 텍스트가 `content`에 함께 온 사례를 기록했지만, 이번 세션의 tool-calling 턴들은 모두 `content=''`였다.
   - What's unclear: 챕터에서 실제로 쓸 최종 프롬프트 문구에 따라 어느 쪽이 나올지는 캡처 시점에 확인해야 한다.
   - Recommendation: 챕터 프로즈는 반드시 **실제 캡처된 `.out`**을 보고 사후 서술한다("모델이 이번에는 설명 없이 바로 도구를 호출했다" 등, 사전 단정 금지). 플랜 단계에서 이미 정해둔 프롬프트 문구는 고정하고, 캡처 후 프로즈를 맞춘다(Phase 1의 `01-04-SUMMARY.md`가 보여준 관례 — `TextAccessor` 타입 이슈를 사실 그대로 문서화한 것과 동일 원칙).

2. **`shared/tools.py`를 Phase 4가 실제로 어떻게 import할지**
   - What we know: Phase 4(GRAPH-02)가 "이 페이즈의 수동 루프를 LangGraph 그래프로 재구현해 같은 최종 답에 도달"해야 한다는 요구는 로드맵 노트에 있다.
   - What's unclear: Phase 4가 `shared/tools.py`를 그대로 import할지, 아니면 `examples/ch04_.../`에서 재정의할지는 이 페이즈의 플래너가 결정할 사항이 아니라 Phase 4 계획 시점의 결정이다.
   - Recommendation: 이 페이즈는 `shared/tools.py`에 안정적이고 순수한(부작용 없는) 도구 인터페이스만 만들어 두면 충분하다 — `ChatOpenAI(` 생성자는 여기 없어야 하고(그 규칙은 `config.py` 전용), 도구 자체는 어떤 그래프/루프에서도 재사용 가능한 순수 `@tool` 함수로 유지한다.

## Sources

### Primary (HIGH confidence)
- 이 세션 라이브 코드 실행 (2026-09-11): `examples/shared/config.py`의 `get_chat_model()`을 경유해 로컬 `flashnext` 엔드포인트에 `@tool`/`bind_tools`/단일 tool call/병렬 tool call/수동 재호출 루프(2단계, 최종 답 도달)/`tool_choice`(3가지 값)/결정성(동일 프롬프트 2회 비교)/도구 예외 전파(`ZeroDivisionError`, pydantic `ValidationError`)/`tool.invoke(전체 dict)` vs `tool.invoke(args만)` 차이/스트리밍 tool_call_chunks를 모두 직접 실행해 확인. 스크립트는 스크래치패드에만 존재, 리포에 커밋되지 않음
- `examples/pyproject.toml`, `uv run --project examples python -c "..."` — langchain-core 1.6.2, langchain-openai 1.6.2 설치 버전 직접 확인
- `.planning/research/PITFALLS.md`, `.planning/research/STACK.md` (이전 세션의 라이브 검증 기록) — 병렬 tool_calls 정상 동작, `finish_reason: tool_calls` 정확 반환, 스트리밍 tool_calls 단일 청크 도착, reasoning 필드 미누출을 이번 세션에서 재확인/보강

### Secondary (MEDIUM confidence)
- [Tools - Docs by LangChain](https://docs.langchain.com/oss/python/langchain/tools) — `@tool` 데코레이터(타입 힌트 필수, docstring=설명), tool_call 구조, 수동 재호출 루프 패턴 설명이 이 세션의 라이브 검증 결과와 일치함을 교차 확인
- [bind_tools | langchain_core Reference](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/bind_tools) — `bind_tools` 시그니처 존재 확인(WebSearch 스니펫)
- [How to force models to call a tool](https://python.langchain.com/v0.2/docs/how_to/tool_choice/) — `tool_choice` 옵션 존재 확인(WebSearch 스니펫; 실제 동작은 이 세션 라이브 테스트로 1차 검증됨)

### Tertiary (LOW confidence)
없음 — 모든 핵심 API 동작은 라이브 실행으로 1차 검증됨.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 버전 고정 확인됨, 신규 패키지 불필요
- Architecture: HIGH — 기존 Phase 1 파이프라인(check_book.py/run_examples.py) 코드를 직접 읽고 신규 챕터 디렉터리에 대해 변경 불필요함을 정적 분석으로 확인
- 도구 호출 API 동작(tool_calls 구조/병렬/결정성/예외 전파/tool_choice) : HIGH — 전부 이 세션의 라이브 호출로 직접 재현
- Pitfalls: HIGH — 이전 세션 기록(PITFALLS.md)과 이번 세션 라이브 재현이 일치하거나(병렬 호출, finish_reason, 스트리밍 청크) 보강됨(content 빈 문자열 관찰, tool_call dict vs args-only 차이는 이번 세션 신규 발견)

**Research date:** 2026-09-11
**Valid until:** 30일 (langchain-core/langchain-openai 버전과 로컬 엔드포인트가 고정되어 있는 한 안정적; 로컬 서버 모델 별칭이나 langchain 메이저 버전이 바뀌면 재검증 필요)
