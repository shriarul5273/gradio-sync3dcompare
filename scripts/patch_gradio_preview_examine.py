from __future__ import annotations

from pathlib import Path


PATCH_SNIPPET = """        component_dir = os.getcwd()
        if component_dir not in sys.path:
            sys.path.insert(0, component_dir)

"""

ANCHOR = '        module_name = pyproject_toml["project"]["name"]\n'


def patch_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    if PATCH_SNIPPET in original:
        return False
    if ANCHOR not in original:
        raise RuntimeError(f"Could not find patch anchor in {path}")

    updated = original.replace(ANCHOR, PATCH_SNIPPET + ANCHOR, 1)
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    targets = [
        repo_root / "frontend" / "node_modules" / "@gradio" / "preview" / "src" / "examine.py",
        repo_root / "frontend" / "node_modules" / "@gradio" / "preview" / "dist" / "examine.py",
    ]

    patched_any = False
    for target in targets:
        if not target.exists():
            raise FileNotFoundError(f"Missing expected file: {target}")
        patched_any = patch_file(target) or patched_any

    print("patched" if patched_any else "already patched")


if __name__ == "__main__":
    main()
