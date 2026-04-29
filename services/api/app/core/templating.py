from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.config import get_settings


templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.globals["settings"] = get_settings()

