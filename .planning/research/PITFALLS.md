# Domain Pitfalls

**Domain:** 한국어 LangChain/LangGraph 튜토리얼 책 (mdBook, 로컬 LLM 실제 출력 캡처, 캡스톤 코딩 에이전트)
**Researched:** 2026-09-11
**Confidence:** MEDIUM-HIGH (LangChain/LangGraph API 동향과 mdBook 이슈는 공식 문서·GitHub 이슈로 교차 검증. 로컬 서버 특유의 quirk 상당수는 이 프로젝트의 실제 LiteLLM(`http://127.0.0.1:4000/v1`, 모델 `flashnext`) 엔드포인트에 라이브 테스트로 직접 재현하여 HIGH 신뢰도로 확인함. Python 3.14 생태계 호환성도 실제 `uv venv --python 3.14`로 설치·임포트해 확인함.)

## Critical Pitfalls

### Pitfall 1: 폐기 예정 API로 책을 쓰다가 출간 직후 낡아버림 (LangChain API 격변)

**What goes wrong:**
2025년 10월 LangChain v1.0 출시 이후 `LLMChain`, `SimpleSequentialChain`, 구식 `Chain` 베이스 클래스, `AgentExecutor`, `initialize_agent`, 심지어 `langgraph.prebuilt.create_react_agent`까지 모두 사실상 폐기 경로로 이동했다. 이들은 하위 호환용 `langchain-classic` 패키지로 옮겨졌을 뿐 신규 코드의 표준이 아니다. 옛 블로그·튜토리얼·Stack Overflow 답변 대부분이 아직 이 구식 API로 작성돼 있어서, 검색해서 베끼면 그대로 "이미 죽은 API"로 책을 쓰게 된다.

**Why it happens:**
LangChain은 최근 1~2년간 두 번(LCEL 도입, v1.0 재설계) API를 크게 갈아엎었다. 인터넷에 남아있는 콘텐츠의 절대다수는 아직 구버전 기준이라, "가장 많이 나오는 예제"가 곧 "최신 예제"가 아니다.

**How to avoid:**
- 신규 에이전트 코드는 `langchain.agents.create_agent` (LangGraph 실행 엔진 위에서 동작, 미들웨어·구조화 출력·스트리밍·체크포인팅 내장)를 표준으로 채택한다.
- 단순 프롬프트→모델→파서 체인은 LCEL(`|` 파이프)로 작성한다.
- 상태·분기·루프가 필요한 순간부터는 LangGraph `StateGraph`를 직접 쓴다.
- 책 집필 시작 시점에 실제로 설치된 `langchain`/`langgraph`/`langchain-openai` 버전을 부록에 고정 기록하고, 매 챕터 코드에 `import langchain; print(langchain.__version__)` 같은 확인 코드를 부록에서 한 번 보여준다.
- `langchain-classic`이라는 이름 자체가 등장하면 "이건 레거시"라는 신호로 책 본문에 명시한다(비교 표로 다뤄도 됨: "예전엔 이렇게 썼다 → 지금은 이렇게 쓴다").

**Warning signs:**
- 예제 코드에 `from langchain.chains import LLMChain`, `initialize_agent`, `AgentExecutor`가 등장하면 즉시 경고.
- `pip show langchain`이 1.x 미만이거나, `langchain-classic`이 의존성에 끌려 들어오면 구식 경로를 타고 있다는 신호.

**Phase to address:** 기초 챕터(도입부에서 스택 버전 고정) + 도구 호출/LangGraph 챕터(에이전트 구축 방식 선택)

---

### Pitfall 2: 로컬 MLX 서버가 speculative decoding(MTP) 중이면 구조화 출력(`response_format=json_schema`)이 통째로 실패한다

**What goes wrong:**
이 프로젝트의 실제 엔드포인트에 `response_format: {"type": "json_schema", ...}`를 보내면 다음과 같이 즉시 500 에러가 난다(라이브 테스트로 재현 완료):

```
litellm.InternalServerError: ... 'detail': 'Generation failed: Structured response_format is not supported with speculative decoding.'
```

응답의 `timings.draft_kind: "mtp"`에서 보이듯 이 MLX 서버는 멀티토큰예측(speculative decoding)으로 생성 속도를 올리고 있는데, 이 모드에서는 JSON 스키마 강제 디코딩(grammar-constrained decoding)을 지원하지 않는다. `with_structured_output(schema, method="json_schema")` 또는 `method="json_mode"`를 그대로 쓰면 챕터 전체가 막힌다.

**Why it happens:**
LangChain의 `with_structured_output` 기본 동작(또는 기본 method 선택)은 모델 provider가 OpenAI라고 판단하면 `json_schema`/strict 모드를 우선 시도하도록 되어 있는 경우가 많다. 로컬 서버는 OpenAI 호환 API 형태만 흉내낼 뿐, 서버 구현(MLX + 드래프트 모델)이 그 기능을 지원하지 않는데도 클라이언트는 이를 알 방법이 없다.

**How to avoid:**
- 이 프로젝트에서는 `with_structured_output(Schema, method="function_calling")`(도구 호출 기반 구조화 출력)을 기본으로 사용한다. 라이브 테스트로 확인한 바, 이 서버는 tool_calls는 정상 동작하므로 함수 호출을 이용한 구조화 출력은 우회로로 유효하다.
- 챕터 본문에 "왜 `json_schema` 대신 `function_calling`을 쓰는가"를 실제 에러 메시지와 함께 보여주면 오히려 좋은 학습 소재가 된다(로컬 LLM 서빙 스택의 실제 제약을 다루는 책의 강점).
- 부록/트러블슈팅 섹션에 이 500 에러 메시지를 그대로 실어 검색으로 찾아올 독자를 돕는다.

**Warning signs:**
- `with_structured_output` 호출 시 `InternalServerError` 또는 500과 함께 "speculative decoding" 문구.
- LiteLLM/MLX 서버 응답의 `timings.draft_kind`가 `"mtp"`이면 이 제약이 적용됨.

