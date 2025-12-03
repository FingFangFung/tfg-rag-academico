from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Dict, Any

from dotenv import load_dotenv


# --- Rutas base ---
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
INDEX_DIR: Path = DATA_DIR / "index"

# --- Carga de .env (desde la raiz del proyecto si existe) ---
DOTENV_PATH = BASE_DIR / ".env"
if DOTENV_PATH.exists():
    load_dotenv(dotenv_path=DOTENV_PATH, override=False)
else:
    # Permite que variables vengan del entorno del sistema si no hay archivo .env
    load_dotenv(override=False)

# --- Variables y defaults de modelos ---
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# Modelo de embeddings y chat por defecto (usados en index/rag)
DEFAULT_EMBED_MODEL = os.getenv("DEFAULT_EMBED_MODEL", "text-embedding-3-small")
DEFAULT_CHAT_MODEL = os.getenv("DEFAULT_CHAT_MODEL", "gpt-4.1-mini")


def _ensure_dirs(paths: Iterable[Path]) -> None:
    """Crea directorios si no existen (idempotente)."""
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def _require_env(name: str) -> str:
    """Lee variable de entorno y exige que exista y no sea vacia."""
    val = os.getenv(name)
    if val is None or val.strip() == "":
        raise RuntimeError(
            f"Falta variable de entorno {name}. "
            f"Crea un archivo .env en {BASE_DIR} con {name}=..."
        )
    return val


def check_config() -> Dict[str, Any]:
    """
    Validaciones basicas de configuracion:
      - Verifica OPENAI_API_KEY
      - Asegura carpetas de datos
      - Devuelve un resumen util de paths y modelos por defecto
    """
    key = _require_env("OPENAI_API_KEY")
    _ensure_dirs([DATA_DIR, RAW_DIR, PROCESSED_DIR, INDEX_DIR])

    return {
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "raw_dir": str(RAW_DIR),
        "processed_dir": str(PROCESSED_DIR),
        "index_dir": str(INDEX_DIR),
        "embed_model": DEFAULT_EMBED_MODEL,
        "chat_model": DEFAULT_CHAT_MODEL,
        "has_api_key": bool(key),
    }
