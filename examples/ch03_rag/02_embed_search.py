"""3부 2장: bge-m3로 임베딩하고 Chroma에 색인한 뒤 한국어 질의로 검색한다."""
import math
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.config import get_embeddings

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


def dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))


print("=== 1. 임베딩 모델 ===")
embeddings = get_embeddings()
print(f"모델: {embeddings.model_name}")
print(f"model_kwargs: {embeddings.model_kwargs}")
vec = embeddings.embed_query("재택근무는 일주일에 며칠 가능한가요?")
print(f"차원: {len(vec)}")
print(f"앞 5개 값: {[f'{x:.6f}' for x in vec[:5]]}")
print(f"벡터 길이(L2 노름): {math.sqrt(dot(vec, vec)):.4f}")

print()
print("=== 2. 뜻이 가까우면 벡터도 가깝다 ===")
base = "연차 휴가는 1년에 며칠인가요?"
similar = "휴가를 한 해에 며칠이나 쓸 수 있나요?"
different = "파이썬 리스트를 정렬하는 방법을 알려주세요."
b, s, d = embeddings.embed_documents([base, similar, different])
print(f"기준: {base}")
print(f"비슷한 뜻: {similar}")
print(f"다른 주제: {different}")
# 정규화된 벡터라 내적이 곧 코사인 유사도
print(f"코사인 유사도(기준, 비슷한 뜻): {dot(b, s):.4f}")
print(f"코사인 유사도(기준, 다른 주제): {dot(b, d):.4f}")

print()
print("=== 3. Chroma에 색인 ===")
chunks = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True
).split_documents(load_documents())
# persist_directory를 주지 않으면 메모리에만 저장된다
vectorstore = Chroma.from_documents(chunks, embedding=embeddings, collection_name="ch03_rag")
print(f"청크 {len(chunks)}개 색인 → 저장된 개수: {len(vectorstore.get()['ids'])}")

print()
print("=== 4. 한국어 질의로 검색 ===")
QUERIES = [
    "LCEL에서 파이프 연산자는 어떤 역할을 하나요?",
    "문서를 자를 때 청크를 겹치게 만드는 이유는?",
    "연차 휴가는 1년에 며칠 받을 수 있나요?",
]
for q in QUERIES:
    print(f"질의: {q}")
    for rank, (doc, score) in enumerate(
        vectorstore.similarity_search_with_score(q, k=3), start=1
    ):
        name = Path(doc.metadata["source"]).name
        print(
            f"  {rank}. {name} start_index={doc.metadata['start_index']} "
            f"거리={score:.4f} | {doc.page_content[:30]!r}"
        )
