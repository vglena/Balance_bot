# Agente Principal — mi-vida-ai-workspace

Este directorio contiene el cerebro operativo del sistema.

## Qué hay aquí

| Archivo | Propósito |
|---------|-----------|
| `master_agent.md` | Comportamiento e instrucciones del agente principal |
| `operating_principles.md` | Principios que guían todas las decisiones |
| `daily_rhythm.md` | Ritmo diario de referencia con bloques de tiempo |

## Cómo usar el sistema

1. Escribe en `/context/current_day.md` lo que pasa hoy (energía, compromisos, imprevistos)
2. Actualiza `/context/today_constraints.md` si hay restricciones especiales
3. Pide al agente que genere un plan diario
4. El agente leerá `/memory`, luego `/context`, aplicará las directivas y generará el plan

## Principio fundamental

El agente no optimiza para la productividad máxima.
Optimiza para un día sostenible: niños atendidos, trabajo avanzando, casa en orden y algo de descanso.
