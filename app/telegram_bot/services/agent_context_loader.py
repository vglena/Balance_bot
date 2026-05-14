from pathlib import Path

# Workspace root is three levels above this file:
# services/ → telegram_bot/ → app/ → workspace root
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

# Single files to always include
_FILES_TO_LOAD = [
    "CLAUDE.md",
]

# Directories: load all .md files at the top level of each
_DIRS_TO_LOAD = [
    "memory",
    "context",
    "directives",
    "skills",
]

# Safety limit per file to avoid overwhelming the LLM context
_MAX_CHARS_PER_FILE = 8_000


def _read_file(path: Path) -> str | None:
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        if len(content) > _MAX_CHARS_PER_FILE:
            content = content[:_MAX_CHARS_PER_FILE] + "\n[... truncado ...]"
        return content
    except Exception:
        return None


def load_agent_context() -> str:
    sections: list[str] = []

    for filename in _FILES_TO_LOAD:
        content = _read_file(_WORKSPACE_ROOT / filename)
        if content:
            sections.append(f"### {filename}\n\n{content}")

    for dirname in _DIRS_TO_LOAD:
        dir_path = _WORKSPACE_ROOT / dirname
        if not dir_path.is_dir():
            continue
        for md_file in sorted(dir_path.glob("*.md")):
            content = _read_file(md_file)
            if content:
                rel = md_file.relative_to(_WORKSPACE_ROOT).as_posix()
                sections.append(f"### {rel}\n\n{content}")

    return "\n\n---\n\n".join(sections)