**Phase to address:** 기초 챕터의 "구조화 출력" 절, RAG 챕터(검색 결과 구조화), LangGraph 챕터(구조화 상태 업데이트) — 이 세 곳 모두 `method="function_calling"`으로 통일해야 함.

---

### Pitfall 3: `<think>` 리즈닝 내용이 최종 답변에 섞여 나오거나 도구 호출 루프를 깨뜨림

**What goes wrong:**
Qwen3 계열(이 프로젝트의 Qwen3.8-Flash-Next 포함) 모델 패밀리는 사고 과정을 `reasoning_content`라는 별도 필드로 분리해 반환하도록 설계되어 있는데, 서버 설정이나 클라이언트가 이를 제대로 처리하지 않으면 `<think>...</think>` 태그가 그대로 `content` 필드에 섞여 나온다. 더 나쁜 경우는, 도구 호출 후 다음 턴에 이전 턴의 `reasoning_content`를 대화 히스토리에 되돌려주지 않으면 모델이 도구 호출 루프에서 이상 동작(반복, 형식 붕괴)을 보인다는 보고가 있다.

**Why it happens:**
OpenAI 호환 스펙에는 원래 `reasoning_content` 필드가 없다. 로컬 서버가 이를 확장 필드로 얹어 보내더라도, LangChain의 `ChatOpenAI` 파서나 사용자 코드가 이 필드를 모르면 무시하거나, 서버 설정에 따라 애초에 `content`에 합쳐 보낼 수 있다.

**How to avoid:**
- 도구 호출/에이전트 챕터를 쓰기 전에, 실제로 `curl`이나 최소 스크립트로 응답 JSON 원형을 찍어보고 `reasoning`/`reasoning_content` 필드가 `provider_specific_fields`(LiteLLM 응답 예: `"provider_specific_fields": {"reasoning": null, ...}`) 등 어디에 들어오는지 먼저 확인한다. (라이브 테스트에서는 tool-calling 상황에서 `reasoning`이 `null`로 비어 있었음 — 이 모델/서버 조합에서는 기본적으로 리즈닝이 새지 않는 것으로 1차 확인됨. 단, 프롬프트나 모델 별칭(`flashnext-reach-xhigh` 등 리즈닝 강화 별칭)을 바꾸면 달라질 수 있으므로 각 챕터에서 실제 사용하는 별칭으로 재확인 필요.)
- 만약 `<think>` 태그가 `content`에 섞여 나오는 경우를 발견하면, 정규식으로 제거하는 후처리 유틸을 도구 호출 챕터 초반에 만들어 이후 모든 챕터에서 재사용한다.
- 멀티턴 도구 호출 루프를 직접 구현할 때(LangGraph 챕터), 이전 assistant 메시지의 리즈닝 관련 필드를 그대로 히스토리에 담아 되돌려주는지 여부를 실험으로 검증하고 책에 기록한다.

**Warning signs:**
- 캡처한 출력에 `<think>`, `</think>` 또는 유사 마커가 그대로 보임.
- 멀티턴 도구 호출에서 두 번째 턴부터 모델이 형식을 깨거나 같은 도구를 무한 반복 호출.

**Phase to address:** 도구 호출 챕터(리즈닝 필드 확인 + 후처리 유틸), LangGraph 챕터(멀티턴 히스토리 구성 시 재확인)

---

### Pitfall 4: 콜드 스타트 지연(첫 요청 63초)을 그냥 넘어가서 타임아웃/사용자 경험 문제로 재발

**What goes wrong:**
관찰된 바로는 273 프롬프트 토큰 처리에 콜드 상태에서 약 63초가 걸렸다(반면 라이브 재테스트에서는 288토큰에 1.7초 — 웜 상태 차이가 30배 이상). MLX 서버는 모델을 새로 로드하거나 KV/프롬프트 캐시가 비어 있을 때 프리필(prefill) 단계가 수십~수백 배 느려지는 것으로 알려져 있다(커뮤니티 보고: 60~400배). 책의 코드 예제를 실행할 때마다 이 콜드 스타트가 랜덤하게 재발할 수 있고, 클라이언트에 짧은 타임아웃을 걸어두면 첫 실행에서만 실패하는 재현 어려운 버그처럼 보인다.

**Why it happens:**
LLM 서버 프로세스가 방금 떴거나, 오랫동안 요청이 없어 프롬프트 캐시가 비워졌거나, 이전과 완전히 다른 프롬프트 프리픽스가 들어오면 캐시 재사용이 안 되어 전체 프리필을 다시 계산해야 한다.

**How to avoid:**
- 코드 예제를 "실행해서 캡처"하기 전에 항상 동일 모델로 워밍업 요청 1회를 날리는 관례를 만들고, 이를 실행 스크립트(캡처 자동화 스크립트)에 포함시킨다.
- `ChatOpenAI`의 요청 타임아웃을 짧게 잡지 않는다(기본값 유지 또는 최소 120초 이상). 특히 캡스톤 코딩 에이전트처럼 여러 번 순차 호출하는 코드에서는 각 노드/툴 콜에 개별 타임아웃을 걸 경우 첫 호출만 넉넉하게 잡는다.
- 책 본문에 "왜 첫 실행이 유독 느린가"를 실제 숫자(63초 vs 1.7초)와 함께 설명하는 짧은 박스를 넣으면 독자가 자기 환경에서 겪을 혼란을 미리 해소해준다.
- 출력 캡처 시 실행 시간을 함께 기록해두면(스크립트가 소요 시간을 stderr로 출력), 나중에 "왜 이 챕터만 오래 걸렸지"를 디버깅하기 쉬워진다.

**Warning signs:**
- 동일 코드가 어떤 실행에서는 즉시 끝나고 어떤 실행에서는 수십 초 걸림.
- `httpx.ReadTimeout` 또는 LiteLLM 게이트웨이 타임아웃이 유독 "그날 첫 실행"에만 발생.

