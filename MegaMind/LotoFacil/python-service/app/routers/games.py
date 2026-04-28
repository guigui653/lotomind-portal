"""
Router — Geração e validação de jogos.
"""
from fastapi import APIRouter, HTTPException, Query

from app.core.engine import LotofacilEngine
from app.core.generator import GeradorJogos
from app.schemas.models import (
    GenerateRequest,
    GeneratedGame,
    EliteRequest,
    EliteResponse,
    EliteGame,
    BacktestRequest,
    BacktestResult,
    ArsenalResponse,
    ArsenalGame,
    ArsenalSimulationResponse,
    ArsenalSimulationEntry,
    ValidationResult,
    ValidationDetail,
)

router = APIRouter(prefix="/games", tags=["Jogos"])

engine = LotofacilEngine()
gerador = GeradorJogos(engine)


def _to_validation_result(validacoes: dict) -> ValidationResult:
    return ValidationResult(
        valido=all(v["valido"] for v in validacoes.values()),
        soma=ValidationDetail(**validacoes["soma"]),
        sequencia=ValidationDetail(**validacoes["sequencia"]),
        primos=ValidationDetail(**validacoes["primos"]),
    )


@router.post("/generate", response_model=GeneratedGame, summary="Gerar jogo validado")
def generate_game(req: GenerateRequest):
    df = engine.buscar_dados_oficiais(req.qtd_concursos)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    _, quentes, frias = engine.analisar_frequencias(df)
    jogo, valido, validacoes = gerador.gerar_jogo_validado(req.estrategia, quentes, frias)

    return GeneratedGame(
        dezenas=jogo,
        valido=valido,
        validacao=_to_validation_result(validacoes),
        estrategia=req.estrategia,
    )


@router.post("/elite", response_model=EliteResponse, summary="Gerar 4 jogos elite")
def generate_elite(req: EliteRequest):
    df = engine.buscar_dados_oficiais(req.qtd_concursos)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    _, quentes, frias = engine.analisar_frequencias(df)
    ultimo_resultado = df.iloc[0]["Dezenas"]

    jogos_raw = gerador.gerar_4_jogos_elite(
        quentes=quentes,
        frios=frias,
        ultimo_resultado=ultimo_resultado,
        melhor_jogo_nome=req.melhor_jogo_nome,
    )

    jogos = []
    for j in jogos_raw:
        jogos.append(EliteGame(
            nome=j["nome"],
            dezenas=j["dezenas"],
            estrategia=j["estrategia"],
            score=j["score"],
            paridade=j["paridade"],
            validacao=ValidationResult(
                valido=j["validacao"]["valido"],
                soma=ValidationDetail(**j["validacao"]["soma"]),
                sequencia=ValidationDetail(**j["validacao"]["sequencia"]),
                primos=ValidationDetail(**j["validacao"]["primos"]),
            ),
        ))

    return EliteResponse(jogos=jogos)


@router.post("/backtest", response_model=BacktestResult, summary="Backtesting de jogo")
def backtest_game(req: BacktestRequest):
    df = engine.buscar_dados_oficiais(req.qtd_concursos)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    resultado = engine.simular_backtesting(req.jogo, df, req.qtd_concursos)
    return BacktestResult(**resultado)


@router.get("/arsenal", response_model=ArsenalResponse, summary="Arsenal de jogos")
def get_arsenal():
    jogos = [ArsenalGame(nome=n, dezenas=d) for n, d in engine.arsenal.items()]
    return ArsenalResponse(jogos=jogos)


@router.get(
    "/arsenal/simulate",
    response_model=ArsenalSimulationResponse,
    summary="Simulação do arsenal",
)
def simulate_arsenal(qtd: int = Query(50, ge=10, le=200)):
    df = engine.buscar_dados_oficiais(qtd)
    if df is None or df.empty:
        raise HTTPException(502, "Falha ao buscar dados")

    ranking_raw = engine.simular_desempenho(df)
    ranking = [ArsenalSimulationEntry(**r) for r in ranking_raw]
    return ArsenalSimulationResponse(ranking=ranking)
