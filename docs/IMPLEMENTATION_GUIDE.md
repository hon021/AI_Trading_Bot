# AI Trading Bot - Guia de implementacion

Esta guia es el documento operativo del proyecto. El roadmap describe **que** se quiere construir; esta guia describe **en que orden**, **como validar cada paso** y **como retomar el trabajo** despues de cambiar de sesion.

> Estado operativo: Fase 5 - backtesting reproducible.
>
> Regla permanente: el proyecto es exclusivamente de paper trading. No se conectara a un broker real durante las fases descritas aqui.

---

## 1. Como usar esta guia

Al comenzar o terminar una sesion:

1. Leer la seccion **Estado actual**.
2. Revisar el ultimo artefacto creado y la lista de bloqueos.
3. Trabajar solo en la fase activa hasta cumplir sus criterios de salida.
4. Ejecutar las validaciones indicadas.
5. Actualizar la seccion **Estado actual** antes de terminar.
6. Registrar cualquier cambio de reglas como una nueva version de estrategia.

El estado de este archivo debe ser la fuente de continuidad del proyecto. Los detalles tecnicos viven en el codigo y las decisiones de estrategia viven en `docs/strategy.md` cuando ese archivo sea creado.

---

## 2. Estado actual

### Fase activa

- **Fase:** 5 - Backtesting y Acceso a Datos (API REST)
- **Version de estrategia:** `v0.1.0-draft`
- **Mercado elegido:** ETFs de Estados Unidos
- **Activos elegidos:** `SPY`, `QQQ`, `IWM`
- **Timeframe:** velas de 1 hora, con limite intradia de `yfinance`
- **Zona horaria:** `America/New_York`
- **Ultimo trabajo completado:** tarea automatica de Windows registrada para iniciar el scheduler de lunes a viernes a las 09:00; API REST implementada para acceso facil a datos
- **Siguiente accion concreta:** observar los ciclos del 14 al 18 de septiembre y revisar los datos via API
- **Bloqueos:** solo hay aproximadamente 60 dias de datos horarios; no avanzar a Qwen ni congelar rentabilidad con esta muestra

### Criterio para cambiar de fase

No avanzar por calendario. Avanzar solamente cuando se cumplan los criterios de salida de la fase y exista evidencia reproducible, como tests, un informe o una ejecucion registrada.

---

## 3. Reglas de trabajo

- Mantener el alcance pequeno hasta tener resultados reproducibles.
- No mezclar ETFs y criptomonedas en el primer experimento.
- No integrar Qwen antes de validar la estrategia cuantitativa base.
- No usar datos futuros al calcular indicadores, senales o ejecuciones.
- No optimizar con el periodo de prueba fuera de muestra.
- Registrar fuente, timestamp, zona horaria y version de cada dataset.
- Registrar comisiones y slippage en todas las simulaciones.
- Mantener dos modos comparables: `quant_only` y `quant_plus_ai`.
- Una modificacion de reglas crea una nueva version de estrategia.
- Si una ejecucion falla, registrar el fallo; no convertirlo silenciosamente en una orden.

---

## 4. Fases y pasos de implementacion

### Fase 0 - Definir reglas y alcance

**Objetivo:** producir una especificacion que pueda implementarse sin decisiones ocultas.

**Tareas:**

- Elegir un unico mercado.
- Elegir 2-3 activos liquidos.
- Definir timeframe, zona horaria y frecuencia de analisis.
- Definir periodos y umbrales de EMA, RSI y ATR.
- Definir exactamente `BUY`, `SELL` y `HOLD`.
- Definir entradas, salidas y comportamiento con posiciones abiertas.
- Definir capital virtual, limites de posicion, exposicion y posiciones simultaneas.
- Definir comision, slippage, redondeo y precio de ejecucion.
- Definir condiciones de no operacion.

**Artefacto:** `docs/strategy.md`.

**Validacion:** otra persona puede implementar la estrategia leyendo solo ese documento.

**Salida:** reglas aprobadas y versionadas, sin parametros pendientes.

---

### Fase 1 - Crear proyecto Python minimo

**Objetivo:** establecer una base ejecutable sin construir todavia el sistema completo.

**Tareas:**

- Crear la estructura `app/`, `tests/`, `config/`, `data/`, `reports/` y `docs/`.
- Elegir version de Python y fijar dependencias.
- Crear configuracion separada del codigo.
- Crear un comando reproducible para ejecutar tests.
- Añadir `.env.example` sin secretos.

**Validacion:** el proyecto instala dependencias y una prueba minima pasa en local.

**Salida:** repositorio ejecutable y limpio.

