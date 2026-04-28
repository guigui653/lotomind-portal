"""
ConsultantService — Módulo de Consultoria e Explicabilidade da Lotofácil.

Atua como um "parceiro analítico":
1. Gera texto explicativo (analise_do_consultor) para cada jogo gerado
2. Analisa sequências do usuário e retorna um veredito detalhado

Tom de voz: sócio/parceiro — "Baseado na nossa análise...", "Minha sugestão..."
"""

import logging
import random
from collections import Counter

import numpy as np
from sqlalchemy import text

from app.core.database import async_session

logger = logging.getLogger(__name__)

# Constantes da Lotofácil
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}


class ConsultantService:
    """Serviço de consultoria estatística com tom de parceiro."""

    # ══════════════════════════════════════════════════════════
    #  EXPLICABILIDADE — Texto para jogo gerado
    # ══════════════════════════════════════════════════════════

    def generate_consultant_analysis(
        self,
        game: list[int],
        strategy: str,
        counter: Counter,
        hot: list[int],
        cold: list[int],
        all_dezenas: list[list[int]],
    ) -> str:
        """
        Gera o texto 'analise_do_consultor' para um jogo gerado.
        Retorna uma string com tom de parceiro/sócio.
        """
        odds = [n for n in game if n % 2 != 0]
        evens = [n for n in game if n % 2 == 0]
        soma = sum(game)
        primos_no_jogo = [n for n in game if n in PRIMOS]

        # Calcular média histórica de soma
        somas_hist = [sum(d) for d in all_dezenas] if all_dezenas else [195]
        soma_media = float(np.mean(somas_hist))

        # Score de calor
        max_freq = max(counter.values()) if counter else 1
        heat_scores = {n: round(counter.get(n, 0) / max_freq * 100, 1) for n in range(1, 26)}
        hot_in_game = [n for n in game if heat_scores.get(n, 0) >= 80]

        # Repetições com último concurso
        last_dezenas = set(all_dezenas[0]) if all_dezenas else set()
        repetitions = sorted(set(game) & last_dezenas)

        # Padrão par/ímpar mais comum
        padrao_atual = f"{len(odds)}Í/{len(evens)}P"

        # Montar texto
        strategy_names = {
            "balanced": "Equilibrada",
            "aggressive": "Agressiva",
            "hot_cold": "Extremos (Quente/Frio)",
            "random": "Surpresinha",
        }
        strat_name = strategy_names.get(strategy, strategy)

        parts = []

        parts.append(
            f"Baseado na nossa análise dos últimos {len(all_dezenas)} concursos, "
            f"montei este jogo usando a estratégia **{strat_name}**."
        )

        # Ímpar/Par
        parts.append(
            f"A distribuição ficou em **{padrao_atual}** — "
            + (
                "excelente equilíbrio, alinhado com os padrões históricos mais premiados."
                if len(odds) in (7, 8)
                else "atenção: esse padrão é menos frequente entre os premiados."
            )
        )

        # Soma
        diff_soma = abs(soma - soma_media)
        if diff_soma <= 5:
            parts.append(
                f"A soma total é **{soma}**, muito próxima da média histórica de "
                f"**{round(soma_media, 1)}**. Isso é um ótimo sinal."
            )
        elif diff_soma <= 15:
            parts.append(
                f"A soma total é **{soma}** (média histórica: **{round(soma_media, 1)}**). "
                f"Está dentro de uma faixa aceitável."
            )
        else:
            parts.append(
                f"Atenção: a soma total é **{soma}**, significativamente "
                f"{'acima' if soma > soma_media else 'abaixo'} da média histórica de "
                f"**{round(soma_media, 1)}**. Isso é menos comum em jogos premiados."
            )

        # Números quentes no jogo
        if hot_in_game:
            hot_str = ", ".join(f"{n:02d}" for n in sorted(hot_in_game))
            parts.append(
                f"Incluí as dezenas **{hot_str}**, que estão com score de calor acima de 80% "
                f"nos últimos concursos — são as que mais apareceram recentemente."
            )

        # Primos
        parts.append(
            f"O jogo contém **{len(primos_no_jogo)}** números primos "
            + ("(dentro do padrão ideal de 5-6)." if len(primos_no_jogo) in (5, 6) else "(fora do padrão ideal de 5-6, mas pode surpreender).")
        )

        # Repetições
        if repetitions:
            rep_str = ", ".join(f"{n:02d}" for n in repetitions)
            parts.append(
                f"Das dezenas do último concurso, **{len(repetitions)}** se repetem neste jogo ({rep_str}) — "
                + (
                    "o que está dentro do padrão estatístico de 8-10 repetições."
                    if 8 <= len(repetitions) <= 10
                    else "observe que o ideal seria entre 8 e 10 repetições."
                )
            )

        parts.append(
            "Minha sugestão: confie nesta combinação e acompanhe os próximos sorteios para ajustar a estratégia. Boa sorte, parceiro! 🍀"
        )

        return " ".join(parts)

    # ══════════════════════════════════════════════════════════
    #  ANÁLISE DE SEQUÊNCIA DO USUÁRIO
    # ══════════════════════════════════════════════════════════

    async def analyze_user_game(self, numbers: list[int]) -> dict:
        """
        Analisa os 15 números do usuário e retorna um veredito completo.
        """
        game = sorted(numbers)

        # Buscar dados do banco
        async with async_session() as session:
            result = await session.execute(
                text("SELECT concurso, dezenas FROM lotomind.concursos ORDER BY data DESC LIMIT 100")
            )
            rows = result.fetchall()

        if not rows:
            return self._empty_verdict(game)

        all_dezenas = [row[1] for row in rows]
        last_contest_id = rows[0][0]
        last_contest_nums = set(all_dezenas[0])

        # ── Métricas ──
        odds = [n for n in game if n % 2 != 0]
        evens = [n for n in game if n % 2 == 0]
        soma = sum(game)
        primos = [n for n in game if n in PRIMOS]

        # Soma histórica
        somas = [sum(d) for d in all_dezenas]
        soma_mean = float(np.mean(somas))
        soma_std = float(np.std(somas))
        soma_min_ideal = int(soma_mean - soma_std)
        soma_max_ideal = int(soma_mean + soma_std)

        # Heat scores (últimos 15 concursos)
        recent_15 = all_dezenas[:min(15, len(all_dezenas))]
        heat_counter = Counter()
        for dezenas in recent_15:
            for n in dezenas:
                heat_counter[n] += 1
        max_heat = max(heat_counter.values()) if heat_counter else 1
        heat_scores = {n: round(heat_counter.get(n, 0) / max_heat * 100, 1) for n in range(1, 26)}

        # Frequência geral
        general_counter = Counter()
        for dezenas in all_dezenas:
            for n in dezenas:
                general_counter[n] += 1

        # Repetições com o último concurso
        repetitions = sorted(set(game) & last_contest_nums)

        # Percentual histórico de jogos com N repetições
        rep_histogram = Counter()
        for i in range(1, len(all_dezenas)):
            prev_set = set(all_dezenas[i - 1])
            curr_set = set(all_dezenas[i])
            rep_count = len(curr_set & prev_set)
            rep_histogram[rep_count] += 1
        total_comparisons = sum(rep_histogram.values())
        rep_pct = round(rep_histogram.get(len(repetitions), 0) / total_comparisons * 100, 1) if total_comparisons else 0

        # Atraso
        delay = {}
        for n in range(1, 26):
            for i, dezenas in enumerate(all_dezenas):
                if n in dezenas:
                    delay[n] = i
                    break
            else:
                delay[n] = len(all_dezenas)

        # ── Score composto (0-100) ──
        score = 0.0
        score_breakdown = {}

        # 1. Ímpar/Par (25 pontos)
        if len(odds) in (7, 8):
            score += 25
            score_breakdown["impar_par"] = 25
        elif len(odds) in (6, 9):
            score += 15
            score_breakdown["impar_par"] = 15
        else:
            score += 5
            score_breakdown["impar_par"] = 5

        # 2. Soma (25 pontos)
        if soma_min_ideal <= soma <= soma_max_ideal:
            score += 25
            score_breakdown["soma"] = 25
        elif abs(soma - soma_mean) <= soma_std * 1.5:
            score += 15
            score_breakdown["soma"] = 15
        else:
            score += 5
            score_breakdown["soma"] = 5

        # 3. Repetição do último (25 pontos)
        if 8 <= len(repetitions) <= 10:
            score += 25
            score_breakdown["repeticao"] = 25
        elif 6 <= len(repetitions) <= 12:
            score += 15
            score_breakdown["repeticao"] = 15
        else:
            score += 5
            score_breakdown["repeticao"] = 5

        # 4. Calor médio dos números (25 pontos)
        avg_heat = float(np.mean([heat_scores.get(n, 0) for n in game]))
        if avg_heat >= 60:
            score += 25
            score_breakdown["calor"] = 25
        elif avg_heat >= 40:
            score += 15
            score_breakdown["calor"] = 15
        else:
            score += 5
            score_breakdown["calor"] = 5

        score = min(100, int(score))

        # ── Pontos Fortes ──
        pontos_fortes = []
        if len(odds) in (7, 8):
            pontos_fortes.append(f"Ótimo equilíbrio de ímpares/pares ({len(odds)}Í/{len(evens)}P)")
        if soma_min_ideal <= soma <= soma_max_ideal:
            pontos_fortes.append(f"Soma ({soma}) dentro da faixa ideal ({soma_min_ideal}-{soma_max_ideal})")
        if 8 <= len(repetitions) <= 10:
            pontos_fortes.append(f"Repetição ideal: {len(repetitions)} números do último concurso")
        if len(primos) in (5, 6):
            pontos_fortes.append(f"Quantidade ideal de primos ({len(primos)})")
        hot_nums = [n for n in game if heat_scores.get(n, 0) >= 70]
        if len(hot_nums) >= 5:
            pontos_fortes.append(f"{len(hot_nums)} números com alto score de calor (≥70%)")

        # ── Pontos Fracos ──
        pontos_fracos = []
        if len(odds) not in (7, 8):
            pontos_fracos.append(
                f"Distribuição ímpar/par ({len(odds)}Í/{len(evens)}P) fora do padrão ideal (7/8 ou 8/7)"
            )
        if soma < soma_min_ideal:
            pontos_fracos.append(
                f"Soma muito baixa ({soma}), abaixo de {soma_min_ideal} — raramente premiada"
            )
        elif soma > soma_max_ideal:
            pontos_fracos.append(
                f"Soma muito alta ({soma}), acima de {soma_max_ideal} — raramente premiada"
            )
        if len(repetitions) < 6:
            pontos_fracos.append(
                f"Apenas {len(repetitions)} repetições do último concurso (o ideal é 8-10)"
            )
        elif len(repetitions) > 12:
            pontos_fracos.append(
                f"Muitas repetições do último concurso ({len(repetitions)}) — diversifique mais"
            )
        cold_nums = [n for n in game if heat_scores.get(n, 0) <= 20]
        if len(cold_nums) >= 5:
            pontos_fracos.append(
                f"{len(cold_nums)} números com score de calor muito baixo (≤20%)"
            )
        if len(primos) not in (5, 6):
            pontos_fracos.append(
                f"Quantidade de primos ({len(primos)}) fora do padrão ideal (5-6)"
            )

        # ── Opinião do Parceiro ──
        opiniao = self._build_partner_opinion(
            game, score, odds, evens, soma, soma_mean,
            repetitions, last_contest_id, rep_pct, heat_scores
        )

        # ── Dados para gráficos ──
        chart_heat_match = [
            {"name": f"{n:02d}", "seu_calor": heat_scores.get(n, 0), "media": round(sum(heat_scores.values()) / 25, 1)}
            for n in game
        ]
        chart_composition = [
            {"name": "Ímpares", "value": len(odds)},
            {"name": "Pares", "value": len(evens)},
        ]
        chart_score_breakdown = [
            {"name": "Par/Ímpar", "score": score_breakdown.get("impar_par", 0), "max": 25},
            {"name": "Soma", "score": score_breakdown.get("soma", 0), "max": 25},
            {"name": "Repetição", "score": score_breakdown.get("repeticao", 0), "max": 25},
            {"name": "Calor", "score": score_breakdown.get("calor", 0), "max": 25},
        ]

        return {
            "score": score,
            "pontos_fortes": pontos_fortes,
            "pontos_fracos": pontos_fracos,
            "opiniao_do_parceiro": opiniao,
            "metricas": {
                "numeros": game,
                "soma": soma,
                "soma_media": round(soma_mean, 1),
                "soma_faixa_ideal": [soma_min_ideal, soma_max_ideal],
                "impares": len(odds),
                "pares": len(evens),
                "primos": len(primos),
                "repeticoes_ultimo": len(repetitions),
                "numeros_repetidos": repetitions,
                "ultimo_concurso": last_contest_id,
                "heat_scores": {f"{n:02d}": heat_scores.get(n, 0) for n in game},
                "calor_medio": round(avg_heat, 1),
            },
            "graficos": {
                "heat_match": chart_heat_match,
                "composicao": chart_composition,
                "score_breakdown": chart_score_breakdown,
            },
        }

    def _build_partner_opinion(
        self, game, score, odds, evens, soma, soma_mean,
        repetitions, last_contest_id, rep_pct, heat_scores
    ) -> str:
        """Monta a opinião do parceiro com tom de sócio."""
        parts = []

        if score >= 80:
            parts.append("Guilherme, analisei sua sequência e gostei muito do que vi!")
            parts.append(f"O jogo tem um score de **{score}/100** — está muito alinhado com as tendências.")
        elif score >= 60:
            parts.append(f"Guilherme, analisei sua sequência e ela tem potencial (score **{score}/100**).")
            parts.append("Tem pontos positivos, mas alguns ajustes podem melhorar suas chances.")
        elif score >= 40:
            parts.append(f"Guilherme, vou ser honesto: esse jogo tem um score de **{score}/100**.")
            parts.append("Ele precisa de ajustes para se alinhar melhor com os padrões históricos.")
        else:
            parts.append(f"Guilherme, eu não faria esse jogo. O score é de apenas **{score}/100**.")

        # Detalhe sobre repetições
        if len(repetitions) >= 11:
            parts.append(
                f"Ele tem **{len(repetitions)}** repetidas do último concurso (#{last_contest_id}), "
                f"o que só aconteceu em **{rep_pct}%** da história. É um padrão raro."
            )
        elif len(repetitions) <= 4:
            parts.append(
                f"Apenas **{len(repetitions)}** números se repetem do último concurso — isso é muito pouco. "
                f"Historicamente, esse padrão aparece em apenas **{rep_pct}%** dos sorteios."
            )

        # Detalhe sobre soma
        if abs(soma - soma_mean) > 20:
            parts.append(
                f"A soma de **{soma}** está bem distante da média histórica de **{round(soma_mean, 1)}**. "
                f"Considere redistribuir os números."
            )

        # Sugestão construtiva
        cold_in_game = [n for n in game if heat_scores.get(n, 0) <= 15]
        if cold_in_game and score < 70:
            cold_str = ", ".join(f"{n:02d}" for n in sorted(cold_in_game)[:3])
            parts.append(
                f"Minha sugestão: considere trocar os números **{cold_str}** "
                f"(score de calor muito baixo) por dezenas mais quentes."
            )

        if score >= 60:
            parts.append("No geral, é uma aposta que eu faria. Vamos em frente! 🍀")
        else:
            parts.append("Mas a decisão final é sua, parceiro. Estou aqui para ajudar!")

        return " ".join(parts)

    def _empty_verdict(self, game: list[int]) -> dict:
        """Retorna um veredito vazio quando não há dados no banco."""
        return {
            "score": 50,
            "pontos_fortes": ["Jogo com 15 números válidos"],
            "pontos_fracos": ["Sem dados históricos para análise completa"],
            "opiniao_do_parceiro": (
                "Guilherme, ainda não temos dados suficientes no banco para uma análise completa. "
                "Sincronize os resultados primeiro e depois me envie seus números novamente!"
            ),
            "metricas": {
                "numeros": game,
                "soma": sum(game),
                "soma_media": 195.0,
                "soma_faixa_ideal": [170, 220],
                "impares": sum(1 for n in game if n % 2 != 0),
                "pares": sum(1 for n in game if n % 2 == 0),
                "primos": sum(1 for n in game if n in PRIMOS),
                "repeticoes_ultimo": 0,
                "numeros_repetidos": [],
                "ultimo_concurso": 0,
                "heat_scores": {},
                "calor_medio": 0.0,
            },
            "graficos": {
                "heat_match": [],
                "composicao": [
                    {"name": "Ímpares", "value": sum(1 for n in game if n % 2 != 0)},
                    {"name": "Pares", "value": sum(1 for n in game if n % 2 == 0)},
                ],
                "score_breakdown": [],
            },
        }
