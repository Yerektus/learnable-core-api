"""Run this script locally to diagnose OpenAPI schema generation errors.
Usage: python debug_openapi.py
"""
import os, sys, traceback, json

# Minimal env for import to succeed
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-diagnostics-only")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("LLM_API_KEY", "dummy")

sys.path.insert(0, os.path.dirname(__file__))

ROUTERS = [
    "auth",
    "users",
    "graphs",
    "admin",
    "kanban",
    "ai",
    "chats",
    "materials",
]


def try_openapi(app):
    """Return (ok, error_str)."""
    try:
        app.openapi_schema = None  # force rebuild
        schema = app.openapi()
        return True, f"{len(schema.get('paths', {}))} paths"
    except Exception:
        return False, traceback.format_exc()


def main():
    print("=" * 60)
    print("Step 1: Full app openapi()")
    print("=" * 60)

    try:
        from app.main import app
        print("App imported OK")
    except Exception:
        print("FAILED to import app:")
        traceback.print_exc()
        return

    ok, msg = try_openapi(app)
    if ok:
        print(f"OPENAPI OK — {msg}")
        print("No schema generation issue found.")
        return

    print(f"OPENAPI FAILED:\n{msg}\n")

    # Binary search: disable routers one by one
    print("=" * 60)
    print("Step 2: Binary search — disabling routers")
    print("=" * 60)

    from fastapi import FastAPI
    from app.config import get_settings
    from app.exceptions import setup_exception_handlers

    settings = get_settings()

    router_modules = {
        "auth":      ("app.modules.auth.router",      "router", "/api/v1/auth",      ["auth"]),
        "users":     ("app.modules.users.router",     "router", "/api/v1/users",     ["users"]),
        "admin":     ("app.modules.users.router",     "admin_router", "/api/v1",     ["admin"]),
        "graphs":    ("app.modules.graphs.router",    "router", "/api/v1/graphs",    ["graphs"]),
        "kanban":    ("app.modules.kanban.router",    "router", "/api/v1/kanban",    ["kanban"]),
        "ai":        ("app.modules.ai.router",        "router", "/api/v1/ai",        ["ai"]),
        "chats":     ("app.modules.chats.router",     "router", "/api/v1/chats",     ["chats"]),
        "materials": ("app.modules.materials.router", "router", "/api/v1/materials", ["materials"]),
    }

    for skip_name in router_modules:
        test_app = FastAPI(title="Test", version="0.0.0")
        setup_exception_handlers(test_app)

        for name, (mod_path, attr, prefix, tags) in router_modules.items():
            if name == skip_name:
                continue
            try:
                import importlib
                mod = importlib.import_module(mod_path)
                r = getattr(mod, attr)
                test_app.include_router(r, prefix=prefix, tags=tags)
            except Exception as e:
                print(f"  Could not load router '{name}': {e}")

        ok, msg = try_openapi(test_app)
        if ok:
            print(f"  SKIP '{skip_name}' → OPENAPI OK  ← '{skip_name}' router is the culprit!")
        else:
            print(f"  SKIP '{skip_name}' → still fails")

    print("\nDone.")


if __name__ == "__main__":
    main()
