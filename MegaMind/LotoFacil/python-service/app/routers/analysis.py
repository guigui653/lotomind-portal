"""
Router — Análise estatística.
"""
from fastapi import APIRouter, HTTPException, Query

from app.core.engine import LotofacilEngine
from app.schemas.models import (
    FrequencyItem,
    FrequencyResponse,
    HeatmapCell,
    HeatmapResponse,
    DashboardResponse,
    ConcursoOut,
)

router = APIRouter(prefix="/analysis", tags=["Análise"])

engine = LotofacilEngine()


@router.get("/dashboard", response_model=DashboardResponse, summary="Dados do Dashboard")
def get_dashboard(qtd: int = Query(50, ge=10, le=200)):
    df = engine.buscar_dados_oficiais(qtd_concursos=qtd)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    contagem, quentes, frias = engine.analisar_frequencias(df)
    ult = df.iloc[0]
    mais_quente = contagem.most_common(1)[0] if contagem else (0, 0)

    frequencias = []
    for dezena in range(1, 26):
        freq = contagem.get(dezena, 0)
        if dezena in quentes[:5]:
            cat = "quente"
        elif dezena in frias:
            cat = "fria"
        else:
            cat = "mediana"
        frequencias.append(FrequencyItem(dezena=dezena, frequencia=freq, categoria=cat))

    return DashboardResponse(
        ultimo_concurso=ConcursoOut(
            concurso=ult["Concurso"],
            data=ult["Data"],
            dezenas=ult["Dezenas"],
            pares=ult["Pares"],
            impares=ult["Impares"],
            soma=ult["Soma"],
        ),
        numero_mais_quente=mais_quente[0],
        frequencia_mais_quente=mais_quente[1],
        media_pares=round(float(df["Pares"].mean()), 2),
        media_impares=round(float(df["Impares"].mean()), 2),
        total_analisado=len(df),
        frequencias=frequencias,
        quentes=quentes,
        frias=frias,
    )


@router.get("/frequencies", response_model=FrequencyResponse, summary="Frequências das dezenas")
def get_frequencies(qtd: int = Query(50, ge=10, le=200)):
    df = engine.buscar_dados_oficiais(qtd_concursos=qtd)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    contagem, quentes, frias = engine.analisar_frequencias(df)

    frequencias = []
    for dezena in range(1, 26):
        freq = contagem.get(dezena, 0)
        if dezena in quentes[:5]:
            cat = "quente"
        elif dezena in frias:
            cat = "fria"
        else:
            cat = "mediana"
        frequencias.append(FrequencyItem(dezena=dezena, frequencia=freq, categoria=cat))

    return FrequencyResponse(
        frequencias=frequencias,
        quentes=quentes,
        frias=frias,
        total_concursos=len(df),
    )


@router.get("/heatmap", response_model=HeatmapResponse, summary="Heatmap de dezenas")
def get_heatmap(qtd: int = Query(50, ge=10, le=200), blocos: int = Query(5, ge=2, le=10)):
    df = engine.buscar_dados_oficiais(qtd_concursos=qtd)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    cells_raw = engine.gerar_heatmap(df, n_blocos=blocos)
    cells = [HeatmapCell(**c) for c in cells_raw]

    bloco_size = max(1, len(df) // blocos)
    labels = [
        f"Bloco {i+1} (conc. {len(df) - i*bloco_size} a {max(1, len(df) - (i+1)*bloco_size + 1)})"
        for i in range(blocos)
    ]

    return HeatmapResponse(cells=cells, blocos_labels=labels)
