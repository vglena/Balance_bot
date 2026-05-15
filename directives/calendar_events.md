# Eventos en Google Calendar

## Objetivo

Crear eventos en Google Calendar desde mensajes de Telegram y programar recordatorios enviados por el propio bot.

## Cuándo usar

El flujo se activa con una frase de activación explícita: la palabra **evento** junto a un verbo de acción, o con mención explícita de **Google Calendar**.

### Activadores para CREAR eventos

Con la palabra "evento" (sin necesidad de mencionar Google Calendar):
- crea evento [día] a las [hora] [título]
- añade evento [día] a las [hora] [título]
- anota evento [día] a las [hora] [título]
- apunta evento [día] a las [hora] [título]
- pon evento [día] a las [hora] [título]

Con Google Calendar explícito:
- añade a Google Calendar
- añade al Google Calendar
- añadir a Google Calendar
- agrega a Google Calendar
- pon en Google Calendar
- anota en Google Calendar
- anota [contenido] en Google Calendar
- anótame en Google Calendar
- apunta en Google Calendar
- apúntame en Google Calendar

### Activadores para BORRAR eventos

Con la palabra "evento":
- borra evento [título] [día] a las [hora]
- elimina evento [título] [día] a las [hora]
- quita evento [título] [día] a las [hora]
- cancela evento [título] [día] a las [hora]

Con Google Calendar explícito:
- borra de Google Calendar [título]
- elimina de Google Calendar [título]
- quita de Google Calendar [título]
- borra el evento [título] de Google Calendar
- elimina [título] en Google Calendar

### Frases que NO activan el flujo

Estas van al LLM normalmente:
- "evento del colegio"
- "qué eventos tengo mañana"
- "hay un evento mañana"
- "anota mañana dentista" (sin "evento" ni Google Calendar)
- "borra dentista" (sin "evento" ni Google Calendar)
- "recuérdame"
- "apunta comprar leche"
- "cancela mañana" (sin "evento" ni Google Calendar)

Si alguna de estas frases parece una acción de calendario sin el activador correcto, el handler muestra un mensaje de guía al usuario antes de llegar al LLM.


## Datos obligatorios

Para crear un evento se necesita:

- título
- fecha
- hora

## Fechas aceptadas

El sistema debe entender:

- hoy
- mañana
- pasado mañana
- lunes, martes, miércoles, jueves, viernes, sábado, domingo
- el jueves
- este jueves
- próximo jueves
- fechas concretas como 23 de mayo, 23/05, 23-05-2026

## Horas aceptadas

El sistema debe entender:

- a las 10
- a las 10:30
- 10:00
- 17:30

## Duración por defecto

Si el usuario no indica duración, usar 30 minutos.

## Recordatorio por Telegram

Todo evento creado por el bot debe tener un recordatorio por Telegram 2 horas antes del evento.

El bot debe enviar el mensaje:

"Recordatorio: en 2 horas tienes [título]."

## Reglas

- No crear eventos si falta fecha.
- No crear eventos si falta hora.
- No inventar fecha ni hora.
- Si falta información, preguntar una sola aclaración.
- No guardar eventos en memory/.
- Google Calendar será la fuente de verdad del evento.
- El archivo context/scheduled_reminders.json puede usarse para persistir recordatorios pendientes del bot.

---

## Conflictos horarios al crear eventos

Cuando el usuario solicita crear un evento, el sistema comprueba si ya hay otro evento diferente en la misma franja horaria.

**Duplicado exacto** (mismo título + misma hora):
- No se crea el evento.
- El bot responde: "Ya existe un evento parecido: [título], [fecha] a las [hora]. No he creado duplicado."

**Conflicto horario** (distinto título, misma franja):
- No se crea el evento automáticamente.
- El bot lista los eventos conflictivos y pregunta: "¿Quieres crearlo igualmente?"
- Si el usuario confirma (sí / si / confirmo / créalo / crealo / adelante): se crea el evento.
- Si el usuario cancela (no / cancelar / cancela): "Cancelado. No he creado el evento."

---

## Ventanas familiares protegidas

Antes de crear cualquier evento, el bot comprueba si el horario propuesto solapa con una ventana familiar protegida. Si solapa, **no crea el evento** — pide confirmación explícita al usuario.

### Lunes a viernes

| Ventana | Horario | Motivo |
|---------|---------|--------|
| Mañana lectiva | 07:30–09:15 | Preparar y llevar a los niños al colegio; entran a las 9:00 |
| Recogida lunes/martes/jueves | 16:45–18:00 | Pequeño a las 17:00 y mayor a las 17:30 |
| Recogida miércoles/viernes | 16:15–17:30 | Mayor a las 16:30 y pequeño a las 17:00 |
| Rutina tarde-noche | 19:00–20:30 | Baños, cena y dormir |
| Transición noche | 20:30–21:00 | Descanso posterior a dormir a los niños |

