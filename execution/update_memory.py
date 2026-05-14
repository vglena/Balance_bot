#!/usr/bin/env python3
"""
update_memory.py

Herramienta de línea de comandos para actualizar archivos de memoria de forma controlada.
Permite añadir entradas a los archivos de memoria sin editar manualmente.

Uso:
    python execution/update_memory.py --list              # Ver archivos de memoria disponibles
    python execution/update_memory.py --file memory/session_notes.md --append "## 2026-05-13\n- Bien: ..."
    python execution/update_memory.py --file memory/home_tasks.md --show
"""

import argparse
import sys
from pathlib import Path
from datetime import date


BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "memory"


def list_memory_files():
    """Lista todos los archivos de memoria disponibles."""
    files = sorted(MEMORY_DIR.glob("*.md"))
    if not files:
        print("No se encontraron archivos de memoria.")
        return
    print("Archivos de memoria disponibles:")
    for f in files:
        size = f.stat().st_size
        print(f"  - memory/{f.name} ({size} bytes)")


def show_file(file_path: Path):
    """Muestra el contenido de un archivo."""
    if not file_path.exists():
        print(f"Error: el archivo '{file_path}' no existe.", file=sys.stderr)
        sys.exit(1)
    print(file_path.read_text(encoding="utf-8"))


def append_to_file(file_path: Path, content: str):
    """Añade contenido al final de un archivo."""
    if not file_path.exists():
        print(f"Error: el archivo '{file_path}' no existe.", file=sys.stderr)
        sys.exit(1)

    # Asegurar que hay una línea en blanco antes del nuevo contenido
    current = file_path.read_text(encoding="utf-8")
    separator = "\n\n" if not current.endswith("\n\n") else ""

    # Reemplazar \n literales en el argumento por saltos de línea reales
    content_processed = content.replace("\\n", "\n")

    with file_path.open("a", encoding="utf-8") as f:
        f.write(separator + content_processed + "\n")

    print(f"Contenido añadido a {file_path.relative_to(BASE_DIR)}")


def resolve_path(file_arg: str) -> Path:
    """Resuelve la ruta del archivo dado un argumento relativo o absoluto."""
    p = Path(file_arg)
    if p.is_absolute():
        return p
    # Intentar relativo al BASE_DIR
    candidate = BASE_DIR / p
    if candidate.exists():
        return candidate
    # Intentar directamente
    if p.exists():
        return p
    # Devolver relativo al BASE_DIR aunque no exista (para mostrar error correcto)
    return BASE_DIR / p


def main():
    parser = argparse.ArgumentParser(
        description="Actualiza archivos de memoria del sistema"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="Lista archivos de memoria disponibles")
    group.add_argument("--show", metavar="FILE", help="Muestra el contenido de un archivo")
    group.add_argument("--append", nargs=2, metavar=("FILE", "CONTENT"),
                       help="Añade contenido al final de un archivo")

    args = parser.parse_args()

    if args.list:
        list_memory_files()
    elif args.show:
        show_file(resolve_path(args.show))
    elif args.append:
        file_arg, content = args.append
        append_to_file(resolve_path(file_arg), content)


if __name__ == "__main__":
    main()
