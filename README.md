English version: [README.en.md](README.en.md)

# Previsión de tesorería · caja, liquidez y antigüedad de saldos

Prevé la caja de los próximos meses y mide, contra el pasado, cuánto se equivoca esa previsión. Incluye
también los ratios de liquidez del balance y la antigüedad de lo pendiente de cobro y de pago.

**Resultado:** a un mes vista, la previsión se equivoca de media en 4.334 €. El método habitual, la media del
mismo mes en años anteriores, se equivoca en 29.444 €. Son 18 meses previstos sin ver el dato real.

```bash
python probar_todo.py
```

Python estándar, sin nada que instalar, sin base de datos y sin red. Genera los datos de ejemplo y ejecuta las
tres demostraciones en un par de segundos.

## El problema de partida

Muchas empresas prevén la caja de un mes con la media de ese mismo mes en los años anteriores, y casi nunca
comprueban cuánto falla. Si la empresa crece, esa media va por detrás del presente. Las decisiones de compras,
contratación o aplazamientos se toman entonces sobre una cifra con error desconocido.

## Qué hay dentro

1. `forecast/` separa la serie mensual de caja en tendencia y estacionalidad, prevé los meses siguientes y se
   examina contra el pasado: para cada mes ya conocido, prevé usando solo los meses anteriores y anota el
   error.
2. `ratios/` clasifica las cuentas del balance según el Plan General Contable y calcula ratio corriente,
   prueba ácida, ratio de caja, fondo de maniobra, endeudamiento y autonomía financiera. Si el balance no
   cuadra, no publica ratios.
3. `aging/` reparte las facturas abiertas por tramos de antigüedad y calcula el DSO y el DPO, los días medios
   de cobro y de pago.
4. `datos_ejemplo/` contiene 42 meses de caja inventados, un balance y siete facturas, con el programa que los
   genera.

## Lo que sale

- **Previsión, a 1 mes:** error medio de 4.334 € frente a 29.444 € del método habitual, en 18 meses.
- **Previsión, a 3 meses:** 8.374 € frente a 87.797 €, en 16 meses.
- **Últimos seis meses examinados:** la previsión gana en los seis.
- **Balance de ejemplo:** cuadra a 0,00; ratio corriente 1,94 y prueba ácida 1,17.
- **Facturas abiertas:** 40.000 €, de los que 22.000 € están vencidos; DSO de 60,8 días.

Para comparar empresas de distinto tamaño, el error también se da como MASE, que lo divide entre la variación
típica de la propia serie: 0,26 la previsión y 1,73 el método habitual, a un mes. Cuanto más bajo, mejor.

## Límites

- Los datos son sintéticos y se generaron con la misma forma que supone el modelo: una subida constante, el
  mismo patrón cada mes del año y un ruido moderado. Demuestra que el cálculo funciona, no que acierte con una
  empresa real que pierde un cliente o retrasa una obra.
- Buena parte de la ventaja sale de que la serie crece unos 1.500 € al mes y el método habitual no ve ese
  crecimiento. En una empresa estable la diferencia sería menor.
- A 12 meses la previsión empeora mucho: 23.985 € de error medio, aunque sigue por debajo de los 346.619 € del
  método habitual.
- Hacen falta dos años de historia mensual antes de la primera previsión.
- El DSO de ejemplo supone unas ventas anuales de 240.000 € fijadas en el código.
- Las pruebas automáticas comparan la previsión con el método habitual; un fallo que afecte a los dos por igual
  no lo detectan.
- [caso_real.md](caso_real.md) recoge una prueba con datos reales que salió mal: añadir los vencimientos ya
  facturados empeoró la previsión. Esas cifras no se pueden reproducir con los datos de ejemplo.

## Datos

Todo es sintético y sale igual en cada ejecución, con la semilla 20260713. No hay datos reales ni personales.

## Repositorios relacionados

- [analisis-contable](https://github.com/jleonceo/analisis-contable): cuenta de resultados y tesorería de 2024
  con pandas, comprobadas por un segundo camino.
- [control-interno-fraude-ia](https://github.com/jleonceo/control-interno-fraude-ia): pruebas de fraude sobre el
  libro diario.
- [de-datos-en-bruto-a-decisiones](https://github.com/jleonceo/de-datos-en-bruto-a-decisiones): un fichero de
  ventas en bruto convertido en respuestas de negocio y en un cuadro de mando.

---

*Parte del portfolio de [Juan Luis León](https://github.com/jleonceo) · [juanluisleon.vercel.app](https://juanluisleon.vercel.app) · Licencia [MIT](LICENSE)*
