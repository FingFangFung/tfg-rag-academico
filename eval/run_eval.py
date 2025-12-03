import csv, time, json
from pathlib import Path
from datetime import datetime
import sys, os

# Añadir el parent al sys.path para importar app.*
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.rag import ask_question, format_answer  # pipeline RAG
from app.config import check_config
from app.index import latest_index_dir  # para anotar qué índice se ha usado

# Parámetros de prueba (ajústalos si quieres)
K = 4
TEMP = 0.1
USE_MMR = True

EVAL_DIR = Path("eval")
EVAL_DIR.mkdir(exist_ok=True)

# Salida con timestamp para no sobrescribir
OUT_CSV = EVAL_DIR / f"resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
IN_CSV = EVAL_DIR / "preguntas.csv"


def main():
    check_config()

    # Determinar índice activo (para registrar en CSV)
    idx_path = latest_index_dir()
    idx_name = idx_path.name if idx_path else "SIN_INDICE"

    # Cargar preguntas
    preguntas = []
    with IN_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            preguntas.append({"id": row["id"], "pregunta": row["pregunta"]})

    rows_out = []
    t_total = 0.0

    for item in preguntas:
        qid = item["id"]
        q = item["pregunta"].strip()
        print(f"\n[TEST] {qid}: {q}")

        t0 = time.perf_counter()
        result = ask_question(q, k=K, temperature=TEMP, use_mmr=USE_MMR)
        dt = (time.perf_counter() - t0) * 1000.0  # ms
        t_total += dt

        ans = result.get("answer", "").strip()
        ctx = result.get("context", [])

        # Serializar fuentes de forma compacta (archivo + página)
        fuentes = []
        for i, d in enumerate(ctx, start=1):
            meta = d.metadata or {}
            source = (meta.get("source") or "").replace("\\", "/").split("/")[-1]
            page_display = meta.get("page_display")
            if page_display is None:
                p = meta.get("page")
                page_display = p + 1 if isinstance(p, int) else "N/A"
            fuentes.append({"i": i, "archivo": source, "pagina": page_display})

        rows_out.append({
            "indice": idx_name,                      # <-- índice usado en esta corrida
            "id": qid,
            "pregunta": q,
            "tiempo_ms": f"{dt:.0f}",
            "respuesta": ans,
            "fuentes_json": json.dumps(fuentes, ensure_ascii=False),
            "correcta(0/1)": "",                     # <-- la marcas a mano (1 / 0 / 0.5)
            "comentario": ""
        })

        # Log amigable en consola
        print(format_answer({"answer": ans, "context": ctx}))
        print(f"[TIEMPO] {dt:.0f} ms")

    # Guardar CSV resultados (con índice y timestamp)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["indice","id","pregunta","tiempo_ms","respuesta","fuentes_json","correcta(0/1)","comentario"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows_out:
            w.writerow(r)

    # Resumen rápido
    print("\n[RESUMEN]")
    print(f"Índice:  {idx_name}")
    print(f"Preguntas: {len(rows_out)}")
    print(f"Tiempo medio: {t_total/len(rows_out):.0f} ms")
    print(f"Guardado: {OUT_CSV.resolve()}")


if __name__ == "__main__":
    main()
