#!/usr/bin/env python3
"""
generate_weekly_review.py

Ensambla el contexto de la semana para facilitar la revisión semanal.
Lee memory/ y context/ y genera un resumen estructurado.
No toma decisiones: solo presenta la información para que el agente haga la revisión.

Uso:
    python execution/generate_weekly_review.py
"""

import sys
from pathlib import Path
from datetime import date, timedelta


BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "memory"
CONTEXT_DIR = BASE_DIR / "context"

DAYS_ES = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
           4: "Viernes", 5: "Sábado", 6: "Domingo"}


def read_file_safe(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"[Archivo no encontrado: {path.relative_to(BASE_DIR)}]"


def get_week_range(today: date) -> tuple[date, date]:
    """Devuelve el lunes y viernes de la semana actual."""
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday


def main():
    today = date.today()
    monday, friday = get_week_range(today)

    week_str = f"{monday.strftime('%d/%m/%Y')} – {friday.strftime('%d/%m/%Y')}"

    # Leer archivos relevantes
    session_notes = read_file_safe(MEMORY_DIR / "session_notes.md")
    work_context = read_file_safe(MEMORY_DIR / "work_context.md")
    home_tasks = read_file_safe(MEMORY_DIR / "home_tasks.md")
    current_week = read_file_safe(CONTEXT_DIR / "current_week.md")
    decision_log = read_file_safe(MEMORY_DIR / "decision_log.md")

    output = f"""# Revisión Semanal
## Semana del {week_str}

---

## Compromisos y contexto de la semana

{current_week}

---

## Notas de sesión de la semana

{session_notes}

---

## Estado del trabajo

{work_context}

---

## Tareas domésticas pendientes

{home_tasks}

---

## Decisiones recientes

{decision_log}

---

## Preguntas para la revisión

Con esta información, responde estas preguntas para hacer la revisión semanal:

1. ¿Qué trabajo he completado esta semana?
2. ¿Qué ha quedado sin hacer? ¿Se mueve a la semana siguiente o se elimina?
3. ¿La logística familiar ha funcionado bien?
4. ¿Las tareas domésticas están razonablemente al día?
5. ¿He descansado suficiente?
6. ¿Un aprendizaje de esta semana?
7. ¿Hay algo del sistema que ajustar?

Aplica la directiva `/directives/weekly_planning.md` para estructurar la revisión completa.
"""
    print(output)


if __name__ == "__main__":
    main()
