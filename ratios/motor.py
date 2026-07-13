# -*- coding: utf-8 -*-
"""
motor.py — Ratios de liquidez y solvencia desde el balance (nucleo PURO).

Sin base de datos, sin IA, sin red. La aritmetica del ratio es trivial; el
trabajo real (y lo que ninguna libreria te ahorra) es el MAPEO al PGC espanol:
clasificar cada cuenta en su masa de balance por prefijo Y por SIGNO del saldo.
Un cliente (43x) con saldo acreedor es un ANTICIPO DE CLIENTE (pasivo corriente),
no un cliente a cobrar; esa reclasificacion por signo es la parte no trivial y
esta explicita.

Autocontrol: el balance debe cerrar (Activo total = Exigible + Patrimonio neto).
Si no cierra, no se publican ratios (se calcula sobre datos, no sobre un descuadre).
"""

# ---------------------------------------------------------------------------
# Clasificación de masas PGC (función PURA, testable)
# ---------------------------------------------------------------------------
# Cada masa se etiqueta con su naturaleza: AC=activo corriente, ANC=activo no corriente,
# PC=pasivo corriente, PNC=pasivo no corriente, PN=patrimonio neto, PYG=resultado (cuenta de
# gestión, año abierto), OTROS=no clasificado (se reporta, nunca se descarta en silencio).
NATURALEZA = {
    "TESORERIA": "AC", "EXISTENCIAS": "AC", "CLIENTES": "AC", "ANTICIPOS_PROVEEDORES": "AC",
    "HP_DEUDORA": "AC", "ANTICIPOS_PERSONAL": "AC",
    "PROVEEDORES": "PC", "ANTICIPOS_CLIENTES": "PC", "REMUN_PEND": "PC",
    "HP_ACREEDORA": "PC", "DEUDA_CP": "PC",
    "ANC": "ANC", "PNC": "PNC", "PN": "PN", "PYG": "PYG", "OTROS": "OTROS",
}


def clasificar_masa(cuenta: str, saldo: float) -> str:
    """Devuelve la MASA de la cuenta según prefijo PGC + signo del saldo (reclasificación correcta)."""
    c = str(cuenta)
    g1, g2 = c[:1], c[:2]
    s = float(saldo)
    if g2 == "57":
        return "TESORERIA"
    if g2 == "52":
        return "DEUDA_CP"
    if g1 == "3":
        return "EXISTENCIAS"
    if g2 in ("43", "44"):                       # deudores comerciales
        return "CLIENTES" if s >= 0 else "ANTICIPOS_CLIENTES"
    if g2 in ("40", "41"):                       # acreedores comerciales
        return "PROVEEDORES" if s < 0 else "ANTICIPOS_PROVEEDORES"
    if g2 == "46":                               # personal
        return "REMUN_PEND" if s < 0 else "ANTICIPOS_PERSONAL"
    if g2 == "47":                               # administraciones públicas
        return "HP_ACREEDORA" if s < 0 else "HP_DEUDORA"
    if g1 == "2":                                # activo no corriente (incl. 28 amortización, signo −)
        return "ANC"
    if g2 in ("10", "11", "12", "13", "14"):     # patrimonio neto
        return "PN"
    if g2 in ("15", "16", "17", "18"):           # pasivo no corriente
        return "PNC"
    if g1 in ("6", "7"):                         # cuentas de gestión (PyG del año abierto)
        return "PYG"
    return "OTROS"


def agregar_masas(cuentas_saldos) -> dict:
    """cuentas_saldos = iterable de (cuenta, saldo). Devuelve {masa: saldo_acumulado}."""
    masas = {}
    for cuenta, saldo in cuentas_saldos:
        m = clasificar_masa(cuenta, saldo)
        masas[m] = masas.get(m, 0.0) + float(saldo)
    return masas


def calcular_ratios(masas: dict) -> dict:
    """Calcula liquidez y solvencia desde las masas agregadas (función PURA)."""
    g = lambda k: float(masas.get(k, 0.0))
    # Activo corriente (saldos deudores, +)
    AC = g("TESORERIA") + g("EXISTENCIAS") + g("CLIENTES") + g("ANTICIPOS_PROVEEDORES") \
        + g("HP_DEUDORA") + g("ANTICIPOS_PERSONAL")
    # Pasivo corriente (saldos acreedores, −) → se niegan para magnitud positiva
    PC = -(g("PROVEEDORES") + g("ANTICIPOS_CLIENTES") + g("REMUN_PEND")
           + g("HP_ACREEDORA") + g("DEUDA_CP"))
    ANC = g("ANC")
    PNC = -g("PNC")
    # Patrimonio neto = capital+reservas + RESULTADO del ejercicio abierto.
    # El resultado vive aún en cuentas de gestión (PyG, grupos 6/7), sin cerrar a 129/120.
    # Sin sumarlo, el PN queda infravalorado y el balance NO cierra (autonomía absurda).
    resultado_ejercicio = -g("PYG")     # saldo PyG acreedor (−) = beneficio (+)
    PN = -g("PN") + resultado_ejercicio
    tesoreria = g("TESORERIA")
    existencias = g("EXISTENCIAS")

    activo_total = AC + ANC
    pasivo_exigible = PC + PNC
    # Autocontrol contable: Activo total = Pasivo exigible + Patrimonio neto.
    descuadre_balance = round(activo_total - (pasivo_exigible + PN), 2)

    def ratio(num, den):
        return round(num / den, 4) if den not in (0, 0.0) else None

    return {
        "activo_corriente": round(AC, 2),
        "pasivo_corriente": round(PC, 2),
        "activo_no_corriente": round(ANC, 2),
        "pasivo_no_corriente": round(PNC, 2),
        "patrimonio_neto": round(PN, 2),
        "resultado_ejercicio": round(resultado_ejercicio, 2),
        "activo_total": round(activo_total, 2),
        "pasivo_exigible": round(pasivo_exigible, 2),
        "descuadre_balance": descuadre_balance,                 # debe ser 0,00 si el balance cierra
        "tesoreria": round(tesoreria, 2),
        "existencias": round(existencias, 2),
        "ratio_corriente": ratio(AC, PC),                       # AC / PC
        "ratio_acida_quick": ratio(AC - existencias, PC),       # (AC − existencias) / PC
        "ratio_caja": ratio(tesoreria, PC),                     # tesorería / PC
        "fondo_maniobra": round(AC - PC, 2),                    # AC − PC
        "ratio_endeudamiento": ratio(pasivo_exigible, activo_total),   # exigible / activo total
        "autonomia_financiera": ratio(PN, activo_total),        # PN / activo total
    }
