from fastapi import FastAPI
from .routers import persons, notes, platforms, profiles, person_links, vehicles, activities, views

app = FastAPI(title="DB Manager API")

# Router registrieren
app.include_router(persons.router)
app.include_router(notes.router)
app.include_router(platforms.router)
app.include_router(profiles.router)
app.include_router(person_links.router)
app.include_router(vehicles.router)
app.include_router(activities.router)
app.include_router(views.router)

@app.get("/")
def root():
    return {"status": "ok"}
