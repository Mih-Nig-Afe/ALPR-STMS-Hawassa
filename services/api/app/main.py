from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette import status as http_status

from app.auth.dependencies import get_current_user_optional
from app.core.config import get_settings
from app.core.templating import templates
from app.db.session import get_db
from app.routers import admin, alerts, api, auth, complaints, home, payments, violations

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.app_debug)
app.state.settings = settings
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")

app.include_router(home.router)
app.include_router(auth.router)
app.include_router(violations.router)
app.include_router(api.router)
app.include_router(alerts.router)
app.include_router(complaints.router)
app.include_router(payments.router)
app.include_router(admin.router)


_ERROR_PAGES: dict[int, tuple[str, str]] = {
    400: ("Bad request", "The request could not be understood."),
    401: ("Sign in required", "Please sign in to access this page."),
    403: ("Access denied", "Your role does not allow this action."),
    404: ("Page not found", "The page you requested does not exist."),
    405: ("Method not allowed", "This action is not supported here."),
    500: ("Something went wrong", "An unexpected error occurred. The incident has been logged."),
}


def _wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    if request.url.path.startswith(("/static/", "/health/", "/payments/callback")):
        return True
    if "application/json" in accept and "text/html" not in accept:
        return True
    return False


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    location = (exc.headers or {}).get("Location") if exc.headers else None
    if location and exc.status_code in (
        http_status.HTTP_301_MOVED_PERMANENTLY,
        http_status.HTTP_302_FOUND,
        http_status.HTTP_303_SEE_OTHER,
        http_status.HTTP_307_TEMPORARY_REDIRECT,
        http_status.HTTP_308_PERMANENT_REDIRECT,
    ):
        return RedirectResponse(location, status_code=exc.status_code)
    if _wants_json(request):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    title, description = _ERROR_PAGES.get(exc.status_code, ("Error", str(exc.detail or "")))
    detail = exc.detail if isinstance(exc.detail, str) else None
    if detail and detail.lower() not in {"not found", "forbidden", "unauthorized", "method not allowed"}:
        description = detail
    try:
        db = next(get_db())
        try:
            current_user = get_current_user_optional(request, db)
        finally:
            db.close()
    except Exception:
        current_user = None
    return templates.TemplateResponse(
        request,
        "shared/error.html",
        {
            "current_user": current_user,
            "status_code": exc.status_code,
            "title": title,
            "description": description,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> Response:
    return await http_exception_handler(request, HTTPException(status_code=404, detail=getattr(exc, "detail", None)))
