# Estrategia inicial de paper trading

**Version:** v0.1.0-draft
**Estado:** borrador pendiente de revision
**Tipo:** experimento educativo y de simulacion; no constituye recomendacion financiera.

## 1. Alcance inicial

La primera evaluacion sera deliberadamente pequena:

- Mercado: ETFs de Estados Unidos.
- Activos: `SPY`, `QQQ` e `IWM`.
- Posiciones: solo largas; no se permiten ventas en corto.
- Capital virtual inicial: USD 500.
- Datos: velas de 1 hora.
- Analisis: cuatro veces por dia durante la sesion regular de Estados Unidos.
- Zona horaria: `America/New_York`.
- Moneda: USD.
- Modelo de IA: fuera de la estrategia base; se evaluara despues.

Los tres simbolos son un universo inicial de trabajo, no una recomendacion de inversion.
No se agregaran criptomonedas hasta terminar y evaluar este experimento.

## 2. Horario de analisis

Las ejecuciones iniciales se programaran a las siguientes horas de Nueva York:

```text
10:00, 12:00, 14:00, 15:30
```

Cada ejecucion usara exclusivamente velas cerradas. La vela que este formandose no
participara en la decision. Si el mercado esta cerrado o no existe una vela valida,
no se genera ninguna orden.

El sistema guardara siempre el timestamp en UTC y la zona horaria original.

## 3. Indicadores

Los indicadores se calcularan independientemente para cada simbolo:

- `EMA20`: media movil exponencial de 20 velas.
- `EMA50`: media movil exponencial de 50 velas.
- `RSI14`: indice de fuerza relativa de 14 velas.
- `ATR14`: Average True Range de 14 velas.
- `ATR_pct`: `ATR14 / close`.

No se generaran senales hasta disponer de al menos 50 velas cerradas validas.

## 4. Senales cuantitativas

La estrategia base se llama `quant_only_v0.1.0`.

### 4.1 BUY

Se genera `BUY` cuando se cumplen todas estas condiciones:

1. `EMA20 > EMA50`.
2. `close > EMA20`.
3. `RSI14 >= 50` y `RSI14 <= 70`.
4. `ATR_pct <= 0.05`.
5. No existe ya una posicion abierta para el simbolo.
6. El Risk Manager permite abrir la posicion.

La orden se ejecuta al precio de apertura de la siguiente vela disponible, aplicando
slippage y comision.

### 4.2 SELL

Se genera `SELL` para una posicion abierta cuando se cumple al menos una de estas
condiciones:

1. `EMA20 < EMA50`.
2. `close < EMA20`.
3. `RSI14 < 40`.
4. Se alcanza el stop loss definido por el Risk Manager.

La orden se ejecuta al precio de apertura de la siguiente vela disponible, excepto el
stop loss, que se tratara segun las reglas de ejecucion del backtester cuando una vela
lo atraviese.

Convencion inicial del backtester para stops: si la apertura esta por debajo del stop,
se ejecuta en la apertura; si no, se ejecuta en el precio del stop. En ambos casos se
aplica el slippage de venta. Esta convencion es conservadora y se mantendra constante
durante la comparacion.

### 4.3 HOLD

Se genera `HOLD` en cualquier otro caso. `HOLD` no abre ni cierra posiciones.

## 5. Reglas de riesgo

El Risk Manager se aplica antes de cada orden.

- Capital inicial: USD 500.
- Perdida maxima teorica por operacion: 1% del capital inicial, USD 5.
- Exposicion maxima por posicion: 20% del valor de cartera, inicialmente USD 100.
- Numero maximo de posiciones simultaneas: 2.
- Exposicion maxima total: 40% del valor de cartera.
- Exposicion maxima por simbolo: una posicion.
- No usar apalancamiento.
- No usar margen.
- No abrir una posicion si el cash disponible no cubre el coste total.
- No abrir una nueva posicion si el drawdown de cartera alcanza 15% desde el maximo
  historico; el sistema queda en `HOLD` hasta revision manual.

### 5.1 Tamano de posicion

El riesgo monetario por operacion se calcula como:

```text
risk_budget = min(USD 5, 1% del capital inicial)
stop_distance = 2 * ATR14
quantity_by_risk = risk_budget / stop_distance
quantity_by_exposure = max_position_value / entry_price
quantity = min(quantity_by_risk, quantity_by_exposure)
```

La cantidad se redondeara hacia abajo a 3 decimales. Si la cantidad resultante es menor
que 0.001, la operacion se rechaza.

El stop inicial de una compra sera:

```text
stop_price = entry_price - (2 * ATR14)
```

No se usara trailing stop en esta primera version.

## 6. Costes de simulacion

Mientras no exista una calibracion mejor, se usaran estos valores explicitos:

- Comision: 0.10% del valor bruto de cada compra o venta.
- Slippage: 0.05% desfavorable respecto al precio de ejecucion.
- Impuestos, dividendos y ajustes corporativos: fuera del primer experimento y deben
  documentarse si el proveedor los incluye.

Estos valores son supuestos de simulacion, no una estimacion universal de costes reales.
Se mantendran constantes durante una comparacion para evitar sesgos.

El `PaperBroker` actual aplica estos costes a compras y ventas aceptadas y registra las
operaciones rechazadas. El broker no activa stops automaticamente a partir de una vela;
esa convencion pertenece al backtester y debe definirse antes de congelar la estrategia.

## 7. Datos y prevencion de data leakage

- Solo se usaran velas cerradas antes del timestamp de la decision.
- Los indicadores se calcularan usando la historia disponible hasta esa vela.
- La senal se generara al cierre de la vela de analisis.
- La entrada normal sera en la apertura de la siguiente vela.
- Los periodos de desarrollo, validacion y prueba fuera de muestra seran distintos.
- Los parametros no se optimizaran usando el periodo fuera de muestra.
- Se registraran proveedor, descarga, timezone, timestamps y version del dataset.
- Datos faltantes, duplicados o desordenados invalidan la ejecucion hasta ser revisados.

