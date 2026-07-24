"""Utilidad compartida para construir o cargar el indice vectorial (Chroma) de un agente.

Cada agente de lectura llama a construir_o_cargar_vectorstore() con SU PROPIO documento y un
nombre de indice unico, generando asi una base de conocimiento embebida independiente por agente
(requisito: "cada agente debe tener su propia base de conocimiento embebida").
"""
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL, GOOGLE_API_KEY, VECTORSTORE_DIR


def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def construir_o_cargar_vectorstore(doc_path: str, nombre_indice: str) -> Chroma:
    """Devuelve el vector store (Chroma) del indice `nombre_indice`.

    Si ya existe en disco (vectorstores/<nombre_indice>/), lo carga tal cual (evita re-embeber
    y volver a gastar tokens de embeddings en cada arranque). Si no existe, lo crea: carga el
    .txt, lo trocea (chunking) y genera embeddings con Gemini para cada chunk.
    """
    persist_dir = str(Path(VECTORSTORE_DIR) / nombre_indice)
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)

    ya_existe = Path(persist_dir).exists() and any(Path(persist_dir).iterdir())
    if ya_existe:
        return Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name=nombre_indice,
        )

    loader = TextLoader(doc_path, encoding="utf-8")
    documentos = loader.load()
    for doc in documentos:
        doc.metadata["fuente"] = Path(doc_path).name

    chunks = _splitter().split_documents(documentos)

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name=nombre_indice,
    )
    print(f"  Indice '{nombre_indice}' creado con {len(chunks)} chunks a partir de {doc_path}")
    return vectordb
