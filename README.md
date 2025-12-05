# Asistente RAG – Documentación técnica (TFG)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2.x-informational)](https://python.langchain.com/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-Chroma-green)](https://www.trychroma.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Asistente conversacional basado en **RAG** (Retrieval-Augmented Generation) para consultar documentación técnica/académica en **PDF**.  
Incluye ingesta, indexado **versionado** con Chroma, recuperación por similitud o **MMR**, LLM de OpenAI y **UI en Streamlit** con subida de PDFs.

## Tabla de contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Quickstart](#quickstart)
- [Instalación](#instalación)
- [Uso](#uso)
- [Evaluación](#evaluación)
- [Configuración (.env)](#configuración-env)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Privacidad](#privacidad)
- [Buenas prácticas](#buenas-prácticas)
- [Solución de problemas](#solución-de-problemas)
- [Capturas](#capturas)
- [Roadmap](#roadmap)
- [Licencia](#licencia)
- [Créditos](#créditos)

---

## Características

- Ingesta de PDFs y split configurable (`CHUNK_SIZE`, `CHUNK_OVERLAP`).
- Embeddings con **OpenAI** y almacenamiento en **Chroma** persistente.
- Prompt “**solo con contexto**” + listado de **fuentes** (archivo/página).
- UI: subida de PDFs, sliders de **k** y **temperatura**, botón **Reconstruir índice**.
- Scripts de evaluación: `preguntas.csv` → resultados → métricas.

---

## Arquitectura

  raw["PDFs<br/>(data/raw)"] --> ingest["Ingesta + Split"]
  ingest --> embed["Embeddings (OpenAI)"]
  embed --> chroma["Chroma<br/>(índice versionado)"]

  user["Consulta del usuario"] --> retrieve["Recuperación<br/>(Sim / MMR)"]
  chroma <-- "vectores" --> retrieve
  retrieve --> prompt["Prompt estructurado"]
  prompt --> llm["LLM<br/>(gpt-4.1-mini)"]
  llm --> answer["Respuesta + Citas a página"]
---

## Quickstart

````bash
# 1) Entorno y deps
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # (Windows)  # macOS/Linux: cp .env.example .env
# 👉 Edita .env y pega tu OPENAI_API_KEY

# 2) Coloca PDFs en data/raw/ y construye índice
python -m app.index

# 3) Lanza la UI
python -m streamlit run ui/app_streamlit.py

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

````

## Uso

1. Indexar (con PDFs en data/raw/)
  python -m app.index
   Crea data/index/index_YYYYMMDD_HHMMSS.

2. Lanzar la UI
   python -m streamlit run ui/app_streamlit.py

Sube PDFs desde la propia UI (se guardan en data/raw/).
Ajusta k y temperatura; activa MMR si quieres más diversidad.
Pulsa Reconstruir índice tras subir/añadir PDFs.

## Evaluación

Edita eval/preguntas.csv (id,pregunta).

1. Ejecuta el runner:
   python eval\run_eval.py
      Genera eval/resultados_YYYYMMDD_HHMMSS.csv con: respuesta, tiempo_ms, fuentes_json, índice…
2. Calcula métricas:
   python eval\metricas.py
      Muestra % de acierto (exacto/parcial) y tiempo medio (detecta el último CSV automáticamente). 

## Configuración (.env)

OPENAI_API_KEY=sk-proj-XXXXXXXXXXXX
DEFAULT_EMBED_MODEL=text-embedding-3-small
DEFAULT_CHAT_MODEL=gpt-4.1-mini
CHUNK_SIZE=1200
CHUNK_OVERLAP=200

## Limitaciones conocidas

````markdown
## Limitaciones conocidas

- **PDFs con tablas complejas / escaneados (OCR)**: el extractor de texto puede perder estructura. (No hay OCR integrado).
- **Imágenes**: solo se indexa texto; figuras y gráficos no se “leen”.
- **Dependencia de OpenAI**: requiere cuota activa para embeddings/LLM.
- **Bloqueo de archivos en Windows**: si Chroma está abierto por la UI, puede fallar el reindexado. Cierra la UI o usa el botón “Reconstruir índice”.
````
---

## Buenas prácticas

Empezar con k=4, MMR activado, temperature=0.1.

Medir: tiempo medio, % preguntas resueltas y calidad de citas.

Ajustar chunking según el tipo de documento (tablas, guías largas, etc.).

---

## Privacidad

- Los PDFs se procesan **localmente**; solo se envían a OpenAI los **chunks de texto** y la **consulta** para embeddings/LLM.
- Mantén `data/raw/` y `data/index/` **fuera** del control de versiones (están en `.gitignore`).

---

## Solución de problemas

- ModuleNotFoundError / streamlit no se reconoce
   Activa el venv e instala dependencias:
      .\.venv\Scripts\activate
      pip install -r requirements.txt

- 429 / cuota excedida
   Revisa el Billing de OpenAI y el modelo configurado.

- WinError 32 al reindexar (archivo en uso)
   Cierra la app de Streamlit (libera data/index/) y vuelve a ejecutar:
      python -m app.index
   (También puedes usar el botón Reconstruir índice en la barra lateral.)

- No aparecen PDFs nuevos
   Verifica que están en data/raw/ y pulsa Reconstruir índice en la UI.
  
-Caracteres raros (mojibake)
   Guarda los .py en UTF-8 y asegúrate de que la consola usa UTF-8.

- streamlit no se reconoce en Windows
   Lánzalo así (usa el python -m):
     python -m streamlit run ui/app_streamlit.py

---

## Capturas

![UI principal](docs/ui_home.png)
![Respuesta con citas](docs/ui_answer.png)
![Subida e indexado](docs/ui_upload.png)

---

## Licencia

Este proyecto se distribuye bajo licencia MIT. Ver LICENSE

---

## Créditos

Autor: Cristian (FingFangFung)
Stack: Python, LangChain, OpenAI, ChromaDB, Streamlit.

