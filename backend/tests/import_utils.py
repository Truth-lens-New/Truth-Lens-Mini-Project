"""
Import isolation helpers for TruthLens unit tests.

TruthLens package __init__ modules import spaCy/transformers/httpx chains.
These helpers stub the internal packages with lightweight namespace shells so a
single stdlib-only module can be imported and its real file executed directly —
without downloading ML models or importing the ML stack.
"""

import contextlib
import importlib
import sys
import types
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def isolated_imports(packages=("app", "app.services")):
    """
    Context manager that:

    1. Removes the real package objects for `packages` (and everything under
       them) from sys.modules, remembering the originals.
    2. Installs stub packages pointing at the real directories on disk.
    3. Yields an ``import_module`` function usable to bring in the exact
       module under test.
    4. Restores the original sys.modules state afterwards.
    """
    saved = {}
    prefixes = tuple(packages)

    for name in list(sys.modules):
        if name in packages or name.startswith(prefixes):
            saved[name] = sys.modules.pop(name)

    path_added = False
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
        path_added = True

    try:
        for pkg in packages:
            stub = types.ModuleType(pkg)
            stub.__path__ = [str(BACKEND_ROOT / pkg.replace(".", "/"))]
            sys.modules[pkg] = stub

        def import_module(module_name: str):
            return importlib.import_module(module_name)

        yield import_module
    finally:
        for name in list(sys.modules):
            if name in packages or name.startswith(prefixes):
                if name not in saved:
                    try:
                        del sys.modules[name]
                    except KeyError:
                        pass
        sys.modules.update(saved)
        if path_added:
            try:
                sys.path.remove(str(BACKEND_ROOT))
            except ValueError:
                pass
