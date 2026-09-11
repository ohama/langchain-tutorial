# 구조화 출력

## 개념: 왜 필요한가

지금까지 모델의 응답은 항상 사람이 읽는 문장이었다. 하지만 실제 프로그램은 문장이 아니라 필드가 있는 데이터 — 이름, 나이, 목록 같은 값 — 를 필요로 할 때가 많다. "김철수는 30살이고 등산과 사진 찍기를 좋아한다"라는 문장에서 `name`, `age`, `hobbies` 같은 필드를 직접 정규식이나 문자열 파싱으로 뽑아내는 건 깨지기 쉽다.

`with_structured_output`은 Pydantic으로 정의한 스키마를 모델에 전달해, 응답을 그 스키마의 인스턴스로 직접 돌려받게 해준다. `Person`처럼 `BaseModel`을 상속한 클래스를 정의하면, 결과는 딕셔너리가 아니라 `result.age`, `result.hobbies`처럼 속성으로 접근할 수 있는 진짜 타입이 있는 객체가 된다.

## 최소 코드

### 이 책의 규약: get_structured_model

```python
{{#include ../../../examples/shared/config.py:structured}}
```

`get_structured_model(schema)`는 `get_chat_model()`이 만든 모델에 `with_structured_output(schema, method="function_calling", strict=False)`를 적용한 것이다. `method="function_calling"`은 스키마를 "도구(tool) 정의"로 모델에 전달해서, 모델이 그 도구를 호출하는 형태로 인자(필드 값)를 채우게 하는 방식이다. `strict=False`는 이 방식이 내부적으로 스키마를 엄격하게 강제하는 디코딩을 타지 않도록 한다. 이유는 아래 트러블슈팅 절에서 다룬다. 이 책의 모든 구조화 출력 예제는 `with_structured_output`을 직접 부르지 않고 항상 이 함수를 거친다.

### 예제 코드

`examples/ch01_basics/05_structured_output.py`

```python
{{#include ../../../examples/ch01_basics/05_structured_output.py}}
```

`=== 1 ===`은 `Person` 스키마로 `get_structured_model(Person)`을 만들고, 두 개의 서로 다른 문장을 넣어 각각 실제 `Person` 인스턴스를 받는다. `result.age + 1`을 계산해서 `age`가 문자열이 아니라 진짜 정수임을 보여주고, `model_dump_json(indent=2)`로 JSON 형태도 함께 출력한다. `=== 2 ===`는 이 책이 왜 `function_calling, strict=False`를 규약으로 삼는지 보여주기 위한 의도적인 안티패턴 예제로, `with_structured_output`을 method 지정 없이(기본값 그대로) 직접 호출한다.

실행 방법 (examples 디렉터리에서):

```bash
uv run python ch01_basics/05_structured_output.py
```

## 실제 출력

아래는 저자가 로컬 `flashnext` 모델로 실제 실행해 캡처한 결과다. LLM 응답이므로 여러분의 결과와 글자 단위로 같지 않을 수 있다.

```text
{{#include ../../../outputs/ch01_basics/05_structured_output.out:2:}}
```

`=== 1 ===`에서 `타입: Person`으로 결과가 진짜 `Person` 인스턴스임을 확인할 수 있고, `나이 + 1: 31`은 `age` 필드가 문자열 `"30"`이 아니라 정수 `30`이라는 뜻이다. `repr`로 두 번째 입력("이영희(27)는 요즘 요리에 빠져 있다.")의 결과도 `Person(name='이영희', age=27, hobbies=['요리'])`처럼 정확히 파싱된 것을 볼 수 있다.

### 트러블슈팅: speculative decoding과 500 에러

`=== 2 ===`에서 method를 지정하지 않고 `with_structured_output(Person)`을 그대로 호출하면, 실제 캡처된 출력처럼 `실패: OpenAIAPIError`와 `status_code=500`이 뜬다. 원인은 이렇다.

- `with_structured_output`의 기본 방식은 서버에게 "이 JSON 스키마를 반드시 지키는 형태로만 생성하라"고 강제하는 스키마 제약 디코딩(schema-constrained decoding)을 요청한다. 엄격(strict) 모드의 `function_calling`도 내부적으로 같은 제약 디코딩 경로를 탄다.
- 이 책이 쓰는 로컬 MLX 서버는 응답 속도를 높이기 위해 스펙큘레이티브 디코딩(speculative decoding, 멀티토큰예측/MTP)을 켜고 있는데, 이 모드는 스키마 제약 디코딩과 함께 쓸 수 없다. 그래서 서버는 요청 자체를 처리하지 못하고 HTTP 500으로 응답한다.

해결책은 `method="function_calling", strict=False`로 호출하는 것이다. 이 조합은 스키마를 도구 정의로만 전달하고 엄격한 제약 디코딩을 요구하지 않으므로, 스펙큘레이티브 디코딩과 충돌하지 않는다. `=== 1 ===`의 성공한 결과가 바로 이 조합으로 얻은 것이다. 이 책은 이 설정을 `shared/config.py`의 `get_structured_model` 한 곳에만 넣어두었기 때문에, 앞으로 나올 모든 장(RAG, LangGraph 등)이 이 함수만 쓰면 자동으로 같은 해결책을 물려받는다.

## 요점 정리

- 구조화 출력은 항상 `get_structured_model`로.
- `get_structured_model(Schema)`는 응답을 딕셔너리가 아니라 `Schema`의 실제 인스턴스로 돌려준다 — 필드는 속성으로 접근하고, 타입(정수, 리스트 등)도 그대로 지켜진다.
- 이 로컬 서버는 스펙큘레이티브 디코딩을 쓰기 때문에 `with_structured_output`의 기본 방식(스키마 제약 디코딩)이 HTTP 500으로 실패한다.
- `method="function_calling", strict=False`는 스키마 제약 디코딩을 피해가므로 이 서버에서 안전하게 동작하며, `shared/config.py`에 한 번만 설정해 모든 장이 공유한다.
