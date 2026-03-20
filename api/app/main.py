from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from .routers import auth, dashboard, entries, history, metadata_schemas, users
from .services.users import ensure_default_admin

app = FastAPI(title="DB Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "https://dbfrontend-production.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(metadata_schemas.router)
app.include_router(entries.router)
app.include_router(dashboard.router)
app.include_router(history.router)

@app.get("/")
def root():
    return {"status": "ok"}


@app.on_event("startup")
def bootstrap_admin_user():
    ensure_default_admin()

@app.get("/__routes")
def list_routes():
    routes = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            routes.append({"path": r.path, "methods": list(r.methods)})
        else:
            routes.append({"path": r.path, "methods": []})
    return routes
