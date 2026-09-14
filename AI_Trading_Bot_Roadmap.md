# AI Trading Bot — Roadmap

## 1. Objetivo

Construir un bot de análisis de mercado que funcione 24/7 en un VPS y revise el mercado **4 veces al día**.

La primera versión será exclusivamente de **paper trading / simulación**, con un capital virtual de **USD 500**.

### Objetivos principales

- Analizar inicialmente un solo mercado y un universo pequeño de 2–3 activos.
- Utilizar un modelo de IA local, inicialmente **Qwen** mediante Ollama.
- Combinar IA con indicadores cuantitativos y reglas de riesgo.
- Generar señales: `BUY`, `SELL` o `HOLD`.
- Simular las operaciones.
- Registrar todas las decisiones.
- Medir el rendimiento frente a estrategias simples de referencia.
- Mantener una arquitectura preparada para crecer posteriormente.

> Regla principal: durante la etapa inicial no ejecutar operaciones financieras reales.

---

# 2. Arquitectura objetivo

```text
                 MARKET DATA
                      |
                      v
              +---------------+
              | Data Collector |
              +-------+-------+
                      |
                      v
              +---------------+
              | Quant Engine   |
              | EMA / RSI / ATR |
              | Volatility      |
              +-------+-------+
                      |
                      v
              +---------------+
              | AI Analyzer    |
              | Qwen / Ollama  |
              +-------+-------+
                      |
                      v
              +---------------+
              | Risk Manager   |
              +-------+-------+
                      |
             +--------+--------+
             |                 |
             v                 v
         BUY/SELL/HOLD      REJECT
             |
             v
        PAPER TRADING
             |
             v
          DATABASE
             |
             v
        PERFORMANCE
          REPORTS
```

---

# 2.1 Acceso a Datos: API REST

Adicional a la arquitectura cuantitativa, se implementó una **API REST** que expone 
los datos del sistema de forma estructurada y accesible.

## Por qué la API

- **Sin logs confusos:** consulta datos en JSON en lugar de buscar en archivos.
- **Base para herramientas:** facilita integración con dashboard, Telegram bot, alertas.
- **Monitoreo:** inspecciona estado del scheduler, signals actuales, portfolio en tiempo real.
- **Debuggeo:** acceso programático a datos sin parseado manual.

## Endpoints principales

```
GET /status/health          → Verificación rápida
GET /status/system          → Estado del scheduler
GET /signals/latest         → Signals actuales (BUY/SELL/HOLD)
GET /portfolio/summary      → Cash, invested, P&L
GET /trades/history         → Histórico de operaciones
GET /backtest/latest        → Resultados de backtests
```

## Ejecución

La API corre en paralelo al scheduler sin conflictos:

```powershell
# Terminal 1: Scheduler automático
.\.venv\Scripts\python.exe -m scripts.local_scheduler

# Terminal 2: API accesible
.\.venv\Scripts\python.exe -m scripts.run_api
```

Documentación interactiva: `http://127.0.0.1:8000/docs`

---

# 3. Fase 0 — Definir reglas y alcance del experimento

## Objetivo

Antes de programar, definir exactamente qué significa una señal.

### Alcance inicial

El primer experimento no debe mezclar ETFs y criptomonedas. Elegir un solo mercado y
2–3 activos líquidos. La expansión a otros activos será un experimento posterior y
deberá conservar las mismas reglas, costes y métricas para que la comparación sea válida.

### Decisiones obligatorias

- Capital virtual: **USD 500**
- Frecuencia: **4 análisis diarios**, con zona horaria documentada.
- Mercado inicial y lista exacta de 2–3 símbolos.
- Timeframe de los datos y momento exacto de cada decisión.
- Señales:
  - BUY
  - SELL
  - HOLD
- Periodos exactos de EMA, RSI y ATR.
- Condiciones deterministas para abrir, mantener y cerrar una posición.
- Riesgo máximo por posición.
- Número máximo de posiciones simultáneas.
- Porcentaje máximo del capital en un solo activo.
- Comisión y slippage simulados.
- Condiciones que obligan a no operar.

No cambiar estas reglas durante una evaluación. Cada variante debe identificarse como
una versión de estrategia independiente.

### Entregable

`docs/strategy.md`

El documento debe ser suficiente para que otra persona implemente la estrategia sin
interpretar reglas ambiguas.

---

# 4. Fase 1 — Preparar el VPS

## Objetivo

Crear un entorno estable para ejecutar el proyecto 24/7.

### Recomendación inicial