**Phase to address:** 기초 챕터(첫 호출 타이밍 설명) + 전체 실행/캡처 자동화(모든 챕터 공통 인프라, 책 인프라 단계)

---

### Pitfall 5: 실제 출력을 캡처해 책에 실었는데, 재실행하면 텍스트가 달라져서 "책과 다르다"는 신뢰 붕괴

**What goes wrong:**
LLM 출력은 본질적으로 비결정적이다(temperature>0이면 물론이고, 0이어도 배치·캐시·speculative decoding 조합에 따라 미세하게 달라질 수 있음). 이 책의 핵심 가치는 "책에 실린 출력은 실제 실행 결과"인데, 코드는 그대로인데 출력 텍스트만 바뀌면 독자(미래의 저자 자신 포함)가 "이 코드가 맞나?"라고 의심하게 된다. 또한 라이브러리 업그레이드 후 예제를 재실행하지 않으면 캡처된 출력이 최신 코드와 어긋나는 "코드-출력 드리프트"가 생긴다.

**Why it happens:**
비결정성은 근본적으로 제거 불가능하고(로컬 모델이라도), 책은 정적 텍스트라서 한 번 캡처하면 재실행 전까지 갱신되지 않는다.

**How to avoid:**
- 예제 스크립트에서 `temperature=0`(또는 이 모델이 지원하는 가장 결정적인 설정)을 기본으로 명시하고, "그래도 완전히 똑같지는 않을 수 있다"는 점을 부록에 한 번 명시적으로 밝힌다.
- 책의 출력 블록에 "실행 시점" 또는 "이 출력은 예시이며 여러분의 실행 결과와 토씨까지 같지 않을 수 있다"는 짧은 캡션 규칙을 SUMMARY.md 작성 규칙에 포함시킨다. → 완벽한 재현을 약속하는 대신 "실제로 실행했다"는 사실 자체를 신뢰의 근거로 삼는다.
- 출력이 매우 긴 경우(특히 LangGraph/캡스톤 에이전트의 다단계 트레이스) 전체를 다 싣지 않고, 핵심 부분만 보여주고 "...(중략)..." 처리하는 규칙을 정한다. 전체 원본은 저장소의 실행 로그 파일로 남긴다.
- 예제 코드와 캡처된 출력을 함께 버전 관리하고, 라이브러리 업그레이드(예: langchain 마이너 버전 상승) 시 "출력 재캡처가 필요한 챕터" 체크리스트를 두어 드리프트를 잡는다. 자동화 스크립트가 "코드 해시 vs 마지막 캡처 시점의 코드 해시"를 비교해 알려주면 이상적이다.
- CI에 "코드가 여전히 실행되는가"만 자동 검증(성공/실패, 형식)하고, 텍스트 완전 일치까지는 강제하지 않는다 — 완전 일치를 CI 게이트로 걸면 매 실행마다 실패하는 무의미한 CI가 된다.

**Warning signs:**
- 같은 챕터를 두 번 실행했는데 출력 길이/구조가 크게 다름(예: 도구를 호출할 때도 있고 안 할 때도 있음).
- 라이브러리 업그레이드 후 실행하면 에러가 나거나 완전히 다른 형식의 출력이 나옴(예: `AgentExecutor`의 verbose 로그 포맷이 버전마다 다름).

**Phase to address:** 책 인프라 단계(캡처 규칙·자동화 스크립트 설계) — 전체 챕터에 걸쳐 적용

---

### Pitfall 6: 캡처된 출력·트레이스백·설정 파일에 API 키나 로컬 절대경로가 섞여 공개 저장소에 노출됨

**What goes wrong:**
`.env`를 커밋하지 않는 것만으로는 부족하다. 실제 위험은 다음 세 가지 형태로 새어나간다.
1. 예외/트레이스백을 그대로 캡처했을 때, 일부 클라이언트 라이브러리는 에러 메시지에 `Authorization` 헤더나 요청 URL 전체(쿼리에 키가 실릴 수 있는 provider도 있음)를 포함시킨다.
2. 로컬 절대경로(`/Users/ohama/...`)가 코딩 에이전트 챕터의 출력(파일 경로, 셸 명령 실행 결과, 스택 트레이스)에 그대로 찍혀 공개된다. 사용자명이 그대로 드러나는 것 자체는 치명적 위험은 아니지만, 재현성을 해치고("독자 환경에서는 이 경로가 없음") 불필요한 개인정보 노출이다.
3. LangSmith를 켜면 프롬프트·응답·메타데이터가 클라우드로 전송된다. 트레이싱 URL을 캡처해서 책에 그대로 붙이면, 그 링크를 통해 프로젝트의 전체 트레이스(입력에 우연히 포함된 민감정보 포함)가 제3자에게 공개될 수 있다.

**Why it happens:**
캡처 자동화가 "터미널에 찍힌 것을 그대로 마크다운에 붙여넣기"로 이루어지면, 스크립트를 실행한 사람의 실제 환경 정보가 무비판적으로 함께 실린다.

**How to avoid:**
- 캡처 스크립트는 항상 API 키를 마스킹하는 공통 유틸(예: 알려진 키 패턴이나 `os.environ["LITELLM_API_KEY"]` 값 자체를 문자열 치환)을 거쳐서 마크다운에 쓴다.
- 예외를 일부러 보여줘야 하는 트러블슈팅 섹션에서는 실제 트레이스백을 캡처하기 전에 직접 눈으로 훑어 키/경로가 없는지 확인하는 절차를 정한다(자동 마스킹 + 수동 리뷰 이중 방어).
- 절대경로가 필요한 캡스톤 챕터(샌드박스 폴더 경로 등)는 실제 홈 디렉터리 대신 `~/sandbox` 같은 플레이스홀더로 치환하거나, 프로젝트 루트 기준 상대경로만 출력하도록 코드를 설계한다(코딩 에이전트의 샌드박스 루트를 항상 상수로 표시하고 절대경로를 로그에 남기지 않는 습관).
- LangSmith 챕터에서 트레이스 공유 링크를 책에 넣을 경우, 반드시 "공개 트레이스"로 명시적으로 전환했는지 확인하고, 그 안에 실제 키·개인 파일 경로·민감한 로컬 파일 내용이 없는지 검토한다. 기본은 트레이스 URL 대신 스크린샷이나 텍스트 요약으로 대체하는 쪽이 안전하다.
- 저장소에 `.env.example`만 커밋하고 `.env`는 `.gitignore`에 넣는 것은 최소 기본이며, 커밋 전 `git status`/`git diff`로 실수로 추가된 파일이 없는지 매번 확인한다.

