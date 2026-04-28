"""Analysis router — exposes heatmap, odd/even, prediction, and smart suggestion endpoints."""

from fastapi import APIRouter, Query

from app.schemas.heatmap_schema import HeatmapResponse, OddEvenResponse, SmartSuggestionResponse
from app.schemas.prediction_schema import PredictionResponse
from app.services.analysis_service import AnalysisService
from app.services.prediction_service import PredictionService

router = APIRouter()

analysis_service = AnalysisService()
prediction_service = PredictionService()


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    last_contests: int = Query(default=15, ge=1, le=500, alias="lastContests"),
) -> HeatmapResponse:
    """
    Gera o Mapa de Calor com dados REAIS do PostgreSQL.
    Frequência dos 25 números nos últimos N concursos.
    """
    return await analysis_service.generate_heatmap(last_contests)


@router.get("/odd-even", response_model=OddEvenResponse)
async def get_odd_even(
    last_contests: int = Query(default=15, ge=1, le=100, alias="lastContests"),
) -> OddEvenResponse:
    """
    Análise de distribuição ímpar/par nos últimos N concursos.
    Retorna contagem por concurso, frequência de cada número, e padrão mais comum.
    """
    return await analysis_service.generate_odd_even(last_contests)


@router.get("/smart-suggestion", response_model=SmartSuggestionResponse)
async def get_smart_suggestion() -> SmartSuggestionResponse:
    """
    Gera sugestão inteligente de jogo baseada em:
    - Score de calor (últimos 15 concursos)
    - Balanceamento ímpar/par (7-8 ou 8-7)
    - Repetição de 8-10 números do último concurso
    - Soma na faixa ideal
    - Fator de atraso
    """
    return await analysis_service.generate_smart_suggestion()


@router.get("/predictions", response_model=PredictionResponse)
async def get_predictions(
    top_n: int = Query(default=10, ge=1, le=25, alias="topN"),
) -> PredictionResponse:
    """
    Retorna previsão de tendências (números quentes/frios)
    baseada em análise estatística e ML.
    """
    return await prediction_service.predict_trends(top_n)
