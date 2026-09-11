"""3부 3장: 검색 결과를 프롬프트에 주입하는 LCEL RAG 체인으로 답을 만든다."""
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.config import get_chat_model, get_embeddings

EXAMPLES_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = EXAMPLES_DIR / "data" / "ch03_rag"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def load_documents() -> list[Document]:
    # 절대경로 대신 저장소 기준 상대경로를 저장한다
    return [
        Document(
            page_content=p.read_text(encoding="utf-8"),
            metadata={"source": p.relative_to(EXAMPLES_DIR.parent).as_posix()},
        )
        for p in sorted(DATA_DIR.glob("*.md"))
    ]


def format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)


def show_sources(docs) -> None:
    for d in docs:
        print(f"  - {Path(d.metadata['source']).name} start_index={d.metadata['start_index']}")


PROMPT = ChatPromptTemplate.from_template(
    "다음 문서만 참고해서 질문에 한국어로 간단히 답하세요. "
    "문서에 답이 없으면 '문서에서 찾을 수 없습니다'라고 답하세요.\n\n"
    "문서:\n{context}\n\n질문: {question}"
)


print("=== 1. 색인과 retriever 준비 ===")
chunks = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True
).split_documents(load_documents())
vectorstore = Chroma.from_documents(chunks, embedding=get_embeddings(), collection_name="ch03_rag")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
print(f"청크 {len(chunks)}개 색인, retriever 타입: {type(retriever).__name__}, k=2")

print()
print("=== 2. 검색 결과를 프롬프트에 주입하기 ===")
question = "재택근무는 일주일에 며칠까지 할 수 있어?"
docs = retriever.invoke(question)
print(f"질문: {question}")
print("검색된 청크:")
show_sources(docs)
print("--- 모델에게 보낼 프롬프트 ---")
print(PROMPT.invoke({"context": format_docs(docs), "question": question}).to_string())

print()
print("=== 3. LCEL RAG 체인 ===")
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | PROMPT
    | get_chat_model()
    | StrOutputParser()
)
print(f"체인 타입: {type(chain).__name__}")
answer = chain.invoke(question)
print(f"질문: {question}")
print(f"답변: {answer}")

print()
print("=== 4. 문서에 없는 질문 ===")
other = "회사 주차 요금은 한 달에 얼마야?"
print(f"질문: {other}")
print("검색된 청크:")
show_sources(retriever.invoke(other))
print(f"답변: {chain.invoke(other)}")
