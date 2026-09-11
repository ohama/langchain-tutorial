"""3부 1장: 한국어 마크다운 문서를 Document로 읽고 RecursiveCharacterTextSplitter로 나눈다."""
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

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


print("=== 1. 문서 로딩 ===")
docs = load_documents()
print(f"문서 {len(docs)}개 (타입: {type(docs[0]).__name__})")
for doc in docs:
    print(f"- {doc.metadata['source']}  글자 수={len(doc.page_content)}")
print(f"첫 문서 metadata: {docs[0].metadata}")

print()
print("=== 2. RecursiveCharacterTextSplitter로 분할 ===")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True
)
chunks = splitter.split_documents(docs)
print(f"chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}")
print(f"문서 {len(docs)}개 -> 청크 {len(chunks)}개")
for i, c in enumerate(chunks):
    name = Path(c.metadata["source"]).name
    print(
        f"[{i:2d}] {name} start_index={c.metadata['start_index']} "
        f"길이={len(c.page_content)} | {c.page_content[:30]!r}"
    )
counts: dict[str, int] = {}
for c in chunks:
    name = Path(c.metadata["source"]).name
    counts[name] = counts.get(name, 0) + 1
for name, n in counts.items():
    print(f"{name}: 청크 {n}개")

print()
print("=== 3. 청크 하나와 겹침 확인 ===")
first_source = docs[0].metadata["source"]
first_chunks = [c for c in chunks if c.metadata["source"] == first_source]
a, b = first_chunks[0], first_chunks[1]
print("--- 청크 0 전체 ---")
print(a.page_content)
print("--- 청크 1 전체 ---")
print(b.page_content)
end_a = a.metadata["start_index"] + len(a.page_content)
start_b = b.metadata["start_index"]
print(f"청크 0 끝 위치: {end_a}, 청크 1 시작 위치: {start_b}")
print(f"겹친 글자 수: {max(0, end_a - start_b)}")
