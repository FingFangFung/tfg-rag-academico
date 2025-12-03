from __future__ import annotations

from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from openai import RateLimitError, AuthenticationError, APIError

from .config import OPENAI_API_KEY, DEFAULT_CHAT_MODEL, check_config
from .index import load_vectorstore


# -------------------------
# LLM
# -------------------------
def get_llm(temperature: float = 0.1, model: Optional[str] = None) -> ChatOpenAI:
    check_config()
    m = model or DEFAULT_CHAT_MODEL
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        raise RuntimeError("OPENAI_API_KEY no esta configurada. Revisa .env.")
    return ChatOpenAI(api_key=OPENAI_API_KEY, model=m, temperature=temperature)


# -------------------------
# Retrieval (similarity o MMR)
# -------------------------
def retrieve_documents(question: str, k: int = 4, use_mmr: bool = False) -> List[Document]:
    vs = load_vectorstore()
    if use_mmr:
        return vs.max_marginal_relevance_search(
            question, k=k, fetch_k=max(8, k * 2), lambda_mult=0.5
        )
    return vs.similarity_search(question, k=k)


# -------------------------
# Prompt
# -------------------------
def build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Eres un asistente especializado en la documentacion proporcionada. "
                    "Responde UNICAMENTE con la informacion del contexto. "
                    "Si no hay informacion suficiente en el contexto, indica que no dispones de datos. "
                    "Incluye referencias a las fuentes con nombre de archivo y pagina cuando sea posible."
                ),
            ),
            ("human", "Contexto:\n{context}\n\nPregunta:\n{input}"),
        ]
    )


# -------------------------
# Pipeline RAG
# -------------------------
def ask_question(
    question: str,
    *,
    k: int = 4,
    temperature: float = 0.1,
    model: Optional[str] = None,
    use_mmr: bool = False,
) -> Dict[str, Any]:
    try:
        docs = retrieve_documents(question, k=k, use_mmr=use_mmr)
        context_text = "\n\n".join(d.page_content for d in docs)

        chain = build_prompt() | get_llm(temperature=temperature, model=model)
        response = chain.invoke({"context": context_text, "input": question})
        answer_text = response.content if hasattr(response, "content") else str(response)

        return {"answer": answer_text, "context": docs}

    except RateLimitError:
        return {
            "answer": (
                "No ha sido posible completar la consulta por limite/cuota de API (429). "
                "Revisa el billing del proyecto en OpenAI."
            ),
            "context": [],
        }
    except AuthenticationError:
        return {
            "answer": "Error de autenticacion con la API. Revisa OPENAI_API_KEY en .env.",
            "context": [],
        }
    except APIError as e:
        return {
            "answer": f"Error de API de OpenAI: {e}",
            "context": [],
        }
    except Exception as e:
        return {"answer": f"Error inesperado en RAG: {e}", "context": []}


# -------------------------
# Formateo salida consola
# -------------------------
def format_answer(result: Dict[str, Any]) -> str:
    answer = result.get("answer", "")
    context_docs: List[Document] = result.get("context", [])
    lines: List[str] = []
    lines.append("=== RESPUESTA ===")
    lines.append(answer.strip())
    lines.append("")
    lines.append("=== FUENTES ===")
    if not context_docs:
        lines.append("No se han encontrado documentos de contexto.")
    else:
        for i, doc in enumerate(context_docs, start=1):
            meta = doc.metadata or {}
            source = meta.get("source", "desconocido")
            fname = source.replace("\\", "/").split("/")[-1]
            page_display = meta.get("page_display")
            if page_display is None:
                page = meta.get("page", "N/A")
                page_display = page + 1 if isinstance(page, int) else "N/A"
            lines.append(f"[{i}] {fname} (pag. {page_display})")
    return "\n".join(lines)


def run_example() -> None:
    pregunta = "Explica brevemente de que trata esta documentacion."
    print(f"[RAG] Lanzando pregunta de prueba:\n{pregunta}\n")
    result = ask_question(pregunta, k=4, temperature=0.1, use_mmr=True)
    print(format_answer(result))


if __name__ == "__main__":
    run_example()
