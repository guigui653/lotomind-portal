"""
Router — Machine Learning endpoints.
"""
from fastapi import APIRouter, HTTPException

from app.core.engine import LotofacilEngine
from app.ml.predictor import LotofacilPredictor
from app.schemas.models import (
    PredictionRequest,
    PredictionResponse,
    DezenaScore,
    ClusterResponse,
    ClusterItem,
)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

engine = LotofacilEngine()
predictor = LotofacilPredictor()


@router.post("/predict", response_model=PredictionResponse, summary="Previsão ML")
def predict_next(req: PredictionRequest):
    """
    Treina o modelo com os últimos N concursos e retorna as
    dezenas mais prováveis para o próximo sorteio.
    """
    df = engine.buscar_dados_oficiais(req.qtd_concursos)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    try:
        resultado = predictor.prever_proximas(df, top_n=req.top_n)
    except ValueError as e:
        raise HTTPException(400, str(e))

    scores = [DezenaScore(**s) for s in resultado["scores"]]

    return PredictionResponse(
        dezenas_recomendadas=resultado["dezenas_recomendadas"],
        scores=scores,
        modelo=resultado["modelo"],
        acuracia_treino=resultado["acuracia_treino"],
        features_importancia=resultado["features_importancia"],
    )


@router.post("/clusters", response_model=ClusterResponse, summary="Clusters de dezenas")
def get_clusters(qtd: int = 100, n_clusters: int = 4):
    """
    Agrupa as 25 dezenas em clusters baseados em co-ocorrência.
    """
    df = engine.buscar_dados_oficiais(qtd)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    try:
        resultado = predictor.identificar_clusters(df, n_clusters=n_clusters)
    except Exception as e:
        raise HTTPException(500, f"Erro no clustering: {e}")

    clusters = [ClusterItem(**c) for c in resultado["clusters"]]

    return ClusterResponse(
        clusters=clusters,
        n_clusters=resultado["n_clusters"],
        descricao=resultado["descricao"],
    )
