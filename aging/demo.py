# -*- coding: utf-8 -*-
"""
demo.py — Aging sobre facturas abiertas sinteticas, con el control de honestidad
que decide si el aging por factura es fiable o solo indicativo.

Uso:  python aging/demo.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import motor  # noqa: E402


def cargar_facturas():
    ruta = Path(__file__).parent.parent / "datos_ejemplo" / "facturas_abiertas_sintetico.csv"
    items = []
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            crudo = (fila.get("dias_vencido") or "").strip()
            tiene_vto = crudo != ""
            dias = int(crudo) if tiene_vto else None
            items.append((float(fila["importe"]), dias, tiene_vto))
    return items


def controles():
    """Controles positivos y negativos de las funciones puras."""
    ok = True
    casos = [(-5, True, "CORRIENTE"), (1, True, "1-30"), (45, True, "31-60"),
             (110, True, "91-120"), (200, True, ">120"), (None, False, "SIN_VENCIMIENTO")]
    for dias, tiene, esperado in casos:
        got = motor.bucket_aging(dias, tiene)
        if got != esperado:
            print(f"  [FALLO] bucket({dias},{tiene}) -> {got}, esperaba {esperado}"); ok = False
    if motor.dso_dpo(100, 365) != 100.0:
        print("  [FALLO] DSO(100,365) deberia ser 100"); ok = False
    if motor.dso_dpo(100, 0) is not None:
        print("  [FALLO] DSO con flujo 0 deberia ser None"); ok = False
    # Control de enlace: by-ref ~= neto -> fiable; by-ref >> neto -> no fiable; sin neto -> None.
    if motor.enlace_fiable(100, 100) is not True:
        print("  [FALLO] enlace(100,100) deberia ser True"); ok = False
    if motor.enlace_fiable(800, 100) is not False:
        print("  [FALLO] enlace(800,100) deberia ser False"); ok = False
    if motor.enlace_fiable(100, 0) is not None:
        print("  [FALLO] enlace(100,0) deberia ser None"); ok = False
    print("  [OK] controles de buckets, DSO y enlace." if ok else "  [FALLO] controles.")
    return ok


def main():
    items = cargar_facturas()
    agg = motor.agregar_aging(items)
    total = round(sum(agg.values()), 2)
    vencido = round(sum(agg[b] for b in ["1-30", "31-60", "61-90", "91-120", ">120"]), 2)
    print(f"Facturas abiertas sinteticas: {len(items)} · total {total:,.2f}\n")
    print("Aging por antiguedad:")
    for b in motor.BUCKETS:
        if agg[b]:
            print(f"  {b:<16} {agg[b]:>12,.2f}")
    print(f"\n  Vencido (1-30 y peores): {vencido:,.2f}")

    # DSO de ejemplo: saldo a cobrar / ventas del periodo x dias.
    dso = motor.dso_dpo(total, 240000)
    print(f"  DSO de ejemplo (saldo/ventas x 365): {dso} dias")

    # El control de honestidad, con dos escenarios:
    print("\nControl de enlace (cobro <-> factura), el aging solo es firme si enlaza:")
    for byref, neto, etiqueta in [(40000, 41000, "cobros enlazan bien"),
                                  (40000, 9000, "cobros NO enlazan")]:
        fiable = motor.enlace_fiable(byref, neto)
        estado = "FIABLE" if fiable else "solo INDICATIVO"
        print(f"  by-ref {byref:,.0f} vs neto {neto:,.0f} ({etiqueta}) -> {estado}")

    print()
    ok = controles()
    print("\nVEREDICTO:", "OK" if ok else "REVISAR")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