**Warning signs:**
- 캡처된 마크다운 파일에서 `Bearer `, `sk-`, `/Users/`, `key=` 같은 패턴이 grep으로 걸림.
- LangSmith 프로젝트가 "Public" 트레이스 공유를 켜둔 채로 방치됨.

**Phase to address:** 책 인프라 단계(마스킹 자동화 + 커밋 전 grep 훅) + LangSmith 챕터 + 캡스톤 챕터(경로 처리) + 배포 단계(공개 전 최종 grep 스캔)

---

### Pitfall 7: 승인 없이 셸 명령을 실행하는 캡스톤 에이전트가 샌드박스 폴더를 벗어남

**What goes wrong:**
"지정된 작업 폴더 안에서 승인 없이 파일 읽기/쓰기·셸 명령 실행"이라는 캡스톤 설계는 필연적으로 샌드박스 탈출 위험을 안는다. 흔한 실패 패턴:
1. 경로 접두사 문자열 비교(`path.startswith(sandbox_root)`)만으로 검증하면 `../../etc/passwd` 같은 상대경로 조작이나, 심볼릭 링크(샌드박스 안에 `escape -> /etc`처럼 링크를 만들어두는 것)로 쉽게 우회된다.
2. 모델이 생성한 셸 명령을 그대로 `subprocess.run(cmd, shell=True)`로 실행하면, `rm -rf`, `curl | sh`, 환경변수 덤프(`env`, `cat ~/.zshrc`) 같은 위험 명령이 검증 없이 실행된다.
3. 모델이 스스로 도구를 반복 호출하는 루프(에이전트가 같은 실패를 계속 재시도)에 빠지면 무한 루프로 비용/시간을 소진하거나, 실수로 파괴적 명령을 반복 실행한다.
4. 셸 명령의 표준출력이 매우 크면(예: 큰 파일 cat, 빌드 로그) 이를 그대로 모델 컨텍스트에 되먹이다가 토큰 한도를 초과하거나 다음 요청의 프롬프트 처리 시간이 폭증한다(이 프로젝트 서버는 프롬프트 토큰이 늘수록 프리필 시간이 선형 이상으로 늘어나는 것을 이미 확인함).

**Why it happens:**
"승인 없이 실행"이라는 요구사항 자체가 사람의 판단을 빼는 것이므로, 그 판단을 코드가 대신 해야 하는데 문자열 매칭 수준의 얕은 방어로 충분하다고 착각하기 쉽다.

**How to avoid:**
- 경로 검증은 반드시 `Path(user_path).resolve()`(심볼릭 링크까지 풀어내는 실경로 해석)로 정규화한 뒤, 그 결과가 샌드박스 루트의 실경로 하위에 있는지 확인한다. 단순 문자열 prefix 비교 금지.
- 샌드박스 루트 자체를 심볼릭 링크가 없는 새 디렉터리로 만들고, 에이전트가 그 안에 새 심볼릭 링크를 만드는 것 자체를 파일 쓰기 도구에서 차단(또는 생성 후 매 접근마다 realpath 재검증)한다.
- 셸 명령 실행은 `shell=True` 문자열 실행 대신 인자 배열(`subprocess.run([...], shell=False)`)을 원칙으로 하고, 최소한 명령의 작업 디렉터리(`cwd`)를 항상 샌드박스 루트로 고정한다. 완전한 격리가 목표가 아니라면(이 프로젝트는 human-in-the-loop을 의도적으로 뺐으므로), 최소한 "위험 명령 블록리스트"(`rm -rf /`, `sudo`, 네트워크 유출성 명령 등)와 "실행 시간/출력 크기 상한"은 반드시 둔다.
- LangGraph로 에이전트 루프를 만들 때는 `recursion_limit`(기본값 25)을 명시적으로 설정하고, 도달 시 `GraphRecursionError`를 잡아 "더 이상 진행하지 않고 중단"하도록 설계한다. 같은 도구를 같은 인자로 N회 이상 연속 호출하면 강제 중단하는 간단한 루프 감지도 넣는다.
- 도구 실행 결과(stdout/stderr)는 모델에 되돌리기 전에 길이 상한(예: 수천 토큰)으로 잘라내고, 잘렸다는 사실을 명시적으로 표시한다.
- 이 모든 방어를 "이 캡스톤은 개인 학습용이며 프로덕션 보안 경계가 아니다"라는 명시적 스코프 선언과 함께 책에 적어, 독자가 그대로 인터넷에 노출된 서비스로 배포하지 않도록 경고한다.

**Warning signs:**
- 샌드박스 밖 파일이 읽히거나 수정됨(테스트: 샌드박스 안에 상위 디렉터리를 가리키는 심볼릭 링크를 만들어 접근을 시도해보는 자체 회귀 테스트).
- 에이전트가 같은 도구 호출을 반복하며 진행이 없음(로그에서 동일 tool_call arguments 반복 관찰).
- 셸 명령 출력이 수만 토큰을 넘어가며 다음 요청의 프롬프트 처리 시간이 급증.

**Phase to address:** 캡스톤 챕터(설계·구현 핵심), LangGraph 챕터(recursion_limit·루프 감지 패턴 사전 학습)

---

## Moderate Pitfalls

