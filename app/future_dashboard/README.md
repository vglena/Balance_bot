# Future Dashboard — Notas de Diseño

> Este directorio es un espacio de planificación para el dashboard futuro.
> No hay código aquí todavía. Solo ideas y requisitos.

---

## Concepto

Un dashboard minimalista que muestre de un vistazo:
- El plan del día
- La hora de recogida
- Las tareas pendientes más urgentes
- El estado de la semana

---

## Requisitos (cuando llegue el momento)

### Funcionales
- Mostrar el plan generado en `/context/current_day.md`
- Mostrar la hora de recogida del día
- Mostrar el inbox de tareas pendientes
- Actualización manual (no en tiempo real para empezar)

### No funcionales
- Sin dependencias externas complejas
- Puede ser un archivo HTML estático si es suficiente
- Debe funcionar en local sin servidor
- No requiere cuenta ni login

---

## Tecnologías candidatas (para cuando sea necesario)

| Opción | Pros | Contras |
|--------|------|---------|
| HTML estático | Sin dependencias | Limitado en interactividad |
| Svelte | Ligero, sin framework pesado | Requiere build step |
| Streamlit (Python) | Fácil de hacer, rápido | Requiere servidor local |

**Decisión actual:** nada todavía. Cuando llegue el momento, elegir la opción más simple que cubra la necesidad.

---

## Notas

- No construir esto hasta que el sistema Markdown funcione bien durante al menos 2-4 semanas
- El dashboard no es un requisito para que el sistema funcione
- Priorizar consolidar los hábitos de uso antes de añadir interfaz