## 8. Modos de experimento

### `quant_only`

Usa unicamente las reglas de este documento. Es la referencia principal.

### `quant_plus_ai`

Se incorporara despues de validar `quant_only`. Qwen recibira indicadores y contexto
estructurado, pero no podra saltarse los limites del Risk Manager.

Regla inicial de combinacion:

- `QuantEngine = BUY` y `AI = BUY`: se puede evaluar la compra.
- Cualquier conflicto: `HOLD`.
- `QuantEngine = SELL`: se mantiene `SELL` independientemente de la IA.
- Respuesta invalida, timeout o error de Qwen: `HOLD` y registro del error.

La IA no podra crear una orden directamente.

Las senales historicas producidas por `QuantEngine` son candidatos tecnicos. No son
operaciones: la posicion abierta, el Risk Manager, los costes y la ejecucion pertenecen
al Paper Broker y al backtester.

## 9. Referencias de comparacion

Cada backtest debe comparar como minimo:

1. `quant_only_v0.1.0`.
2. `Buy & Hold` del mismo universo y periodo.
3. Una estrategia de referencia simple, por ejemplo comprar y mantener una ponderacion
   equitativa de los tres ETFs.

Todas las referencias deben usar el mismo capital inicial, periodo, costes y convencion
de ejecucion siempre que sea aplicable.

## 10. Metricas de evaluacion

Se reportaran:

- Retorno total.
- Retorno anualizado si el periodo lo permite.
- Maximo drawdown.
- Sharpe Ratio, indicando la tasa libre de riesgo asumida.
- Win rate.
- Profit factor.
- Numero de operaciones.
- Ganancia o perdida media por operacion.
- Comisiones y slippage acumulados.
- Tiempo invertido y exposicion maxima.

No se aceptara una estrategia como mejor por una sola metrica. La evaluacion debe
considerar el periodo fuera de muestra y la estabilidad entre regimenes de mercado.

## 11. Fuente de datos confirmada

La primera descarga se realizo correctamente con `yfinance` 0.2.66:

- Intervalo: 1 hora.
- Periodo solicitado: 60 dias.
- Resultado: 420 velas por simbolo para `SPY`, `QQQ` e `IWM`.
- Rango observado: 2026-06-17 a 2026-09-11.
- Almacenamiento: `data/raw/{SYMBOL}_1h.csv`.
- Timestamps almacenados en UTC.

Este dataset es suficiente para validar el pipeline y los indicadores, pero no para
concluir que la estrategia funciona en distintos regimenes de mercado. `yfinance` limita
el historico intradia disponible, por lo que los resultados se trataran como una prueba
tecnica inicial y no como evidencia de rentabilidad.

## 12. Resultado tecnico inicial

La primera corrida reproducible se guardo en `reports/` con la estrategia
`quant_only_v0.1.0` sobre los 420 registros horarios disponibles por simbolo:

```text
Estrategia:    USD 489.72 (-2.06%)
Buy & Hold:    USD 495.45 (-0.91%)
Max drawdown:  -2.33% estrategia, -5.60% Buy & Hold
Trades:        21 cierres, 42 operaciones aceptadas
Costes:        USD 4.15
```

Este resultado solo confirma que el pipeline es ejecutable y reproducible. No permite
validar rentabilidad porque el periodo es corto y aun no esta separado en desarrollo,
validacion y prueba fuera de muestra.

La division provisional 50%/25%/25% produjo estos resultados:

```text
Periodo          Estrategia       Buy & Hold
Desarrollo       -1.10%           -2.91%
Validacion       -0.03%           +2.03%
Fuera de muestra -0.94%           -1.47%
```

La estrategia no supera al benchmark en validacion y solo lo supera ligeramente en la
prueba fuera de muestra. No se modificaran parametros usando estos resultados; primero
se necesita mas historial o una fuente intradia con mayor cobertura.

## 13. Plan de paper trading en tiempo real

La recopilacion operativa comenzara el 14 de septiembre de 2026 y tendra una duracion
objetivo de seis meses. El sistema seguira ejecutando `quant_only_v0.1.0` sin cambios
durante ese periodo para evitar optimizacion continua sobre resultados recientes.

La semana del 14 al 18 de septiembre servira para validar la infraestructura: scheduler,
descarga, timestamps, señales y logs. No se considera suficiente para evaluar rentabilidad.

Las revisiones seran:

- Semanales: errores, datos faltantes, ejecuciones y calidad de logs.
- Al mes: primera revision formal.
- A los tres meses: revision intermedia.
- A los seis meses: evaluacion principal contra `Buy & Hold`.

Backtesting historico y walk-forward pueden ejecutarse en paralelo, pero no se cambiaran
los parametros de la estrategia usando el periodo fuera de muestra ni el paper trading
reciente. Qwen permanecera fuera de la estrategia principal hasta cerrar esta evaluacion.

## 14. Decisiones pendientes antes de congelar `v0.1.0`

Estas decisiones deben confirmarse antes de congelar `v0.1.0`:

- Confirmar si se acepta el limite intradia de `yfinance` para la primera prueba.
- Disponibilidad real de velas de 1 hora para todo el periodo elegido.
- Tratamiento de dividendos y splits.
- Periodos exactos de desarrollo, validacion y prueba.
- Confirmar la convencion de stop documentada para `v0.1.0`.
- Si se permiten fracciones de ETF en el Paper Broker.

Hasta confirmar estas decisiones, este documento sigue siendo un borrador y no debe
usarse como especificacion definitiva de implementacion.
