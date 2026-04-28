"""
LotoMind Portal — Motor Híbrido Monte Carlo + IA (Lotofácil) v1.0
==================================================================
Funil de Precisão em 3 Fases:

  Fase 1 (Monte Carlo): Gera N cenários vetorizados ponderados pelo
          histórico de frequências (herda LotofacilMonteCarlo).

  Fase 2 (IA — Scoring): Aplica os 8+ filtros de padrão da
          LotofacilIntelligenceEngine em cada cenário bruto e calcula
          um score_ia ponderado (0–100).

  Fase 3 (Ranking): Ordena os cenários por score_ia e retorna as
          top-K apostas com todos os detalhes de avaliação.
"""

import time
import numpy as np
from collections import Counter


class LotofacilHybridEngine:
    """
    Motor Híbrido Monte Carlo + IA para Lotofácil.

    Parâmetros
    ----------
    monte_carlo : LotofacilMonteCarlo
        Instância já inicializada com engine e df.
    intel : LotofacilIntelligenceEngine
        Instância já carregada com histórico.
    """

    MOLDURA = frozenset({1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25})
    MIOLO   = frozenset({7, 8, 9, 12, 13, 14, 17, 18, 19})
    PRIMOS  = frozenset({2, 3, 5, 7, 11, 13, 17, 19, 23})

    def __init__(self, monte_carlo, intel):
        self.mc    = monte_carlo
        self.intel = intel

    # ════════════════════════════════════════════════════════════
    #  FASE 1 — MONTE CARLO (geração vetorial de cenários)
    # ════════════════════════════════════════════════════════════

    def _fase1_monte_carlo(self, num_simulacoes: int) -> list[dict]:
        """
        Roda o Monte Carlo e retorna lista de cenários brutos.
        Cada item: {'dezenas': [...15...], 'score_mc': float}
        """
        # Usamos um número ligeiramente maior para garantir pool suficiente
        # após filtragem prévia do MC (pares, soma básica).
        resultados = self.mc.simular(num_simulacoes=num_simulacoes, top_n=min(num_simulacoes, 3000))
        return resultados  # já vêm como [{'dezenas': [...], 'score': float}]

    # ════════════════════════════════════════════════════════════
    #  FASE 2 — IA SCORING (filtros de padrão sobre os cenários)
    # ════════════════════════════════════════════════════════════

    def _calcular_score_ia(self, dezenas: list[int]) -> tuple[float, dict]:
        """
        Calcula score_ia (0–100) aplicando os filtros de padrão da IA.
        Retorna (score_normalizado, detalhes_dict).
        """
        s = sorted(dezenas)
        score_bruto = 0
        detalhes   = {}

        # ── 1. Paridade (7–9 ímpares) — peso 20 ────────────────
        impares   = sum(1 for x in s if x % 2 != 0)
        par_ok    = 7 <= impares <= 9
        par_score = 20 if par_ok else max(0, 20 - abs(impares - 8) * 5)
        score_bruto += par_score
        detalhes['paridade'] = {
            'impares': impares, 'pares': 15 - impares,
            'aprovado': par_ok, 'score': par_score,
        }

        # ── 2. Primos (5–6 primos) — peso 15 ───────────────────
        n_primos  = sum(1 for x in s if x in self.PRIMOS)
        primo_ok  = 5 <= n_primos <= 6
        primo_sc  = 15 if primo_ok else max(0, 15 - abs(n_primos - 5) * 4)
        score_bruto += primo_sc
        detalhes['primos'] = {
            'qtd': n_primos, 'aprovado': primo_ok, 'score': primo_sc,
        }

        # ── 3. Moldura (8–11 na moldura) — peso 18 ─────────────
        n_moldura = sum(1 for x in s if x in self.MOLDURA)
        mold_ok   = 8 <= n_moldura <= 11
        mold_sc   = 18 if mold_ok else max(0, 18 - abs(n_moldura - 9) * 4)
        score_bruto += mold_sc
        detalhes['moldura'] = {
            'qtd_moldura': n_moldura, 'qtd_miolo': 15 - n_moldura,
            'aprovado': mold_ok, 'score': mold_sc,
        }

        # ── 4. Soma (166–220) — peso 15 ─────────────────────────
        soma    = sum(s)
        soma_ok = 166 <= soma <= 220
        soma_sc = 15 if soma_ok else max(0, 15 - abs(soma - 193) // 8)
        score_bruto += soma_sc
        detalhes['soma'] = {'soma': soma, 'aprovado': soma_ok, 'score': soma_sc}

        # ── 5. Sequência máxima de consecutivos (≤4) — peso 12 ─
        max_seq = 1
        seq_at  = 1
        for i in range(1, len(s)):
            if s[i] == s[i-1] + 1:
                seq_at += 1
                max_seq = max(max_seq, seq_at)
            else:
                seq_at = 1
        seq_ok = max_seq <= 4
        seq_sc = 12 if seq_ok else max(0, 12 - (max_seq - 4) * 4)
        score_bruto += seq_sc
        detalhes['sequencia'] = {
            'max_consecutivos': max_seq, 'aprovado': seq_ok, 'score': seq_sc,
        }

        # ── 6. Atraso / Decaimento Temporal — peso 10 ───────────
        if self.intel.decaimento:
            atraso_map = {d['dezena']: d['atraso'] for d in self.intel.decaimento}
            media_atr  = np.mean([d['atraso'] for d in self.intel.decaimento])
            # Bônus por incluir dezenas mais atrasadas
            bonus_atr  = sum(
                min(atraso_map.get(x, 0) / max(media_atr, 1), 2.0)
                for x in s if atraso_map.get(x, 0) > media_atr
            )
            atr_sc     = min(round(bonus_atr * 2), 10)
        else:
            atr_sc = 5
        score_bruto += atr_sc
        detalhes['atraso'] = {'score': atr_sc}

        # ── 7. Ciclos de Fechamento — peso 8 ────────────────────
        faltam = set(self.intel.ciclos.get('faltam', []))
        if faltam:
            acertos_ciclo = len(set(s) & faltam)
            ciclo_sc      = min(acertos_ciclo * 3, 8)
        else:
            ciclo_sc = 6  # ciclo fechado → pontuação neutra
        score_bruto += ciclo_sc
        detalhes['ciclos'] = {'score': ciclo_sc, 'faltam': sorted(faltam)}

        # ── 8. Coocorrência (Pares de Ouro) — peso 10 ───────────
        if self.intel.coocorrencia is not None:
            cooc_score = self.intel.score_coocorrencia(s)
            cooc_sc    = min(round(cooc_score), 10)
        else:
            cooc_sc = 5
        score_bruto += cooc_sc
        detalhes['coocorrencia'] = {'score': cooc_sc}

        # ── Normalização para 0–100 ──────────────────────────────
        max_possivel = 20 + 15 + 18 + 15 + 12 + 10 + 8 + 10  # = 108
        score_ia = round(score_bruto / max_possivel * 100, 1)

        # ── Quantas diretrizes aprovadas ────────────────────────
        aprovadas = sum([
            par_ok, primo_ok, mold_ok, soma_ok, seq_ok,
            atr_sc >= 5, ciclo_sc >= 4, cooc_sc >= 6,
        ])

        return score_ia, {**detalhes, 'aprovadas': aprovadas, 'total': 8}

    def _fase2_ia_scoring(self, cenarios: list[dict]) -> list[dict]:
        """
        Recebe lista de cenários do Monte Carlo e aplica o scoring da IA.
        Retorna lista enriquecida com score_ia e detalhes.
        """
        resultado = []
        for c in cenarios:
            dezenas = c['dezenas']
            score_ia, detalhes = self._calcular_score_ia(dezenas)
            resultado.append({
                'dezenas'  : dezenas,
                'score_mc' : round(c.get('score', 0), 2),
                'score_ia' : score_ia,
                'detalhes' : detalhes,
            })
        return resultado

    # ════════════════════════════════════════════════════════════
    #  FASE 3 — RANKING E RETORNO
    # ════════════════════════════════════════════════════════════

    def gerar_aposta_hibrida(
        self,
        qtd_apostas: int = 5,
        num_simulacoes: int = 10_000,
    ) -> dict:
        """
        Pipeline principal do Motor Híbrido.

        Parâmetros
        ----------
        qtd_apostas : int
            Número de apostas finais a retornar (1–20).
        num_simulacoes : int
            Quantidade de simulações Monte Carlo (1.000–50.000).

        Retorna
        -------
        dict com:
            apostas     : list[dict]  — top N apostas com score_ia, detalhes
            stats_mc    : dict        — estatísticas do Monte Carlo
            tempo_ms    : float       — tempo total de processamento (ms)
        """
        qtd_apostas    = max(1, min(qtd_apostas, 20))
        num_simulacoes = max(1_000, min(num_simulacoes, 50_000))

        t0 = time.perf_counter()

        # ── Fase 1: Monte Carlo ──────────────────────────────────
        cenarios_brutos = self._fase1_monte_carlo(num_simulacoes)

        stats_mc = {
            'simulacoes_solicitadas' : num_simulacoes,
            'cenarios_gerados'       : len(cenarios_brutos),
        }

        if not cenarios_brutos:
            return {'apostas': [], 'stats_mc': stats_mc, 'tempo_ms': 0.0}

        # ── Fase 2: IA — Scoring de cada cenário ────────────────
        cenarios_avaliados = self._fase2_ia_scoring(cenarios_brutos)

        # ── Fase 3: Ranking por score_ia ────────────────────────
        cenarios_avaliados.sort(key=lambda x: x['score_ia'], reverse=True)

        # Remover duplicatas (tuplas de dezenas iguais)
        vistos   = set()
        top_uniq = []
        for c in cenarios_avaliados:
            chave = tuple(c['dezenas'])
            if chave not in vistos:
                vistos.add(chave)
                top_uniq.append(c)
            if len(top_uniq) >= qtd_apostas:
                break

        tempo_ms = round((time.perf_counter() - t0) * 1000, 1)

        # Classificação narrativa
        for ap in top_uniq:
            s = ap['score_ia']
            if s >= 80:
                ap['classificacao'] = '⭐ ELITE — Score Máximo'
            elif s >= 65:
                ap['classificacao'] = '🏆 OURO — Alta Precisão'
            elif s >= 50:
                ap['classificacao'] = '🥈 PRATA — Boa Cobertura'
            else:
                ap['classificacao'] = '🥉 BRONZE — Padrão Básico'

        return {
            'apostas'  : top_uniq,
            'stats_mc' : {**stats_mc, 'cenarios_avaliados': len(cenarios_avaliados)},
            'tempo_ms' : tempo_ms,
        }
