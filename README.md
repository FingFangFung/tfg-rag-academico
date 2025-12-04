# Asistente RAG – Documentación técnica (TFG)

Asistente conversacional basado en **RAG (Retrieval-Augmented Generation)** para consultar documentación técnica/académica en **PDF**, con:

- Ingesta y **troceado** configurable.
- **Indexado versionado** (cada reconstrucción crea `data/index/index_YYYYMMDD_HHMMSS`).
- Recuperación por **similitud** o **MMR** (diversidad de fragmentos).
- Respuestas **limitadas al corpus** con **citas** (archivo y página).
- **UI en Streamlit** con subida de PDFs y control de parámetros.
- **Evaluación reproducible** (CSV de preguntas + métricas).

---

## Características

- Ingesta de PDFs y split configurable (`CHUNK_SIZE`, `CHUNK_OVERLAP`).
- Embeddings con **OpenAI** y almacenamiento en **Chroma** persistente.
- Prompt “**solo con contexto**” + listado de **fuentes** (archivo/página).
- UI: subida de PDFs, sliders de **k** y **temperatura**, botón **Reconstruir índice**.
- Scripts de evaluación: `preguntas.csv` → resultados → métricas.

---

## Arquitectura

PDFs (data/raw)
│
├─ Ingesta + Split ────────────────┐
│ │
└─ Embeddings (OpenAI) → Chroma ←───┘ (índice versionado)
│
Recuperación (Sim / MMR)
│
Prompt estructurado + LLM
│
Respuesta + Citas a página

---

## Requisitos

- **Python 3.10+** (Windows/macOS/Linux).
- Cuenta de **OpenAI** con **API key** y crédito activo.

---

## Estructura

app/ # config, ingest, index, rag
ui/ # app_streamlit.py (Streamlit)
eval/ # preguntas.csv, run_eval.py, metricas.py
data/
raw/ # PDFs (no se suben)
processed/# preview opcional
index/ # índices versionados (no se suben)
scripts/ # run_ui.cmd, reindex.cmd, etc.
.env.example
.gitignore
requirements.txt
requirements_lock.txt
LICENSE
README.md

---

## Instalación

### Opción A (normal, recomendada)

```bat
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   & rem añade tu OPENAI_API_KEY

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements_lock.txt
copy .env.example .env   & rem añade tu OPENAI_API_KEY

```

## Uso

1. Indexar (con PDFs en data/raw/)
   python -m app.index

Crea data/index/index_YYYYMMDD_HHMMSS.

2. Lanzar la UI
   python -m streamlit run ui/app_streamlit.py

Sube PDFs desde la propia UI (se guardan en data/raw/).

Ajusta k y temperatura; activa MMR si quieres más diversidad.

Usa Reconstruir índice tras subir/añadir PDFs.

## Evaluación

Edita eval/preguntas.csv (id,pregunta).

Ejecuta:

python eval\run_eval.py

→ genera eval/resultados_YYYYMMDD_HHMMSS.csv con respuesta, tiempo y fuentes. 3) Métricas:

python eval\metricas.py

→ muestra % de acierto (exacto/parcial) y tiempo medio (detecta el último CSV).

## Configuración (.env)

OPENAI_API_KEY=sk-proj-XXXXXXXXXXXX
DEFAULT_EMBED_MODEL=text-embedding-3-small
DEFAULT_CHAT_MODEL=gpt-4.1-mini
CHUNK_SIZE=1200
CHUNK_OVERLAP=200

---

## Capturas

![UI principal](docs/ui_home.png)
![Respuesta con citas](docs/ui_answer.png)
![Subida e indexado](docs/ui_upload.png)

---

## Buenas prácticas

Empezar con k=4, MMR activado, temperature=0.1.

Medir: tiempo medio, % preguntas resueltas y calidad de citas.

Ajustar chunking según el tipo de documento (tablas, guías largas, etc.).

---

## Solución de problemas

ModuleNotFoundError → activa el venv y reinstala:
.\.venv\Scripts\activate
pip install -r requirements.txt
429 / quota exceeded → revisa Billing en OpenAI.

WinError 32 al reindexar → cierra la UI (libera data/index/) y vuelve a ejecutar python -m app.index.
PDFs no aparecen → verifica que están en data/raw/ y pulsa “Reconstruir índice”.
Texto con caracteres raros → guarda los .py en UTF-8.
streamlit no se reconoce → ejecuta con:
python -m streamlit run ui/app_streamlit.py

---

## Licencia

Este proyecto se distribuye bajo licencia MIT. Ver LICENSE

---

## Créditos

Autor: Cristian (FingFangFung)
Stack: Python, LangChain, OpenAI, ChromaDB, Streamlit.
