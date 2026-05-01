from pathlib import Path


DOCS_PATH = Path("/app/Docs/src/content/docs")
DOCS_ROOT = DOCS_PATH.resolve()


def resolve_docs_file(filename: str) -> tuple[str, Path]:
    normalized = filename.strip().replace("\\", "/")
    if not normalized:
        raise ValueError("Filename is required.")

    if Path(normalized).is_absolute():
        raise ValueError("Filename must be relative to the docs directory.")

    if normalized.endswith("/"):
        raise ValueError("Filename must point to an .mdx file.")

    if not normalized.endswith(".mdx"):
        normalized = normalized + ".mdx"

    file_path = (DOCS_PATH / normalized).resolve()
    if DOCS_ROOT not in file_path.parents:
        raise ValueError("Filename must stay inside the docs directory.")

    return file_path.relative_to(DOCS_ROOT).as_posix(), file_path