- Ubuntu LTS
- 4–6 vCPU
- 8–16 GB RAM
- SSD/NVMe
- Docker
- Ollama

No es necesario comenzar con GPU.

### Software

```text
Ubuntu
Docker
Python 3.x
Git
Ollama
SQLite o PostgreSQL
```

### Entregable

Servidor preparado y repositorio funcionando.

---

# 5. Fase 2 — Crear el proyecto Python

## Estructura propuesta

```text
ai-trading-bot/
│
├── app/
│   ├── data/
│   ├── indicators/
│   ├── ai/
│   ├── strategy/
│   ├── risk/
│   ├── portfolio/
│   ├── paper_trading/
│   ├── reporting/
│   └── scheduler/
│
├── tests/
│
├── config/
│
├── data/
│
├── reports/
│
├── docs/
│
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Principio

Separar claramente:

1. Datos
2. Indicadores
3. IA
4. Estrategia
5. Riesgo
6. Ejecución simulada
7. Persistencia
8. Reportes

---

# 6. Fase 3 — Obtener datos de mercado

## Objetivo

Crear un componente independiente que obtenga información de mercado.

Datos potenciales:

- OHLCV
- Volumen
- Precio actual
- Variación porcentual
- Volatilidad
- Datos históricos

Inicialmente utilizar fuentes gratuitas o de bajo costo.

### Importante

No mezclar el código de adquisición de datos con la estrategia.

Conservar la marca temporal original, la zona horaria, la fuente y la calidad de cada
observación. El sistema no debe rellenar silenciosamente datos faltantes ni utilizar
datos posteriores al momento de la decisión.

Crear una interfaz como:

```python
get_market_data(symbol)
get_historical_data(symbol, period)
```

### Entregable

El sistema puede obtener y almacenar datos históricos correctamente.

---

# 7. Fase 4 — Motor cuantitativo

Antes de utilizar IA, construir una estrategia puramente cuantitativa.

## Indicadores iniciales

- SMA
- EMA
- RSI
- ATR
- Volumen
- Volatilidad
- Momentum

Ejemplo conceptual:

```text
Trend      = bullish / bearish / neutral
Momentum   = positive / negative
Volatility = low / medium / high
```

La estrategia debe poder generar una señal sin utilizar un LLM.

La primera versión debe ser completamente determinista. Por ejemplo, sus reglas pueden
definir una tendencia mediante EMA, confirmar momentum mediante RSI y utilizar ATR para
filtrar volatilidad o calcular el tamaño de posición. Los periodos y umbrales concretos
deben quedar en `docs/strategy.md`, no implícitos en el código.

### Entregable

`QuantEngine`

---

# 8. Fase 5 — Integrar Qwen

## Objetivo

Utilizar IA como una segunda capa de análisis y medir si mejora la estrategia cuantitativa.
Qwen no debe considerarse una fuente de verdad ni una condición necesaria para que el
motor cuantitativo pueda funcionar.

El LLM NO debe recibir libertad total para operar.

Debe recibir información estructurada:

```json
{
  "symbol": "ETF",
  "price": 100.50,
  "trend": "bullish",
  "rsi": 57,
  "volatility": "medium",
  "momentum": "positive"
}
```

Y devolver exclusivamente una estructura controlada:

```json
{
  "signal": "HOLD",
  "confidence": 0.72,
  "risk": "MEDIUM",
  "reason": "..."
}
```

## Reglas

- Validar JSON.
- Rechazar respuestas inválidas.
- Limitar longitud de respuesta.
- No permitir instrucciones arbitrarias del modelo.
- Registrar prompt y respuesta.
- Mantener un modo `quant_only` para comparar resultados sin IA.
- Registrar la versión del modelo y la configuración usada.
- Si Qwen falla, la ejecución debe quedar registrada y no convertirse automáticamente
        en una orden.

---

# 9. Fase 6 — Motor de decisión

Combinar el análisis cuantitativo con la IA.

Ejemplo:

```text
Quant Engine
     |
     +--> BUY
     |
     +--> HOLD
     |
     +--> SELL
             |
             v
        AI Analysis
             |
             v
       Decision Engine
```

Una posible regla inicial:

```text
Si Quant = BUY
y AI = BUY
y Risk Manager = OK
    -> PAPER BUY

Si existe conflicto
    -> HOLD
