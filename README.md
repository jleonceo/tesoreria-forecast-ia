# tesoreria-forecast-ia

**Prever la caja de una empresa y demostrar con datos que la previsión acierta.**
**Forecasting a company's cash and proving with data that the forecast works.**

Sin dependencias (solo Python estándar), sin base de datos, sin IA, sin red.
No dependencies (standard Python only), no database, no AI, no network.

[Español](#español) · [English](#english)

---

## Español

### El problema

Es día ocho y en la cuenta corriente hay cuarenta mil euros. Las nóminas salen el treinta. De aquí a esa fecha entrarán cobros de clientes. Saldrán también pagos a proveedores, el alquiler y el IVA del trimestre. La pregunta del gerente cabe en una línea: ¿llego?

Casi todo el mundo la contesta igual. Mira lo que entró y salió en ese mismo mes de los años anteriores y saca la media. El método tiene su lógica, porque un agosto se parece bastante a otro agosto. Aun así arrastra dos defectos de nacimiento. El primero es que no ve que la empresa lleva tres años creciendo. El segundo es que nadie ha comprobado nunca si acierta. Del segundo defecto sale el daño de verdad. Cuando la previsión falla por veinte mil euros y nadie lo mide, la empresa decide a quién contrata, qué compra y qué aplaza. Lo decide sobre una cifra que suena a dato y es una corazonada con decimales. Este repositorio enseña a prever la caja partiendo la serie en piezas que se comportan de manera distinta. Sobre todo enseña a examinar esa previsión contra el pasado para saber de cuánto es su error.

### Qué hay dentro

Un repositorio es una carpeta de trabajo publicada en internet con todo su historial de cambios. Este contiene tres motores de cálculo, sus demostraciones, unos datos inventados y el programa que los inventa. Al primero le entregas los cobros y pagos netos de cada mes pasado. Te devuelve la previsión de los meses que vienen. La acompaña de la nota que esa previsión saca en un examen sobre el pasado. Los otros dos miran el presente en vez del futuro. Uno calcula los ratios de liquidez desde el balance. El otro ordena por antigüedad lo que está pendiente de cobro.

Todo son cuentas, sin inteligencia artificial dentro, sin base de datos, sin tocar la red y sin nada que instalar. Usa solo lo que Python trae de serie. Ante la misma entrada devuelve siempre la misma salida. Esa propiedad en la jerga se llama **determinista**. Aquí importa porque una previsión que cambiara de valor entre dos pasadas no se podría defender delante de un banco.

### El ejemplo

Los datos son cuarenta y dos meses de caja inventados por un programa. Van de enero de 2023 a junio de 2026. La semilla es fija, así que salen idénticos en cada ejecución. Cada línea trae el mes y el neto de ese mes. Así se ve una:

```
2026-06,153219.4
```

Sobre esas líneas el motor parte la serie en tendencia y estacionalidad. Proyecta la tendencia hacia delante, le suma el índice del mes que toque y devuelve la cifra. Después vuelve atrás y repite el proceso entero desde cada punto del pasado para poder darse una nota. Al ejecutar la demostración eso es lo que aparece en pantalla:

```
  h=1  MASE modelo=0.255  naif=1.7288  bate_naif=True  (origenes=18)
  h=3  MASE modelo=0.4955  naif=5.1899  bate_naif=True  (origenes=16)
```

Ese examen se puede leer en euros. A un mes de horizonte el error medio del motor es de 4.334,19 euros. El del método de la media es de 29.443,86 euros. Son dieciocho exámenes corregidos a un mes de distancia y dieciséis a tres meses. Todos ellos sobre meses que el programa no había visto cuando escribió su cifra.

| Horizonte | Error del motor (MASE) | Error del método habitual (MASE) | ¿Gana el motor? |
|---|---|---|---|
| 1 mes | 0,255 | 1,7288 | sí |
| 3 meses | 0,4955 | 5,1899 | sí |
| 12 meses | 1,4504 | 20,783 | sí |

### Los conceptos

**Descomponer** una serie consiste en partirla en piezas que se comportan de manera distinta. Cada una se predice por separado y al final se suman. Aquí las piezas son tres. La **tendencia** es hacia dónde va el nivel a largo plazo. En estos datos sube alrededor de mil quinientos euros al mes. La **estacionalidad** es lo que cada mes del calendario se aparta de ese nivel por costumbre del negocio. Siempre en el mismo sentido, con agosto por debajo y noviembre por encima. Lo que queda después de quitar las dos es **ruido**, que no se predice porque carece de forma.

Las dos primeras se estiman a la vez, alternando entre ellas hasta que dejan de moverse. La técnica en la jerga se llama **backfitting** iterativo. Tanto cuidado tiene su razón. Si calculas la tendencia sin descontar antes el vaivén de los meses, un verano flojo se cuela dentro de ella. Acabas prediciendo un declive inexistente. El **método ingenuo** es el del apartado anterior: la media de ese mismo mes en los años anteriores. La literatura lo llama *naïf*. Está programado dentro del repositorio tal cual se usa en las empresas, sin caricaturizarlo para que pierda. Ganarle a un rival de paja no demuestra nada.

**Backtesting** es probar la previsión contra un pasado que ya se conoce. En esa idea se apoya todo lo demás. Suena a examen con las respuestas delante, así que lo que importa es cómo se tapan. Para juzgar la previsión de mayo de 2025, al programa solo se le deja leer lo anterior a mayo de 2025. Entrega su cifra, se destapa el mes real y se anota la diferencia en euros. Después se avanza un mes y se repite el ejercicio con el siguiente. Esa forma de mover el punto de corte recibe el nombre de **rolling-origin**. Lo que se gana con eso es tiempo. Para corregir una previsión sobre el mes que viene hay que esperar treinta días. Sobre tres años de historia hay hoy mismo dieciocho exámenes corregidos.

Los errores salen en euros. Cinco mil euros de fallo significan una cosa en una empresa que mueve veinte mil al mes. En una que mueve dos millones significan otra. Para poder compararlos se divide el error entre una vara de medir sacada de la propia serie. El resultado se llama **MASE**. Cuanto más bajo, mejor. El listón está escrito dentro del código. La previsión vale si su MASE queda por debajo del que saca el método ingenuo al mismo horizonte. Bajar de un número redondo elegido a conveniencia no cuenta como aprobado.

### Los otros dos motores

El de **ratios** reparte cada cuenta del balance en su masa y calcula liquidez y solvencia. Son el ratio corriente, la prueba ácida y el ratio de caja. También el fondo de maniobra, el endeudamiento y la autonomía financiera. La aritmética es trivial. El trabajo real está en el reparto. Se hace por el prefijo de la cuenta en el plan contable español y por el signo del saldo. La cuenta `43000011` es de clientes y tiene saldo de menos trece mil novecientos cuarenta y cinco euros. Esa señal dice que el cliente pagó por adelantado. La empresa le debe una entrega en vez de tener con él un cobro pendiente.

Si el balance no cuadra, el programa se niega a publicar ratios.

El de **aging** ordena por antigüedad lo que está pendiente de cobro y de pago. Lo reparte en tramos: lo que aún no ha vencido, lo vencido hace menos de un mes, entre uno y dos meses. Así hasta el cajón de lo que lleva más de ciento veinte días. Calcula además el **DSO** y el **DPO**. Son los días medios que se tarda en cobrar a los clientes y en pagar a los proveedores. Hay un cajón que casi nadie pone. Una factura sin fecha de vencimiento apuntada va a `SIN_VENCIMIENTO`. Desconocer cuándo vence algo es cosa distinta de saber que aún no vence. Y el veredicto del reparto baja a la categoría de indicativo cuando los cobros no enlazan con su factura. No se fingen tramos exactos.

### Qué está medido

Cifras obtenidas ejecutando el repositorio el 22/07/2026 con Python 3.14.6:

| Comprobación | Resultado |
|---|---|
| `probar_todo.py` | los tres programas de muestra en verde, sin instalar nada |
| Serie generada | 42 meses, de enero de 2023 a junio de 2026, semilla 20260713 |
| Previsión a 1 mes, 18 exámenes | MASE 0,255 del motor contra 1,7288 del método ingenuo |
| Previsión a 3 meses, 16 exámenes | MASE 0,4955 contra 5,1899 |
| Error medio a 1 mes, en euros | 4.334,19 del motor contra 29.443,86 del método ingenuo |
| Últimos seis exámenes | el motor gana los seis |
| Balance | cuadra a 0,00; ratio corriente 1,935 y prueba ácida 1,1749 |
| Aging | 7 facturas, 40.000,00 abiertos, 22.000,00 vencidos, DSO 60,8 días |

### Lo que no sale tan bien como parece

Conviene empezar por la victoria, que resulta más pequeña de lo que aparenta.

El método ingenuo pierde por veintinueve mil euros de media. La diferencia tiene una causa medible. Al promediar el mismo mes de años anteriores, sus datos están veinte meses por detrás del presente. A mil quinientos euros de crecimiento mensual eso son treinta mil euros de retraso estructural. Entre 29.443,86 y esos treinta mil no queda mucho margen para otra explicación. El motor gana sobre todo porque el rival no puede ver una subida. Estos datos la llevan sembrada desde el origen.

La segunda cosa la reconoce el propio repositorio en el fichero que gobierna sus pruebas automáticas. Allí queda escrito que una auditoría interna encontró que la suite no detecta ciertos fallos. Se comprueba estropeando el código a propósito. La técnica se llama prueba de mutación y consiste en meter un error conocido para ver si alguna comprobación se pone roja. Al sustituir por un uno fijo la vara de medir del MASE, las cifras se disparan a 4.334 y 29.443. El veredicto no deja de salir verde. Al dejar que el examen mire los meses que tenía que adivinar, ocurre lo mismo. La causa es idéntica en los dos casos. El veredicto compara el motor con el método ingenuo, así que todo aquello que afecte a los dos por igual pasa desapercibido.

La tercera nació en este mismo README. Hasta hoy prometía amortiguar la tendencia para que no se dispare al alejarse el horizonte. Ese freno existe programado en `forecast/modelo.py`, con un factor que multiplica el avance de la tendencia en cada paso hacia delante. Viene fijado en 1,0, valor que lo deja inactivo. Ni la demostración ni `probar_todo.py` pasan otro valor, de manera que el repositorio nunca ha amortiguado nada. Al activarlo con 0,9 la previsión a tres meses empeora de 0,4955 a 0,5168. La de doce meses pasa de 1,4504 a 3,7361. La frase que aquí se prometía describía una pieza apagada que además empeoraría el resultado.

La cuarta no la enseña el repositorio en ningún sitio. Estirando el horizonte a doce meses, el MASE del motor sube a 1,4504, casi seis veces peor que a un mes. El método ingenuo a esa distancia se va hasta 20,783.

### Cuándo no sirve

El límite mayor está en los datos, y el propio generador lo deja a la vista. La serie se fabrica sumando una subida recta, unos índices de mes fijos y un ruido moderado. Esa es exactamente la receta que el modelo supone. Medir así demuestra que la maquinaria funciona cuando la realidad se porta. No dice nada de un año con un cliente que se marcha o una obra que se retrasa.

Hacen falta además dos años de historia mensual antes de la primera previsión. Buena parte de las empresas pequeñas no los tienen apuntados con esa limpieza.

Del lado del aging conviene mirar la letra pequeña. Dos parejas de cifras escritas a mano dentro del código enseñan cómo funciona el control que decide si los tramos son de fiar. El DSO de sesenta coma ocho días sale de suponer doscientos cuarenta mil euros de ventas anuales, escritos también a mano. Ilustran el mecanismo sin medir esta cartera. El repositorio guarda por último un resultado negativo propio en [caso_real.md](caso_real.md). Se probó a meter en la previsión los vencimientos ya facturados, que parecen dato firme. La medición dijo que empeoraba. Las cifras que allí se citan salieron de la contabilidad del sistema del que nace este repositorio. No se pueden reproducir con estos datos inventados.

### Pruébalo

```bash
python probar_todo.py
```

Genera los datos sintéticos y ejecuta las tres demostraciones en un par de segundos. No hace falta instalar nada.

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

Todo es sintético y reproducible con semilla fija. No hay ningún dato real ni personal.

### Frontera honesta

El motor calcula dato firme. La lectura de negocio es otra cosa: si ese nivel de caja es sano y qué conviene hacer con él. Eso corresponde al criterio de una persona y queda fuera de este repositorio.

### Repos relacionados

Este repo es la pieza de **tesorería** de una serie sobre construir y evaluar sistemas de IA en los que se puede confiar:

- [tu-primer-asistente-ia-web](https://github.com/jleonceo/tu-primer-asistente-ia-web): qué es un asistente de IA, para quien empieza de cero.
- [llm-eval-contable](https://github.com/jleonceo/llm-eval-contable): evaluar una skill como se examina a un alumno.
- [accounting-agent-swarm](https://github.com/jleonceo/accounting-agent-swarm): el enjambre de agentes contables de principio a fin.
- [control-interno-fraude-ia](https://github.com/jleonceo/control-interno-fraude-ia): buscar fraude en el libro contable con pura aritmética.
- [orquestacion-enjambres-ia](https://github.com/jleonceo/orquestacion-enjambres-ia): el enrutado multi-agente.
- [gobernanza-skills-analiticas](https://github.com/jleonceo/gobernanza-skills-analiticas): las reglas para gobernar skills.
- [verificacion-determinista-ia](https://github.com/jleonceo/verificacion-determinista-ia): comprobar la coherencia del estado sin IA.
- [agent-memory-governance](https://github.com/jleonceo/agent-memory-governance): que la memoria del agente no se pudra.

---

## English

### The problem

It is the eighth of the month and there are forty thousand euros in the current account. Payroll goes out on the thirtieth. Between now and then customer payments will come in. Supplier payments, rent and the quarterly VAT go out. The manager's question fits in one line: will I make it?

Almost everyone answers it the same way. They look at what came in and went out that same month in previous years and take the average. The method has its logic, because one August resembles another August fairly well. Even so it carries two birth defects. The first is that it cannot see the company has been growing for three years. The second is that nobody has ever checked whether it is right. The real damage comes from that second defect. When the forecast is off by twenty thousand euros and nobody measures it, the company decides who to hire, what to buy and what to postpone. It decides on a figure that sounds like data and is a hunch with decimals. This repository shows how to forecast cash by splitting the series into pieces that behave differently. Above all it shows how to examine that forecast against the past to learn the size of its error.

### What is inside

A repository is a working folder published on the internet together with its full history of changes. This one holds three calculation engines, their demonstrations, some invented data and the program that invents it. You hand the first engine the net collections and payments of every past month. It returns the forecast for the months ahead. With it comes the mark that forecast earned in an examination on the past. The other two look at the present instead of the future. One computes liquidity ratios from the balance sheet. The other sorts by age whatever is still awaiting collection.

It is all arithmetic, with no artificial intelligence inside, no database, no network access and nothing to install. It uses only what Python ships with. Given the same input it always returns the same output. That property is known in the jargon as **deterministic**. It matters here because a forecast changing value between two runs could not be defended in front of a bank.

### The example

The data is forty-two months of cash invented by a program. It goes from January 2023 to June 2026. The seed is fixed, so it comes out identical on every run. Each line carries the month and the net figure for that month. This is what one looks like:

```
2026-06,153219.4
```

Over those lines the engine splits the series into trend and seasonality. It projects the trend forward, adds the index of the relevant month and returns the figure. It then goes back and repeats the whole process from every point in the past so it can give itself a mark. When the demonstration is executed, this is what appears on screen:

```
  h=1  MASE modelo=0.255  naif=1.7288  bate_naif=True  (origenes=18)
  h=3  MASE modelo=0.4955  naif=5.1899  bate_naif=True  (origenes=16)
```

That examination can be read in euros. At one month of horizon the engine's mean error is 4,334.19 euros. The averaging method's is 29,443.86 euros. That is eighteen corrected examinations at one month of distance and sixteen at three months. All of them on months the program had not seen when it wrote its figure.

| Horizon | Engine error (MASE) | Usual method error (MASE) | Does the engine win? |
|---|---|---|---|
| 1 month | 0.255 | 1.7288 | yes |
| 3 months | 0.4955 | 5.1899 | yes |
| 12 months | 1.4504 | 20.783 | yes |

### The concepts

To **decompose** a series means splitting it into pieces that behave differently. Each one is predicted separately and they are added up at the end. Here there are three pieces. The **trend** is where the level is heading in the long run. In this data it climbs by around one thousand five hundred euros a month. **Seasonality** is how much each calendar month departs from that level out of business habit. Always in the same direction, with August below and November above. What is left after removing both is **noise**, which cannot be predicted because it has no shape.

The first two are estimated at the same time, alternating between them until they stop moving. The technique is known in the jargon as iterative **backfitting**. So much care has its reason. If you compute the trend without first discounting the monthly swing, a weak summer creeps inside it. You end up predicting a decline that does not exist. The **naive method** is the one from the first section: the average of that same month in previous years. The literature calls it *naïf*. It is programmed inside the repository exactly as companies use it, without being caricatured so that it loses. Beating a straw rival demonstrates nothing.

**Backtesting** means testing the forecast against a past you already know. Everything else here rests on that idea. It sounds like an examination with the answers in plain sight, so what matters is how they are covered up. To judge the forecast for May 2025, the program is only allowed to read what came before May 2025. It delivers its figure, the real month is uncovered and the difference in euros is recorded. The cut-off then advances one month and the exercise is repeated with the next one. That way of moving the cut-off goes by the name of **rolling-origin**. What this buys is time. Correcting a forecast about next month takes thirty days of waiting. Three years of history offer eighteen corrected examinations today.

The errors come out in euros. Five thousand euros of error mean one thing in a company that moves twenty thousand a month. In one that moves two million they mean another. To make them comparable, the error is divided by a yardstick taken from the series itself. The result is called **MASE**. The lower, the better. The bar is written inside the code. The forecast is valid when its MASE falls below the naive method's at the same horizon. Dropping below a round number chosen for convenience does not count as a pass.

### The other two engines

The **ratios** engine assigns every balance-sheet account to its block and computes liquidity and solvency. Those are current ratio, quick ratio and cash ratio. Also working capital, leverage and financial autonomy. The arithmetic is trivial. The real work sits in the assignment. It is done by the account prefix in the Spanish chart of accounts and by the sign of the balance. Account `43000011` is a customer account holding a balance of minus thirteen thousand nine hundred and forty-five euros. That sign says this customer paid in advance. The company owes them a delivery rather than holding a receivable.

If the balance sheet does not tie out, the program refuses to publish ratios.

The **aging** engine sorts by age whatever is awaiting collection and payment. It spreads them across buckets: not yet due, overdue by less than a month, between one and two months. And so on up to the drawer holding anything past one hundred and twenty days. It also computes **DSO** and **DPO**. Those are the average number of days taken to collect from customers and to pay suppliers. There is one drawer almost nobody adds. An invoice with no due date recorded goes to `SIN_VENCIMIENTO`. Not knowing when something falls due is a different matter from knowing it is not due yet. And the verdict on the buckets drops to the indicative category when payments do not link to their invoice. Exact buckets are not faked.

### What has been measured

Figures obtained by executing the repository on 22/07/2026 with Python 3.14.6:

| Check | Result |
|---|---|
| `probar_todo.py` | the three sample programs green, with nothing to install |
| Generated series | 42 months, January 2023 to June 2026, seed 20260713 |
| One-month forecast, 18 examinations | MASE 0.255 for the engine against 1.7288 for the naive method |
| Three-month forecast, 16 examinations | MASE 0.4955 against 5.1899 |
| Mean one-month error, in euros | 4,334.19 for the engine against 29,443.86 for the naive method |
| Last six examinations | the engine wins all six |
| Balance sheet | ties out to 0.00; current ratio 1.935 and quick ratio 1.1749 |
| Aging | 7 invoices, 40,000.00 open, 22,000.00 overdue, DSO 60.8 days |

### What does not hold up as well as it looks

It is worth starting with the victory, which turns out smaller than it appears.

The naive method loses by twenty-nine thousand euros on average. The gap has a measurable cause. By averaging the same month of previous years, its data sits twenty months behind the present. At one thousand five hundred euros of monthly growth that amounts to thirty thousand euros of structural lag. Between 29,443.86 and those thirty thousand there is little room left for another explanation. The engine wins mostly because its rival cannot see a climb. This data has carried it since its origin.

The second point is admitted by the repository itself in the file that governs its automated tests. It is written there that an internal audit found the suite fails to detect certain faults. This is checked by damaging the code on purpose. The technique is called mutation testing and consists of injecting a known error to see whether any check turns red. Replacing the MASE yardstick with a fixed one sends the figures up to 4,334 and 29,443. The verdict keeps coming out green. Letting the examination look at the months it was supposed to guess produces the same outcome. The cause is identical in both cases. The verdict compares the engine against the naive method, so anything that affects both equally goes unnoticed.

The third point was born in this very README. Until today it promised to damp the trend so it would not run away as the horizon lengthens. That brake does exist in `forecast/modelo.py`, as a factor multiplying the trend advance at each step forward. The factor ships set to 1.0, a value that leaves it inactive. Neither the demonstration nor `probar_todo.py` passes any other value, so the repository has never damped anything. Turning it on at 0.9 worsens the three-month forecast from 0.4955 to 0.5168. The twelve-month one goes from 1.4504 to 3.7361. The sentence promised here described a part that was switched off and would also make the result worse.

The fourth point is shown nowhere in the repository. Stretching the horizon to twelve months, the engine's MASE climbs to 1.4504, almost six times worse than at one month. The naive method at that distance goes all the way to 20.783.

### When it does not work

The biggest limit sits in the data, and the generator itself leaves it in plain view. The series is built by adding a straight climb, some fixed monthly indices and moderate noise. That is exactly the recipe the model assumes. Measuring this way demonstrates that the machinery works when reality behaves. It says nothing about a year with a customer who leaves or a project that slips.

Two years of monthly history are also required before the first forecast. A good share of small companies do not have them recorded that cleanly.

On the aging side the small print is worth reading. Two pairs of figures hard-coded inside the program show how the control that decides whether the buckets are trustworthy behaves. The DSO of sixty point eight days comes from assuming two hundred and forty thousand euros of annual sales, also hard-coded. They illustrate the mechanism without measuring this portfolio. The repository lastly keeps a negative result of its own in [caso_real.md](caso_real.md). Feeding the already invoiced due dates into the forecast was tried, since they look like firm data. The measurement said it made things worse. The figures quoted there came from the accounting of the system this repository grew out of. They cannot be reproduced with this invented data.

### Try it

```bash
python probar_todo.py
```

It generates the synthetic data and runs the three demonstrations in a couple of seconds. Nothing to install.

### Structure

```
tesoreria-forecast-ia/
  forecast/    modelo.py (pure engine) + demo.py
  ratios/      motor.py + demo.py
  aging/       motor.py + demo.py
  datos_ejemplo/   SYNTHETIC data + its generator
  caso_real.md     where this comes from, with an honest finding
  probar_todo.py   runs everything at once
```

### Data and privacy

Everything is synthetic and reproducible with a fixed seed. There is no real or personal data.

### Honest boundary

The engine computes firm figures. The business reading is another matter: whether this cash level is healthy and what should be done about it. That belongs to a person's judgement and stays outside this repository.

### Related repositories

This repo is the **treasury** piece of a series on building and evaluating AI systems you can trust:

- [tu-primer-asistente-ia-web](https://github.com/jleonceo/tu-primer-asistente-ia-web): what an AI assistant is, for absolute beginners.
- [llm-eval-contable](https://github.com/jleonceo/llm-eval-contable): evaluating a skill the way you examine a student.
- [accounting-agent-swarm](https://github.com/jleonceo/accounting-agent-swarm): the accounting agent swarm end to end.
- [control-interno-fraude-ia](https://github.com/jleonceo/control-interno-fraude-ia): hunting fraud in the ledger with pure arithmetic.
- [orquestacion-enjambres-ia](https://github.com/jleonceo/orquestacion-enjambres-ia): multi-agent routing.
- [gobernanza-skills-analiticas](https://github.com/jleonceo/gobernanza-skills-analiticas): the rules for governing skills.
- [verificacion-determinista-ia](https://github.com/jleonceo/verificacion-determinista-ia): checking state coherence without AI.
- [agent-memory-governance](https://github.com/jleonceo/agent-memory-governance): keeping the agent's memory from rotting.

---

*Licencia / License: [MIT](LICENSE). Datos sintéticos, sin información real ni personal. Synthetic data, no real or personal information.*
