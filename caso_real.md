# De dónde sale esto (y un hallazgo honesto)

Este repo nace de un sistema en uso real: la contabilidad de una empresa **ficticia** (TechAcces SL) con ~17.000 líneas de diario, sobre la que desarrollo enjambres de agentes de IA con evaluación continua. El dinero no es real; el problema, sí.

Lo que había para prever la caja era una vista de manual: la media del mismo mes de otros años. Funciona, pero no aprende ni tendencia ni estacionalidad. Nadie había medido si acertaba. Este motor la sustituye por una previsión por descomposición y la somete a backtesting: proyectar a una fecha pasada y medir el error contra lo que ocurrió de verdad.

## El hallazgo honesto

La primera intuición fue mezclar en la previsión el **calendario comprometido** de la cartera: los vencimientos ya facturados parecen dato firme y deberían ayudar. Se backtesteó ese híbrido con reconstrucción rigurosa. Salió **mucho peor** que el modelo estadístico puro: MASE 2,82 frente a 1,06 a un mes.

La causa: en los datos, el cobro no está atado al vencimiento, así que el "comercial comprometido idealizado" y el comercial real tenían signos opuestos en varios meses. La señal se anulaba.

La decisión: el calendario comprometido **no** entra en la previsión del neto (manda el estadístico). Sí se usa para el calendario contractual, que es lo que representa. Se documentó el resultado negativo para no recablearlo a ciegas más adelante. En datos donde el pago sí ronde el vencimiento, esa capa ayudaría. Aquí no. Decirlo es parte del trabajo.

## Lo que esto enseña

Una previsión sin backtesting es una opinión con decimales. Aquí no hay un "cuadre" contra el que puntear como en la contabilidad, así que el backtesting es lo que separa un forecast defendible de una caja negra. Y a veces la medida dice que tu idea buena era peor: eso también se publica.
