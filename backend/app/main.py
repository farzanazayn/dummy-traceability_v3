from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import technicians, packages, lots, request, dashboard, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dummy Unit Lot Traceability System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(technicians.router)
app.include_router(packages.router)
app.include_router(lots.router)
app.include_router(request.router)
app.include_router(dashboard.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