```

La estrategia exacta debe probarse mediante backtesting; no asumir que esta regla es rentable.

---

# 10. Fase 7 — Risk Manager

Esta será una de las partes más importantes.

## Debe controlar

- Capital disponible.
- Tamaño máximo de posición.
- Exposición máxima por activo.
- Número máximo de posiciones.
- Pérdida máxima simulada.
- Drawdown.
- Concentración.
- Comisiones.
- Slippage.

Ejemplo conceptual:

```text
Capital = $500

Max position = 20%
           = $100

Max crypto exposure = X%

Max ETF exposure = Y%
```

Los porcentajes son parámetros experimentales, no recomendaciones de inversión.

---

# 11. Fase 8 — Paper Trading

Crear un broker ficticio interno.

Debe permitir:

```text
BUY
SELL
HOLD
```

y mantener:

```text
cash
positions
average_price
realized_pnl
unrealized_pnl
fees
```

Cada operación debe quedar registrada.

### Ejemplo

```text
2026-09-12 08:00
Asset: XYZ
Signal: BUY
Price: 102.30
Quantity: 0.8
AI confidence: 0.74
Risk: LOW
```

---

# 12. Fase 9 — Backtesting

Antes de dejar el bot funcionando continuamente, probarlo contra datos históricos.

El backtest debe separar como mínimo los periodos de desarrollo, validación y prueba
fuera de muestra. Cada decisión solo puede usar datos disponibles hasta ese instante;
queda prohibido utilizar valores futuros al calcular indicadores, señales o precios de
ejecución. Las operaciones se ejecutarán en la siguiente observación disponible o con
una regla de ejecución documentada, nunca con información del futuro.

## Métricas

- Return
- CAGR
- Maximum Drawdown
- Sharpe Ratio
- Win Rate
- Profit Factor
- Número de operaciones
- Average trade
- Volatilidad

Comparar contra:

```text
Strategy
vs
Buy & Hold
```

También realizar pruebas durante:

- Mercado alcista
- Mercado bajista
- Alta volatilidad
- Mercado lateral

---

# 13. Fase 10 — Scheduler

Configurar cuatro análisis diarios.

Ejemplo:

```text
08:00
12:00
16:00
20:00
```

El horario definitivo debe considerar la zona horaria de los mercados que se estén analizando.

Cada ejecución:

```text
1. Descargar datos
2. Validar datos
3. Calcular indicadores
4. Ejecutar análisis IA
5. Ejecutar Risk Manager
6. Generar decisión
7. Ejecutar paper trade
8. Guardar resultado
9. Enviar/loggear reporte
```

---

# 14. Fase 11 — Monitoring

El bot debe poder avisar cuando algo falle.

Monitorizar:

- VPS
- CPU
- RAM
- Disco
- Ollama
- Data provider
- Base de datos
- Scheduler
- Errores
- Operaciones

Crear un heartbeat:

```text
BOT_STATUS = OK
LAST_RUN = timestamp
```

Si el bot deja de ejecutarse, debe ser detectable.

---

# 15. Fase 12 — Dashboard

Crear posteriormente un dashboard sencillo.

Información:

```text
Portfolio
----------------
Cash
Invested
Total Value
P&L
Drawdown

Positions
----------------
Asset
Quantity
Entry
Current
P&L

Signals
----------------
Time
Asset
Quant
AI
Decision
```

Tecnologías posibles:

- FastAPI
- React
- Streamlit

Para empezar, Streamlit puede ser suficiente.

---

# 16. Fase 13 — Evaluación

Después de varias semanas de paper trading:

## Preguntas

- ¿La estrategia gana dinero?
- ¿Cuál es el drawdown?
- ¿La IA mejora al Quant Engine?
- ¿La IA empeora los resultados?
- ¿Qué activos funcionan mejor?
- ¿Cuántas señales son falsas?
- ¿Cuánto afecta el slippage?
- ¿Cuánto afectan las comisiones?
- ¿El modelo cambia de criterio frecuentemente?

No evaluar solamente por rentabilidad.

---

# 17. Fase 14 — Experimentos

Mantener diferentes versiones:

```text
Strategy V1
Strategy V2
Strategy V3
```

Y comparar:

```text
Quant only
Quant + Qwen
Quant + otro modelo
Buy & Hold
```

Nunca cambiar las reglas sin registrar la versión.

---

# 18. Fase 15 — Seguridad

## VPS

- SSH keys
- Firewall
- Actualizaciones automáticas controladas
- Docker
- Secrets mediante variables de entorno
- Backups
- Logs rotativos

## Aplicación

- No guardar API keys en Git.
- No guardar credenciales en código.
- Validar todas las respuestas del LLM.
- Usar límites estrictos.
- Registrar todas las decisiones.

---

# 19. Fase 16 — Evolución futura

Una vez validado el sistema:

```text
V1
Paper Trading
     |
     v
