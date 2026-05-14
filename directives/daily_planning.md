# Planificación diaria

## Objetivo

Generar un plan diario realista que combine trabajo, casa, niños, recados y descanso sin sobrecargar el día.

## Orden obligatorio de planificación

El agente debe planificar en este orden:

1. Leer context/current_day.md.
2. Leer memory/user_profile.md.
3. Leer memory/work_context.md.
4. Leer memory/home_tasks.md.
5. Leer memory/children_schedule.md.
6. Leer memory/locations.md.
7. Leer directives/school_pickup_protocol.md.
8. Identificar compromisos fijos.
9. Bloquear recogidas y rutina familiar.
10. Planificar trabajo.
11. Planificar casa y recados.
12. Añadir pausas solo si encajan.
13. Crear plan mínimo si el día se complica.

## Reglas obligatorias

- La recogida de los niños siempre gana.
- Ningún bloque de trabajo debe poner en riesgo la recogida.
- No planificar trabajo profundo cerca de la salida para recoger.
- No llenar el día con demasiadas tareas domésticas.
- El plan debe adaptarse a la energía indicada en current_day.md.
- Si falta información, usar una opción conservadora.
- Si hay conflicto entre trabajo y familia, señalarlo explícitamente.
- Siempre incluir un plan mínimo.
- No inventar el nivel de energía del usuario. Si el usuario no indica energía, cansancio o estado físico/mental, no asumir "media", "alta" o "baja". En ese caso, planificar de forma conservadora y mencionar que la energía no fue indicada.
- En días lectivos, antes de las 9:00 debe considerarse franja familiar/logística de mañana. El trabajo real, recados o desplazamientos no esenciales deben planificarse normalmente después de dejar a los niños, salvo indicación explícita del usuario.
- Diferenciar siempre entre entrada y recogida:
  - Entrada: por la mañana, los niños entran al colegio/guardería a las 9:00.
  - Recogida: por la tarde, se aplica el horario de memory/children_schedule.md y directives/school_pickup_protocol.md.
  - Nunca llamar "recogida" a la entrada de las 9:00.
  - Nunca tratar las 9:00 como hora de recogida.

## Formato de salida del plan diario

El agente debe responder con esta estructura:

# Plan de hoy

## 1. Resumen rápido
Estado indicado por el usuario, restricciones, trabajo clave, niños y clima.

## 2. Tres prioridades reales
Máximo tres prioridades.

## 3. Bloques del día
Mañana, mediodía, tarde y noche.

## 4. Logística de niños
Separar explícitamente:
- Entrada de mañana: hora en que los niños entran al colegio/guardería (9:00 en días lectivos).
- Recogidas de tarde: hora exacta según el día, aplicando memory/children_schedule.md.
Opción recomendada después de recoger.

## 5. Trabajo
Bloques de trabajo profundo, ligero o reuniones.

## 6. Casa y recados
Solo tareas realistas.

## 7. Descanso
Pausas posibles si no compiten con lo importante.

## 8. Riesgos del día
Conflictos, cansancio, clima, retrasos o exceso de tareas.

## 9. Plan mínimo
Qué hacer si el día se complica.

## 10. Memoria a actualizar
Qué debería registrarse al final del día.

## Validaciones finales

Antes de entregar el plan, comprobar:

- ¿Está protegida la recogida?
- ¿Está protegida la rutina de baños desde las 19:00?
- ¿El trabajo cabe realmente?
- ¿Las tareas de casa son razonables?
- ¿Hay plan mínimo?
- ¿El plan respeta la energía del usuario si fue indicada?
- ¿El plan respeta la entrada de los niños a las 9:00 y no ocupa la franja previa con tareas incompatibles?
- ¿El plan diferencia correctamente entrada de mañana y recogida de tarde?
- ¿El plan evita inventar energía o estado del usuario no indicado?

## Resultado esperado

Un plan diario claro, realista, ejecutable y compatible con la logística familiar.
