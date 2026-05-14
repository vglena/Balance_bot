# Execution — Scripts y Checklists

Esta carpeta contiene scripts deterministas y checklists operativos.

## Qué hay aquí

| Archivo | Propósito |
|---------|-----------|
| `generate_daily_plan.py` | Genera un plan diario leyendo contexto y memoria |
| `generate_weekly_review.py` | Genera la revisión semanal |
| `update_memory.py` | Actualiza archivos de memoria desde línea de comandos |
| `checklists/` | Checklists en Markdown para rutinas diarias |

## Principios de esta carpeta

- Los scripts son deterministas: dado el mismo input, producen el mismo output
- No hay lógica de negocio aquí: solo procesamiento de archivos
- Las decisiones las toma el agente, no los scripts
- Los scripts leen de `/memory` y `/context`, escriben en `/context` o en stdout

## Cómo ejecutar

```bash
python execution/generate_daily_plan.py
python execution/generate_weekly_review.py
python execution/update_memory.py --file memory/home_tasks.md
```

## Dependencias

- Python 3.8+
- No se requieren librerías externas (solo stdlib)
- Los archivos de entrada deben existir y estar en formato Markdown correcto
