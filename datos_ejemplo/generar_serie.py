# -*- coding: utf-8 -*-
"""
generar_serie.py — Genera la serie mensual de netos de caja SINTETICA.

Datos 100% inventados, reproducibles (semilla fija). La serie tiene estructura
real (tendencia + estacionalidad + ruido moderado), que es justo lo que un
forecast por descomposicion sabe aprovechar y un naif-media no. El dato y su
"verdad" nacen del mismo sitio: no hay ningun dato real ni personal aqui.

Uso:  python generar_serie.py   (escribe serie_caja_sintetica.csv)
"""
import csv
import random
from pathlib import Path

SEMILLA = 20260713      # fija: la serie es la misma en cada ejecucion
N_MESES = 42
ANYO_INICIO, MES_INICIO = 2023, 1

NIVEL = 100_000.0       # caja neta base
TENDENCIA = 1_500.0     # crecimiento por mes
RUIDO_SIGMA = 4_000.0   # ruido gaussiano moderado (no ahoga la estructura)

# Estacionalidad por mes-calendario (1-12): un patron plausible de tesoreria de
# comercio (peor en verano y cierre, mejor en primavera y campana de otono).
ESTACIONAL = {1: -8000, 2: -5000, 3: 2000, 4: 4000, 5: 6000, 6: -3000,
              7: -9000, 8: -12000, 9: 5000, 10: 8000, 11: 10000, 12: -8000}


def generar():
    random.seed(SEMILLA)
    filas = []
    anyo, mes = ANYO_INICIO, MES_INICIO
    for i in range(N_MESES):
        cal = ((MES_INICIO - 1 + i) % 12) + 1
        neto = NIVEL + TENDENCIA * i + ESTACIONAL[cal] + random.gauss(0, RUIDO_SIGMA)
        filas.append((f"{anyo:04d}-{mes:02d}", round(neto, 2)))
        mes += 1
        if mes > 12:
            mes, anyo = 1, anyo + 1
    return filas


if __name__ == "__main__":
    filas = generar()
    destino = Path(__file__).parent / "serie_caja_sintetica.csv"
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mes", "neto"])
        w.writerows(filas)
    print(f"{len(filas)} meses escritos en {destino.name}")
