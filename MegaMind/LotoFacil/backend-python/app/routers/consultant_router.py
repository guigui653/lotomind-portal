"""Consultant router — exposes the analyze-my-game endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Any

from app.services.consultant_service import ConsultantService

router = APIRouter()
consultant_service = ConsultantService()


class AnalyzeGameRequest(BaseModel):
    """Request body for analyze-my-game."""
    numbers: list[int] = Field(..., description="15 números para análise (1-25)")

    @field_validator("numbers")
    @classmethod
    def validate_numbers(cls, v: list[int]) -> list[int]:
        if len(v) != 15:
            raise ValueError("Envie exatamente 15 números")
        if len(set(v)) != 15:
            raise ValueError("Os números não podem se repetir")
        if not all(1 <= n <= 25 for n in v):
            raise ValueError("Todos os números devem estar entre 1 e 25")
        return sorted(v)


class AnalyzeGameResponse(BaseModel):
    """Response from analyze-my-game."""
    score: int = Field(..., ge=0, le=100, description="Score de alinhamento (0-100)")
    pontos_fortes: list[str] = Field(..., description="Lista de pontos fortes")
    pontos_fracos: list[str] = Field(..., description="Lista de pontos fracos")
    opiniao_do_parceiro: str = Field(..., description="Opinião com tom de sócio")
    metricas: dict[str, Any] = Field(..., description="Métricas detalhadas")
    graficos: dict[str, Any] = Field(..., description="Dados para gráficos do frontend")


@router.post("/analyze-my-game", response_model=AnalyzeGameResponse)
async def analyze_my_game(request: AnalyzeGameRequest) -> AnalyzeGameResponse:
    """
    Analisa os 15 números do usuário e retorna um veredito completo:
    - Score de 0 a 100
    - Pontos fortes e fracos
    - Opinião do parceiro
    - Métricas e dados para gráficos
    """
    try:
        result = await consultant_service.analyze_user_game(request.numbers)
        return AnalyzeGameResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")
