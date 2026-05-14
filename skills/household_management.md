# Skill: Household Management — Gestión del Hogar

## Para qué sirve

Mantener un seguimiento de las tareas domésticas, priorizarlas y distribuirlas en el tiempo de forma que no se acumulen y no generen carga mental innecesaria.

---

## Inputs útiles

- Lista de tareas domésticas pendientes (`/memory/home_tasks.md`)
- Tiempo disponible en el día
- Nivel de energía del usuario
- Fecha de última realización de tareas recurrentes

---

## Outputs esperados

- Lista priorizada de tareas domésticas para el día (máximo 2)
- Slot horario recomendado para cada tarea
- Alerta si alguna tarea lleva demasiado tiempo sin hacerse
- Propuesta de lista de la compra si faltan productos básicos

---

## Categorías y frecuencias orientativas

| Tarea | Frecuencia | Urgencia si se retrasa |
|-------|-----------|----------------------|
| Compra semanal | Cada 5-7 días | Alta (sin comida) |
| Barrer/fregar | Semanal | Media |
| Baños/aseos | Semanal | Media |
| Ropa (lavar y doblar) | 2 veces por semana | Media |
| Ordenar juguetes | Cada 2-3 días | Baja |
| Papeles/administración | Mensual o según necesidad | Variable |

---

## Lógica de priorización

1. **Urgente**: falta comida, hay suciedad que afecta la salud o el funcionamiento
2. **Importante**: lleva más de 2 semanas sin hacerse
3. **Normal**: forma parte del mantenimiento regular
4. **Diferible**: mejora estética, orden no urgente

---

## Reglas de integración en el día

- Máximo 2 tareas domésticas por día en días de trabajo normal
- Las tareas que requieren salir (compra, recados) se combinan con rutas ya planificadas
- Las tareas del hogar no se hacen en el bloque familiar (17:00–20:30)
- Si hay poca energía, solo tarea urgente (categoría 1)

---

## Límites

- No gestiona tareas de trabajo ni logística de niños
- No propone reformas ni mejoras del hogar (fuera del alcance)
- No asume que el usuario tiene tiempo si el día ya está lleno