### Pitfall: 스트리밍과 비스트리밍 응답의 형식이 미묘하게 다름

**What goes wrong:** 라이브 테스트에서 비스트리밍 응답은 도구 호출 전에 한국어 설명 텍스트(`"두 도시의 날씨를 확인하겠습니다."`)를 `content`에 함께 담아 왔지만, 스트리밍 응답에서는 같은 프롬프트로도 델타에 텍스트 없이 tool_calls만 통째로 한 청크에 담겨 왔다(OpenAI 정식 스펙처럼 인자를 문자 단위로 잘게 스트리밍하지 않고 한 번에 완성된 tool_calls 청크로 옴). "delta.content와 tool_calls가 같은 청크에 섞여 오는 경우"와 "tool_calls만 오는 경우"를 모두 처리하지 못하는 파싱 코드는 챕터마다 다른 방식으로 실패한다.

**Prevention:** 스트리밍 예제 코드는 반드시 `content`와 `tool_calls` 델타를 모두 안전하게 이어붙이는(존재하지 않으면 스킵) 방식으로 작성하고, 스트리밍/비스트리밍 두 경로 모두 실제로 실행해서 각각 출력 형태를 책에 보여준다. LangChain의 `AIMessageChunk` 누적(`+=`) 방식을 그대로 활용해 직접 파싱 코드를 새로 짜지 않는다.

---

### Pitfall: LangSmith를 켠 채로 다른 챕터 예제까지 실행해 불필요한 트레이스 비용·데이터 전송 발생

**What goes wrong:** `LANGSMITH_TRACING=true`를 전역 `.env`에 넣어두면, LangSmith 챕터가 아닌 다른 챕터(RAG, 캡스톤 등)를 실행할 때도 모든 요청이 클라우드로 트레이싱된다. 로컬 전용을 원칙으로 하는 이 책의 취지와 어긋나고, 캡스톤처럼 셸 명령 결과가 프롬프트에 들어가는 경우 의도치 않은 로컬 파일 내용이 클라우드로 전송될 수 있다.

**Prevention:** `LANGSMITH_TRACING`은 LangSmith 챕터 전용 환경설정(`.env.langsmith` 또는 해당 챕터 스크립트 내부에서만 설정)으로 분리하고, 기본 `.env`에는 꺼둔 상태를 명시한다. 코드에서 `with tracing_context(enabled=True):`처럼 범위를 좁혀 켜는 패턴을 그 챕터에서 가르친다.

---

### Pitfall: `langchain-community`/개별 통합 패키지 경로 혼동

**What goes wrong:** 벡터스토어·임베딩·문서 로더 등 다수 통합이 `langchain-community`에서 각자의 전용 패키지(`langchain-chroma`, `langchain-huggingface` 등)로 계속 이전되고 있다. 오래된 예제를 참고하면 `from langchain_community.vectorstores import Chroma` 같은, 여전히 동작은 하지만 지원이 줄어드는 경로를 쓰게 된다.

**Prevention:** RAG 챕터 집필 시점에 각 통합의 "권장 임포트 경로"를 PyPI/공식 레퍼런스로 재확인하고(`langchain-chroma`, `langchain-huggingface` 등 전용 패키지 우선), `langchain-community` 사용이 불가피한 부분만 명시적으로 이유를 남긴다.

---

### Pitfall: 다국어 임베딩 모델 로딩이 LLM 서버와 메모리를 두고 경쟁함

**What goes wrong:** 관찰된 MLX LLM 서버의 피크 메모리는 약 124.7GB(128GB 중)로, RAG 챕터에서 별도 프로세스로 다국어 임베딩 모델(예: `sentence-transformers`의 multilingual 모델 또는 BAAI/bge-m3급)을 함께 로드하면 메모리 압박으로 스와핑이 발생하거나 LLM 서버가 OOM으로 죽을 수 있다.

**Prevention:** 임베딩은 가능하면 CPU 전용 소형 모델(bge-m3보다 작은 multilingual-e5-small/base급)을 선택하고, RAG 챕터 실행 전 LLM 서버가 이미 최대 부하 상태인지 확인하는 절차를 안내한다. 임베딩 계산은 배치로 한 번에 끝내고 프로세스를 종료해 메모리를 반환하는 패턴(임베딩 생성 스크립트와 질의응답 스크립트 분리)을 권장한다. 필요하면 임베딩 모델을 미리 계산해 벡터스토어에 영구 저장해두고, 질의 시점에는 임베딩 모델을 다시 로드하지 않는 구조(질의 임베딩만 계산)로 메모리 사용을 최소화한다.

---

## Minor Pitfalls

### Pitfall: mdBook 기본 검색이 한국어(CJK)를 토큰 단위로 제대로 쪼개지 못함

**What goes wrong:** mdBook의 기본 검색은 lunr.js 기반이며 공백 기준 토크나이징을 전제로 한다. 한국어는 공백으로 형태소가 잘 분리되지 않아(교착어 특성), 검색 인덱스가 사실상 문장 단위로만 매칭되거나 부분 일치가 잘 안 될 수 있다. mdBook 자체 이슈 트래커에도 CJK 검색 미지원이 오래된 미해결 이슈로 남아 있다.

**Prevention:** 완벽한 형태소 분석 검색을 도입하기보다, (1) 검색이 "완벽하지 않다"는 점을 감수하고 SUMMARY.md의 목차 구조와 챕터 제목을 충실히 해서 목차 탐색으로 보완하거나, (2) `book.toml`의 `[output.html.search]`에서 `bigram`/개별 글자 단위에 가깝게 토큰이 쪼개지도록 설정을 조정해보고 실제로 한국어 검색어로 테스트한다. 검색 품질을 과신하지 말고 배포 전 실제 한국어 키워드 몇 개로 직접 검색해본다.

---

### Pitfall: `book.toml`의 `site-url`을 안 맞춰서 GitHub Pages 프로젝트 페이지에서 CSS/404가 깨짐

