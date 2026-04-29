from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers import admin, alerts, auth, complaints, home, payments, violations

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.app_debug)
app.state.settings = settings
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")

app.include_router(home.router)
app.include_router(auth.router)
app.include_router(violations.router)
app.include_router(alerts.router)
app.include_router(complaints.router)
app.include_router(payments.router)
app.include_router(admin.router)
