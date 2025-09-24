from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from .routers import persons, notes, platforms, profiles, person_links, vehicles, activities, views, stats

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

app.include_router(persons.router)
app.include_router(notes.router)
app.include_router(platforms.router)
app.include_router(profiles.router)
app.include_router(person_links.router)
app.include_router(vehicles.router)
app.include_router(activities.router)
app.include_router(views.router)
app.include_router(stats.router)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/__routes")
def list_routes():
    routes = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            routes.append({"path": r.path, "methods": list(r.methods)})
        else:
            routes.append({"path": r.path, "methods": []})
    return routes
