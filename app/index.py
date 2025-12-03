from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma  # si migras: from langchain_chroma import Chroma

from .config import INDEX_DIR, OPENAI_API_KEY, DEFAULT_EMBED_MODEL, check_config
from .ingest import load_pdf_documents, split_documents


# -------------------------
# Helpers de gestión de índices versionados
# -------------------------
def _new_index_dir(base: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base / f"index_{ts}"


def list_indices(base: Path = INDEX_DIR) -> List[Path]:
    """Devuelve todas las subcarpetas de índice (index_YYYYMMDD_hhmmss) ordenadas por fecha ascendente."""
    if not base.exists():
        return []
    subs = [p for p in base.iterdir() if p.is_dir() and p.name.startswith("index_")]
    return sorted(subs, key=lambda p: p.name)


def latest_index_dir(base: Path = INDEX_DIR) -> Optional[Path]:
    """Devuelve la carpeta del índice más reciente, o None si no hay."""
    indices = list_indices(base)
    return indices[-1] if indices else None


# -------------------------
# Build / Load
# -------------------------
def build_index(
    persist_dir: Optional[Path] = None,
    embed_model: str = DEFAULT_EMBED_MODEL,
) -> Path:
    """
    Crea un NUEVO índice en una carpeta versionada (no borra el anterior).
    Devuelve la ruta del nuevo índice.
    """
    check_config()

    base_dir = INDEX_DIR
    base_dir.mkdir(parents=True, exist_ok=True)
    target_dir = _new_index_dir(base_dir)

    print("[INDEX] Cargando documentos PDF...")
    documents = load_pdf_documents()
    if not documents:
        print("[INDEX] No se han encontrado documentos para indexar.")
        return target_dir

    print("[INDEX] Dividiendo documentos en chunks...")
    chunks = split_documents(documents)
    if not chunks:
        print("[INDEX] No se han generado chunks. Abortando indexado.")
        return target_dir

    if OPENAI_API_KEY is None or OPENAI_API_KEY.strip() == "":
        raise RuntimeError("OPENAI_API_KEY no está configurada. Revisa el archivo .env.")

    print(f"[INDEX] Creando embeddings '{embed_model}' para {len(chunks)} chunks...")
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model=embed_model)

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INDEX] Construyendo vectorstore Chroma en {target_dir} ...")

    # En chromadb 0.5+ la persistencia es automática al usar persist_directory
    _ = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(target_dir),
    )

    print("[INDEX] Indexado completado:", target_dir)
    return target_dir


def load_vectorstore(
    persist_dir: Optional[Path] = None,
    embed_model: str = DEFAULT_EMBED_MODEL,
) -> Chroma:
    """
    Carga el índice MÁS RECIENTE de INDEX_DIR si no se especifica persist_dir.
    """
    check_config()

    if persist_dir is None:
        persist_dir = latest_index_dir(INDEX_DIR)
        if persist_dir is None:
            raise RuntimeError("No hay ningún índice disponible. Reconstrúyelo.")

    if OPENAI_API_KEY is None or OPENAI_API_KEY.strip() == "":
        raise RuntimeError("OPENAI_API_KEY no está configurada. Revisa el archivo .env.")

    print(f"[INDEX] Cargando vectorstore Chroma desde {persist_dir} ...")
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model=embed_model)
    vs = Chroma(persist_directory=str(persist_dir), embedding_function=embeddings)
    print("[INDEX] Vectorstore cargado correctamente.")
    return vs


# -------------------------
# Utilidades de inspección
# -------------------------
def count_docs(persist_dir: Optional[Path] = None) -> Tuple[Path, int]:
    """
    Devuelve (ruta_indice, numero_docs) del índice a inspeccionar (último por defecto).
    """
    idx = persist_dir or latest_index_dir(INDEX_DIR)
    if idx is None:
        return (INDEX_DIR, 0)
    vs = load_vectorstore(idx)
    try:
        n = vs._collection.count()  # API interna de Chroma wrapper
    except Exception:
        n = 0
    return (idx, n)


# -------------------------
# CLI
# -------------------------
def run_build_index() -> None:
    build_index()


if __name__ == "__main__":
    run_build_index()
