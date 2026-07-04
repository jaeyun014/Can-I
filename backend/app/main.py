from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, auth, logs
from app.core.config import settings

app = FastAPI(
    title="Can I? API",
    description="AI-ready safety assistant MVP powered by a JSON rule engine.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(logs.router, prefix="/api", tags=["logs"])
