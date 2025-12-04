# Asistente RAG – Documentación técnica (TFG)

Asistente conversacional basado en **RAG** (Retrieval-Augmented Generation) para consultar documentación técnica/ académica en PDF.  
Incluye: ingesta, indexado **versionado** con Chroma, recuperación (similarity o **MMR**), LLM de OpenAI y **UI en Streamlit** con subida de PDFs.

## Características

- Ingesta de PDFs y **troceado** configurable.
- **Indexado versionado** en `data/index/index_YYYYMMDD_hhmmss`.
- Recuperación por similitud y **MMR** (diversidad de fragmentos).
- Respuestas **solo** con contexto del índice + **citas** (archivo/página).
- UI con subida de PDFs, sliders de `k` y **temperatura**, reconstrucción de índice.
- Scripts de evaluación: **preguntas en CSV**, resultados y **métricas**.

---

## Arquitectura

PDFs -> Ingesta + Split -> Embeddings -> Chroma (persistente)
|
Retrieval (MMR/Sim)
|
Prompt + LLM (gpt-4.1-mini)
|
Respuesta + Fuentes (UI)

---

## Requisitos

- Python 3.10+ (probado en Windows 10/11)
- Cuenta de **OpenAI** con API Key activa y crédito
- Windows/macOS/Linux

---

## Estructura

app/ # config, ingest, index, rag
ui/ # app_streamlit.py (Streamlit)
eval/ # preguntas.csv, run_eval.py, metricas.py
data/
raw/ # PDFs (no se suben al repo)
processed/ # (preview opcional)
index/ # índices versionados (no se suben)
scripts/ # run_ui.cmd, reindex.cmd, etc.

---

## Instalación

    ### Opción A: instalación normal (recomendada)
    pip install -r requirements.txt

    ### Opción B: instalación congelada (reproducible 1:1)
    pip install -r requirements_lock.txt

```bash
# 1) Crear y activar entorno
python -m venv .venv
.\.venv\Scripts\activate         # Windows
# source .venv/bin/activate      # macOS/Linux

# 2) Instalar dependencias
pip install -r requirements.txt

# 3) Crear .env a partir de la plantilla
copy .env.example .env           # Windows
# cp .env.example .env           # macOS/Linux

# 4) Editar .env y pegar tu OPENAI_API_KEY

---

Contenido recomendado de .env:
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXX
DEFAULT_EMBED_MODEL=text-embedding-3-small
DEFAULT_CHAT_MODEL=gpt-4.1-mini
CHUNK_SIZE=1200
CHUNK_OVERLAP=200

---

Indexado del corpus
# Coloca tus PDFs en data/raw/.
# Construir índice (crea data/index/index_YYYYMMDD_hhmmss)
python -m app.index

## UI (Streamlit)
Sube PDFs desde la propia UI si quieres.
Ajusta k (chunks) y temperatura.
Botón Reconstruir índice en la barra lateral.

# (opcional) Previsualizar chunks generados
python -m app.ingest
# Lanzar la UI
python -m streamlit run ui/app_streamlit.py

---

En la UI puedes:

Subir PDFs (se guardan en data/raw) → reindexa automáticamente.
Ajustar k (nº de chunks), temperatura y MMR (diversificación).
Ver fuentes por respuesta (archivo y página).
Reconstruir índice manualmente desde la barra lateral.

## Evaluación

Edita eval/preguntas.csv (id,pregunta).
Ejecuta:
python eval\run_eval.py
Genera eval/resultados_YYYYMMDD_HHMMSS.csv con:
respuesta, tiempo_ms, fuentes_json, indice…
Marca a mano correcta(0/1) con 1, 0.5 o 0.

Métricas:
python eval\metricas.py
Muestra acierto (exactas y equivalentes) y tiempo medio. Detecta el último CSV automáticamente.

---

Scripts útiles (carpeta scripts/)

setup_venv.cmd – crea venv e instala requirements.
reindex.cmd – reconstruye índice.
run_ui.cmd – arranca la UI.
ingest_preview.cmd – genera chunks_preview.txt.
open_folders.cmd – abre data/raw e index en Explorer.

---

Parámetros importantes (por defecto)

CHUNK_SIZE=1200, CHUNK_OVERLAP=200 (ver app/ingest.py)
Embeddings: text-embedding-3-small
LLM: gpt-4.1-mini, temperature=0.1 (ver app/rag.py)
Retrieval: similitud o MMR (activable en UI y run_eval.py)

---

Variables (.env)

OPENAI_API_KEY (obligatoria)
DEFAULT_EMBED_MODEL (text-embedding-3-small por defecto)
DEFAULT_CHAT_MODEL (gpt-4.1-mini por defecto)
CHUNK_SIZE / CHUNK_OVERLAP (por defecto 1200 / 200)

---

Métricas y validación (guía breve)

Prepara 8–10 preguntas reales sobre tus PDFs.
Registra para cada una: Correcta / Parcial / Incorrecta, tiempo, y fuentes.
Calcula: % acierto, tiempo medio y efecto de parámetros (k, MMR, temperatura).
Punto de partida recomendado: k=4, MMR activado, temperatura=0.1.

---

Problemas frecuentes

ModuleNotFoundError: activa el venv (.\.venv\Scripts\activate) y reinstala pip install -r requirements.txt.
429 / cuota excedida → revisa el billing del proyecto en OpenAI.
WinError 32 (archivo en uso) al reindexar → cierra la app Streamlit y vuelve a ejecutar python -m app.index.
No aparecen PDFs nuevos → verifica que están en data/raw y pulsa Reconstruir índice.
Texto con caracteres raros (Ã, Â, …) → guarda archivos .py en UTF-8.
streamlit no se reconoce → activa el venv y usa python -m streamlit run ui/app_streamlit.py.
Índice bloqueado en Windows: cierra procesos que usen data/index/ y vuelve a ejecutar.
Mojibake/acentos: usa UTF-8 (guardado de archivos y consola).

---

Privacidad

Los PDFs no se suben a la nube; se procesan localmente.
Se envían a OpenAI: texto de chunks + consulta para embeddings/LLM.

```

## Capturas

### Pantalla principal

![UI principal](docs/ui_home.png)


### Subida e indexado de PDFs

![Subida e indexado](docs/ui_upload.png)

### Respuesta con citas a página

![Respuesta con citas](docs/ui_answer.png)
