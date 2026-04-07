# 🏎️ iRacing Telemetry Tracker v2

Sistema completo de seguimiento de tu carrera en iRacing.

**Combina:**
- 🔴 **pyiRSDK** → Telemetría en tiempo real mientras corres
- 🟢 **iracing_garage** → iRating, SR y resultados oficiales después de carrera

## 📦 Instalación

### 1. Instalar dependencias

```bash
pip install pyirsdk iracing-garage python-dotenv
```

### 2. Configurar credenciales

1. Copia `.env-template` a `.env`
2. Edita `.env` con tus datos:

```
IRACING_EMAIL=tu_email@iracing.com
IRACING_PASSWORD=tu_contraseña
IRACING_CUST_ID=123456
```

**¿Dónde encuentro mi Customer ID?**
- Ve a: iRacing Members Site → My Account
- Tu Customer ID aparece en la página

### 3. Estructura de archivos

```
📁 iRacingTracker/
├── iracing_logger.py    # Captura datos mientras corres
├── analyzer.py          # Analiza tu rendimiento
├── .env                  # Tus credenciales (NO compartir)
├── .env-template         # Plantilla de credenciales
├── iracing_data.db       # Base de datos (se crea automáticamente)
└── README.md
```

## 🚀 Uso

### Capturar datos mientras corres

```bash
python iracing_logger.py
```

**Lo que hace:**
1. ✅ Conecta a la API de iRacing y guarda tu iRating/SR actual
2. ⏳ Espera a que abras iRacing
3. 🏁 Detecta cuando entras en pista
4. 📊 Captura cada vuelta (tiempo, posición, incidentes, telemetría)
5. 🏆 Al terminar, obtiene tu nuevo iRating/SR y el cambio
6. 💾 Guarda los resultados oficiales

### Analizar tu progreso

```bash
python analyzer.py
```

**Opciones:**
1. **Resumen de carrera** - Tu perfil completo y tendencias
2. **Historial de iRating** - Evolución en tus últimas carreras
3. **Estadísticas por coche** - En qué coches rindes mejor
4. **Ver sesiones** - Lista de todas tus sesiones
5. **Detalle de sesión** - Vuelta por vuelta con tiempos
6. **Estadísticas por pista** - Tu rendimiento en cada circuito
7. **Análisis de incidentes** - En qué vueltas tienes más problemas

## 📊 Datos que se capturan

### Durante la carrera (pyiRSDK)
| Dato | Frecuencia |
|------|------------|
| Tiempo de vuelta | Cada vuelta |
| Posición | Cada vuelta |
| Incidentes | Cada vuelta |
| Combustible | Cada vuelta |
| Velocidad, RPM, pedales | Cada segundo |
| Aceleraciones G | Cada segundo |

### Después de la carrera (iracing_garage)
| Dato | Cuándo |
|------|--------|
| iRating antes/después | Al terminar sesión |
| Safety Rating antes/después | Al terminar sesión |
| Resultados oficiales | 30s después de terminar |
| Posición final oficial | Con resultados |

## 📈 Análisis disponibles

- **Progresión de iRating** - ¿Estás mejorando o estancado?
- **Consistencia** - Desviación entre tus vueltas
- **Incidentes por vuelta** - ¿En qué vuelta la lías?
- **Rendimiento por coche** - ¿En cuál ganas más iRating?
- **Rendimiento por pista** - ¿Dónde eres más competitivo?
- **Comparativa sesiones** - Evolución en una pista específica

## 🗄️ Base de datos

Los datos se guardan en SQLite (`iracing_data.db`).

### Tablas:
- `driver_profile` - Snapshots de tu perfil
- `sessions` - Cada sesión con iRating/SR
- `laps` - Cada vuelta con tiempos e incidentes
- `telemetry` - Datos de telemetría por segundo
- `official_results` - JSON completo de resultados oficiales

### Ver con DB Browser
Descarga [DB Browser for SQLite](https://sqlitebrowser.org/) para explorar los datos visualmente.

## 🔧 Configuración avanzada

En `iracing_logger.py`:

```python
POLL_RATE = 1  # Frecuencia de telemetría (segundos)
```

- `1` = Una lectura por segundo (recomendado)
- `0.1` = 10 lecturas por segundo (más datos, más espacio)

## ❓ FAQ

### No me conecta a la API
- Verifica email/password en `.env`
- Asegúrate de que el archivo se llame `.env` (sin extensión)

### No detecta iRacing
- El logger debe estar corriendo ANTES de entrar en pista
- Asegúrate de que iRacing está abierto y en sesión

### No tengo iRating después de carrera
- El iRating tarda ~30 segundos en actualizarse
- El logger espera automáticamente

### ¿Funciona con carreras privadas/hosted?
- La telemetría sí funciona
- El iRating/SR solo cambia en carreras oficiales

## 🐛 Problemas

### "ModuleNotFoundError: No module named 'xxx'"
```bash
pip install pyirsdk iracing-garage python-dotenv
```

### "Invalid credentials" al conectar
- Verifica tu email y contraseña en el archivo `.env`
- Prueba a hacer login en la web de iRacing con esos datos

## 📬 Próximas funciones

- [ ] Dashboard web con gráficos
- [ ] Comparativa de telemetría entre vueltas
- [ ] Alertas de tendencias (racha negativa, etc.)
- [ ] Exportar informes a PDF
- [ ] Integración con CrewChief

---

**¿Dudas?** Comparte tu `iracing_data.db` conmigo y te ayudo a analizarlo 🏁
