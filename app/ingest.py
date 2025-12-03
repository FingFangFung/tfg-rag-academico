from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .config import RAW_DIR, PROCESSED_DIR

# --- Parametros de split desde .env con defaults seguros ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))


def _normalize_doc_meta(doc: Document, pdf_path: Path) -> Document:
    """Asegura metadatos consistentes: source absoluto y page 0/1-based."""
    meta = dict(doc.metadata or {})
    meta["source"] = str(pdf_path.resolve())
    page0 = meta.get("page", meta.get("page_number"))
    try:
        page0 = int(page0) if page0 is not None else 0
    except Exception:
        page0 = 0
    meta["page"] = page0
    meta["page_display"] = page0 + 1
    return Document(page_content=doc.page_content, metadata=meta)


def _load_single_pdf(pdf_path: Path) -> List[Document]:
    """Carga un PDF por paginas, intentando PyMuPDF y cayendo a PyPDF."""
    print(f"[INGEST] Cargando PDF: {pdf_path.name}")
    try:
        loader = PyMuPDFLoader(str(pdf_path))
        docs = loader.load()
    except Exception:
        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()
    return [_normalize_doc_meta(d, pdf_path) for d in docs]


def load_pdf_documents(raw_dir: Path = RAW_DIR) -> List[Document]:
    """Recorre data/raw y carga todos los PDFs como Documents por pagina."""
    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[INGEST] No se han encontrado PDFs en {raw_dir}")
        return []

    print(f"[INGEST] Encontrados {len(pdf_files)} PDFs en {raw_dir}")
    all_docs: List[Document] = []
    for pdf in pdf_files:
        try:
            docs = _load_single_pdf(pdf)
            if not docs:
                print(f"[INGEST] Aviso: {pdf.name} no produjo texto (posible PDF escaneado).")
            all_docs.extend(docs)
        except Exception as e:
            print(f"[INGEST] Error leyendo {pdf.name}: {e}")
    print(f"[INGEST] Total de documentos (paginas) cargados: {len(all_docs)}")
    return all_docs


def split_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """Trocea los documentos en fragmentos del tamaño indicado."""
    if not documents:
        print("[INGEST] No hay documentos para trocear.")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )

    print(
        f"[INGEST] Iniciando split de documentos. "
        f"chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
    )
    chunks = splitter.split_documents(documents)

    # Hereda/asegura metadatos basicos en cada chunk
    for c in chunks:
        meta = dict(c.metadata or {})
        meta.setdefault("source", meta.get("source", "desconocido"))
        meta.setdefault("page", meta.get("page", 0))
        meta.setdefault("page_display", meta.get("page_display", meta["page"] + 1))
        c.metadata = meta

    print(f"[INGEST] Documentos troceados: {len(chunks)} chunks generados.")
    return chunks


def save_chunks_to_disk(
    chunks: List[Document],
    output_path: Path | None = None,
) -> None:
    """Guarda un preview legible de los chunks en data/processed/chunks_preview.txt."""
    if output_path is None:
        output_path = PROCESSED_DIR / "chunks_preview.txt"

    if not chunks:
        print("[INGEST] No hay chunks para guardar.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[INGEST] Guardando preview de chunks en: {output_path}")

    with output_path.open("w", encoding="utf-8") as f:
        for i, doc in enumerate(chunks, start=1):
            meta = doc.metadata or {}
            source = meta.get("source", "desconocido")
            page_disp = meta.get("page_display", meta.get("page", 0) + 1)
            f.write(f"=== CHUNK {i} ===\n")
            f.write(f"FILE: {source}\n")
            f.write(f"PAGE: {page_disp}\n")
            f.write(doc.page_content)
            f.write("\n\n")

    print("[INGEST] Guardado completado.")


def run_ingest() -> None:
    """1) carga PDFs, 2) trocea, 3) guarda preview."""
    docs = load_pdf_documents()
    chunks = split_documents(docs)
    save_chunks_to_disk(chunks)


if __name__ == "__main__":
    run_ingest()
