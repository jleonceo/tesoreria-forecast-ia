# -*- coding: utf-8 -*-
"""
motor.py — Aging de cobros y pagos (nucleo PURO).

Sin base de datos, sin IA, sin red. Clasifica cada saldo abierto en su bucket de
antiguedad, calcula DSO/DPO, y trae un control de HONESTIDAD poco habitual:
`enlace_fiable` decide si el aging por factura es de fiar. Solo lo es si los
cobros/pagos enlazan a su factura (bruto por referencia ~= neto real); si no,
el bucketing sobreestima y el veredicto baja a INDICATIVO en vez de fingir
buckets firmes. Un vencimiento vacio NO es "al corriente": es SIN_VENCIMIENTO.
"""

# ---------------------------------------------------------------------------
# Lógica de buckets (PURA, testable)
# ---------------------------------------------------------------------------
BUCKETS = ["CORRIENTE", "1-30", "31-60", "61-90", "91-120", ">120", "SIN_VENCIMIENTO"]


def bucket_aging(dias_vencido, tiene_vto: bool) -> str:
    """
    dias_vencido = FECHA_REF − fecha_vencimiento (positivo = ya vencido).
    CORRIENTE = aún no vence (<=0). Sin fecha → SIN_VENCIMIENTO.
    """
    if not tiene_vto or dias_vencido is None:
        return "SIN_VENCIMIENTO"
    d = int(dias_vencido)
    if d <= 0:
        return "CORRIENTE"
    if d <= 30:
        return "1-30"
    if d <= 60:
        return "31-60"
    if d <= 90:
        return "61-90"
    if d <= 120:
        return "91-120"
    return ">120"


def agregar_aging(items) -> dict:
    """items = iterable de (importe_abierto, dias_vencido, tiene_vto). Devuelve {bucket: importe}."""
    agg = {b: 0.0 for b in BUCKETS}
    for importe, dias, tiene in items:
        agg[bucket_aging(dias, tiene)] += float(importe)
    return {b: round(v, 2) for b, v in agg.items()}


def dso_dpo(saldo_abierto: float, flujo_periodo: float, dias: int = 365):
    """DSO/DPO = saldo abierto / flujo del período × días. None si no hay flujo."""
    if not flujo_periodo:
        return None
    return round(saldo_abierto / flujo_periodo * dias, 1)


def enlace_fiable(gross_byref: float, neto: float, tol: float = 0.10):
    """
    ¿El aging por factura es fiable? Lo es si el bruto por referencia ≈ el neto real
    (los cobros enlazan a su factura). Si diverge mucho → los cobros NO referencian la
    factura y el bucketing por referencia sobreestima. None si no hay neto.
    """
    if neto is None or neto <= 0:
        return None
    return abs(gross_byref - neto) <= tol * neto
