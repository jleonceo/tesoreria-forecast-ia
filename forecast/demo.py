# -*- coding: utf-8 -*-
"""
demo.py — Ejecuta el forecast sobre la serie sintetica y demuestra, con
backtesting rolling-origin, que BATE al naif-media (el metodo naif de "media del
mismo mes de otros anyos", que es lo que hacia la vista naif que este motor
sustituye).

Uso:  python forecast/demo.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import modelo  # noqa: E402

MES_INICIO = 1  # la serie sintetica arranca en enero


def cargar_serie():
    ruta = Path(__file__).parent.parent / "datos_ejemplo" / "serie_caja_sintetica.csv"
    if not ruta.exists():
        sys.exit("Falta la serie. Ejecuta antes: python datos_ejemplo/generar_serie.py")
    y = []
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            y.append(float(fila["neto"]))
    return y


def main():
    y = cargar_serie()
    print(f"Serie sintetica: {len(y)} meses.\n")
    print("Backtesting rolling-origin (entrenar con el pasado, prever, comparar):\n")
    ok = True
    for h in (1, 3):
        r = modelo.backtest_rolling(y, MES_INICIO, horizonte=h)
        bate = r["bate_naif"]
        ok = ok and bool(bate)
        print(f"  h={h}  MASE modelo={r['mase_modelo']}  naif={r['mase_naif']}  "
              f"bate_naif={bate}  (origenes={r['n_origenes']})")
    print()
    diag = modelo.diagnostico_reciente(y, MES_INICIO)
    print(f"  Honestidad reciente: el modelo gana {diag['modelo_gana_en']}/{diag['k']} "
          f"de los ultimos origenes (alerta_degradacion={diag['alerta_degradacion']})")
    print()
    print("VEREDICTO:", "OK (el modelo bate al naif en h=1 y h=3)" if ok
          else "REVISAR (el modelo no bate al naif en algun horizonte)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
