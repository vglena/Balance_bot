#!/usr/bin/env python3
"""
generate_daily_plan.py

Lee el contexto del día y la memoria del sistema y genera un plan diario estructurado.
No toma decisiones: solo ensambla la información disponible en un formato útil.
Las decisiones de planificación las toma el agente.

Uso:
    python execution/generate_daily_plan.py
    python execution/generate_daily_plan.py --date 2026-05-14
"""

import argparse
import sys
from pathlib import Path
from datetime import date, datetime


# Rutas base del workspace
BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "memory"
CONTEXT_DIR = BASE_DIR / "context"


DAYS_ES = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

# Horarios de recogida por día (0=lunes, 4=viernes)
PICKUP_SCHEDULE = {
    0: {"mayor": "17:30", "pequeño": "17:00", "salir": "~16:50"},
    1: {"mayor": "17:30", "pequeño": "17:00", "salir": "~16:50"},
    2: {"mayor": "16:30", "pequeño": "17:00", "salir": "~16:15"},
    3: {"mayor": "17:30", "pequeño": "17:00", "salir": "~16:50"},
    4: {"mayor": "16:30", "pequeño": "17:00", "salir": "~16:15"},
}


def read_file_safe(path: Path) -> str:
    """Lee un archivo de forma segura. Devuelve string vacío si no existe."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"[Archivo no encontrado: {path.relative_to(BASE_DIR)}]"


def get_pickup_info(weekday: int) -> str:
    """Devuelve la información de recogida para el día dado."""
    if weekday >= 5:
        return "Fin de semana — no hay recogida escolar"

    schedule = PICKUP_SCHEDULE[weekday]
    day_name = DAYS_ES[weekday]

    if weekday in (2, 4):  # Miércoles y viernes
        return (
            f"**Recogida temprana ({day_name}):**\n"
            f"- Salir de casa: {schedule['salir']}\n"
            f"- Mayor (Colegio Los Olivos): {schedule['mayor']}\n"
            f"- Pequeño (guardería): {schedule['pequeño']}"
        )
    else:
        return (
            f"**Recogida estándar ({day_name}):**\n"
            f"- Salir de casa: {schedule['salir']}\n"
            f"- Pequeño (guardería): {schedule['pequeño']}\n"
            f"- Mayor (Colegio Los Olivos): {schedule['mayor']}"
        )


def generate_plan(target_date: date) -> str:
    """Genera el resumen de contexto para el plan del día."""
    weekday = target_date.weekday()
    day_name = DAYS_ES[weekday]
    date_str = target_date.strftime("%d/%m/%Y")

    # Leer archivos de contexto
    current_day = read_file_safe(CONTEXT_DIR / "current_day.md")
    constraints = read_file_safe(CONTEXT_DIR / "today_constraints.md")
    inbox = read_file_safe(CONTEXT_DIR / "inbox.md")

    # Leer archivos de memoria relevantes
    work_context = read_file_safe(MEMORY_DIR / "work_context.md")
    home_tasks = read_file_safe(MEMORY_DIR / "home_tasks.md")

    # Información de recogida
    pickup_info = get_pickup_info(weekday)

    output = f"""# Contexto para el plan del día
## {day_name}, {date_str}

---

## Recogida de hoy

{pickup_info}

---

## Contexto del día

{current_day}

---

## Restricciones de hoy

{constraints}

---

## Inbox (pendientes)

{inbox}

---

## Trabajo activo

{work_context}

---

## Tareas domésticas pendientes

{home_tasks}

---

## Instrucciones para el agente

Con esta información, aplica la directiva `/directives/daily_planning.md` para generar el plan del día.
Recuerda:
- Máximo 3 tareas de trabajo
- Bloque familiar protegido ({pickup_info.split(chr(10))[0]})
- 1-2 tareas domésticas si las hay
- Descanso si hay margen
"""
    return output


def main():
    parser = argparse.ArgumentParser(description="Genera el contexto para el plan diario")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Fecha en formato YYYY-MM-DD (por defecto: hoy)",
    )
    args = parser.parse_args()

    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: formato de fecha inválido '{args.date}'. Usar YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = date.today()

    plan_context = generate_plan(target_date)
    print(plan_context)


if __name__ == "__main__":
    main()