---

### Fase 2 - Datos historicos

**Objetivo:** obtener un dataset confiable para el primer experimento.

**Tareas:**

- Implementar una interfaz de proveedor independiente de la estrategia.
- Descargar OHLCV y volumen para los simbolos definidos.
- Guardar timestamps, fuente, zona horaria y periodo cubierto.
- Validar faltantes, duplicados, precios invalidos y orden temporal.
- Guardar una copia versionada o identificable del dataset usado.

**Validacion:** las mismas entradas producen el mismo dataset o una diferencia explicable por la fuente.

**Salida:** dataset validado y loader reproducible.

---

### Fase 3 - Indicadores y QuantEngine

**Objetivo:** generar senales sin depender de un LLM.

**Tareas:**

- Implementar EMA, RSI y ATR.
- Probar cada indicador con casos pequenos y conocidos.
- Implementar la estrategia determinista definida en `docs/strategy.md`.
- Evitar mirar filas futuras al calcular cualquier valor.
- Registrar la version de estrategia junto con cada senal.

**Validacion:** tests unitarios de indicadores y tests de senales en escenarios controlados.

**Salida:** `QuantEngine` determinista que produce `BUY`, `SELL` o `HOLD`.

---

### Fase 4 - Riesgo y Paper Broker

**Objetivo:** convertir senales en operaciones simuladas con limites verificables.

**Tareas:**

- Implementar capital, posiciones y cash.
- Implementar limite por posicion y exposicion total.
- Aplicar comisiones y slippage.
- Calcular P&L realizado y no realizado.
- Rechazar operaciones que violen reglas de riesgo.
- Registrar cada senal, decision, orden simulada y motivo de rechazo.

**Validacion:** tests de compras, ventas, posiciones insuficientes, costes y limites de riesgo.

**Salida:** paper broker determinista con ledger de operaciones.

---

### Fase 5 - Backtesting

**Objetivo:** medir la estrategia sin contaminar el resultado con informacion futura.

**Tareas:**

- Definir periodos de desarrollo, validacion y prueba fuera de muestra.
- Ejecutar la orden en la siguiente observacion disponible o segun la regla documentada.
- Evitar recalcular parametros usando el periodo de prueba.
- Calcular retorno, drawdown, Sharpe, win rate, profit factor y numero de operaciones.
- Comparar contra `Buy & Hold` y una referencia simple.
- Guardar configuracion, dataset, version y resultados de cada corrida.

**Validacion:** un segundo lanzamiento con la misma configuracion reproduce los resultados dentro de una tolerancia documentada.

**Salida:** informe que indique si la estrategia base merece pasar al experimento con IA.

---

### Fase 6 - Integracion experimental de Qwen

**Objetivo:** medir si la IA aporta valor adicional.

**Precondicion:** Fases 0-5 completadas y estrategia cuantitativa reproducible.

**Tareas:**

- Instalar Ollama y fijar el modelo exacto.
- Enviar solo datos estructurados y necesarios.
- Validar el JSON de respuesta con un esquema estricto.
- Limitar longitud, tiempo de espera y reintentos.
- Registrar prompt, respuesta, modelo y version.
- Mantener el modo `quant_only` sin llamadas al modelo.
- Comparar `quant_only` contra `quant_plus_ai` usando el mismo dataset y costes.

**Validacion:** respuestas invalidas, timeout o caidas del modelo no generan operaciones validas.

**Salida:** informe comparativo, no una conclusion basada solo en una corrida.

---

### Fase 7 - Paper trading continuo

**Objetivo:** ejecutar el sistema en simulacion con datos nuevos.

**Tareas:**

- Ejecutar primero en local.
- Añadir scheduler con zona horaria explicita.
- Implementar idempotencia para no procesar dos veces la misma observacion.
- Registrar heartbeat, errores y ultima ejecucion.
- Generar reportes periodicos.
- Crear API REST para acceso facil a datos sin necesidad de leer logs.

**Validacion:** ejecuciones repetidas no duplican operaciones y los fallos quedan visibles; API expone datos en JSON.

**Salida:** varias semanas de paper trading con logs completos y API accesible.

El scheduler local ya disponible ejecuta solo el ciclo de analisis cuantitativo y no
realiza paper trades todavia. Para probar un ciclo inmediato:

```powershell
\.venv\Scripts\python.exe -m scripts.local_scheduler --run-now
```

Para mantenerlo activo durante la jornada laboral:

```powershell
\.venv\Scripts\python.exe -m scripts.local_scheduler
```