V2
Better Backtesting
     |
     v
V3
Multiple AI Models
     |
     v
V4
Advanced Risk Engine
     |
     v
V5
Production-grade monitoring
```

Cualquier transición posterior a operaciones financieras reales debe realizarse únicamente después de una evaluación independiente de riesgos, requisitos regulatorios, seguridad y funcionamiento.

---

# 20. Stack recomendado

## Backend

- Python
- FastAPI
- Pandas
- NumPy

## AI

- Ollama
- Qwen
- Opcionalmente DeepSeek para comparación

## Database

Inicial:

```text
SQLite
```

Después:

```text
PostgreSQL
```

## Deployment

```text
Ubuntu
Docker
Docker Compose
```

## Monitoring

Inicial:

```text
Logs + health check
```

Después:

```text
Prometheus + Grafana
```

---

# 21. Orden recomendado de implementación

No intentar construir todo al mismo tiempo. El primer objetivo es validar una estrategia
reproducible en local; el VPS, el scheduler y el dashboard vienen después.

```text
[x] 1. Crear repositorio y proyecto Python mínimo
[ ] 2. Definir `docs/strategy.md`
[x] 3. Elegir un mercado, 2–3 activos y una fuente de datos
[x] 4. Descargar, validar y almacenar datos históricos
[x] 5. Implementar EMA, RSI y ATR
[x] 6. Implementar el `QuantEngine` determinista
[x] 7. Implementar costes, Risk Manager y Paper Broker
[x] 8. Implementar backtesting reproducible
[x] 9. Comparar Quant, Buy & Hold y una estrategia de referencia simple
[x] 10. Separar periodos de desarrollo, validación y prueba fuera de muestra
[ ] 11. Instalar Ollama y Qwen
[ ] 12. Añadir `AI Analyzer` como experimento `quant_plus_ai`
[ ] 13. Comparar el resultado con y sin IA
[x] 14. Ejecutar paper trading local y registrar decisiones
[x] 14.1. Crear API REST para acceso a datos sin buscar en logs
[ ] 15. Preparar el VPS y desplegar el MVP validado
[ ] 16. Añadir scheduler, heartbeat y alertas
[ ] 17. Crear reportes y dashboard
[ ] 18. Evaluar resultados antes de cambiar reglas o ampliar activos
```

---

# 22. Primera versión mínima (MVP)

El MVP debe responder una sola pregunta: si una estrategia cuantitativa reproducible
supera a una referencia sencilla después de costes y riesgo. Qwen se incorpora después
como una comparación controlada, no como requisito para probar la base.

```text
Un mercado
        +
2–3 activos
        +
Datos históricos validados
        +
EMA + RSI + ATR
        +
QuantEngine determinista
        +
Risk Manager
        +
Paper Broker
        +
Backtester reproducible
        +
API REST para acceso a datos
        +
SQLite
        +
Reportes básicos
```

Después del MVP cuantitativo, añadir una variante experimental:

```text
MVP cuantitativo + API
        +
Qwen / Ollama
        +
Respuesta JSON validada
        +
Comparación quant_only vs quant_plus_ai
```

El entorno inicial puede ejecutarse localmente. El VPS solo debe introducirse cuando el
backtest, el paper broker, la persistencia, la API y los logs sean reproducibles.

Nada más.

La prioridad inicial no es construir un sistema sofisticado, sino responder una pregunta:

> **¿La combinación de estrategia cuantitativa + IA consigue mejores resultados que una estrategia sencilla de Buy & Hold después de considerar riesgo y costos?**

Si la respuesta es no, no tiene sentido añadir más complejidad.

---

# 23. Resultado esperado

Al finalizar el MVP, el VPS debería poder ejecutar automáticamente:

```text
Every scheduled run
        |
        v
Market data
        |
        v
Indicators
        |
        v
Qwen analysis
        |
        v
Risk validation
        |
        v
BUY / SELL / HOLD
        |
        v
Paper portfolio
        |
        v
Database
        |
        v
Performance report
```

El objetivo final de esta primera etapa es tener un **laboratorio de trading algorítmico reproducible**, no intentar maximizar ganancias rápidamente. Ninguna mejora se acepta por una sola métrica o por un único periodo favorable: debe evaluarse fuera de muestra y frente a las referencias definidas.
