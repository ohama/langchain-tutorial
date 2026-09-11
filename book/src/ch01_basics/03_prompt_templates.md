# 프롬프트 템플릿

## 개념: 왜 필요한가

앞 장에서는 메시지를 직접 문자열로 만들어 넣었다. 실제 애플리케이션에서는 고정된 지시문(instruction)과 매번 바뀌는 입력(사용자 질문, 문서 내용 등)을 분리해서 관리하는 편이 훨씬 유지보수하기 쉽다. `ChatPromptTemplate`은 `{변수}` 자리표시자가 들어간 메시지 목록을 만들어 두고, 나중에 실제 값을 채워 완성된 메시지 리스트로 바꿔준다. 같은 템플릿을 여러 입력에 재사용할 수 있다는 것이 핵심 이점이다.

few-shot(퓨샷)은 모델에게 원하는 출력 형식을 규칙으로 설명하는 대신, 입력-출력 예시 몇 개를 보여줘서 패턴을 따라 하게 만드는 기법이다. `FewShotChatMessagePromptTemplate`은 예시 목록을 `human`/`ai` 메시지 쌍으로 자동 확장해 최종 프롬프트에 끼워 넣는다. 이 장의 예제는 아직 LCEL의 `|` 연산자를 쓰지 않고 `prompt.invoke(...)`와 `model.invoke(...)`를 따로 호출한다. 두 단계를 파이프로 연결하는 방법은 다음 장(LCEL)에서 다룬다.

## 최소 코드

`examples/ch01_basics/03_prompt_templates.py`

```python
{{#include ../../../examples/ch01_basics/03_prompt_templates.py}}
```

`=== 1 ===`은 `{level}`, `{topic}` 두 변수가 있는 템플릿을 만들고, `prompt.invoke(...)`로 값을 채워 넣은 뒤(아직 LLM을 호출하지 않은 상태) 그 결과 메시지를 그대로 출력해서 치환이 어떻게 일어나는지 보여준다. 그다음에야 `model.invoke(value)`로 실제 응답을 받는다. `=== 2 ===`는 `input`/`output` 쌍 몇 개를 `few_shot` 템플릿으로 만들고, 최종 프롬프트에 끼워 넣어 확장된 메시지(예시들이 `Human`/`AI` 메시지로 변환된 모습)를 출력한 뒤, 새 단어 세 개에 대해 실제로 반대말을 물어본다.

실행 방법 (examples 디렉터리에서):

```bash
uv run python ch01_basics/03_prompt_templates.py
```

## 실제 출력

아래는 저자가 로컬 `flashnext` 모델로 실제 실행해 캡처한 결과다. LLM 응답이므로 여러분의 결과와 글자 단위로 같지 않을 수 있다.

```text
{{#include ../../../outputs/ch01_basics/03_prompt_templates.out:2:}}
```

`=== 1 ===`에서 `input_variables`가 `['level', 'topic']`로 출력되고, 포맷된 `SystemMessage`/`HumanMessage`에 `{level}`, `{topic}` 자리에 "초급", "재귀 함수"가 정확히 들어간 것을 볼 수 있다. `=== 2 ===`에서는 `examples` 리스트의 두 쌍("행복"→"슬픔", "크다"→"작다")이 각각 `HumanMessage`/`AIMessage`로 변환되어 프롬프트 안에 나타나고, 이 few-shot 예시를 본 모델이 "빠르다", "밝다", "무겁다"에 대해서도 규칙 설명 없이 한 단어 형식(느리다/어둡다/가볍다)으로 정확히 답한다.

## 요점 정리

- `ChatPromptTemplate.from_messages(...)`로 `{변수}`가 포함된 메시지 템플릿을 만들고, `prompt.invoke({...})`로 값을 채운다.
- 템플릿을 채우는 것과 모델을 호출하는 것은 서로 다른 단계다 — 채워진 메시지만 먼저 확인할 수 있다.
- `FewShotChatMessagePromptTemplate`은 입력-출력 예시 목록을 `Human`/`AI` 메시지 쌍으로 자동 확장한다.
- few-shot 예시는 규칙을 길게 설명하지 않고도 모델이 원하는 출력 형식을 따르게 만드는 효과적인 방법이다.
- 다음 장에서 `|` 연산자(LCEL)로 템플릿과 모델 호출을 하나의 체인으로 연결하는 법을 배운다.
