import csv
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

EVAL_DIR = Path("eval")

def _to_float(x: str) -> float:
    if x is None:
        return 0.0
    s = str(x).strip().replace(",", ".")
    if not s:
        return 0.0
    try:
        return float(s)
    except:
        return 0.0

def _latest_resultados_csv() -> Optional[Path]:
    """Busca el resultados_YYYYMMDD_HHMMSS.csv más reciente. Fallback: resultados.csv."""
    if not EVAL_DIR.exists():
        return None
    # Buscar resultados con timestamp
    ts_files = sorted(EVAL_DIR.glob("resultados_*.csv"))
    if ts_files:
        return ts_files[-1]
    # Fallback
    f = EVAL_DIR / "resultados.csv"
    return f if f.exists() else None

def _accumulate(row: Dict[str, str], acc: Dict[str, Any]) -> None:
    acc["total"] += 1
    c = _to_float(row.get("correcta(0/1)", "0"))
    if c >= 0.999:
        acc["ok"] += 1
    elif 0.49 <= c <= 0.51:
        acc["parcial"] += 1
    acc["ok_equiv"] += c
    acc["t_sum"] += _to_float(row.get("tiempo_ms", "0"))

def _make_acc() -> Dict[str, Any]:
    return {"total": 0, "ok": 0, "parcial": 0, "ok_equiv": 0.0, "t_sum": 0.0}

def _fmt(acc: Dict[str, Any]) -> Tuple[str, str, str]:
    total = acc["total"] or 0
    if total == 0:
        return ("0/0 (0.0%)", "0", "0 ms")
    ok = acc["ok"]
    parc = acc["parcial"]
    ok_equiv = acc["ok_equiv"]
    t_med = acc["t_sum"] / total if total else 0.0
    exactas = f"{ok}/{total} ({(ok/total*100):.1f}%)"
    parciales = str(parc)
    acc_equiv = f"{(ok_equiv/total*100):.1f}%"
    tiempo = f"{t_med:.0f} ms"
    return exactas, parciales, acc_equiv, tiempo

def main():
    csv_path = _latest_resultados_csv()
    if not csv_path:
        print("No se encontró ningún CSV de resultados en eval/. Ejecuta antes run_eval.py.")
        return

    print(f"Archivo: {csv_path}")

    global_acc = _make_acc()
    per_index: Dict[str, Dict[str, Any]] = {}

    with csv_path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        has_indice = "indice" in (r.fieldnames or [])
        for row in r:
            idx = row.get("indice", "SIN_INDICE") if has_indice else "SIN_INDICE"
            if idx not in per_index:
                per_index[idx] = _make_acc()
            _accumulate(row, global_acc)
            _accumulate(row, per_index[idx])

    # Global
    ex, pa, ae, tm = _fmt(global_acc)
    print("\n== GLOBAL ==")
    print(f"Preguntas: {global_acc['total']}")
    print(f"Acierto (exactas): {ex}")
    print(f"Parciales (0.5):   {pa}")
    print(f"Acierto equivalente (1=OK, 0.5=parcial): {ae}")
    print(f"Tiempo medio: {tm}")

    # Por índice
    if len(per_index) > 1 or ("SIN_INDICE" not in per_index or per_index["SIN_INDICE"]["total"] != global_acc["total"]):
        print("\n== POR ÍNDICE ==")
        for idx, acc in per_index.items():
            exi, pai, aei, tmi = _fmt(acc)
            print(f"- {idx}")
            print(f"  Preguntas: {acc['total']}")
            print(f"  Acierto (exactas): {exi}")
            print(f"  Parciales (0.5):   {pai}")
            print(f"  Acierto equivalente: {aei}")
            print(f"  Tiempo medio: {tmi}")

if __name__ == "__main__":
    main()
