import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from neon.api.routers import greeks, options, stock, surface

app = FastAPI(title="Neon Dashboard API")

origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(stock.router)
app.include_router(options.router)
app.include_router(greeks.router)
app.include_router(surface.router)