**What goes wrong:** GitHub Pages 프로젝트 사이트는 루트가 아니라 `https://<user>.github.io/<repo>/`처럼 하위 경로에 배포된다. `output.html.site-url`(기본값 `/`)을 리포지토리 경로에 맞추지 않으면 절대경로로 참조되는 CSS/JS 및 404 페이지가 깨진다.

**Prevention:** `book.toml`에 `[output.html] site-url = "/<repo-name>/"`를 명시하고, CI 배포 후 실제 GitHub Pages URL에서 새로고침·직접 하위 경로 접근·404 페이지까지 확인하는 체크리스트를 배포 단계에 둔다.

---

### Pitfall: CI 환경은 로컬 LLM에 접근할 수 없어 "코드 실행 검증"과 "출력 캡처"를 혼동함

**What goes wrong:** GitHub Actions 등 CI 러너는 이 프로젝트의 로컬 LiteLLM(`127.0.0.1:4000`)에 네트워크로 접근할 수 없다. CI에서 예제를 실제로 실행해 출력을 갱신하려는 시도는 필연적으로 실패한다.

**Prevention:** CI의 역할을 "mdBook 빌드 성공 + 정적 검사(코드 블록 문법, 링크 깨짐)"로 한정하고, "코드를 실제로 실행해 출력을 캡처하는 것"은 로컬(저자의 M4 Max 머신)에서만 수행하는 별도 스크립트로 분리한다. 필요하다면 CI에 `pytest -k "not requires_llm"` 같은 마커로 로컬 LLM이 필요한 테스트를 스킵하는 규칙을 둔다.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|------------------|
| `with_structured_output`을 `json_schema`로 먼저 시도하고 실패하면 대충 프롬프트로 JSON 요청 | 빠르게 예제 작동 | 파싱 실패·재시도 로직 산재, speculative decoding 제약을 이해 못한 채 우회 | 트러블슈팅 절에서 실패 사례로 잠깐 보여줄 때만 |
| 캡처 출력에 수동으로 키/경로 지우기(자동화 없이) | 초기 셋업 시간 절약 | 언젠가 한 번은 놓쳐서 새어나감(사람의 실수는 반복됨) | 절대 권장 안 함 — 자동 마스킹 스크립트를 book 인프라 단계에서 먼저 만든다 |
| 캡스톤 에이전트에 위험 명령 블록리스트만 두고 realpath 검증 생략 | 구현 단순 | 심볼릭 링크로 손쉽게 우회당함 | 없음 — 개인 로컬 학습용이라도 realpath 검증은 구현 난이도가 낮으므로 생략할 이유가 없음 |
| 모든 챕터에서 `temperature` 등을 매번 다르게 설정 | 각 예제 튜닝 자유도 | 재현성 저하, "왜 이 챕터만 다르게 동작하나" 혼란 | RAG처럼 확실히 다른 목적(다양성 필요)이 있을 때만, 그 이유를 본문에 명시 |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|-----------------|-------------------|
| LiteLLM 프록시 + MLX 백엔드 | `finish_reason`이 도구 호출 시에도 `"stop"`으로 오는 provider별 불일치를 가정하고 코드 작성 | 이 프로젝트 엔드포인트는 라이브 테스트에서 `finish_reason: "tool_calls"`를 정확히 반환함을 확인했으나, 다른 모델 별칭(`flashnext-codex` 등)으로 바꿀 때마다 재확인 습관화 |
| `ChatOpenAI(base_url=...)` | API 키가 없어도 되는 로컬 서버라고 가정하고 키 파라미터를 생략 → LiteLLM이 인증 요구 시 에러 | `.env`의 `LITELLM_API_KEY`를 항상 `api_key` 파라미터로 명시 전달(빈 문자열이 아닌 실제 값) |
| LangSmith | 트레이싱을 켜두면 자동으로 민감정보가 마스킹된다고 착각 | 기본적으로 마스킹 없음 — 필요 시 LangSmith의 PII 마스킹/redaction 설정을 명시적으로 켜야 함(엔터프라이즈 기능일 수 있어 개인 계정에서는 아예 안 켜는 것을 기본으로) |
| mdBook + GitHub Actions | `mdbook build`만 CI에 넣고 링크 검사·검색 인덱스 생성 확인을 생략 | `mdbook build` 후 `mdbook test`(코드 블록 유효성) 및 배포 후 실제 URL 스모크 체크를 CI 단계에 포함 |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|-----------------|
| 콜드 프리필을 매 챕터 실행마다 감수 | 어떤 실행은 1~2초, 어떤 실행은 수십 초 | 캡처 스크립트에 워밍업 요청을 항상 선행 | 서버 재시작 직후, 또는 완전히 새로운 프롬프트 프리픽스 사용 시 |
| 셸 명령/파일 읽기 결과를 무제한으로 프롬프트에 이어붙임(캡스톤) | 프롬프트 토큰 수가 챕터마다 들쭉날쭉 증가, 프리필 시간 폭증 | 도구 결과 길이 상한 + 요약본만 전달 | 도구 출력이 수천 토큰을 넘는 순간부터 체감 |
| RAG에서 임베딩 모델을 질의마다 새로 로드 | 매 질의응답이 수 초~수십 초 지연 | 임베딩 모델을 프로세스 시작 시 1회만 로드해 재사용 | 문서 수가 늘어나거나 실시간성이 필요한 예제부터 |
| LangGraph 체크포인터에 전체 대화 상태를 매 스텝 통째로 직렬화 | 스텝이 진행될수록 저장/로드 지연 증가 | 상태에는 필요한 최소 필드만 유지, 큰 도구 출력은 상태에 직접 넣지 않고 별도 저장 | 멀티턴 대화가 길어지거나 도구 출력이 큰 경우부터 |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| 캡스톤 에이전트의 파일 쓰기 도구가 경로 문자열만 검사 | 심볼릭 링크/상대경로로 샌드박스 밖 파일 덮어쓰기 | `Path.resolve()`로 실경로 계산 후 샌드박스 루트 하위인지 검증 |
| 셸 명령을 `shell=True`로 그대로 실행 | 명령 인젝션, 파이프/리다이렉트를 통한 임의 실행 | 인자 배열 + `shell=False`, 위험 명령 블록리스트, 실행 시간 제한 |
| `.env` 대신 코드에 API 키 하드코딩한 예제를 실수로 커밋 | 공개 저장소에 키 노출 | 모든 예제가 `os.environ`/`python-dotenv`로만 키를 읽도록 강제, pre-commit에 키 패턴 grep 훅 추가 |
| LangSmith 트레이스를 "Public"으로 공유해 책에 링크 | 프로젝트 전체 트레이스(민감 프롬프트 포함 가능)가 제3자에 노출 | 트레이스는 비공개 유지, 책에는 스크린샷/텍스트 요약만 |
| 캡스톤 에이전트가 네트워크 접근 도구까지 승인 없이 실행 | 외부로 데이터 유출, 원격 코드 다운로드 실행(`curl | sh`) | 이 프로젝트 스코프에서는 네트워크 호출성 명령을 블록리스트에 포함하거나 아예 셸 도구에서 네트워크 인터페이스 접근을 제한 |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-------------------|
| 매우 긴 LangGraph/에이전트 트레이스 출력을 그대로 책에 전부 붙임 | 독자가 스크롤 피로로 핵심을 놓침 | 핵심 스텝만 발췌 + "전체 로그는 저장소 파일 링크"로 안내 |
| 챕터마다 다른 방식으로 에러 처리 코드 스타일이 바뀜 | 독자가 매번 새로운 패턴을 학습해야 함 | 공통 유틸(타임아웃 처리, 리즈닝 마스킹, 도구 출력 자르기)을 초반에 한 번 만들고 이후 챕터에서 재사용 |
| 실행 시간이 긴 예제(콜드 스타트 포함)에 대한 사전 안내 없음 | 독자가 "멈춘 줄" 알고 중단 | 예제 코드 실행 전 "첫 실행은 수십 초 걸릴 수 있음" 안내 박스 |

