"""Boundary rules: views never hold business logic or import other modules' models."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"


def imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module, [a.name for a in node.names]


def test_api_layers_do_not_import_foreign_models():
    bad = []
    for f in MODULES.glob("*/api/*.py"):
        own = f.parts[f.parts.index("modules") + 1]
        for mod, _ in imports(f):
            parts = mod.split(".")
            if (
                parts[0] == "modules"
                and len(parts) > 2
                and parts[2] == "models"
                and parts[1] not in (own, "common")
            ):
                bad.append(f"{f.relative_to(ROOT)} imports {mod}")
    # content.api composes game reads (selectors) and serialises its own models; platform metrics reads counters
    allowed = {
        "modules/platform/api/views.py",
        "modules/content/api/views.py",
        "modules/content/api/serializers.py",
    }
    bad = [b for b in bad if b.split(" ")[0] not in allowed]
    assert not bad, bad


def test_domain_layers_do_not_depend_on_api_or_admin():
    bad = []
    for f in (
        list(MODULES.glob("*/services.py"))
        + list(MODULES.glob("*/selectors.py"))
        + list(MODULES.glob("*/models.py"))
    ):
        for mod, _ in imports(f):
            if ".api" in mod or mod.endswith(".admin"):
                bad.append(f"{f.relative_to(ROOT)} -> {mod}")
    assert not bad, bad


def test_games_and_sources_do_not_depend_on_content_or_ingest():
    for name in ("games", "sources"):
        for f in (MODULES / name).rglob("*.py"):
            if "migrations" in f.parts or "management" in f.parts:
                continue
            for mod, _ in imports(f):
                assert not mod.startswith(
                    ("modules.content", "modules.ingest", "modules.review", "modules.newsletter")
                ) or f.name in ("hook_views.py",), f"{f} -> {mod}"


def test_llm_package_has_no_domain_model_imports():
    for f in (ROOT / "llm").glob("*.py"):
        for mod, _ in imports(f):
            assert not (mod.startswith("modules.") and mod.endswith("models")), f"{f} -> {mod}"