El proceso usa `America/New_York`, ignora fines de semana, evita repetir una franja en
`reports/.scheduler_state.json` y registra la salida en `reports/scheduler.log`. Las
señales actuales se escriben en `reports/latest_signals.json`. Detenerlo con `Ctrl+C`.

### Inicio automatico en Windows

Para no depender de iniciar manualmente la consola cada manana, se puede registrar el
proceso en el Programador de tareas de Windows. Desde la raiz del proyecto, ejecutar
PowerShell una sola vez:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_windows_scheduler.ps1
```

La tarea `AI Trading Bot - Local Scheduler` se ejecutara de lunes a viernes a las 09:00
de la hora local de Windows y usara `.venv`. El equipo debe estar encendido y el usuario
debe haber iniciado sesion; esta configuracion no ejecuta el proceso si el computador
esta apagado.

Para iniciar o detener la tarea manualmente:

```powershell
Start-ScheduledTask -TaskName "AI Trading Bot - Local Scheduler"
Stop-ScheduledTask -TaskName "AI Trading Bot - Local Scheduler"
```

Para eliminarla:

```powershell
.\scripts\uninstall_windows_scheduler.ps1
```

La tarea inicia el scheduler, que permanece activo durante la jornada. Los logs se
guardan en `reports/scheduler.log`; no se debe registrar una segunda tarea equivalente.

### API REST para acceso a datos

Una API REST complementaria expone los datos generados por el scheduler, facilitando 
consultas sin necesidad de buscar en archivos o logs:

- Ultimas signals (BUY/SELL/HOLD) generadas
- Estado de portfolio (cash, posiciones, P&L)
- Historico de operaciones ejecutadas
- Resultados de backtests por periodo
- Estado del sistema (scheduler activo, ultima ejecucion)

**Razon:** Un servidor HTTP es mas practico que buscar en logs. Proporciona base para 
herramientas futuras (dashboard, Telegram bot, alertas). Facilita debugging y monitoreo.

Para ejecutar la API durante la sesion de trabajo:

```powershell
\.venv\Scripts\python.exe -m scripts.run_api
```

Se iniciara en `http://127.0.0.1:8000` con documentacion interactiva en `/docs` y `/redoc`.

**Ejecucion en paralelo:** Scheduler y API son independientes:

```powershell
# Terminal 1: Scheduler (se ejecuta a las 09:00 automaticamente via Windows Task Scheduler)
\.venv\Scripts\python.exe -m scripts.local_scheduler

# Terminal 2: API (permanente durante la sesion, sirve datos en HTTP)
\.venv\Scripts\python.exe -m scripts.run_api
```

Para detalles completos, ver [docs/API.md](API.md).

### Plan de observacion de seis meses

El paper trading en tiempo real comenzara el lunes 14 de septiembre de 2026. La
observacion objetivo sera de seis meses, hasta aproximadamente el 14 de marzo de 2027.
Durante este periodo:

- El scheduler ejecutara el analisis de lunes a viernes.
- Se conservaran señales, timestamps, errores y datos utilizados.
- La estrategia `quant_only_v0.1.0` no cambiara por resultados semanales.
- Se revisaran logs y calidad de datos una vez por semana.
- Se generaran evaluaciones formales al completar 1, 3 y 6 meses.
- Los backtests historicos y walk-forward podran ejecutarse en paralelo.
- No se conectara ningun broker real.
- Qwen no se integrara en la estrategia principal durante esta etapa.

Las revisiones semanales son de observacion y control operativo, no de optimizacion.
Cualquier cambio de reglas debera crear una nueva version y conservar la version anterior
para comparacion.

#### Calendario de evaluacion

```text
14-18 sep 2026: validar scheduler, datos, logs y señales
14 oct 2026:    primera revision formal mensual
14 dic 2026:    revision intermedia de tres meses
14 mar 2027:    evaluacion principal de seis meses
```

#### Criterios de la evaluacion de seis meses

Comparar `quant_only_v0.1.0` contra `Buy & Hold` y revisar conjuntamente:

- Retorno total y retorno mensual.
- Drawdown maximo y recuperacion.
- Numero de operaciones cerradas.
- Win rate y profit factor.
- Comisiones y slippage acumulados.
- Consistencia entre meses y regimenes de mercado.
- Errores, datos faltantes y ejecuciones perdidas.

El resultado de seis meses no autoriza por si solo operaciones reales. Solo decide si la
estrategia merece una nueva ronda experimental, una variante con Qwen o ser descartada.

---

### Fase 8 - VPS y operacion

**Objetivo:** desplegar el MVP validado, no desarrollar la estrategia directamente en el servidor.

