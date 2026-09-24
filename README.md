# AI Trading Bot

Bot de analisis cuantitativo para ETFs de Estados Unidos. El proyecto funciona actualmente como un laboratorio reproducible de datos, indicadores, senales, gestion de riesgo, backtesting y paper trading en desarrollo.

> **Importante:** este proyecto no ejecuta operaciones reales y no constituye una recomendacion financiera.

## Estado actual

- Estrategia base: `quant_only_v0.1.0`
- Activos: `SPY`, `QQQ`, `IWM`
- Datos: velas OHLCV de 1 hora mediante `yfinance`
- Zona horaria: `America/New_York`
- Capital virtual del backtest: USD 500
- Scheduler: cuatro analisis diarios durante la sesion regular
- API: FastAPI con documentacion OpenAPI
- IA: Qwen/Ollama aun no integrado en el flujo de produccion
- Ejecucion en tiempo real: actualmente solo genera senales candidatas; `paper_trade_executed` permanece en `false`

La estrategia y sus reglas detalladas estan documentadas en [docs/strategy.md](docs/strategy.md). El estado y el plan de implementacion se mantienen en [docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md).

## Requisitos

- Python 3.11 o compatible
- Windows, Linux o macOS
- Conexion a Internet para descargar datos de mercado

Las dependencias principales estan en [requirements.txt](requirements.txt): pandas, yfinance, FastAPI, Uvicorn y Pydantic.

## Instalacion en Windows

Desde la raiz del repositorio:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Comandos principales

### Ejecutar tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Descargar datos y generar senales

Ejecuta un ciclo de analisis, usando solamente velas cerradas, y guarda el resultado en `reports/latest_signals.json`:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_analysis
```

### Ejecutar un backtest

Lee los archivos de `data/raw/` y genera los reportes reproducibles en `reports/`:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_backtest
```

Los principales artefactos son:

- `reports/backtest_summary.json`
- `reports/equity_curve.csv`
- `reports/trades.csv`

### Ejecutar el scheduler

Para ejecutar un ciclo inmediatamente:

```powershell
.\.venv\Scripts\python.exe -m scripts.local_scheduler --run-now
```

Para mantener el scheduler activo:

```powershell
.\.venv\Scripts\python.exe -m scripts.local_scheduler
```

El scheduler usa `America/New_York`, evita repetir un slot y registra los resultados en:

- `reports/.scheduler_state.json`
- `reports/scheduler.log`
- `reports/latest_signals.json`

### Ejecutar la API

```powershell
.\.venv\Scripts\python.exe -m scripts.run_api
```

La API queda disponible en `http://127.0.0.1:8000`.

Documentacion interactiva:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Endpoints principales:

- `GET /status/health`
- `GET /status/system`
- `GET /signals/latest`
- `GET /portfolio/summary`
- `GET /trades/history`
- `GET /backtest/latest`

Para usar API y scheduler al mismo tiempo, ejecuta cada comando en una terminal separada.

## Arquitectura

```text
Data provider
    |
    v
OHLCV en data/raw/
    |
    v
Indicadores EMA / RSI / ATR
    |
    v
QuantEngine: BUY / SELL / HOLD
    |
    v
Risk Manager
    |
    +--> Paper Broker
    +--> Backtester
    +--> Reports y API REST
```

El codigo principal esta organizado en:

```text
app/
  api/             API FastAPI y endpoints
  backtesting/     Motor de backtesting reproducible
  data/            Descarga y lectura de datos
  indicators/      EMA, RSI, ATR y calculos tecnicos
  paper_trading/   Broker y operaciones simuladas
  risk/             Limites de riesgo y tamano de posicion
  strategy/         Motor de senales cuantitativas
scripts/            Comandos de ejecucion
reports/            Resultados y logs generados
 tests/             Pruebas unitarias
```

## Resultado de referencia

El backtest inicial sobre el historico intradia disponible produjo:

- Estrategia: USD 489.72, retorno de -2.06%
- Buy & Hold: USD 495.45, retorno de -0.91%
- Maximo drawdown de la estrategia: -2.33%
- 21 operaciones cerradas
- Win rate: 14.3%
- Costes simulados: USD 4.15

La muestra es corta y no permite concluir que la estrategia sea rentable. Los parametros deben mantenerse congelados mientras se recopilan mas datos y se completa el periodo de paper trading.

## Reglas de seguridad del proyecto

1. No conectar un broker real.
2. No usar apalancamiento ni margen.
3. No modificar parametros usando el periodo fuera de muestra.
4. Mantener comisiones y slippage explicitos.
5. Registrar timestamps UTC y zona horaria de mercado.
6. Tratar las senales como candidatos, no como ordenes reales.

## Documentacion adicional

- [Roadmap](AI_Trading_Bot_Roadmap.md)
- [Guia de implementacion](docs/IMPLEMENTATION_GUIDE.md)
- [Reglas de estrategia](docs/strategy.md)
- [API REST](docs/API.md)
- [Analisis de referencias](docs/PROJECT_REFERENCE_ANALYSIS.md)
