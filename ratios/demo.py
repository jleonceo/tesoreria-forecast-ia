# -*- coding: utf-8 -*-
"""
demo.py — Calcula los ratios sobre un balance sintetico y comprueba las trampas
que un calculo ingenuo se traga.

Uso:  python ratios/demo.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import motor  # noqa: E402


def cargar_balance():
    ruta = Path(__file__).parent.parent / "datos_ejemplo" / "balance_sintetico.csv"
    pares = []
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            pares.append((fila["cuenta"], float(fila["saldo"])))
    return pares


def controles():
    """Controles positivos y negativos: lo que separa el mapeo correcto del ingenuo."""
    ok = True
    # Reclasificacion por SIGNO (la parte no trivial):
    casos = [
        ("57200002", 3000.0, "TESORERIA"),
        ("43000003", 62000.0, "CLIENTES"),
        ("43000011", -13945.0, "ANTICIPOS_CLIENTES"),   # cliente acreedor = anticipo (PC)
        ("40000003", -49364.0, "PROVEEDORES"),
        ("40000002", 2755.0, "ANTICIPOS_PROVEEDORES"),  # proveedor deudor = anticipo (AC)
    ]
    for cuenta, saldo, esperado in casos:
        got = motor.clasificar_masa(cuenta, saldo)
        if got != esperado:
            print(f"  [FALLO] {cuenta} ({saldo}) -> {got}, esperaba {esperado}"); ok = False
    # Division por cero protegida: sin pasivo corriente, el ratio es None (no excepcion).
    r0 = motor.calcular_ratios({"TESORERIA": 100.0})
    if r0["ratio_corriente"] is not None:
        print(f"  [FALLO] PC=0 deberia dar None, got {r0['ratio_corriente']}"); ok = False
    print("  [OK] controles de clasificacion y division por cero." if ok else "  [FALLO] controles.")
    return ok


def main():
    pares = cargar_balance()
    suma = round(sum(s for _, s in pares), 2)
    print(f"Balance sintetico: {len(pares)} cuentas. Suma de saldos = {suma:.2f} (debe cerrar a 0).\n")
    if abs(suma) > 0.01:
        print("INTEGRIDAD_ROTA: el balance no cierra; no se publican ratios.")
        return 1

    masas = motor.agregar_masas(pares)
    r = motor.calcular_ratios(masas)
    print("Masas de balance:")
    for m, v in sorted(masas.items()):
        if m != "PYG":
            print(f"  {m:<22} {v:>14,.2f}")
    print()
    print(f"  Ratio corriente (AC/PC):      {r['ratio_corriente']}")
    print(f"  Ratio acida / quick:          {r['ratio_acida_quick']}")
    print(f"  Ratio de caja:                {r['ratio_caja']}")
    print(f"  Fondo de maniobra:            {r['fondo_maniobra']:,.2f}")
    print(f"  Endeudamiento:                {r['ratio_endeudamiento']}")
    print(f"  Autonomia financiera:         {r['autonomia_financiera']}")
    print(f"  Cuadre del balance (=0 si cierra): {r['descuadre_balance']:.2f}")
    print()
    ok = controles() and r["descuadre_balance"] == 0.0
    print("\nVEREDICTO:", "OK" if ok else "REVISAR")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