**Tareas:**

- Preparar Ubuntu, Docker y Ollama.
- Configurar secretos mediante variables de entorno.
- Configurar backups y rotacion de logs.
- Añadir health check y alertas.
- Documentar restauracion y reinicio.

**Validacion:** reinicio controlado, recuperacion de base de datos y deteccion de una ejecucion fallida.

**Salida:** servicio estable de paper trading.

---

## 5. Checklist de aceptacion del MVP

- [x] Un mercado y 2-3 activos definidos.
- [ ] `docs/strategy.md` completo y versionado; quedan decisiones pendientes.
- [x] Dataset historico validado.
- [x] Indicadores probados.
- [x] `QuantEngine` determinista.
- [x] Risk Manager probado.
- [x] Paper Broker con ledger.
- [x] Costes incluidos.
- [x] Backtest reproducible.
- [x] Comparacion contra Buy & Hold.
- [x] Periodo fuera de muestra separado.
- [x] Reporte cuantitativo guardado.
- [x] API REST para acceso facil a datos sin buscar en logs.
- [ ] Qwen evaluado solo despues de la base cuantitativa.
- [ ] No existe ninguna ruta de ejecucion real.

---

## 6. Plantilla de cierre de sesion

Copiar y completar esta seccion al finalizar cada sesion, sustituyendo la anterior.

```text
Fecha:
Fase activa:
Version de estrategia:
Objetivo de la sesion:
Trabajo completado:
Archivos modificados:
Validaciones ejecutadas:
Resultados relevantes:
Decision tomada:
Siguiente accion concreta:
Bloqueos o riesgos:
Preguntas pendientes:
```

### Ejemplo breve

```text
Fecha: 2026-09-12
Fase activa: 0 - Definir reglas y alcance
Version de estrategia: v0.1.0
Objetivo de la sesion: elegir universo inicial y documentar senales
Trabajo completado: seleccionados 3 ETFs y timeframe diario
Archivos modificados: docs/strategy.md, docs/IMPLEMENTATION_GUIDE.md
Validaciones ejecutadas: revision manual de reglas
Resultados relevantes: no hay parametros pendientes salvo slippage
Decision tomada: usar slippage fijo documentado para el primer backtest
Siguiente accion concreta: completar la tabla de costes
Bloqueos o riesgos: confirmar proveedor de datos
Preguntas pendientes: ninguna
```

---

## 7. Registro de decisiones y experimentos

Cada experimento debe registrar como minimo:

- Identificador y version de estrategia.
- Fecha de ejecucion.
- Dataset y proveedor.
- Simbolos y timeframe.
- Parametros completos.
- Costes y slippage.
- Modo: `quant_only` o `quant_plus_ai`.
- Modelo y configuracion de IA, si aplica.
- Metricas obtenidas.
- Interpretacion y decision siguiente.

Una mejora no se considera valida si no puede reproducirse y compararse contra la version anterior.

### Registro de esta sesion

```text
Fecha: 2026-09-14
Fase activa: 5 - Backtesting y Acceso a Datos
Version de estrategia: v0.1.0-draft
Objetivo de la sesion: crear API REST para acceso facil a datos del scheduler
Trabajo completado: 
  - Creada estructura FastAPI en app/api/ con 5 rutas modulares
  - Implementados endpoints: status, signals, portfolio, trades, backtest
  - Creados modelos Pydantic para todas las respuestas
  - Script run_api.py para ejecutar servidor
  - Tests unitarios (8/8 endpoints pasando)
  - Documentacion API.md completa
Archivos modificados: 
  - app/api/ (nueva estructura)
  - scripts/run_api.py (nueva entrada)
  - tests/test_api.py (nuevos tests)
  - docs/API.md (nueva documentacion)
  - requirements.txt (+ FastAPI, Uvicorn, Pydantic)
  - IMPLEMENTATION_GUIDE.md (actualizado con API)
  - AI_Trading_Bot_Roadmap.md (actualizado con API)
Validaciones ejecutadas: 8 endpoints testados exitosamente, API corriendo en puerto 8000
Resultados relevantes: API lista para produccion local, expone datos en JSON sin parsado manual
Decision tomada: API corre independiente del scheduler, ambos en paralelo sin conflictos
Siguiente accion concreta: observar ciclos 14-18 sept, validar scheduler ejecutandose a las 09:00
Bloqueos o riesgos: ningun bloqueo nuevo; API solo lee datos, scheduler sigue siendo fuente de verdad
Preguntas pendientes: implementar wrapper de reintentos si API falla (no urgente)
```
