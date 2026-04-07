# Fantan Bot 🤖

**Fantan Bot** es un bot de Twitch diseñado para interactuar con el chat de manera sarcástica y divertida, gestionar comandos personalizados, guardar memoria por usuario, y ofrecer soporte para redes sociales, sorteos, frases automáticas y más.

---

## 📝 Funcionalidades principales

- **Comandos de información y utilidad**: permite a los usuarios interactuar con el bot y obtener datos del canal o del bot.
- **Sistema de niveles y memoria**: el bot recuerda lo que le dices mediante `!oye` y lleva un registro del nivel de trato del usuario (suscriptor/favorito).
- **Frases sarcásticas y automáticas**: se emiten frases según eventos en iRacing o interacciones en el chat.
- **Sorteos y dinámicas de juego**: sistema de niveles basado en interacciones y suscripciones, con votaciones para elegir el siguiente destino.
- **Redes sociales y promociones**: comandos para promocionar redes sociales o links de patrocinio, con posibilidad de emitirlos periódicamente.
- **Integración con Discord y otros servicios**: puede emitir mensajes o frases en diferentes plataformas según configuración.
- **Gestión avanzada de comandos**: comandos para todos, para mods y broadcasters, incluyendo administración remota de usuarios.

---

## 🎮 Comandos disponibles

### Comandos para todos los usuarios

| Comando | Descripción |
|---------|-------------|
| `!bot` | Presentación del bot |
| `!botcomandos` | Lista todos los comandos disponibles |
| `!edad` | Muestra la edad del streamer o del bot |
| `!discord` | Muestra el enlace de Discord |
| `!redes` | Muestra todas las redes sociales |
| `!instagram` | Muestra el enlace de Instagram |
| `!tiktok` | Muestra el enlace de TikTok |
| `!nivel` | Muestra tu nivel de trato actual (suscriptor/favorito) |
| `!instantgaming` | Envía una frase promocional de Instant Gaming |
| `!salir` | Cierra el bot (para mods o broadcasters) |

> Algunas frases promocionales se envían automáticamente cada X minutos (configurable).

### Comandos para mods y broadcasters

- `!salir` → Cierra el bot de forma segura.  
- Gestión de memoria y niveles de usuarios.  
- Administración de sorteos y votaciones en Twitch.  

---

## ⏱ Funcionalidades automáticas

- **Frases periódicas**: el bot puede enviar mensajes automáticos cada X minutos, como promociones o recordatorios.  
- **Registro de eventos**: guarda interacciones, niveles de usuarios y suscripciones.  
- **Sistema de memoria por usuario**: recuerda lo que le dijiste usando `!oye` y lo utiliza en futuras interacciones.  
- **Integración con iRacing**: genera frases sarcásticas según incidentes de pista (`X1_PHRASES`, `X2_PHRASES`, etc.).  

---

## 🛠 Estructura del proyecto

```text
bot_fantan/
├─ bot.py                 # Archivo principal del bot
├─ cogs/
│  ├─ promo.py
│  ├─ salir.py
│  └─ ...
├─ commands/
├─ core/
│  ├─ memory.py
│  ├─ twitch_manager.py
│  └─ iracing_listener.py
├─ data/
└─ phrases/
   ├─ bot/
   │  ├─ arrival.py
   │  ├─ exit.py
   │  └─ ...
   ├─ social/
   ├─ hello.py
   │  └─ instantgaming.py
   └─ ...
```

---

## 🔧 Requisitos

- Python 3.11+  
- Librerías indicadas en `requirements.txt`  
- Configuración de tokens y credenciales para Twitch, Discord y OpenAI (si se usan respuestas generadas)  

Instalación rápida de dependencias:

```bash
pip install -r requirements.txt
```