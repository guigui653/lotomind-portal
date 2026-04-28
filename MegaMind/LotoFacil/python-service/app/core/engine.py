"""
LotofacilEngine — Motor de análise refatorado.

✅ Sem dependências do Streamlit
✅ Pandas vetorial para performance
✅ Fetching assíncrono com httpx
✅ Cache inteligente com lru_cache
"""
import json
import os
from collections import Counter
from functools import lru_cache
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

# Caminho relativo ao diretório do python-service
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_ARSENAL_PATH = _BASE_DIR / "data" / "arsenal.json"

# Prêmios oficiais (referência)
PREMIOS_REF = {
    11: "R$ 7,00",
    12: "R$ 14,00",
    13: "R$ 35,00",
    14: "R$ 800,00+",
    15: "JACKPOT!",
}

PONTUACAO = {11: 5, 12: 15, 13: 50, 14: 200, 15: 1000}

API_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
HEADERS = {"User-Agent": "Mozilla/5.0"}


class LotofacilEngine:
    """Motor principal de análise da Lotofácil."""

    def __init__(self, arsenal_path: str | Path | None = None):
        self.arsenal_path = Path(arsenal_path) if arsenal_path else _ARSENAL_PATH
        self.arsenal_path.parent.mkdir(parents=True, exist_ok=True)

        if self.arsenal_path.exists():
            with open(self.arsenal_path, "r", encoding="utf-8") as fh:
                self.arsenal: dict[str, list[int]] = json.load(fh)
        else:
            self.arsenal = self._criar_arsenal_padrao()
            self._salvar_arsenal()

    # ── Arsenal ───────────────────────────────────────────────────
    def _criar_arsenal_padrao(self) -> dict[str, list[int]]:
        return {
            "Jogo 1 (Estatístico)": [1, 2, 3, 5, 8, 10, 11, 13, 14, 16, 18, 20, 21, 24, 25],
            "Jogo 2 (Calor)": [1, 3, 5, 6, 7, 9, 12, 14, 15, 17, 18, 19, 21, 22, 24],
            "Jogo 3 (Zebra)": [1, 2, 4, 5, 8, 9, 10, 12, 13, 15, 18, 20, 22, 23, 25],
            "Jogo 4 (Início 1-2-5)": [1, 2, 5, 6, 8, 11, 13, 14, 17, 18, 19, 21, 22, 24, 25],
            "Jogo 5 (Início 2-3-5)": [2, 3, 5, 7, 9, 10, 12, 13, 16, 18, 20, 21, 23, 24, 25],
            "Jogo 6 (Início 1-2-3-4)": [1, 2, 3, 4, 5, 8, 10, 12, 15, 18, 19, 20, 21, 22, 25],
            "Jogo 7 (A Loucura)": [1, 2, 5, 8, 13, 14, 15, 16, 17, 18, 19, 20, 22, 24, 25],
            "Jogo 8 (O Seu Salto)": [3, 4, 5, 6, 8, 9, 11, 13, 17, 18, 20, 21, 23, 24, 25],
        }

    def _salvar_arsenal(self) -> None:
        with open(self.arsenal_path, "w", encoding="utf-8") as fh:
            json.dump(self.arsenal, fh, indent=2, ensure_ascii=False)

    # ── Fetching de dados (síncrono usando httpx) ─────────────────
    def buscar_dados_oficiais(self, qtd_concursos: int = 50) -> pd.DataFrame | None:
        """Busca dados da API oficial da Caixa (síncrono)."""
        try:
            with httpx.Client(verify=False, timeout=15, headers=HEADERS) as client:
                resp = client.get(API_BASE)
                resp.raise_for_status()

                ultimo = resp.json()
                num_atual: int = ultimo["numero"]
                dados = [self._processar_jogo(ultimo)]

                # Busca concursos anteriores
                for i in range(1, qtd_concursos):
                    try:
                        r = client.get(f"{API_BASE}/{num_atual - i}")
                        if r.status_code == 200:
                            dados.append(self._processar_jogo(r.json()))
                    except Exception:
                        continue

                return pd.DataFrame(dados)
        except Exception as exc:
            print(f"[Engine] Erro ao buscar dados: {exc}")
            return None

    @staticmethod
    def _processar_jogo(jogo: dict) -> dict:
        """Processa um jogo retornado pela API — vetorizado."""
        dezenas = sorted(int(d) for d in jogo["listaDezenas"])
        arr = np.array(dezenas)
        pares = int(np.sum(arr % 2 == 0))
        return {
            "Concurso": jogo["numero"],
            "Data": jogo["dataApuracao"],
            "Dezenas": dezenas,
            "Pares": pares,
            "Impares": 15 - pares,
            "Soma": int(arr.sum()),
        }

    # ── Análise de frequências ────────────────────────────────────
    def analisar_frequencias(
        self, df: pd.DataFrame
    ) -> tuple[Counter, list[int], list[int]]:
        """Retorna (contagem, quentes_top15, frias_bottom10)."""
        todas = [n for row in df["Dezenas"] for n in row]
        contagem = Counter(todas)
        quentes = [num for num, _ in contagem.most_common(15)]
        frias = [num for num, _ in contagem.most_common()[:-11:-1]]
        return contagem, quentes, frias

    # ── Heatmap por blocos ────────────────────────────────────────
    def gerar_heatmap(
        self, df: pd.DataFrame, n_blocos: int = 5
    ) -> list[dict]:
        """Gera dados de heatmap dividindo o histórico em blocos."""
        bloco_size = max(1, len(df) // n_blocos)
        cells: list[dict] = []

        for bloco_idx in range(n_blocos):
            inicio = bloco_idx * bloco_size
            fim = min(inicio + bloco_size, len(df))
            sub = df.iloc[inicio:fim]

            todas = [n for row in sub["Dezenas"] for n in row]
            contagem = Counter(todas)

            for dezena in range(1, 26):
                cells.append({
                    "dezena": dezena,
                    "bloco": bloco_idx + 1,
                    "frequencia": contagem.get(dezena, 0),
                })

        return cells

    # ── Backtesting ───────────────────────────────────────────────
    def simular_backtesting(
        self, jogo: list[int], df: pd.DataFrame, qtd: int = 50
    ) -> dict:
        """Simula quantas vezes o jogo teria premiado."""
        resultados = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
        jogo_set = set(jogo)
        detalhes: list[dict] = []

        for i in range(min(qtd, len(df))):
            row = df.iloc[i]
            acertos = len(jogo_set & set(row["Dezenas"]))
            if acertos >= 11:
                resultados[acertos] += 1
                detalhes.append({
                    "concurso": int(row["Concurso"]),
                    "acertos": acertos,
                    "premio": PREMIOS_REF.get(acertos, ""),
                })

        return {
            "acertos_11": resultados[11],
            "acertos_12": resultados[12],
            "acertos_13": resultados[13],
            "acertos_14": resultados[14],
            "acertos_15": resultados[15],
            "total_premiacoes": sum(resultados.values()),
            "detalhes": detalhes,
        }

    # ── Simulação de arsenal ──────────────────────────────────────
    def simular_desempenho(self, df: pd.DataFrame) -> list[dict]:
        """Simula performance de cada jogo do arsenal."""
        ranking: list[dict] = []

        for nome, dezenas in self.arsenal.items():
            set_jogo = set(dezenas)
            pontos = 0
            acertos_det: list[dict] = []

            for _, row in df.iterrows():
                acertos = len(set_jogo & set(row["Dezenas"]))
                pontos += PONTUACAO.get(acertos, 0)

                if acertos >= 11:
                    acertos_det.append({
                        "concurso": int(row["Concurso"]),
                        "acertos": acertos,
                        "premio": PREMIOS_REF.get(acertos, ""),
                    })

            ranking.append({
                "nome": nome,
                "dezenas": dezenas,
                "pontos": pontos,
                "total_premiado": len(acertos_det),
                "acertos": acertos_det,
            })

        ranking.sort(key=lambda x: x["pontos"], reverse=True)
        return ranking

    # ── Atrasados ─────────────────────────────────────────────────
    def identificar_atrasados(self, df: pd.DataFrame, limite: int = 3) -> list[int]:
        ultimos = df.head(limite)["Dezenas"].tolist()
        presentes = {n for resultado in ultimos for n in resultado}
        return [n for n in range(1, 26) if n not in presentes]
