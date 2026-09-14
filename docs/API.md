# API REST - AI Trading Bot

La API REST permite acceder a todos los datos del sistema de trading: signals, portfolio, trades, backtest results y status del sistema.

## Inicio rápido

```powershell
# Instalar dependencias (si no lo has hecho)
.\.venv\Scripts\pip install -r requirements.txt

# Ejecutar la API
.\.venv\Scripts\python.exe -m scripts.run_api

# Con opciones
.\.venv\Scripts\python.exe -m scripts.run_api --host 0.0.0.0 --port 8000 --reload
```

La API estará disponible en: `http://127.0.0.1:8000`

## Documentación Interactiva

Una vez que la API esté ejecutándose, accede a:

- **Swagger UI (recomendado)**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

## Endpoints principales

### Status y Health

- `GET /status/health` - Health check básico
- `GET /status/system` - Estado del sistema, scheduler, última ejecución

### Signals

- `GET /signals/latest` - Últimas signals del quant engine
- `GET /signals/history?limit=100` - Histórico de signals

### Portfolio

- `GET /portfolio/summary` - Resumen de cartera (cash, invested, total)
- `GET /portfolio/positions` - Posiciones abiertas

### Trades

- `GET /trades/history?limit=100` - Histórico de operaciones
- `GET /trades/stats` - Estadísticas de trades

### Backtest

- `GET /backtest/latest` - Últimos resultados de backtest
- `GET /backtest/metrics/{period}` - Métricas por período (development, validation, out_of_sample)

## Ejemplos de uso

### Con curl

```bash
# Verificar API
curl http://127.0.0.1:8000/

# Obtener signals actuales
curl http://127.0.0.1:8000/signals/latest

# Obtener resumen de portfolio
curl http://127.0.0.1:8000/portfolio/summary

# Obtener últimos 20 trades
curl "http://127.0.0.1:8000/trades/history?limit=20"
```

### Con Python

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Obtener signals
response = requests.get(f"{BASE_URL}/signals/latest")
signals = response.json()
print(json.dumps(signals, indent=2))

# Obtener status
response = requests.get(f"{BASE_URL}/status/system")
status = response.json()
print(f"Scheduler activo: {status['scheduler_active']}")
print(f"Última ejecución: {status['last_run']}")
```

## Ejecución paralela con Scheduler

Puedes ejecutar la API y el scheduler simultáneamente en diferentes terminales:

```powershell
# Terminal 1: Scheduler
.\.venv\Scripts\python.exe -m scripts.local_scheduler

# Terminal 2: API
.\.venv\Scripts\python.exe -m scripts.run_api
```

Ambos comparten la misma base de datos SQLite (`reports/`) y pueden ejecutarse sin conflictos.

## Integración con Windows Task Scheduler

La API puede ejecutarse automáticamente como servicio. Ver `install_windows_scheduler.ps1` para detalles.

## Estructura de la API

```
app/api/
├── __init__.py
├── main.py                 # Aplicación FastAPI principal
├── schemas.py              # Modelos Pydantic
└── routes/
    ├── __init__.py
    ├── status.py           # Status y health endpoints
    ├── signals.py          # Signals endpoints
    ├── portfolio.py        # Portfolio endpoints
    ├── trades.py           # Trades history endpoints
    └── backtest.py         # Backtest results endpoints
```

## Response Models

Todos los endpoints devuelven JSON con modelos tipados:

- `HealthResponse` - Status y mensaje
- `StatusResponse` - Estado del sistema
- `SignalResponse` - Una signal individual
- `PortfolioResponse` - Estado de la cartera
- `TradeResponse` - Un trade del histórico
- `BacktestMetrics` - Métricas de backtest

## CORS

La API permite CORS desde cualquier origen (`*`). Esto facilita pruebas locales y futuras integraciones con dashboards.

## Desarrollo

Para ejecutar con auto-reload durante desarrollo:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_api --reload
```

## Testing

```powershell
.\.venv\Scripts\python.exe tests/test_api.py
```

## Próximos pasos

- [x] API básica con endpoints principales
- [ ] Autenticación y API keys (para producción)
- [ ] Rate limiting
- [ ] Webhooks para alertas de signals
- [ ] Integración con Telegram Bot
- [ ] Dashboard web (Streamlit o React)
- [ ] Persistencia mejorada (PostgreSQL)
