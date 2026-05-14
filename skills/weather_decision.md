# Skill: Weather Decision

## Objetivo

Ayudar al agente a tomar decisiones de tarde teniendo en cuenta clima, hora, energía, margen hasta baños y logística familiar.

## Cuándo usar esta skill

Usar cuando el usuario pregunte cosas como:

- "¿Voy al parque o a casa?"
- "¿Da tiempo al Parque del Cine?"
- "¿Nos quedamos en el colegio?"
- "¿Qué hacemos esta tarde?"
- "¿Hace buen día para parque?"

## Fuentes de clima

El agente debe usar la mejor fuente disponible, en este orden:

1. Clima indicado por el usuario en `context/current_day.md`.
2. Clima indicado por el usuario en la conversación.
3. Herramienta meteorológica si el entorno dispone de acceso a internet o API.
4. Si no hay datos, tratar el clima como desconocido y elegir opción conservadora.

## Regla importante

No inventar el clima.

Si el agente no puede consultar el clima real y el usuario no lo ha indicado, debe decir claramente:
"Ahora mismo no tengo clima confirmado."

## Criterios para Parque del Cine

Proponer Parque del Cine solo si:

- El clima es bueno o aceptable.
- Hay margen suficiente antes de baños.
- La energía del usuario no es baja.
- Los niños no están claramente cansados.
- No hay recados o tareas urgentes.
- El desplazamiento no añade estrés.

## Criterios para parque de la urbanización

Proponer parque de la urbanización si:

- Hay poco margen.
- Hay algo de energía, pero no mucha.
- Los niños necesitan moverse un poco.
- Se necesita una opción fácil de cortar.
- La rutina de baños está cerca.

## Criterios para volver a casa

Proponer casa si:

- Hay cansancio.
- El clima es malo o desconocido.
- Queda poco margen antes de baños.
- Hay riesgo de llegar con prisas.
- El usuario quiere una tarde tranquila.
- Los niños necesitan bajar revoluciones.

## Regla de prioridad

El clima favorable no basta por sí solo para ir al parque.

Aunque haga buen tiempo, si hay poco margen, cansancio o riesgo de retrasar la rutina familiar, el agente debe recomendar una opción más cercana o volver a casa.

## Resultado esperado

Una recomendación clara y práctica:
- opción recomendada
- alternativa simple
- motivo
- hora límite para volver o empezar rutina
La lluvia es más frecuente en otoño e invierno.
En verano, el calor puede hacer que la tarde sea mejor que la mañana para actividades exteriores con los niños.

---

## Límites

- No accede a información meteorológica en tiempo real
- El usuario debe indicar el tiempo en `/context/current_day.md`
- Si no se indica el tiempo, asumir "bueno" por defecto en la planificación
