# Telegram Bot — mi-vida-ai

Telegram es el canal principal de interacción con el sistema.
El IDE se usa solo para desarrollar. El usuario interactúa desde el móvil via Telegram.

---

## Arquitectura

```
app/telegram_bot/
├── bot.py                          ← punto de entrada
├── config.example.env              ← plantilla de variables de entorno
├── requirements.txt
├── handlers/
│   └── message_handler.py          ← recibe y procesa mensajes
├── services/
│   ├── runtime_context.py          ← genera fecha/hora/día automáticamente
│   ├── agent_context_loader.py     ← carga archivos del workspace
│   └── llm_client.py               ← cliente placeholder para el modelo IA
└── prompts/
    └── telegram_system_prompt.md   ← instrucciones del sistema para el bot
```

La lógica cognitiva del sistema vive en `/agent`, `/memory`, `/directives` y `/skills`.
El bot es solo el canal de conversación.

---

## Configuración del .env

Copia `config.example.env` como `.env` en la raíz del workspace:

```
cp app/telegram_bot/config.example.env .env
```

> ⚠️ El archivo `.env` nunca debe subirse a Git. Añádelo a `.gitignore`.

### Variables del bot de Telegram

| Variable | Descripción |
|---|---|
| `BOT_NAME` | Nombre del bot (solo informativo) |
| `BOT_USERNAME` | Username del bot en Telegram (sin @) |
| `BOT_LINK` | Enlace directo al bot (t.me/...) |
| `BOT_API` | **Token del bot de Telegram. Obtenido de @BotFather. Es el token de autenticación.** |

### Variables del modelo IA

| Variable | Descripción |
|---|---|
| `LLM_PROVIDER` | Proveedor del modelo (ej: `openai`, `anthropic`, `openrouter`) |
| `LLM_API_KEY` | API key del proveedor del modelo |
| `LLM_MODEL` | Nombre del modelo (ej: `gpt-4o`, `claude-3-5-sonnet-20241022`) |

### Variables de seguridad

| Variable | Descripción |
|---|---|
| `AUTHORIZED_TELEGRAM_USER_ID` | ID numérico de Telegram del usuario autorizado. Si está vacío, el bot acepta mensajes de cualquier usuario. Para saber tu ID, habla con @userinfobot en Telegram. |

---

## Formato del .env

El archivo `.env` debe usar el formato `CLAVE=VALOR` (sin espacios alrededor del `=`):

```
BOT_API=tu_token_aqui
LLM_PROVIDER=openai
```

> ⚠️ No uses `CLAVE: VALOR` (formato YAML). `python-dotenv` espera `CLAVE=VALOR`.

---

## Ejecutar en local

```bash
cd c:\Users\bison\Documents\mi-vida-ai-workspace

# Instalar dependencias
pip install -r app/telegram_bot/requirements.txt

# Ejecutar el bot (polling)
python app/telegram_bot/bot.py
```

El bot arranca en modo **polling**: consulta activamente a Telegram por nuevos mensajes.
No requiere webhook ni servidor público.

---

## Seguridad

- `BOT_API` es el token de autenticación del bot. Trátalo como una contraseña.
- Si el token se expone accidentalmente, revócalo en @BotFather con `/revoke`.
- Configura `AUTHORIZED_TELEGRAM_USER_ID` para que solo tú puedas usar el bot.
- Añade `.env` a `.gitignore` antes de hacer cualquier commit.

### Cómo obtener tu Telegram user ID

1. Abre Telegram y busca **@userinfobot**.
2. Escríbele cualquier mensaje (por ejemplo, `/start`).
3. Te responderá con tu ID numérico, por ejemplo: `Id: 123456789`.
4. Copia ese número y ponlo en `.env`:
   ```
   AUTHORIZED_TELEGRAM_USER_ID=123456789
   ```

### Comportamiento según configuración

| Situación | Comportamiento |
|---|---|
| `AUTHORIZED_TELEGRAM_USER_ID` vacío | El bot responde a cualquier usuario. Muestra advertencia en logs al arrancar. |
| `AUTHORIZED_TELEGRAM_USER_ID` configurado, usuario coincide | El bot responde normalmente. |
| `AUTHORIZED_TELEGRAM_USER_ID` configurado, usuario no coincide | El bot responde "No autorizado." y registra el intento en logs. No llama al LLM. |

---

## Proactive check-ins

The bot sends an automatic message to the authorized user at two fixed times on weekdays:

| Time | Purpose |
|---|---|
| 13:00 | Midday check-in — review morning progress and plan before pickups |
| 18:30 | Afternoon check-in — review family situation before baths and close of day |

**Active days:** Monday to Friday only. No messages on Saturday or Sunday.

**Requirements:**
- `AUTHORIZED_TELEGRAM_USER_ID` must be set. If not configured, check-ins are skipped with a warning in the logs.
- The bot must be running at the scheduled time (polling mode). There is no persistence — if the bot is stopped, missed check-ins are not sent.

**Disable check-ins temporarily:**

Set `ENABLE_PROACTIVE_CHECKINS=false` in `.env` and restart the bot:

```
ENABLE_PROACTIVE_CHECKINS=false
```

To re-enable, set it back to `true` or remove the variable entirely.

**Test commands (manual trigger):**

| Command | What it does |
|---|---|
| `/test_checkin_midday` | Sends the 13:00 check-in message immediately |
| `/test_checkin_afternoon` | Sends the 18:30 check-in message immediately |

These commands are for testing only. They do not replace the automatic scheduled check-ins. Both require `AUTHORIZED_TELEGRAM_USER_ID` to match the sender — unauthorized users receive "No autorizado."
