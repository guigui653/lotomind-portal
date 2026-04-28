"""
LotoFácil Pro 3.0 — Microsserviço de Data Science (FastAPI).

Endpoints:
  /data      → Dados históricos da Caixa
  /analysis  → Frequências, heatmap, dashboard
  /games     → Geração, validação, backtesting, arsenal
  /ml        → Predição (Random Forest) e Clusters (KMeans)

Rodar:
  uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import data, analysis, games, ml


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 LotoFácil Python Service — iniciando...")
    yield
    print("🛑 LotoFácil Python Service — encerrando...")


app = FastAPI(
    title="LotoFácil Pro 3.0 — Data Science API",
    description=(
        "Microsserviço de análise estatística, geração de jogos "
        "e Machine Learning para a Lotofácil."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# CORS — aceita requisições do Java backend e do frontend em dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js dev
        "http://localhost:8080",   # Spring Boot
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(data.router)
app.include_router(analysis.router)
app.include_router(games.router)
app.include_router(ml.router)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "LotoFácil Data Science API",
        "version": "3.0.0",
    }
