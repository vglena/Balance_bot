# App — Interfaz de Usuario (futura)

Esta carpeta está reservada para la futura experiencia de usuario o dashboard del sistema.

**En esta fase inicial, no hay nada que construir aquí.**
El sistema funciona íntegramente desde Markdown y línea de comandos.

---

## Cuándo usar esta carpeta

Solo cuando se decida construir una interfaz gráfica, una aplicación web o un dashboard visual.
Hasta entonces, esta carpeta existe como placeholder para mantener la arquitectura limpia.

---

## Principios para cuando se construya

1. La app es una capa de presentación, no de lógica
2. La lógica sigue viviendo en `/agent`, `/directives` y `/skills`
3. La app lee de `/memory` y `/context`, no duplica información
4. La app no debe romper el funcionamiento del sistema sin UI

---

## Ideas para el futuro (no compromisos)

- Dashboard diario en HTML/CSS simple
- Vista de plan del día generada automáticamente
- Checklist interactivo para la rutina de tarde
- Visualización del estado de proyectos de trabajo

---

## Ver también

- `future_dashboard/README.md` — notas sobre el dashboard eventual
