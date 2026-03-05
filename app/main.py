import logging
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import jobs, cv, cover, github, profile, tasks


def setup_logging():
    log_dir = settings.logs_path
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")

    file_handler = RotatingFileHandler(
        log_dir / "agent.log", maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def create_app() -> FastAPI:
    setup_logging()

    application = FastAPI(
        title="Job Agent API",
        description="CV Generation & Job Tracking Agent",
        version="4.0.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(jobs.router)
    application.include_router(cv.router)
    application.include_router(cover.router)
    application.include_router(github.router)
    application.include_router(profile.router)
    application.include_router(tasks.router)

    @application.get("/")
    def root():
        return {"message": "Job Agent API v4.0", "docs": "/docs"}

    return application


app = create_app()
