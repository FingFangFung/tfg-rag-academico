import sys
import os
import gc
from pathlib import Path

# AÑADE el parent al sys.path ANTES de importar app.*
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

# Import robusto: si falla INDEX_DIR/RAW_DIR, usamos fallback calculado
try:
    from app.rag import retrieve_documents, get_llm, build_prompt, format_answer
    from app.index import build_index
    from app.config import check_config, OPENAI_API_KEY, INDEX_DIR, RAW_DIR

    CFG_INDEX_DIR = INDEX_DIR  # alias para usarlo en el resto del script
except Exception:
    BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__))).resolve()
    CFG_INDEX_DIR = BASE_DIR / "data" / "index"
    RAW_DIR = BASE_DIR / "data" / "raw"
    from app.rag import retrieve_documents, get_llm, build_prompt, format_answer
    from app.index import build_index
    from app.config import check_config, OPENAI_API_KEY

# --- Page config ---
st.set_page_config(
    page_title="Asistente RAG – Documentación técnica", page_icon="🧠", layout="wide"
)
st.title("🧠 Asistente RAG – Documentación técnica")

# --- Carga de documentos desde la UI ---
st.subheader("Añadir documentos")
uploaded = st.file_uploader(
    "Sube PDFs para indexar", type=["pdf"], accept_multiple_files=True
)
if uploaded:
    # Guardar en data/raw
    saved = []
    for up in uploaded:
        out = RAW_DIR / up.name
        with open(out, "wb") as f:
            f.write(up.getbuffer())
        saved.append(out.name)
    st.success(f"Guardados: {', '.join(saved)}")

    # Indexar tras subir
    with st.spinner("Reconstruyendo índice con los nuevos PDFs..."):
        build_index()
    st.success("Índice reconstruido.")

# --- Sidebar: estado y ajustes ---
with st.sidebar:
    st.header("Estado")
    try:
        check_config()
        if not OPENAI_API_KEY:
            st.error("OPENAI_API_KEY no encontrada. Revisa tu .env")

        # Chequeo del índice SIN cargar Chroma (evita bloqueo en Windows)
        hay_indice = any(
            p.is_dir() and p.name.startswith("index_")
            for p in Path(CFG_INDEX_DIR).glob("*")
        )
        if hay_indice:
            st.success(f"Índice presente en:\n{CFG_INDEX_DIR}")
        else:
            st.warning("Índice no encontrado. Reconstrúyelo.")
    except Exception as e:
        st.error(f"Problema al verificar el entorno: {e}")

    # Accesos rápidos a carpetas
    if st.button("📂 Abrir carpeta RAW"):
        import subprocess

        subprocess.Popen(rf'explorer "{RAW_DIR}"')
    if st.button("📂 Abrir carpeta ÍNDICES"):
        import subprocess

        subprocess.Popen(rf'explorer "{CFG_INDEX_DIR}"')

    st.divider()
    st.header("Ajustes de consulta")
    k_chunks = st.slider("Chunks recuperados (k)", 1, 12, 4, 1)
    temp = st.slider("Temperatura", 0.0, 1.0, 0.1, 0.1)
    use_mmr = st.checkbox("Diversificar resultados (MMR)", value=True)
    st.caption("A mayor temperatura, respuestas más creativas; a menor, más precisas.")

    st.divider()
    if st.button("🔄 Reconstruir índice"):
        with st.spinner("Indexando documentos..."):
            try:
                # Liberar posibles referencias antes de reconstruir
                for k in list(st.session_state.keys()):
                    if k.startswith("vs") or k.startswith("vectorstore"):
                        st.session_state.pop(k, None)
                gc.collect()
                build_index()
                st.success("Índice reconstruido.")
            except Exception as e:
                st.error(f"Fallo al reconstruir el índice: {e}")

st.caption(
    "Escribe una pregunta. El asistente responde solo con lo indexado y lista las fuentes."
)

# Historial simple en sesión
if "history" not in st.session_state:
    st.session_state.history = []

# Input principal (botón alineado abajo con el campo)
col1, col2 = st.columns([5, 1], vertical_alignment="bottom")

with col1:
    question = st.text_input(
        label="Pregunta",
        placeholder="Ej.: Resume los puntos clave del documento",
        label_visibility="collapsed",
    )

with col2:
    ask = st.button("Preguntar", type="primary", use_container_width=True)

# Lógica
if ask:
    if not question.strip():
        st.warning("Escribe una pregunta primero.")
    else:
        with st.spinner("Consultando el índice y generando respuesta..."):
            try:
                # 1) recuperar docs según k (y MMR si procede)
                docs = retrieve_documents(question.strip(), k=k_chunks, use_mmr=use_mmr)
                # 2) contexto con esos docs
                context_text = "\n\n".join(d.page_content for d in docs)
                # 3) LLM con temperatura elegida
                llm = get_llm(temperature=temp)
                chain = build_prompt() | llm
                response = chain.invoke(
                    {"context": context_text, "input": question.strip()}
                )
                answer_text = (
                    response.content if hasattr(response, "content") else str(response)
                )

                formatted = format_answer({"answer": answer_text, "context": docs})
                st.code(formatted, language="markdown")
                st.session_state.history.append({"q": question.strip(), "a": formatted})
            except Exception as e:
                st.error(f"Ocurrió un error al procesar la consulta: {e}")

st.divider()
st.subheader("Historial de la sesión")
if not st.session_state.history:
    st.caption("Sin consultas todavía.")
else:
    for i, item in enumerate(reversed(st.session_state.history), start=1):
        with st.expander(f"Q{i}: {item['q'][:80]}"):
            st.code(item["a"], language="markdown")

with st.expander("¿Cómo funciona RAG?"):
    st.markdown(
        (
            "**RAG (Retrieval-Augmented Generation)**  \n"
            "1) Se calcula un embedding de tu pregunta.  \n"
            "2) Se recuperan los *k* fragmentos más similares del índice vectorial.  \n"
            "3) Se construye un prompt con esos fragmentos como contexto.  \n"
            "4) El LLM redacta la respuesta apoyándose en ese contexto y se listan las fuentes."
        )
    )
