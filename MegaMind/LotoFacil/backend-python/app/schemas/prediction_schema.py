"""Pydantic schemas for prediction responses."""

from pydantic import BaseModel, Field


class NumberTrend(BaseModel):
    """Trend classification for a single number."""

    number: int = Field(..., ge=1, le=25)
    trend: str = Field(..., description="'hot', 'cold', or 'neutral'")
    score: float = Field(..., description="Confidence score (0.0 - 1.0)")
    frequency: int = Field(..., description="Frequency in analyzed window")


class PredictionResponse(BaseModel):
    """Response with top-N number trend predictions."""

    hot_numbers: list[NumberTrend] = Field(..., description="Números quentes (alta frequência)")
    cold_numbers: list[NumberTrend] = Field(..., description="Números frios (baixa frequência)")
    model_accuracy: float = Field(..., description="Acurácia do modelo no último backtest")
    contests_analyzed: int = Field(..., description="Quantidade de concursos analisados")
