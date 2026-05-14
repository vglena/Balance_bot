from datetime import datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Europe/Madrid")

_DAYS_ES = {
    0: "lunes",
    1: "martes",
    2: "miércoles",
    3: "jueves",
    4: "viernes",
    5: "sábado",
    6: "domingo",
}


def get_runtime_context() -> dict:
    now = datetime.now(tz=_TZ)
    weekday = now.weekday()
    return {
        "fecha": now.strftime("%Y-%m-%d"),
        "hora": now.strftime("%H:%M"),
        "dia_semana": _DAYS_ES[weekday],
        "zona_horaria": "Europe/Madrid",
        "es_fin_de_semana": weekday >= 5,
    }


def format_runtime_context(ctx: dict) -> str:
    fin_semana = "sí" if ctx["es_fin_de_semana"] else "no"
    return (
        f"Fecha: {ctx['fecha']}\n"
        f"Hora: {ctx['hora']}\n"
        f"Día de la semana: {ctx['dia_semana']}\n"
        f"Zona horaria: {ctx['zona_horaria']}\n"
        f"Fin de semana: {fin_semana}"
    )
