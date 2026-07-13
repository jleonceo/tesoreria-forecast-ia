# -*- coding: utf-8 -*-
"""
probar_todo.py — Genera los datos sinteticos y ejecuta las tres demos de una vez.

Sin dependencias: solo Python estandar (>=3.8). Sin base de datos, sin red, sin IA.

Uso:  python probar_todo.py
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).parent
PY = sys.executable


def paso(titulo, *args):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)
    r = subprocess.run([PY, *[str(a) for a in args]], cwd=str(RAIZ))
    return r.returncode


def main():
    fallos = 0
    paso("1/4 · Generar la serie de caja sintetica", RAIZ / "datos_ejemplo" / "generar_serie.py")
    fallos += paso("2/4 · Forecast de caja (bate al naif, backtesting)", RAIZ / "forecast" / "demo.py")
    fallos += paso("3/4 · Ratios de salud financiera", RAIZ / "ratios" / "demo.py")
    fallos += paso("4/4 · Aging de cobros y pagos", RAIZ / "aging" / "demo.py")
    print("\n" + "=" * 70)
    print("TODO VERDE" if fallos == 0 else f"HAY {fallos} DEMO(S) EN ROJO")
    print("=" * 70)
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