### Sábado y domingo

No se aplican las ventanas de colegio ni recogida escolar.
Sí se aplican rutina tarde-noche (19:00–20:30) y transición noche (20:30–21:00).

### Respuesta si hay conflicto familiar

Un único conflicto:
> "Ese horario coincide con [motivo]. ¿Quieres crearlo igualmente?"

Varios conflictos:
> "Ese horario tiene varios conflictos familiares:
> - [motivo 1]
> - [motivo 2]
> ¿Quieres crearlo igualmente?"

### Confirmación y cancelación

Confirmación (sí / si / confirmo / créalo / crealo / adelante) → continuar con validaciones de Google Calendar (duplicado → conflicto → crear).
Cancelación (no / cancelar / cancela) → "Cancelado. No he creado el evento."

### Orden completo de validaciones al crear un evento

1. Parsear fecha, hora y título.
2. Comprobar ventanas familiares protegidas.
3. Si hay conflicto familiar → pedir confirmación. Si cancela, parar.
4. Si no hay conflicto familiar (o el usuario confirmó) → comprobar duplicado exacto en Google Calendar.
5. Comprobar conflicto horario con otros eventos de Google Calendar.
6. Crear evento.
7. Programar recordatorio Telegram 2 horas antes.

Si hay conflicto familiar Y conflicto de Google Calendar: se resuelven en orden. Primero familiar, luego Google Calendar. No se crea hasta que todas las confirmaciones estén resueltas.

---

## Borrar eventos de Google Calendar

El flujo de borrado se activa con la palabra **evento** junto a un verbo de borrado, o con mención explícita de **Google Calendar**. Ver sección "Cuándo usar" al inicio.

Frases que **no** activan el flujo de borrado:

- borra esto
- elimina dentista (sin "evento")
- quita la tarea del martes (sin "evento")
- cancela mañana (sin "evento")

Estas frases, si parecen referirse a un calendario, son interceptadas antes del LLM con un mensaje de guía.

**Proceso de borrado:**

1. El sistema busca eventos que coincidan con el título y, si se indica, la fecha y/o hora.
2. Si no se encuentra ningún evento: "No he encontrado ningún evento que coincida con tu búsqueda."
3. Si se encuentra uno solo: el bot muestra el evento y pregunta: "¿Quieres borrarlo?"
4. Si se encuentran varios: el bot lista todos y pide al usuario que elija por número.
5. Tras confirmar, el bot borra el evento y cancela el recordatorio de Telegram si lo había.

**Palabras de confirmación para borrar:** sí / si / confirmo / bórralo / borralo / elimínalo / eliminalo
**Palabras de cancelación:** no / cancelar / cancela

Reglas de seguridad:
- Nunca borrar sin confirmación explícita del usuario.
- Nunca borrar en bloque (varios a la vez).
- No borrar si ENABLE_GOOGLE_CALENDAR=false.
- No ejecutar ningún borrado si el mensaje es ambiguo.

---

## Borrados masivos — bloqueados por seguridad

Frases como:
- "borra todos los eventos"
- "elimina todos los eventos de mañana"
- "borra mis eventos"
- "cancela todos"
- "eliminar mis eventos"

Son rechazadas sin ninguna acción.

Respuesta: "No puedo borrar eventos en masa por seguridad. Puedo ayudarte a borrar uno cada vez. Ejemplo: borra evento Dentista mañana a las 10."

---

## Modificación de eventos — no implementada

Frases con "modifica evento", "cambia evento", "mueve evento", "actualiza evento" reciben una respuesta informativa:
"Todavía no modifico eventos directamente. Puedo ayudarte a borrar el evento anterior y crear uno nuevo."

---

## Fallback defensivo antes del LLM

Frases que usan verbos de acción de calendario sin "evento" ni "Google Calendar" son interceptadas antes de llegar al LLM.

Ejemplos interceptados:
- "crea mañana dentista" → guía: usa "crea evento mañana a las [hora] Dentista"
- "borra dentista" → guía
- "cancela lo de mañana" → guía
- "modifica dentista" → guía

Respuesta del fallback: "Para acciones reales de calendario usa una frase con la palabra evento. Ejemplo: crea evento mañana a las 10 Dentista o borra evento Dentista mañana a las 10."

---

## Cancelación de recordatorios

Al borrar un evento de Google Calendar, el recordatorio de Telegram programado para ese evento queda cancelado automáticamente.
El recordatorio se marca como "cancelled" en context/scheduled_reminders.json y el job de APScheduler se elimina de la cola.
