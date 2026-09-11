"""4장: LCEL로 체인 만들기 — Runnable을 파이프(|)로 연결한다."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel
from shared.config import get_chat_model

model = get_chat_model()

print("=== 1. 파이프로 연결 ===")
prompt = ChatPromptTemplate.from_messages(
    [("human", "{topic}을(를) 한 문장으로 설명해줘.")]
)
chain = prompt | model | StrOutputParser()
print("체인 타입:", type(chain).__name__)
result = chain.invoke({"topic": "벡터 데이터베이스"})
print("결과 타입:", type(result).__name__)
print("결과:", result)

print()
print("=== 2. RunnableLambda ===")


def to_input(text: str) -> dict:
    return {"topic": text.strip().upper()}


lambda_chain = RunnableLambda(to_input) | prompt | model | StrOutputParser()
lambda_result = lambda_chain.invoke("  streaming  ")
print("입력: '  streaming  ' ->", lambda_result)

print()
print("=== 3. RunnableParallel ===")
paragraph = (
    "라마(LLaMA)는 메타가 공개한 오픈소스 대규모 언어 모델 계열이다. "
    "다양한 크기로 배포되어 연구자와 개발자가 자유롭게 활용할 수 있다."
)
summary_prompt = ChatPromptTemplate.from_messages(
    [("human", "다음 글을 한 문장으로 요약해줘:\n{text}")]
)
keyword_prompt = ChatPromptTemplate.from_messages(
    [("human", "다음 글에서 핵심 키워드 3개를 쉼표로 구분해서 알려줘:\n{text}")]
)
parallel = RunnableParallel(
    summary=summary_prompt | model | StrOutputParser(),
    keywords=keyword_prompt | model | StrOutputParser(),
)
parallel_result = parallel.invoke({"text": paragraph})
print("키:", sorted(parallel_result.keys()))
for key, value in parallel_result.items():
    print(f"{key}: {value}")

print()
print("=== 4. batch ===")
topics = ["임베딩", "토큰", "프롬프트"]
batch_results = chain.batch([{"topic": t} for t in topics])
for topic, answer in zip(topics, batch_results):
    print(f"{topic} -> {answer}")

print()
print("=== 5. stream ===")
chunk_count = 0
first_chunk_type = None
for chunk in chain.stream({"topic": "스트리밍"}):
    if first_chunk_type is None:
        first_chunk_type = type(chunk).__name__
    print(chunk, end="")
    chunk_count += 1
print()
print("청크 타입:", first_chunk_type)
print("청크 개수:", chunk_count)
