# Skill: Scheduling — Planificación de Bloques Horarios

## Para qué sirve

Asignar tareas a bloques horarios concretos dentro del día, respetando el ritmo personal y la logística familiar.
Evita solapar trabajo con recogidas, rutinas o descanso.

---

## Inputs útiles

- Día de la semana (determina hora de recogida)
- Nivel de energía del usuario (`/context/current_day.md`)
- Lista de tareas a planificar
- Restricciones del día (`/context/today_constraints.md`)
- Horarios familiares (`/memory/children_schedule.md`)

---

## Outputs esperados

- Plan con tareas asignadas a bloques horarios
- Bloques protegidos claramente marcados
- Indicación de qué queda fuera si hay sobrecarga

---

## Lógica de asignación

### Tipos de bloques disponibles

| Bloque | Horario habitual | Mejor para |
|--------|-----------------|------------|
| Trabajo profundo | 09:00–13:00 | Tareas de alta concentración |
| Trabajo ligero | 14:30–16:30 | Emails, revisiones, gestiones |
| Pre-recogida | Variable | Recados, tareas cortas |
| Nocturno | 21:00–22:00 | Planificación, tareas suaves |

### Reglas de asignación

1. Las tareas de alta concentración van por la mañana
2. Las reuniones y emails van a la tarde si es posible
3. Las tareas domésticas van en pausas o tarde pre-recogida
4. El bloque nocturno es opcional y no se sobrecarga
5. Si hay más tareas que tiempo, se pospone lo menos urgente

---

## Límites

- No asigna tareas al bloque 17:00–20:30 (bloque familiar)
- No asigna trabajo profundo al bloque nocturno si hay señales de fatiga
- No crea bloques ficticios: si no hay tiempo, no hay tiempo
- No ignora las restricciones declaradas en el contexto del día