## "Looks Done But Isn't" Checklist

- [ ] **구조화 출력 챕터:** `with_structured_output` 예제가 `method="json_schema"`로 되어 있지 않은지 확인 — 이 서버에서는 500 에러로 실패함
- [ ] **도구 호출 챕터:** 멀티턴 시나리오(도구 호출 → 결과 반영 → 후속 답변)까지 실제로 실행해 캡처했는지, 단발 호출만 보여주고 끝내지 않았는지 확인
- [ ] **RAG 챕터:** 한국어 질의로 실제 검색 품질을 확인했는지(영어 임베딩 모델을 그대로 쓰다 방치되지 않았는지)
- [ ] **LangGraph 챕터:** `recursion_limit`을 명시적으로 다뤘는지, 무한 루프 시나리오를 한 번은 일부러 재현해 `GraphRecursionError` 처리 예제를 보여줬는지
- [ ] **LangSmith 챕터:** 트레이싱 on/off 범위가 명확한지(전역이 아닌 챕터 국소적으로 켜짐), 공개 저장소 배포 시 API 키가 코드에 없는지
- [ ] **캡스톤 챕터:** 심볼릭 링크·`../` 경로 탈출 시나리오를 실제로 한 번 공격해보고 막히는지 자체 검증했는지, 셸 명령 출력 크기 상한이 있는지
- [ ] **배포 단계:** GitHub Pages 실제 URL에서 하위 경로·404 페이지·검색 기능(한국어 키워드)을 눈으로 확인했는지
- [ ] **전체 저장소:** 커밋 전 `git diff`/`grep -r "Bearer\|/Users/"`로 키·절대경로 잔존 여부를 확인했는지

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|-----------------|------------------|
| 구조화 출력 500 에러로 챕터가 막힘 | LOW | `method="function_calling"`으로 전환, 실패했던 에러를 트러블슈팅 박스로 재활용 |
| 캡처 출력에 API 키/경로가 이미 커밋됨 | MEDIUM-HIGH | 즉시 키 폐기·재발급(LiteLLM 키 로테이션), git history에서 해당 커밋 rewrite 또는 새 저장소로 이전 검토, 절대경로는 텍스트만 치환하는 후속 커밋으로 충분 |
| 라이브러리 업그레이드로 여러 챕터 출력이 stale해짐 | MEDIUM | 코드 실행 자동화 스크립트로 전체 챕터 일괄 재실행·재캡처, diff로 변경된 챕터만 리뷰 |
| 캡스톤 에이전트가 샌드박스를 벗어나 파일을 손상시킴 | MEDIUM | 작업 폴더를 git으로 버전 관리해두면 `git checkout`으로 즉시 복구 가능 — 캡스톤 챕터 시작 전 샌드박스 폴더를 별도 git repo로 초기화해두는 것을 권장 사항으로 명시 |
| mdBook 검색이 한국어에서 기대만큼 안 됨 | LOW | 검색 기능 자체를 "베스트에포트"로 문서화하고 목차/링크 내비게이션 보강으로 대체 |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|----------------|
| 폐기 API로 예제 작성 (Pitfall 1) | 기초 챕터 (스택 버전 고정) | 부록에 버전 표 존재, 코드에 `LLMChain`/`initialize_agent` 미검출(grep) |
| `json_schema` 구조화 출력 500 에러 (Pitfall 2) | 기초 챕터 구조화 출력 절 | 모든 `with_structured_output` 호출이 `method="function_calling"` 사용 |
| 리즈닝 내용 누출 (Pitfall 3) | 도구 호출 챕터 | 캡처 출력에 `<think>` 미검출(grep), 멀티턴 예제 실행 성공 |
| 콜드 스타트 타임아웃 (Pitfall 4) | 책 인프라(캡처 자동화) | 캡처 스크립트에 워밍업 단계 존재, 타임아웃 설정값이 120초 이상 |
| 출력 드리프트/비결정성 (Pitfall 5) | 책 인프라(캡처 규칙) | 출력 블록에 "실행 시점" 캡션 규칙 적용, 재실행 체크리스트 문서화 |
| 키/경로 노출 (Pitfall 6) | 책 인프라 + 배포 단계 | 커밋 전 grep 훅 통과, `.env` 미추적 확인, LangSmith 트레이스 비공개 확인 |
| 샌드박스 탈출/무한 루프 (Pitfall 7) | 캡스톤 챕터 | 심볼릭 링크 탈출 시나리오 테스트 통과, `recursion_limit` 설정 존재, 도구 출력 길이 상한 존재 |
| mdBook 한국어 검색 한계 | 배포 단계 | 실제 한국어 키워드로 검색 스모크 테스트 |
| CI가 로컬 LLM 접근 불가 | 배포 단계 | CI는 빌드/링크 검증만 수행, 실행 캡처는 로컬 전용임을 문서화 |

