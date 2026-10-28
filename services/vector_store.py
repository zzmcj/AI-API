from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter

embeddings = OpenAIEmbeddings(
    model="bge-m3",
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    check_embedding_ctx_length=False,
)
store = Milvus(
    embedding_function=embeddings,
    collection_name="pan_file_chunk",
    connection_args={"uri": "http://localhost:19530"},
    auto_id=True,
)


def save_chunks(file_id: int, text: str) -> None:
    if not text.strip():
        return
    if store.client.has_collection(store.collection_name):
        store.delete(expr=f"file_id == {file_id}")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    store.add_texts(chunks, metadatas=[{"file_id": file_id} for _ in chunks])