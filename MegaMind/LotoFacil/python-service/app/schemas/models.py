"""
Pydantic Schemas — Modelos de validação para request/response da API.
"""
from pydantic import BaseModel, Field
from typing import Optional


# ─── Data / History ───────────────────────────────────────────────
class ConcursoOut(BaseModel):
    concurso: int
    data: str
    dezenas: list[int]
    pares: int
    impares: int
    soma: int


class HistoryResponse(BaseModel):
    total: int
    concursos: list[ConcursoOut]


# ─── Frequency Analysis ──────────────────────────────────────────
class FrequencyItem(BaseModel):
    dezena: int
    frequencia: int
    categoria: str  # "quente", "fria", "mediana"


class FrequencyResponse(BaseModel):
    frequencias: list[FrequencyItem]
    quentes: list[int]
    frias: list[int]
    total_concursos: int


# ─── Heatmap ──────────────────────────────────────────────────────
class HeatmapCell(BaseModel):
    dezena: int
    bloco: int  # 1-based block index
    frequencia: int


class HeatmapResponse(BaseModel):
    cells: list[HeatmapCell]
    blocos_labels: list[str]


# ─── Game Validation ──────────────────────────────────────────────
class ValidationDetail(BaseModel):
    valor: int | float
    valido: bool
    esperado: str


class ValidationResult(BaseModel):
    valido: bool
    soma: ValidationDetail
    sequencia: ValidationDetail
    primos: ValidationDetail


# ─── Game Generation ──────────────────────────────────────────────
class GenerateRequest(BaseModel):
    estrategia: str = Field(
        default="equilibrado",
        description="quente | fria | equilibrado | random",
    )
    qtd_concursos: int = Field(default=50, ge=10, le=200)


class GeneratedGame(BaseModel):
    dezenas: list[int]
    valido: bool
    validacao: ValidationResult
    estrategia: str


class EliteRequest(BaseModel):
    melhor_jogo_nome: str = Field(default="Jogo 1 (Estatístico)")
    qtd_concursos: int = Field(default=50, ge=10, le=200)


class EliteGame(BaseModel):
    nome: str
    dezenas: list[int]
    estrategia: str
    score: int
    paridade: str
    validacao: ValidationResult


class EliteResponse(BaseModel):
    jogos: list[EliteGame]


# ─── Backtesting ──────────────────────────────────────────────────
class BacktestRequest(BaseModel):
    jogo: list[int] = Field(..., min_length=15, max_length=15)
    qtd_concursos: int = Field(default=50, ge=10, le=200)


class BacktestResult(BaseModel):
    acertos_11: int
    acertos_12: int
    acertos_13: int
    acertos_14: int
    acertos_15: int
    total_premiacoes: int
    detalhes: list[dict]


# ─── Arsenal ──────────────────────────────────────────────────────
class ArsenalGame(BaseModel):
    nome: str
    dezenas: list[int]


class ArsenalResponse(BaseModel):
    jogos: list[ArsenalGame]


# ─── Arsenal Simulation ──────────────────────────────────────────
class ArsenalSimulationEntry(BaseModel):
    nome: str
    dezenas: list[int]
    pontos: int
    total_premiado: int
    acertos: list[dict]


class ArsenalSimulationResponse(BaseModel):
    ranking: list[ArsenalSimulationEntry]


# ─── ML Predictions ──────────────────────────────────────────────
class PredictionRequest(BaseModel):
    qtd_concursos: int = Field(default=100, ge=30, le=500)
    top_n: int = Field(default=15, ge=10, le=20)


class DezenaScore(BaseModel):
    dezena: int
    probabilidade: float
    ranking: int


class PredictionResponse(BaseModel):
    dezenas_recomendadas: list[int]
    scores: list[DezenaScore]
    modelo: str
    acuracia_treino: float
    features_importancia: list[dict]


class ClusterItem(BaseModel):
    dezena: int
    cluster: int


class ClusterResponse(BaseModel):
    clusters: list[ClusterItem]
    n_clusters: int
    descricao: list[str]


# ─── Dashboard ────────────────────────────────────────────────────
class DashboardResponse(BaseModel):
    ultimo_concurso: ConcursoOut
    numero_mais_quente: int
    frequencia_mais_quente: int
    media_pares: float
    media_impares: float
    total_analisado: int
    frequencias: list[FrequencyItem]
    quentes: list[int]
    frias: list[int]
