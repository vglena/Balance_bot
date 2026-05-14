# Adaptación del día en curso

## Objetivo

Permitir que el agente ayude al usuario en cualquier momento del día, no solo por la mañana.

El sistema debe poder responder a cambios, dudas, huecos libres, cansancio, imprevistos, tareas nuevas o decisiones familiares sin rehacer innecesariamente todo el plan diario.

## Cuándo usar esta directiva

Usar cuando el usuario diga cosas como:

- "¿Qué hago ahora?"
- "Tengo un hueco de 30 minutos"
- "He terminado antes"
- "No me ha dado tiempo"
- "Estoy cansado"
- "Cambio de planes"
- "Tengo que comprar algo"
- "¿Voy al parque o a casa?"
- "Reajusta el plan"
- "Ya he hecho esto"
- "Me falta esto"

## Principios

- No rehacer todo el día si solo hace falta ajustar una parte.
- Mantener protegidas las recogidas de los niños.
- Mantener protegida la rutina de baños desde las 19:00.
- Priorizar lo siguiente más útil, no lo ideal.
- Adaptar la respuesta al tiempo disponible.
- Si hay poca energía, reducir ambición.
- Si hay incertidumbre, elegir la opción conservadora.
- No proponer tareas que generen estrés antes de una recogida.
- Distinguir entre trabajo profundo, trabajo ligero, casa, recados, niños y descanso.
- Si quedan menos de 60 minutos antes de salir para una recogida y la energía no es alta, recomendar una sola acción principal, breve y cerrable, más preparación para salir. No encadenar varias tareas aunque parezcan pequeñas.

## Información que debe revisar

Antes de responder, el agente debe revisar:

1. `context/current_day.md`
2. `memory/children_schedule.md`
3. `memory/locations.md`
4. `memory/work_context.md`
5. `memory/home_tasks.md`
6. `directives/school_pickup_protocol.md`
7. `directives/evening_routine.md`
8. `directives/daily_planning.md` si necesita el plan completo

## Preguntas mínimas si falta contexto

Si falta información importante, preguntar solo lo imprescindible:

- ¿Qué hora es ahora?
- ¿Cuánto tiempo real tienes?
- ¿Dónde estás?
- ¿Cómo estás de energía?
- ¿Qué es lo más urgente ahora?

No hacer más de dos preguntas a la vez salvo necesidad clara.

## Tipos de respuesta

### Si el usuario tiene un hueco corto

Proponer una acción pequeña:

- ordenar una zona
- revisar notas
- responder un mensaje
- preparar mochila
- poner lavadora
- recoger cocina
- descansar 10 minutos
- preparar salida

### Si el usuario está cerca de una recogida

Priorizar margen, calma y puntualidad.

No proponer:
- trabajo profundo
- compras largas
- limpieza grande
- recados con riesgo
- llamadas que puedan alargarse

Con menos de 60 minutos de margen, priorizar:
1. cerrar lo abierto
2. preparar salida
3. una única tarea ligera de máximo 15-20 minutos si hay calma real
4. salir con margen

En miércoles y viernes, cuando la recogida del mayor es a las 16:30, no apurar hasta el último minuto. El sistema debe preferir llegar tranquilo antes que exprimir un hueco.

### Si el usuario terminó trabajo antes

Revisar:
- si queda trabajo ligero
- si hay tareas domésticas pequeñas
- si conviene descansar
- si hay preparación para la tarde
- si existe margen antes de recogidas

### Si el usuario está cansado

Reducir a:
1. niños
2. trabajo urgente real
3. casa mínima
4. descanso

### Si el usuario pregunta por parque, colegio o casa

Cuando la decisión implique parque, colegio o volver a casa, consultar `skills/weather_decision.md` además de `directives/evening_routine.md` y `directives/school_pickup_protocol.md`.

Si existe acceso a clima real, usarlo. Si no existe, no inventar el clima y decir claramente que el clima no está confirmado.

Aunque el clima sea bueno, si hay cansancio, poco margen antes de baños o riesgo de llegar con prisas, priorizar parque de la urbanización o casa.

Decidir según:
- hora actual
- clima
- energía del usuario
- cansancio de los niños
- margen antes de baños
- si hay amigos en el colegio
- si hay tareas urgentes en casa

Opciones:
- colegio si hay amigos y no rompe la rutina
- Parque del Cine si hay tiempo, clima y energía
- parque de la urbanización si hay poco margen
- casa si hay cansancio, clima dudoso o poco tiempo

## Formato de respuesta recomendado

# Reajuste del plan

## Situación actual
Resumen breve.

## Mejor siguiente acción
Una recomendación clara.

## Alternativa si cambia algo
Plan B simple.

## Qué evitar ahora
Acciones que no convienen.
- No proponer una secuencia de varias tareas pequeñas justo antes de una recogida si eso puede crear sensación de carrera.

## Próximo punto de control
Cuándo volver a revisar.

## Regla crítica

En cualquier reajuste del día, la recogida de los niños y la rutina de tarde-noche tienen prioridad sobre cualquier optimización del plan.
