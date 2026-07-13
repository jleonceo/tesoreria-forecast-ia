# tesoreria-forecast-ia

**Previsión de caja con criterio, y la prueba de que acierta.**
**Cash-flow forecasting with judgement, and the proof that it works.**

Sin dependencias (solo Python estándar), sin base de datos, sin IA, sin red.
No dependencies (standard Python only), no database, no AI, no network.

[Español](#español) · [English](#english)

---

## Español

### Qué resuelve

Registrar lo que ya pasó es la parte fácil de la contabilidad. Lo difícil es mirar hacia delante: ¿llego a fin de mes?, ¿cubro las nóminas y el IVA del trimestre?, ¿cuándo se me tensa la caja? Este repositorio enseña a **prever la caja con criterio** y, sobre todo, a **demostrar que la previsión acierta** en vez de pedir que te fíes de ella.

Lo habitual para prever la caja es la media del mismo mes de otros años. Funciona, pero no aprende ni tendencia ni estacionalidad, y casi nunca se comprueba si acierta. Aquí el motor la sustituye por una previsión por descomposición y la somete a **backtesting**: proyectar a una fecha pasada y medir el error contra lo que de verdad ocurrió.

### El ejemplo

Sobre una serie sintética de caja mensual, el motor se compara con ese método naïf usando *backtesting rolling-origin* (entrenar solo con el pasado de cada punto, prever, comparar con el real). El error se mide con MASE (error escalado por un naïf de referencia). Lo que importa no es un umbral fijo, sino que el MASE del modelo sea menor que el del naïf al mismo horizonte:

| Horizonte | MASE del modelo | MASE del naïf | ¿Bate al naïf? |
|---|---|---|---|
| 1 mes | 0,26 | 1,73 | sí |
| 3 meses | 0,50 | 5,19 | sí |

La cifra no es una promesa: sale de ejecutar el backtesting, y es reproducible con `python probar_todo.py`.

### Cómo funciona

Tres piezas, todas de cálculo determinista (la aritmética siempre da lo mismo, sin depender de ningún modelo de IA):

- **forecast:** previsión del neto mensual por descomposición en tendencia y estacionalidad (*backfitting* iterativo, para que la estacionalidad no se filtre a la tendencia), con amortiguamiento para que la tendencia no extrapole sin freno. Trae su propio backtesting y un naïf de referencia como competidor.
- **ratios:** liquidez y solvencia desde el balance (ratio corriente, prueba ácida, caja, fondo de maniobra, endeudamiento, autonomía financiera). La aritmética es trivial; el trabajo real es el **mapeo al PGC español por prefijo y por signo**: un cliente con saldo acreedor es un anticipo (pasivo), no un cobro pendiente. Autocontrol: si el balance no cierra, no se publican ratios.
- **aging:** antigüedad de cobros y pagos por tramos, DSO/DPO, y un control de honestidad poco habitual: el aging por factura solo es firme si los cobros enlazan a su factura; si no, el veredicto baja a "indicativo" en vez de fingir tramos exactos. Un vencimiento vacío no es "al corriente": es "sin vencimiento".

### Pruébalo

```bash
python probar_todo.py
```

Genera los datos sintéticos y ejecuta las tres demos. No hace falta instalar nada.

### Estructura

```
tesoreria-forecast-ia/
  forecast/    modelo.py (motor puro) + demo.py
  ratios/      motor.py + demo.py
  aging/       motor.py + demo.py
  datos_ejemplo/   datos SINTETICOS + su generador
  caso_real.md     de donde sale esto, con un hallazgo honesto
  probar_todo.py   ejecuta todo de una vez
```

### Datos y privacidad

Todo es sintético y reproducible (semilla fija). No hay ningún dato real ni personal.

### Frontera honesta

El motor **calcula** dato firme. La **lectura de negocio** (¿es sano este nivel de caja?, ¿qué hago?) es criterio, no cálculo, y no está en este repo. Y el forecast tuvo un resultado negativo que se documenta en [caso_real.md](caso_real.md): una idea que parecía buena resultó peor al medirla, y por eso no se usa.

### Repos relacionados

Este repo es la pieza de **tesorería** de una serie sobre construir y evaluar sistemas de IA en los que se puede confiar:

- [tu-primer-asistente-ia-web](https://github.com/jleonceo/tu-primer-asistente-ia-web): qué es un asistente de IA, para quien empieza de cero.
- [llm-eval-contable](https://github.com/jleonceo/llm-eval-contable): evaluar una skill como se examina a un alumno.
- [accounting-agent-swarm](https://github.com/jleonceo/accounting-agent-swarm): el enjambre de agentes contables de principio a fin.
- [orquestacion-enjambres-ia](https://github.com/jleonceo/orquestacion-enjambres-ia): el enrutado multi-agente.
- [gobernanza-skills-analiticas](https://github.com/jleonceo/gobernanza-skills-analiticas): las reglas para gobernar skills.
- [verificacion-determinista-ia](https://github.com/jleonceo/verificacion-determinista-ia): comprobar la coherencia del estado sin IA.
- [agent-memory-governance](https://github.com/jleonceo/agent-memory-governance): que la memoria del agente no se pudra.

---

## English

### What it solves

Recording what already happened is the easy part of accounting. The hard part is looking ahead: will I make it to month-end? can I cover payroll and quarterly VAT? when does cash get tight? This repository shows how to **forecast cash with judgement** and, above all, how to **prove the forecast works** instead of asking you to trust it.

The usual way to forecast cash is the average of the same month in prior years. It works, but it learns neither trend nor seasonality, and it is rarely checked. Here the engine replaces it with a decomposition forecast and puts it through **backtesting**: project to a past date and measure the error against what actually happened.

### The example

On a synthetic monthly cash series, the engine is compared to that naive method using rolling-origin backtesting (train only on each point's past, forecast, compare to actuals). Error is measured with MASE (error scaled by a reference naive). What matters is not a fixed threshold but that the model's MASE is lower than the naive's at the same horizon:

| Horizon | Model MASE | Naive MASE | Beats naive? |
|---|---|---|---|
| 1 month | 0.26 | 1.73 | yes |
| 3 months | 0.50 | 5.19 | yes |

The figure is not a promise: it comes from running the backtest, reproducible with `python probar_todo.py`.

### How it works

Three pieces, all deterministic (the arithmetic always returns the same, with no dependence on any AI model):

- **forecast:** monthly net forecast by decomposition into trend and seasonality (iterative backfitting, so seasonality does not leak into the trend), with damping so the trend does not extrapolate unchecked. It ships its own backtesting and a naive baseline as competitor.
- **ratios:** liquidity and solvency from the balance sheet (current, quick, cash, working capital, leverage, financial autonomy). The arithmetic is trivial; the real work is the **mapping to the Spanish chart of accounts by prefix and sign**: a customer with a credit balance is an advance (a liability), not a receivable. Self-check: if the balance sheet does not tie out, no ratios are published.
- **aging:** receivables/payables aging by bucket, DSO/DPO, and an unusual honesty control: invoice-level aging is only firm if payments link to their invoice; otherwise the verdict drops to "indicative" instead of faking exact buckets. A missing due date is not "current": it is "no due date".

### Try it

```bash
python probar_todo.py
```

It generates the synthetic data and runs the three demos. Nothing to install.

### Data and privacy

Everything is synthetic and reproducible (fixed seed). There is no real or personal data.

### Honest boundary

The engine **computes** firm figures. The **business reading** (is this cash level healthy? what should I do?) is judgement, not calculation, and is not in this repo. And the forecast had a negative result documented in [caso_real.md](caso_real.md): an idea that looked good turned out worse when measured, which is why it is not used.

### Related repositories

This repo is the **treasury** piece of a series on building and evaluating AI systems you can trust:

- [tu-primer-asistente-ia-web](https://github.com/jleonceo/tu-primer-asistente-ia-web): what an AI assistant is, for absolute beginners.
- [llm-eval-contable](https://github.com/jleonceo/llm-eval-contable): evaluating a skill the way you examine a student.
- [accounting-agent-swarm](https://github.com/jleonceo/accounting-agent-swarm): the accounting agent swarm end to end.
- [orquestacion-enjambres-ia](https://github.com/jleonceo/orquestacion-enjambres-ia): multi-agent routing.
- [gobernanza-skills-analiticas](https://github.com/jleonceo/gobernanza-skills-analiticas): the rules for governing skills.
- [verificacion-determinista-ia](https://github.com/jleonceo/verificacion-determinista-ia): checking state coherence without AI.
- [agent-memory-governance](https://github.com/jleonceo/agent-memory-governance): keeping the agent's memory from rotting.

---

*Licencia / License: [MIT](LICENSE). Datos sintéticos, sin información real ni personal. Synthetic data, no real or personal information.*
