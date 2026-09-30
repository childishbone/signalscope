"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from signalscope.api.routers import securities, signal_events, signals, watchlist
from signalscope.config import get_settings

app = FastAPI(title="SignalScope API")

settings = get_settings()
origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(watchlist.router)
app.include_router(securities.router)
app.include_router(signals.router)
app.include_router(signal_events.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