## Sources

- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) — LLMChain/AgentExecutor → langchain-classic 이전, create_agent 권장
- [What's new in LangGraph v1](https://docs.langchain.com/oss/python/releases/langgraph-v1) — langgraph.prebuilt 폐기, v2.0까지 안정성 공약
- [LangChain and LangGraph 1.0 announcement](https://www.langchain.com/blog/langchain-langgraph-1dot0)
- [Is AgentExecutor Deprecated in LangChain? (BSWEN, 2026)](https://docs.bswen.com/blog/2026-06-16-is-agentexecutor-deprecated-langchain/)
- [initialize_agent deprecation issue #29277](https://github.com/langchain-ai/langchain/issues/29277)
- [langgraph-checkpoint 2.0.26→2.1.0 breaking change issue #5385](https://github.com/langchain-ai/langgraph/issues/5385)
- [LangGraph checkpointer RCE chain research (Check Point / CSA, 2026)](https://research.checkpoint.com/2026/from-sqli-to-rce-exploiting-langgraphs-checkpointer/) — checkpointer 최신 버전 유지 필요성 근거
- [Python 3.14 support issue #34441 (langchain-ai/langchain)](https://github.com/langchain-ai/langchain/issues/34441)
- [init_chat_model Python 3.14 UserWarning issue #33926](https://github.com/langchain-ai/langchain/issues/33926)
- 라이브 검증: `uv venv --python 3.14` 환경에 `langchain==1.4.0`, `langgraph==1.2.11`, `langchain-openai`, `chromadb`, `sentence-transformers`, `faiss-cpu`, `langchain-chroma`, `langchain-huggingface`, `torch==2.14.0` 설치·임포트 성공 확인 (2026-09-11, 이 세션에서 직접 실행)
- [Qwen reasoning_content leak into content field issue](https://github.com/QwenLM/Qwen3.8/issues/26)
- [Persistent `<think>` tags despite enable_thinking:false (llama.cpp issue #13189)](https://github.com/ggml-org/llama.cpp/issues/13189)
- 라이브 검증: `127.0.0.1:4000/v1/chat/completions`에 실제 tool-calling 요청 — 병렬 tool_calls 정상 동작, `provider_specific_fields.reasoning: null`(리즈닝 미누출) 확인 (2026-09-11)
- 라이브 검증: 동일 엔드포인트에 `response_format: json_schema` 요청 시 `500 Structured response_format is not supported with speculative decoding` 재현 (2026-09-11)
- 라이브 검증: 스트리밍 요청 시 tool_calls가 단일 청크로 도착(문자 단위 점진 스트리밍 아님) 확인 (2026-09-11)
- 라이브 검증: 동일 엔드포인트 웜 상태에서 288 프롬프트 토큰 처리 1.7초(프로젝트 컨텍스트에 기록된 콜드 상태 63초 대비 약 35배 차이) 확인 (2026-09-11)
- [MLX cold prefill 60-400x slower than warm (ollama issue #16051)](https://github.com/ollama/ollama/issues/16051)
- [MLX KV cache accumulation / swap issue (ollama issue #16698)](https://github.com/ollama/ollama/issues/16698)
- [LiteLLM parallel_tool_calls drop_params issue](https://github.com/paperclipai/paperclip/issues/2525) — ollama_chat 계열에서 parallel_tool_calls 미지원 사례(참고, 이 프로젝트 서버는 병렬 호출 정상 확인됨)
- [LiteLLM finish_reason "stop" vs "tool_calls" inconsistency](https://docs.litellm.ai/docs/guides/tools_integrations)
- [LangSmith data storage and privacy](https://docs.langchain.com/langsmith/data-storage-and-privacy)
- [Disable/toggle LangSmith tracing during execution](https://support.langchain.com/articles/2491399069-how-do-i-disable-or-toggle-langsmith-tracing-during-execution)
- [Sandboxing LLM Coding Agents Part 2 - Practical Implementation](https://virtuslab.com/blog/ai/sandboxing-llm-coding-agents-part2) — symlink escape, realpath 검증 권고
- [The Balkanization of Execution-Security Research for AI Coding Agents (arXiv 2607.05743)](https://arxiv.org/pdf/2607.05743)
- [mdBook non-English search support issue #2393](https://github.com/rust-lang/mdBook/issues/2393)
- [mdBook CJK search issue #2052](https://github.com/rust-lang/mdBook/issues/2052)
- [mdBook chinese search PR #1496](https://github.com/rust-lang/mdBook/pull/1496)
- [mdBook renderers/site-url configuration docs](https://rust-lang.github.io/mdBook/format/configuration/renderers.html)
- [GitHub Pages absolute URL subpath issue discussion](https://github.com/orgs/community/discussions/188844)

---
*Pitfalls research for: 한국어 LangChain/LangGraph 튜토리얼 (mdBook, 로컬 LLM, 코딩 에이전트 캡스톤)*
*Researched: 2026-09-11*
