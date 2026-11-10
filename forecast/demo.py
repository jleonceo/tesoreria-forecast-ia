# -*- coding: utf-8 -*-
"""
demo.py — Ejecuta el forecast sobre la serie sintetica y comprueba, con
backtesting rolling-origin, si BATE a dos referencias: el naif-media (la media
del mismo mes en años anteriores, el metodo habitual) y el naif con tendencia
(el mismo mes del año anterior mas la tendencia), que es la exigente.

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


def _cerca(a, b, tol=1e-6):
    return a is not None and b is not None and abs(a - b) <= tol


def controles():
    """Controles con casos calculados a mano o por otro camino. Cada uno cae si se rompe lo que vigila:
    la escala del MASE, que el backtesting no mire el futuro, que a h>1 se mida la suma del horizonte y
    la referencia del mismo mes del año anterior más la tendencia."""
    ok = True

    # 1. Escala del MASE a mano: en 0, 1, ..., 23 cada mes dista 12 del mismo mes del año anterior.
    if not _cerca(modelo.escala_mase([float(t) for t in range(24)]), 12.0):
        print("  [FALLO] escala_mase(0..23) deberia ser 12"); ok = False

    # 2. Serie de prueba: dos años tranquilos y despues meses con saltos grandes. Si la escala o el
    #    modelo usaran meses posteriores al origen, las cifras del backtesting cambiarian.
    base = [100.0 + 2.0 * t + (10.0 if t % 12 in (5, 6) else 0.0) for t in range(24)]
    saltos = [400.0, 50.0, 700.0, 20.0, 900.0, 10.0, 650.0, 30.0, 800.0, 40.0]
    serie = base + saltos
    for h in (1, 3):
        r = modelo.backtest_rolling(serie, 1, horizonte=h)
        errores, escalas, err_der = [], [], []
        for o in range(24, len(serie) - h + 1):
            real = sum(serie[o:o + h])                       # a h>1 se mide la SUMA del horizonte
            errores.append(abs(real - sum(v for _, v in modelo.prever(serie[:o], 1, h))))
            escalas.append(modelo.escala_mase(serie[:o]))     # solo el pasado del origen
            err_der.append(abs(real - sum(modelo.prever_naif_deriva(serie[:o], h))))
        if r["n_origenes"] != len(errores):
            print(f"  [FALLO] h={h}: {r['n_origenes']} origenes, esperaba {len(errores)}"); ok = False
        if not _cerca(r["mae_modelo"], round(sum(errores) / len(errores), 2), 0.006):
            print(f"  [FALLO] h={h}: el error del modelo no sale solo del pasado de cada origen"); ok = False
        if not _cerca(r["escala_mase"], round(sum(escalas) / len(escalas), 2), 0.006):
            print(f"  [FALLO] h={h}: la escala del MASE no sale solo del pasado de cada origen"); ok = False
        if not _cerca(r["mae_naif_deriva"], round(sum(err_der) / len(err_der), 2), 0.006):
            print(f"  [FALLO] h={h}: el error de la referencia con tendencia no cuadra"); ok = False
        # El veredicto contra la referencia con tendencia, rehecho a mano. En esta serie, a h=1 el
        # modelo PIERDE (los saltos castigan su recta), asi que un veredicto fijo en True cae aqui.
        mase_mod = sum(e / s for e, s in zip(errores, escalas)) / len(errores)
        mase_der = sum(e / s for e, s in zip(err_der, escalas)) / len(err_der)
        if r["bate_naif_deriva"] is not (round(mase_mod, 4) < round(mase_der, 4)):
            print(f"  [FALLO] h={h}: el veredicto contra la referencia con tendencia no cuadra"); ok = False
        if h == 1 and r["bate_naif_deriva"] is not False:
            print("  [FALLO] h=1: en la serie de prueba el modelo tiene que perder"); ok = False

    # 3. Referencia con tendencia a mano: con tendencia lineal y estacionalidad fija la acierta exacta,
    #    tambien a mas de 12 meses (usa el mismo mes de hace dos años mas dos años de tendencia).
    estac = [5.0, -3.0, 0.0, 8.0, -6.0, 2.0, 0.0, -4.0, 7.0, 1.0, -9.0, -1.0]
    exacta = [10.0 * t + estac[t % 12] for t in range(48)]
    prevision = modelo.prever_naif_deriva(exacta[:24], 24)
    if len(prevision) != 24 or not all(_cerca(p, r) for p, r in zip(prevision, exacta[24:48])):
        print("  [FALLO] prever_naif_deriva no reproduce una serie con tendencia y estacionalidad exactas")
        ok = False

    print("  [OK] controles de escala, pasado, suma del horizonte y referencia con tendencia." if ok
          else "  [FALLO] controles.")
    return ok


def main():
    y = cargar_serie()
    print(f"Serie sintetica: {len(y)} meses.\n")
    print("Backtesting rolling-origin (entrenar con el pasado, prever, comparar).")
    print("Dos referencias: naif-media (media del mismo mes en los ejercicios anteriores) y naif")
    print("con tendencia (el mismo mes 12 meses antes mas la tendencia). A h>1 el error es el de")
    print("la SUMA de los h meses. El veredicto mira h=1 y h=3; h=12 es informativo.\n")
    ok = True
    for h in (1, 3, 12):
        r = modelo.backtest_rolling(y, MES_INICIO, horizonte=h)
        if h in (1, 3):
            ok = ok and bool(r["bate_naif"]) and bool(r["bate_naif_deriva"])
        print(f"  h={h:<2} error medio (MAE): modelo={r['mae_modelo']:,.2f}  "
              f"naif-media={r['mae_naif']:,.2f}  naif con tendencia={r['mae_naif_deriva']:,.2f}  "
              f"(origenes={r['n_origenes']})")
        print(f"       MASE: modelo={r['mase_modelo']}  naif-media={r['mase_naif']}  "
              f"naif con tendencia={r['mase_naif_deriva']}  "
              f"bate a las dos={bool(r['bate_naif']) and bool(r['bate_naif_deriva'])}")
    print()
    diag = modelo.diagnostico_reciente(y, MES_INICIO)
    print(f"  Honestidad reciente: en los ultimos {diag['k']} origenes el modelo gana "
          f"{diag['modelo_gana_en']} al naif-media y {diag['modelo_gana_a_deriva_en']} al naif "
          f"con tendencia (alerta_degradacion={diag['alerta_degradacion']})")
    print()
    controles_ok = controles()
    print()
    print("VEREDICTO:", "OK (el modelo bate a las dos referencias en h=1 y h=3)" if ok and controles_ok
          else "REVISAR (el modelo no bate a alguna referencia en h=1 o h=3, o falla un control)")
    ok = ok and controles_ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
