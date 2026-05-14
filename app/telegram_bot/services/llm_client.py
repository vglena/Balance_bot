import logging
import os
import httpx

logger = logging.getLogger(__name__)


def _placeholder_response(user_message: str) -> str:
    preview = user_message[:80] + "..." if len(user_message) > 80 else user_message
    return (
        "✅ Mensaje recibido.\n"
        "✅ Contexto operativo generado (fecha, hora, día de la semana).\n"
        "✅ Contexto del sistema cargado (memory, directives, skills).\n\n"
        f"Mensaje recibido: «{preview}»\n\n"
        "⚠️ Modelo IA no configurado.\n"
        "Para activar respuestas reales, rellena en .env:\n"
        "  LLM_PROVIDER=\n"
        "  LLM_API_KEY=\n"
        "  LLM_MODEL="
    )


async def call_llm(system_prompt: str, user_message: str) -> str:
    """
    Llama al modelo IA configurado y devuelve la respuesta como texto.

    Lee la configuración en cada llamada para respetar cambios en .env
    sin necesidad de reiniciar el proceso.
    """
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if not provider or not api_key or not model:
        logger.info("LLM no configurado — devolviendo respuesta placeholder.")
        return _placeholder_response(user_message)

    if provider in ("openai", "openrouter"):
        return await _call_openai_compatible(provider, api_key, model, system_prompt, user_message)

    return f"⚠️ Proveedor '{provider}' no implementado todavía."


async def _call_openai_compatible(
    provider: str, api_key: str, model: str, system_prompt: str, user_message: str
) -> str:
    base_urls = {
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
    }
    base_url = base_urls.get(provider, "https://api.openai.com/v1")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 800,
        "temperature": 0.4,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        return f"⚠️ Error del modelo ({e.response.status_code}). Inténtalo de nuevo."
    except Exception:
        return "⚠️ Error al conectar con el modelo IA. Inténtalo de nuevo."
