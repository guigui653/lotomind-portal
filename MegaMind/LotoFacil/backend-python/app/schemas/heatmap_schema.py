"""Pydantic schemas for analysis responses."""

from pydantic import BaseModel, Field
from typing import Any


class HeatmapResponse(BaseModel):
    """Response schema for frequency heatmap."""
    numbers: list[int] = Field(..., description="Números da Lotofácil (1-25)")
    frequencies: list[int] = Field(..., description="Frequência absoluta de cada número")
    metadata: dict = Field(
        default_factory=dict,
        description="Metadados (concursos analisados, data, etc.)",
    )


class OddEvenResponse(BaseModel):
    """Response schema for odd/even analysis."""
    contests: list[dict[str, Any]] = Field(
        ..., description="Lista de concursos com contagem ímpar/par"
    )
    summary: dict[str, Any] = Field(
        ..., description="Resumo: média, padrão mais comum, distribuição"
    )
    odd_numbers_freq: dict[int, int] = Field(
        default_factory=dict,
        description="Frequência de cada número ímpar"
    )
    even_numbers_freq: dict[int, int] = Field(
        default_factory=dict,
        description="Frequência de cada número par"
    )


class SmartSuggestionResponse(BaseModel):
    """Response schema for smart probability-based game suggestion."""
    game: list[int] = Field(..., description="Os 15 números sugeridos")
    filters_applied: list[str] = Field(
        ..., description="Filtros estatísticos aplicados"
    )
    metrics: dict[str, Any] = Field(
        ..., description="Métricas: soma, pares/ímpares, repetições, scores"
    )
    explanation: str = Field(
        ..., description="Explicação textual da lógica usada"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Score de confiança (0.0 a 1.0)"
    )
