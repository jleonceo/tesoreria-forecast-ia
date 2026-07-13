# -*- coding: utf-8 -*-
"""
modelo.py — Motor de prevision de caja por descomposicion transparente.

Nucleo PURO (sin base de datos, sin IA, sin red): tendencia + estacionalidad por
backfitting iterativo, prevision amortiguada (damped), naif estacional como
competidor, y backtesting rolling-origin con MASE (Hyndman & Koehler 2006).

Es el mismo motor que valida el repo, extraido de un sistema en uso real y
saneado (sin rutas ni credenciales). Se alimenta de una serie mensual de netos;
en `demo.py` esa serie sale de datos sinteticos.

Criterio de exito del forecast: BATIR al naif-media al mismo horizonte
(MASE_modelo < MASE_naif). El "<1" es informativo, no criterio (ver backtest_rolling).
"""

from datetime import datetime, date, timedelta

PERIODO = 12          # estacionalidad mensual
MIN_ENTRENO = 24      # minimo de meses para arrancar el backtesting (2 ciclos)
PHI = 1.0             # amortiguamiento de la tendencia (1.0 = tendencia lineal pura)

def _mediana(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def _media(xs):
    return sum(xs) / len(xs) if xs else 0.0


def meses_calendario(n, mes_inicio):
    """Lista de los meses-calendario (1-12) para n puntos que arrancan en `mes_inicio`."""
    return [((mes_inicio - 1 + i) % 12) + 1 for i in range(n)]


def ajustar_tendencia(y):
    """OLS de y sobre t=1..n. Devuelve (a, b): ŷ_tendencia(t) = a + b*t. Función pura."""
    n = len(y)
    if n == 0:
        return 0.0, 0.0
    if n == 1:
        return float(y[0]), 0.0
    ts = list(range(1, n + 1))
    mt = _media(ts)
    my = _media(y)
    sxx = sum((t - mt) ** 2 for t in ts)
    sxy = sum((t - mt) * (yi - my) for t, yi in zip(ts, y))
    b = sxy / sxx if sxx else 0.0
    a = my - b * mt
    return a, b


def ajustar_modelo(y, mes_inicio, robusto=True, iters=25):
    """Estimación CONJUNTA de tendencia y estacionalidad por BACKFITTING iterativo, para evitar
    la fuga estacional→tendencia de un OLS ingenuo sobre la serie cruda: en cada pasada se ajusta
    la tendencia sobre la serie DESESTACIONALIZADA y se recalcula el estacional sobre la DESTENDIDA.
    Converge a trend y estacional ortogonales. `robusto=True` usa mediana (resiste outliers como
    2026-06). Devuelve (a, b, idx). Función pura."""
    n = len(y)
    meses = meses_calendario(n, mes_inicio)
    agreg = _mediana if robusto else _media
    idx = {m: 0.0 for m in range(1, 13)}
    a, b = 0.0, 0.0
    for _ in range(iters):
        desest = [y[i] - idx.get(meses[i], 0.0) for i in range(n)]
        a, b = ajustar_tendencia(desest)
        resid = [y[i] - (a + b * (i + 1)) for i in range(n)]
        nuevo = {}
        for m in range(1, 13):
            vals = [resid[i] for i in range(n) if meses[i] == m]
            if vals:
                nuevo[m] = agreg(vals)
        if nuevo:                       # centrar a media 0 (un mes 'normal' no mueve el nivel)
            centro = _media(list(nuevo.values()))
            nuevo = {m: v - centro for m, v in nuevo.items()}
        idx = nuevo
    return a, b, idx


def indices_estacionales(y, mes_inicio, robusto=True):
    """Índice estacional por mes-calendario (1-12), centrado a suma 0, con la tendencia ya
    separada por backfitting (sin fuga). Función pura."""
    return ajustar_modelo(y, mes_inicio, robusto=robusto)[2]


def prever(y, mes_inicio, horizonte, robusto=True, phi=1.0):
    """Previsión de los próximos `horizonte` meses (netos). Función pura.
    `phi` = factor de AMORTIGUAMIENTO de la tendencia (0<phi<=1): cada paso adelante añade
    b*phi^h en vez de b, así la tendencia no extrapola sin freno (diseño 'damped' tipo
    Holt-Winters). phi=1 → tendencia lineal pura (caso por defecto, mantiene el autotest exacto).
    Devuelve lista de (mes_calendario, neto_previsto)."""
    n = len(y)
    a, b, idx = ajustar_modelo(y, mes_inicio, robusto=robusto)
    nivel_n = a + b * n            # nivel de tendencia en el último punto observado
    out = []
    acum_phi = 0.0
    for h in range(1, horizonte + 1):
        acum_phi += phi ** h       # phi + phi^2 + ... + phi^h  (con phi=1 = h)
        m_f = ((mes_inicio - 1 + n + h - 1) % 12) + 1
        yhat = nivel_n + b * acum_phi + idx.get(m_f, 0.0)
        out.append((m_f, yhat))
    return out


def naif_estacional_media(y, mes_inicio, indice_objetivo):
    """Naïf-MEDIA (lógica de v_proyeccion_tesoreria): previsión del punto `indice_objetivo`
    (0-based) = media de los puntos previos del MISMO mes-calendario. Si no hay, media global.
    Sólo usa y[:indice_objetivo] (no mira el futuro). Función pura."""
    meses = meses_calendario(indice_objetivo + 1, mes_inicio)
    m_obj = meses[indice_objetivo]
    previos = [y[j] for j in range(indice_objetivo) if meses[j] == m_obj]
    if previos:
        return _media(previos)
    return _media(y[:indice_objetivo]) if indice_objetivo else 0.0


def mae(errores):
    return _media([abs(e) for e in errores]) if errores else None


def escala_mase(y, periodo=PERIODO):
    """Denominador del MASE = MAE del naïf estacional un-paso in-sample:
    media|y_t − y_{t-periodo}|. Hyndman & Koehler 2006. Función pura."""
    difs = [abs(y[i] - y[i - periodo]) for i in range(periodo, len(y))]
    return _media(difs) if difs else None


# ===========================================================================
# CAPA DETERMINISTA: vencimientos comprometidos de la cartera abierta (P3)
# ===========================================================================
# El flujo COMERCIAL (cobros de clientes 43x / pagos a proveedores 40x) tiene vencimiento
# conocido en la cartera. La capa determinista AGENDA ese flujo comprometido al mes en que se
# espera el cobro/pago (vencimiento + lag de comportamiento). Es DATO FIRME, no modelo.
# Límite honesto: una FOTO de la cartera capta lo ya facturado; NO las facturas aún por emitir
# que vencerán en 2-3 meses → la cobertura determinista decae con el horizonte (completa a h=1).
#
# ⚠️ VALIDACIÓN 30/06 (resultado NEGATIVO documentado para no recablearlo a ciegas):
# Se backtesteó un HÍBRIDO (determinista comercial + estadístico no-comercial) con reconstrucción
# rigurosa (facturas emitidas<=origen, venciendo en el mes objetivo). Resultado: MUCHO PEOR que el
# estadístico puro (h=1 MASE 2.82 vs 1.06; h=3 8.37 vs 2.14). Causa: en el SEED sintético el cobro
# NO está atado al vencimiento (comercial comprometido idealizado vs comercial real: signos opuestos
# en varios meses, MAE 40.566 ≈ magnitud del propio comercial 47.358 → señal nula). Por eso el
# determinista NO se mezcla en la previsión del neto (el estadístico manda). SÍ se usa para el
# CALENDARIO comprometido (P7): los vencimientos contractuales son movimientos esperados legítimos
# para `tes_calendario_caja`, y en datos REALES (pago en torno a vencimiento) esta capa sí ayudaría.

LAG_COBRO = 7    # los clientes cobran ~7 días tras vencimiento (lag de comportamiento)
LAG_PAGO = 15    # a proveedores se paga ~15 días tras vencimiento

def _a_fecha(x):
    """Normaliza a date desde date/datetime/str ISO. None→None. Función pura."""
    if x is None:
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    s = str(x)[:10]
    try:
        return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except Exception:
        return None


def _clave_mes(f):
    return f"{f.year:04d}-{f.month:02d}"


def programar_vencimientos(partidas, primer_mes, lag_cobro=LAG_COBRO, lag_pago=LAG_PAGO):
    """Agenda los vencimientos comprometidos por mes de cobro/pago esperado. Función pura.
    `partidas` = iterable de (tipo, fecha_vencimiento(date|str|None), importe_pendiente).
      tipo: 'COBRAR' = entrada (+), 'PAGAR' = salida (−). Otros (anticipos) se ignoran
      (ya son saldos, no flujos futuros).
    `primer_mes` = 'YYYY-MM' primer mes del horizonte: los YA VENCIDOS (fecha esperada < primer_mes)
      se agendan ahí (catch-up: siguen pendientes → se cobran/pagan pronto).
    Devuelve {mes: {'cobros':x, 'pagos':y, 'neto':z, 'n':k}} (pagos en valor positivo)."""
    out = {}
    py, pm = int(primer_mes[:4]), int(primer_mes[5:7])
    for tipo, fvenc, imp in partidas:
        f = _a_fecha(fvenc)
        if f is None or tipo not in ("COBRAR", "PAGAR"):
            continue
        imp = float(imp or 0.0)
        if imp == 0.0:
            continue
        lag = lag_cobro if tipo == "COBRAR" else lag_pago
        fesp = f + timedelta(days=lag)
        # Si la fecha esperada cae antes del primer mes del horizonte → catch-up en el primer mes.
        clave = _clave_mes(fesp)
        if (fesp.year, fesp.month) < (py, pm):
            clave = primer_mes
        d = out.setdefault(clave, {"cobros": 0.0, "pagos": 0.0, "neto": 0.0, "n": 0})
        if tipo == "COBRAR":
            d["cobros"] += imp
            d["neto"] += imp
        else:
            d["pagos"] += imp
            d["neto"] -= imp
        d["n"] += 1
    for k in out:
        out[k] = {kk: (round(vv, 2) if kk != "n" else vv) for kk, vv in out[k].items()}
    return out


def backtest_rolling(y, mes_inicio, horizonte=1, robusto=True, min_entreno=MIN_ENTRENO, phi=1.0):
    """Backtesting ROLLING-ORIGIN (ventana expansible). En cada origen o (entrenando con
    y[:o]) prevé el punto o (h=1) o el ACUMULADO de o..o+h-1 (h>1) y lo compara con el real,
    tanto para el MODELO como para el NAÏF-media. Devuelve dict con MAE/MASE de ambos.
    Función pura (no toca BD)."""
    n = len(y)
    err_mod, err_naif, escalas = [], [], []
    o = max(min_entreno, periodo_seguro(y))
    while o + horizonte <= n:
        ytr = y[:o]
        # ESCALA CAUSAL: MAE del naïf estacional un-paso in-sample SOBRE EL ENTRENO y[:o] (sólo el
        # pasado disponible en el origen). Estrictamente sin look-ahead (Hyndman & Koehler 2006).
        esc_o = escala_mase(ytr)
        if not esc_o or esc_o <= 0:
            o += 1
            continue
        # MODELO: previsión a `horizonte` desde el origen o.
        pred = prever(ytr, mes_inicio, horizonte, robusto=robusto, phi=phi)
        real_acum = sum(y[o:o + horizonte])
        pred_acum = sum(p for _, p in pred)
        err_mod.append(real_acum - pred_acum)
        # NAÏF-media: acumulado de las previsiones un-paso para cada mes del horizonte.
        naif_acum = 0.0
        for k in range(horizonte):
            naif_acum += naif_estacional_media(y[:o + k], mes_inicio, o + k)
        err_naif.append(real_acum - naif_acum)
        escalas.append(esc_o)
        o += 1
    mae_mod, mae_naif = mae(err_mod), mae(err_naif)
    res = {
        "horizonte": horizonte, "n_origenes": len(err_mod),
        "mae_modelo": round(mae_mod, 2) if mae_mod is not None else None,
        "mae_naif": round(mae_naif, 2) if mae_naif is not None else None,
        "escala_mase": round(_media(escalas), 2) if escalas else None,
        "mase_modelo": None, "mase_naif": None, "mase_bajo_1": None, "bate_naif": None,
    }
    if escalas:
        # MASE por origen promediado: media de |error_o| / escala_o (escala causal del origen).
        mase_mod = _media([abs(e) / s for e, s in zip(err_mod, escalas)])
        mase_naif = _media([abs(e) / s for e, s in zip(err_naif, escalas)])
        res["mase_modelo"] = round(mase_mod, 4)
        res["mase_naif"] = round(mase_naif, 4)
        # CRITERIO DE ÉXITO = BATIR al competidor (naïf-media) al MISMO horizonte: MASE_modelo <
        # MASE_naïf. El "<1" es sólo INFORMATIVO (no criterio): la escala del MASE es de un paso, y
        # en multi-paso acumulado MASE>1 es lo esperado aunque el modelo gane. Además, con escala
        # causal por origen el "<1" de h=1 deja de cumplirse — era un artefacto del denominador
        # in-sample (escéptico 30/06), no una propiedad robusta del modelo. La portería no se mueve.
        res["mase_bajo_1"] = res["mase_modelo"] < 1.0
        res["bate_naif"] = res["mase_modelo"] < res["mase_naif"]
    return res


def periodo_seguro(y):
    """Mínimo de puntos para estimar estacionalidad (al menos 1 ciclo + 1)."""
    return min(len(y), PERIODO + 1)


def diagnostico_reciente(y, mes_inicio, robusto=True, k=6, min_entreno=MIN_ENTRENO, phi=1.0):
    """Honestidad prospectiva: en los ÚLTIMOS k orígenes (h=1), ¿cuántos gana el modelo al naïf?
    El backtest agregado puede estar sostenido por el pasado mientras el modelo se degrada en el
    tramo reciente (hallazgo del escéptico 30/06). Función pura. Devuelve dict."""
    n = len(y)
    registro = []   # (idx_objetivo, err_mod, err_naif)
    o = max(min_entreno, periodo_seguro(y))
    while o + 1 <= n:
        pred = prever(y[:o], mes_inicio, 1, robusto=robusto, phi=phi)[0][1]
        naif = naif_estacional_media(y[:o], mes_inicio, o)
        registro.append((o, y[o] - pred, y[o] - naif))
        o += 1
    ultimos = registro[-k:]
    gana_mod = sum(1 for _, em, en in ultimos if abs(em) < abs(en))
    return {
        "k": len(ultimos),
        "modelo_gana_en": gana_mod,
        "mae_modelo_reciente": round(mae([em for _, em, _ in ultimos]), 2) if ultimos else None,
        "mae_naif_reciente": round(mae([en for _, _, en in ultimos]), 2) if ultimos else None,
        "alerta_degradacion": bool(ultimos) and gana_mod < len(ultimos) / 2.0,
    }
