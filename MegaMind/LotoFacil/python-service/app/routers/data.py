"""
Router — Dados históricos da Lotofácil.
"""
from fastapi import APIRouter, HTTPException, Query

from app.core.engine import LotofacilEngine
from app.schemas.models import ConcursoOut, HistoryResponse

router = APIRouter(prefix="/data", tags=["Dados"])

engine = LotofacilEngine()


@router.get("/latest", response_model=ConcursoOut, summary="Último concurso")
def get_latest():
    df = engine.buscar_dados_oficiais(qtd_concursos=1)
    if df is None or df.empty:
        raise HTTPException(502, "Não foi possível buscar dados da Caixa")
    row = df.iloc[0]
    return ConcursoOut(
        concurso=row["Concurso"],
        data=row["Data"],
        dezenas=row["Dezenas"],
        pares=row["Pares"],
        impares=row["Impares"],
        soma=row["Soma"],
    )


@router.get("/history", response_model=HistoryResponse, summary="Histórico de concursos")
def get_history(qtd: int = Query(50, ge=1, le=200)):
    df = engine.buscar_dados_oficiais(qtd_concursos=qtd)
    if df is None or df.empty:
        raise HTTPException(502, "Não foi possível buscar dados da Caixa")

    concursos = [
        ConcursoOut(
            concurso=row["Concurso"],
            data=row["Data"],
            dezenas=row["Dezenas"],
            pares=row["Pares"],
            impares=row["Impares"],
            soma=row["Soma"],
        )
        for _, row in df.iterrows()
    ]
    return HistoryResponse(total=len(concursos), concursos=concursos)
