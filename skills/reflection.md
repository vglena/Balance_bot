# Skill: Reflection

## Objetivo

Ayudar al agente a revisar cómo ha ido el día y extraer aprendizajes útiles para mejorar planes futuros.

## Cuándo usar esta skill

Usar al final del día o al día siguiente cuando el usuario diga algo como:

- "Cierra el día"
- "Haz revisión del día"
- "Actualiza memoria"
- "Esto funcionó"
- "Esto no funcionó"
- "Aprende esto para la próxima"

## Inputs útiles

- Plan generado para el día
- Qué se completó
- Qué no se completó
- Qué se retrasó
- Nivel de energía real
- Problemas con recogidas, trabajo, casa o niños
- Decisiones tomadas durante la tarde
- Feedback del usuario

## Outputs esperados

La skill debe producir:

1. Resumen breve del día.
2. Qué funcionó.
3. Qué no funcionó.
4. Aprendizajes para futuros planes.
5. Cambios sugeridos en memoria.
6. Próxima acción recomendada.

## Reglas

- No culpar al usuario si no se cumplió el plan.
- Distinguir entre fallo de planificación y cambio real de contexto.
- No guardar demasiadas cosas en memoria.
- Guardar solo patrones útiles o decisiones importantes.
- Si algo ocurrió una sola vez, registrarlo en session_notes.md.
- Si algo es una preferencia estable, sugerir añadirlo a preferences.md.
- Si una decisión cambia reglas futuras, sugerir añadirla a decision_log.md.

## Formato de revisión diaria

# Revisión del día

## 1. Resumen

## 2. Qué funcionó

## 3. Qué no funcionó

## 4. Aprendizajes

## 5. Memoria a actualizar

## 6. Próxima acción

## Resultado esperado

Una revisión ligera, útil y accionable que ayude al sistema a mejorar sin convertir el cierre del día en otra carga más.
