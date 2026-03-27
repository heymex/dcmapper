import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.public import router as public_router
from app.db import models
from app.db.session import Base, engine
from app.security import apply_security_headers, check_rate_limit

app = FastAPI(title="dcmapper", version="0.1.0")
templates = Jinja2Templates(directory="app/templates")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(public_router)


@app.on_event("startup")
def startup() -> None:
    # Prefer migrations; allow opt-in schema bootstrap for local experiments.
    if os.getenv("DCMAPPER_AUTO_CREATE_SCHEMA", "false").lower() == "true":
        Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def hardening_middleware(request: Request, call_next):
    limited_response = check_rate_limit(request)
    if limited_response is not None:
        return limited_response

    response = await call_next(request)
    apply_security_headers(response)
    return response


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
