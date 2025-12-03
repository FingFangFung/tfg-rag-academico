import sys, os, gc
from pathlib import Path
from app.config import RAW_DIR

# AÃ‘ADE el parent al sys.path ANTES de importar app.*
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

# Import robusto: si falla INDEX_DIR, usamos fallback calculado
try:
    from app.rag import retrieve_documents, get_llm, build_prompt, format_answer
    from app.index import build_index
    from app.config import check_config, OPENAI_API_KEY, INDEX_DIR
    CFG_INDEX_DIR = INDEX_DIR  # alias para usarlo en el resto del script
except Exception:
    BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__))).resolve()
    CFG_INDEX_DIR = BASE_DIR / "data" / "index"
    from app.rag import retrieve_documents, get_llm, build_prompt, format_answer
    from app.index import build_index
    from app.config import check_config, OPENAI_API_KEY

# --- Page config ---
st.set_page_config(page_title="Asistente RAG (TFG)", page_icon="ðŸ§ ", layout="wide")
st.title("ðŸ§  Asistente RAG â€“ DocumentaciÃ³n tÃ©cnica")
st.subheader("AÃ±adir documentos")
uploaded = st.file_uploader("Sube PDFs para indexar", type=["pdf"], accept_multiple_files=True)
if uploaded:
    # Guardar en data/raw
    from app.config import RAW_DIR
    saved = []
    for up in uploaded:
        out = (RAW_DIR / up.name)
        with open(out, "wb") as f:
            f.write(up.getbuffer())
        saved.append(out.name)
    st.success(f"Guardados: {', '.join(saved)}")
    # Indexar tras subir
    with st.spinner("Reconstruyendo Ã­ndice con los nuevos PDFs..."):
        build_index()
    st.success("Ãndice reconstruido.")

# --- Sidebar: estado y ajustes ---
with st.sidebar:
    st.header("Estado")
    try:
        check_config()
        if not OPENAI_API_KEY:
            st.error("OPENAI_API_KEY no encontrada. Revisa tu .env")

        # Chequeo del Ã­ndice SIN cargar Chroma (evita bloqueo en Windows)
        hay_indice = any(
            p.is_dir() and p.name.startswith("index_")
            for p in Path(CFG_INDEX_DIR).glob("*")
        )
        if hay_indice:
            st.success(f"Ãndice presente en:\n{CFG_INDEX_DIR}")
        else:
            st.warning("Ãndice no encontrado. ReconstrÃºyelo.")
    except Exception as e:
        st.error(f"Problema al verificar el entorno: {e}")

    if st.button("ðŸ“‚ Abrir carpeta RAW"):
        import subprocess
        subprocess.Popen(rf'explorer "{RAW_DIR}"')
    if st.button("ðŸ“‚ Abrir carpeta ÃNDICES"):
        import subprocess
        subprocess.Popen(rf'explorer "{CFG_INDEX_DIR}"')

    st.divider()
    st.header("Ajustes de consulta")
    k_chunks = st.slider("Chunks recuperados (k)", 1, 12, 4, 1)
    temp = st.slider("Temperatura", 0.0, 1.0, 0.1, 0.1)
    st.caption("A mayor temperatura, respuestas mÃ¡s creativas; a menor, mÃ¡s precisas.")

    st.divider()
    if st.button("ðŸ”„ Reconstruir Ã­ndice"):
        with st.spinner("Indexando documentos..."):
            try:
                # Liberar posibles referencias antes de reconstruir
                for k in list(st.session_state.keys()):
                    if k.startswith("vs") or k.startswith("vectorstore"):
                        st.session_state.pop(k, None)
                gc.collect()
                build_index()
                st.success("Ãndice reconstruido.")
            except Exception as e:
                st.error(f"Fallo al reconstruir el Ã­ndice: {e}")

st.caption("Escribe una pregunta. El asistente responde solo con lo indexado y lista las fuentes.")

# Historial simple en sesiÃ³n
if "history" not in st.session_state:
    st.session_state.history = []

# Input principal
col1, col2 = st.columns([4, 1])
with col1:
    question = st.text_input("Pregunta", placeholder="Ej.: Resume los puntos clave del documento")
with col2:
    ask = st.button("Preguntar", type="primary", use_container_width=True)

# LÃ³gica
if ask:
    if not question.strip():
        st.warning("Escribe una pregunta primero.")
    else:
        with st.spinner("Consultando el Ã­ndice y generando respuesta..."):
            try:
                # 1) recuperar docs segÃºn k
                docs = retrieve_documents(question.strip(), k=k_chunks, use_mmr=use_mmr)
                # 2) contexto con esos docs
                context_text = "\n\n".join(d.page_content for d in docs)
                # 3) LLM con temperatura elegida
                llm = get_llm(temperature=temp)
                chain = build_prompt() | llm
                response = chain.invoke({"context": context_text, "input": question.strip()})
                answer_text = response.content if hasattr(response, "content") else str(response)

                formatted = format_answer({"answer": answer_text, "context": docs})
                st.code(formatted, language="markdown")
                st.session_state.history.append({"q": question.strip(), "a": formatted})
            except Exception as e:
                st.error(f"OcurriÃ³ un error al procesar la consulta: {e}")

st.divider()
st.subheader("Historial de la sesiÃ³n")
if not st.session_state.history:
    st.caption("Sin consultas todavÃ­a.")
else:
    for i, item in enumerate(reversed(st.session_state.history), start=1):
        with st.expander(f"Q{i}: {item['q'][:80]}"):
            st.code(item["a"], language="markdown")

with st.expander("Â¿CÃ³mo funciona RAG?"):
    st.markdown(
        (
            "**RAG (Retrieval-Augmented Generation)**  \n"
            "1) Se calcula un embedding de tu pregunta.  \n"
            "2) Se recuperan los *k* fragmentos mÃ¡s similares del Ã­ndice vectorial.  \n"
            "3) Se construye un prompt con esos fragmentos como contexto.  \n"
            "4) El LLM redacta la respuesta apoyÃ¡ndose en ese contexto y se listan las fuentes."
        )
    )


