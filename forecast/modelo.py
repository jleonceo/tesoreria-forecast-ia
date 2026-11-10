# -*- coding: utf-8 -*-
"""
modelo.py — Motor de prevision de caja por descomposicion transparente.

Nucleo PURO (sin base de datos, sin IA, sin red): tendencia + estacionalidad por
backfitting iterativo, prevision amortiguada (damped), dos referencias con las
que compararse y backtesting rolling-origin con MASE (Hyndman & Koehler 2006).

Las dos referencias:
- naif-media: la media del mismo mes en los años anteriores, el metodo habitual;
- naif con tendencia: el mismo mes del año anterior mas la tendencia de los dos
  ultimos años. Es la referencia exigente: la media del mismo mes no ve que la
  serie crece, asi que ganarle a ella sola dice poco.

Se alimenta de una serie mensual de netos; en `demo.py` esa serie sale de datos
sinteticos.

Criterio de exito del forecast: BATIR a las dos referencias al mismo horizonte
(MASE del modelo menor que el de cada una). El "MASE < 1" es informativo, no
criterio (ver backtest_rolling).
"""

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
    Converge a trend y estacional ortogonales. `robusto=True` usa mediana (resiste meses
    atípicos). Devuelve (a, b, idx). Función pura."""
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


def prever_naif_deriva(y, horizonte, periodo=PERIODO):
    """Naïf estacional CON TENDENCIA: el punto n+k se prevé con el mismo mes del año anterior
    (o de hace dos años, si k >= periodo) más la tendencia de esos años. La tendencia mensual es
    (media de los últimos 12 meses − media de los 12 anteriores) / 12. Necesita dos ciclos de
    historia. Sólo usa `y` (el pasado). Función pura. Devuelve la lista de `horizonte` previsiones."""
    n = len(y)
    if n < 2 * periodo:
        raise ValueError(f"prever_naif_deriva necesita {2 * periodo} meses de historia y tiene {n}")
    deriva = (_media(y[n - periodo:n]) - _media(y[n - 2 * periodo:n - periodo])) / periodo
    out = []
    for k in range(horizonte):
        retardo = periodo * (k // periodo + 1)          # 12 para k<12, 24 para k<24, ...
        out.append(y[n + k - retardo] + deriva * retardo)
    return out


def mae(errores):
    return _media([abs(e) for e in errores]) if errores else None


def escala_mase(y, periodo=PERIODO):
    """Denominador del MASE = MAE del naïf estacional un-paso in-sample:
    media|y_t − y_{t-periodo}|. Hyndman & Koehler 2006. Función pura."""
    difs = [abs(y[i] - y[i - periodo]) for i in range(periodo, len(y))]
    return _media(difs) if difs else None


def backtest_rolling(y, mes_inicio, horizonte=1, robusto=True, min_entreno=MIN_ENTRENO, phi=1.0):
    """Backtesting ROLLING-ORIGIN (ventana expansible). En cada origen o (entrenando con
    y[:o]) prevé el punto o (h=1) o el ACUMULADO de o..o+h-1 (h>1) y lo compara con el real,
    para el MODELO y para las dos referencias (naïf-media y naïf con tendencia). A h>1 el error
    es el de la SUMA de los h meses, no el de cada mes. Devuelve dict con MAE/MASE de los tres.
    Función pura (no toca BD)."""
    n = len(y)
    err_mod, err_naif, err_der, escalas = [], [], [], []
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
        # NAÏF CON TENDENCIA: sólo ve el entreno y[:o].
        err_der.append(real_acum - sum(prever_naif_deriva(ytr, horizonte)))
        escalas.append(esc_o)
        o += 1
    mae_mod, mae_naif, mae_der = mae(err_mod), mae(err_naif), mae(err_der)
    res = {
        "horizonte": horizonte, "n_origenes": len(err_mod),
        "mae_modelo": round(mae_mod, 2) if mae_mod is not None else None,
        "mae_naif": round(mae_naif, 2) if mae_naif is not None else None,
        "mae_naif_deriva": round(mae_der, 2) if mae_der is not None else None,
        "escala_mase": round(_media(escalas), 2) if escalas else None,
        "mase_modelo": None, "mase_naif": None, "mase_naif_deriva": None, "mase_bajo_1": None,
        "bate_naif": None, "bate_naif_deriva": None,
    }
    if escalas:
        # MASE por origen promediado: media de |error_o| / escala_o (escala causal del origen).
        mase_mod = _media([abs(e) / s for e, s in zip(err_mod, escalas)])
        mase_naif = _media([abs(e) / s for e, s in zip(err_naif, escalas)])
        mase_der = _media([abs(e) / s for e, s in zip(err_der, escalas)])
        res["mase_modelo"] = round(mase_mod, 4)
        res["mase_naif"] = round(mase_naif, 4)
        res["mase_naif_deriva"] = round(mase_der, 4)
        # CRITERIO DE ÉXITO = BATIR a cada referencia al MISMO horizonte: MASE_modelo < MASE_ref.
        # El "<1" es sólo INFORMATIVO: la escala del MASE es la de un paso, y a h>1 se divide el
        # error de la SUMA de h meses, así que MASE>1 es lo esperado aunque el modelo gane.
        res["mase_bajo_1"] = res["mase_modelo"] < 1.0
        res["bate_naif"] = res["mase_modelo"] < res["mase_naif"]
        res["bate_naif_deriva"] = res["mase_modelo"] < res["mase_naif_deriva"]
    return res


def periodo_seguro(y):
    """Mínimo de puntos para estimar estacionalidad (al menos 1 ciclo + 1)."""
    return min(len(y), PERIODO + 1)


def diagnostico_reciente(y, mes_inicio, robusto=True, k=6, min_entreno=MIN_ENTRENO, phi=1.0):
    """Honestidad prospectiva: en los ÚLTIMOS k orígenes (h=1), ¿cuántos gana el modelo a cada
    referencia? El backtest agregado puede estar sostenido por el pasado mientras el modelo se
    degrada en el tramo reciente. Función pura. Devuelve dict."""
    n = len(y)
    registro = []   # (idx_objetivo, err_mod, err_naif, err_naif_deriva)
    o = max(min_entreno, periodo_seguro(y))
    while o + 1 <= n:
        pred = prever(y[:o], mes_inicio, 1, robusto=robusto, phi=phi)[0][1]
        naif = naif_estacional_media(y[:o], mes_inicio, o)
        deriva = prever_naif_deriva(y[:o], 1)[0]
        registro.append((o, y[o] - pred, y[o] - naif, y[o] - deriva))
        o += 1
    ultimos = registro[-k:]
    gana_mod = sum(1 for _, em, en, _ in ultimos if abs(em) < abs(en))
    gana_der = sum(1 for _, em, _, ed in ultimos if abs(em) < abs(ed))
    return {
        "k": len(ultimos),
        "modelo_gana_en": gana_mod,
        "modelo_gana_a_deriva_en": gana_der,
        "mae_modelo_reciente": round(mae([em for _, em, _, _ in ultimos]), 2) if ultimos else None,
        "mae_naif_reciente": round(mae([en for _, _, en, _ in ultimos]), 2) if ultimos else None,
        "alerta_degradacion": bool(ultimos) and min(gana_mod, gana_der) < len(ultimos) / 2.0,
    }
