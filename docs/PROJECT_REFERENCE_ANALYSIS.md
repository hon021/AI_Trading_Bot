# Analisis de referencias opensource para el diseño futuro

Este documento recoge la comparacion de tres proyectos de referencia. Sus copias locales no se publican en este repositorio; se enlazan las fuentes originales:

- [Backtrader](https://github.com/mementum/backtrader)
- [Freqtrade](https://github.com/freqtrade/freqtrade)
- [Qlib](https://github.com/microsoft/qlib)

La intencion no es copiar sus implementaciones, sino extraer lecciones de arquitectura, validacion y flujo operativo para la proxima version del proyecto.

---

## 1. Conclusion general

El proyecto actual ya tiene una base solida para un laboratorio cuantitativo local:

- ingest de datos
- calculo de indicadores
- motor cuantitativo determinista
- gestion de riesgo
- paper broker
- backtesting reproducible
- scheduler local
- API para lectura de datos

La principal diferencia respecto a repositorios maduros es que aun falta una capa formal de trazabilidad, calidad de datos y registro de ejecucion por corrida. Eso es lo que hace que un proyecto pase de ser un prototipo funcional a un sistema de investigacion con evidencia reproducible.

---

## 2. Lecciones de cada referencia

### 2.1 Backtrader

Referencia principal para flujo de estrategia + backtesting.

Lo mas valioso:

- separa claramente estrategia, datos y ordenes
- modela posiciones, ejecucion y eventos de mercado de forma clara
- enfatiza la reproducibilidad del backtest
- ayuda a pensar en indicadores y execution logic como piezas discretas

Leccion para este proyecto:

- mantener el `QuantEngine` separado de la logica de ejecucion
- definir claramente el ciclo de una orden desde signal hasta trade
- formalizar la diferencia entre `signal`, `decision` y `trade`

### 2.2 Freqtrade

Referencia principal para bot operativo con validacion de riesgo y ejecucion automatizada.

Lo mas valioso:

- dry-run y persistence real
- gestion de riesgo y control de posicion
- estrategia con logs y metricas de performance
- enfoque pragmatico para un sistema que corre periodicamente

Leccion para este proyecto:

- requerir un `run_id` por ciclo
- guardar resultados por ejecucion, no solo el ultimo estado global
- separar claramente `signal generation`, `risk validation`, `trade execution` y `performance summary`
- mantener una base persistente de trades y resultados para comparacion historica

### 2.3 Qlib

Referencia principal para investigacion cuantitativa y flujo de validacion cientifica.

Lo mas valioso:

- pipeline completo de datos, modelado y backtesting
- enfoque en validacion, comparacion y reproduccion
- infraestructura de research con metricas y workflow
- gran enfasis en evitar data leakage y mantener experimentos comparables

Leccion para este proyecto:

- definir experimentos con dataset, version de estrategia, fechas y parametros
- separar periodos de entrenamiento, validacion y test fuera de muestra
- mantener comparacion sistematica contra `Buy & Hold`
- guardar metadata del dataset y la configuracion en cada ejecucion

---

## 3. Gap actual del proyecto

El proyecto ya tiene una base funcional, pero aun presenta varios huecos respecto a repositorios maduros:

- Log unico acumulado, sin estructura por corrida
- Estado del scheduler guardado, pero sin metadata suficiente por ejecucion
- `latest_signals.json` refleja el ultimo resultado, pero no permite reconstruir la historia detallada de cada ciclo
- No existe una capa formal de `quality gate` para datos y estatus de validez
- Los warnings de compatibilidad de `yfinance` y NumPy no son fatales, pero ensucian la trazabilidad
- Los resultados de ejecucion no estan completamente convertidos en un modelo de observabilidad por experimentos

---

## 4. Recomendacion de arquitectura para la siguiente implementacion

### 4.1 Estructura conceptual recomendada

El flujo ideal para una proxima version es:

1. Data fetch
2. Data validation
3. Indicator compute
4. Signal generation
5. Risk validation
6. Decision outcome
7. Execution / paper trade
8. Metrics update
9. Run record persistence

Cada paso debe producir un artefacto o evento explicito.

### 4.2 Registro por ejecucion

Cada ciclo debe tener un identificador unico, por ejemplo:

- `run_id`
- `strategy_version`
- `timestamp_utc`
- `timezone`
- `symbol`
- `market_data_source`
- `status` (`ok`, `warning`, `rejected`, `error`)
- `signal`
- `risk_decision`
- `trade_accepted`
- `reason`

Esto convierte la ejecucion en un evento auditable, y no simplemente en una linea de log.

### 4.3 Validacion de datos

Antes de aceptar una senal, el sistema debe comprobar:

- datos disponibles para el simbolo
- timestamps ordenados y completos
- ultima vela cerrada reciente
- historial minimo suficiente
- ausencia de duplicados o huecos significativos

Si falla cualquiera de estas comprobaciones, la ejecucion debe registrarse como `rejected_for_data_quality` y no continuar como si fuera un analisis valido.

### 4.4 Persistencia sugerida

Se recomienda guardar:

- `reports/runs/<run_id>.json`
- `reports/signals/<date>.jsonl`
- `reports/metrics/<date>.csv`
- `reports/events/<date>.jsonl`
- `reports/quality/<date>.json`

Esto hace que sea mucho mas facil revisar ejecuciones, comparar estrategias y reconstruir el historial sin depender de logs crudos.

---

## 5. Recomendacion de metricas para cada corrida

Cada ejecucion debe guardar al menos:

- retorno acumulado
- drawdown maximo
- numero de trades aceptados
- numero de trades rechazados
- comisiones
- slippage
- benchmark comparativo
- exposicion maxima
- sesgo de datos / warnings

Esto permite que el analisis no dependa solo de un `BUY` o `HOLD`, sino de evidencia cuantitativa comparada.

---

## 6. Recomendacion operativa

### Prioridad de implementacion

1. run_id + traceabilidad por ejecucion
2. validacion de calidad de datos antes de la senal
3. registro detallado de decisiones y rechazos
4. metricas resumidas por corrida
5. limpieza de warnings de runtime
6. comparacion contra benchmark por ejecucion y por periodo

### Prioridad de estrategia

- mantener `quant_only` como referencia principal
- no mezclar IA hasta validar base cuantitativa
- no optimizar parametros con resultados recientes
- conservar versiones de estrategia para cada cambio de reglas

---

## 7. Conclusiones finales

Los tres proyectos analizados muestran una tendencia clara:

- separar capas bien definidas
- guardar evidencia reproducible
- comparar experimentos por version y datos
- no confiar en logs crudos como unica fuente de verdad

El proyecto actual ya tiene una arquitectura razonable y un camino operativo real. La mejora mas valiosa para la proxima implementacion es pasar de un sistema funcional a un sistema trazable, validado y comparado.

Con eso, la base cuantitativa tendra una calidad mucho mas cercana a proyectos profesionales de referencia, sin abandonar el enfoque educativo y de paper trading planteado en este repositorio.
