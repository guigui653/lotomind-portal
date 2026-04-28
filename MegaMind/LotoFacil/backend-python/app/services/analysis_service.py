"""
AnalysisService — Análise Estatística Avançada da Lotofácil.

Usa dados REAIS do PostgreSQL para calcular:
- Mapa de calor (frequência de cada número 1-25)
- Análise ímpar/par por concurso
- Sugestão inteligente baseada em probabilidade, soma, atraso e repetição

Resultados cacheados via Redis para performance.
"""

import logging
import random
from collections import Counter
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import text

from app.core.config import settings
from app.core.database import async_session
from app.core.redis_client import redis_manager
from app.schemas.heatmap_schema import HeatmapResponse, OddEvenResponse, SmartSuggestionResponse

logger = logging.getLogger(__name__)


class AnalysisService:
    """Serviço de análise estatística com dados reais do banco."""

    # ══════════════════════════════════════════════════════════
    #  HEATMAP (dados reais)
    # ══════════════════════════════════════════════════════════

    async def generate_heatmap(self, last_contests: int = 15) -> HeatmapResponse:
        """Gera o Mapa de Calor com dados REAIS do PostgreSQL."""
        cache_key = f"heatmap:real:{last_contests}"

        cached = await redis_manager.get_cached(cache_key)
        if cached:
            logger.info("Heatmap served from cache (key=%s)", cache_key)
            return HeatmapResponse(**cached)

        logger.info("Computing REAL heatmap for last %d contests...", last_contests)
        heatmap_data = await self._compute_heatmap(last_contests)

        await redis_manager.set_cached(
            cache_key, heatmap_data.model_dump(), ttl=settings.REDIS_CACHE_TTL
        )
        return heatmap_data

    async def _compute_heatmap(self, last_contests: int) -> HeatmapResponse:
        """Calcula heatmap com dados reais do banco."""
        async with async_session() as session:
            result = await session.execute(
                text("SELECT dezenas FROM lotomind.concursos ORDER BY data DESC LIMIT :limit"),
                {"limit": last_contests}
            )
            rows = result.fetchall()

        if not rows:
            logger.warning("No contests in database, returning empty heatmap")
            return HeatmapResponse(
                numbers=list(range(1, 26)),
                frequencies=[0] * 25,
                metadata={"contests_analyzed": 0, "source": "empty"}
            )

        # Contar frequência de cada número
        counter = Counter()
        for row in rows:
            for num in row[0]:
                counter[num] += 1

        all_numbers = list(range(1, 26))
        frequencies = [counter.get(n, 0) for n in all_numbers]

        freq_array = np.array(frequencies)
        mean_freq = float(np.mean(freq_array))
        std_freq = float(np.std(freq_array))

        hot_threshold = mean_freq + std_freq
        cold_threshold = mean_freq - std_freq
        hot_count = int(np.sum(freq_array >= hot_threshold))
        cold_count = int(np.sum(freq_array <= cold_threshold))

        return HeatmapResponse(
            numbers=all_numbers,
            frequencies=frequencies,
            metadata={
                "contests_analyzed": len(rows),
                "mean_frequency": round(mean_freq, 2),
                "std_deviation": round(std_freq, 2),
                "hot_count": hot_count,
                "cold_count": cold_count,
                "hot_threshold": round(hot_threshold, 2),
                "cold_threshold": round(cold_threshold, 2),
                "source": "database",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    # ══════════════════════════════════════════════════════════
    #  ANÁLISE ÍMPAR / PAR
    # ══════════════════════════════════════════════════════════

    async def generate_odd_even(self, last_contests: int = 15) -> OddEvenResponse:
        """Gera análise de distribuição ímpar/par dos últimos concursos."""
        cache_key = f"oddeven:{last_contests}"

        cached = await redis_manager.get_cached(cache_key)
        if cached:
            return OddEvenResponse(**cached)

        data = await self._compute_odd_even(last_contests)

        await redis_manager.set_cached(
            cache_key, data.model_dump(), ttl=settings.REDIS_CACHE_TTL
        )
        return data

    async def _compute_odd_even(self, last_contests: int) -> OddEvenResponse:
        """Calcula distribuição ímpar/par por concurso."""
        async with async_session() as session:
            result = await session.execute(
                text("""
                    SELECT concurso, data, dezenas
                    FROM lotomind.concursos
                    ORDER BY data DESC
                    LIMIT :limit
                """),
                {"limit": last_contests}
            )
            rows = result.fetchall()

        if not rows:
            return OddEvenResponse(
                contests=[],
                summary={"avg_odd": 0, "avg_even": 0, "most_common_pattern": "N/A"},
                odd_numbers_freq={},
                even_numbers_freq={},
            )

        contests = []
        all_odd_nums = Counter()
        all_even_nums = Counter()
        patterns = Counter()

        for row in rows:
            concurso, data, dezenas = row
            odds = [n for n in dezenas if n % 2 != 0]
            evens = [n for n in dezenas if n % 2 == 0]

            for n in odds:
                all_odd_nums[n] += 1
            for n in evens:
                all_even_nums[n] += 1

            pattern = f"{len(odds)}I/{len(evens)}P"
            patterns[pattern] += 1

            contests.append({
                "concurso": concurso,
                "data": data.isoformat() if hasattr(data, 'isoformat') else str(data),
                "odd_count": len(odds),
                "even_count": len(evens),
                "odd_numbers": sorted(odds),
                "even_numbers": sorted(evens),
            })

        avg_odd = sum(c["odd_count"] for c in contests) / len(contests)
        avg_even = sum(c["even_count"] for c in contests) / len(contests)
        most_common = patterns.most_common(1)[0][0] if patterns else "N/A"

        return OddEvenResponse(
            contests=contests,
            summary={
                "avg_odd": round(avg_odd, 2),
                "avg_even": round(avg_even, 2),
                "most_common_pattern": most_common,
                "pattern_distribution": dict(patterns.most_common()),
                "total_contests": len(rows),
            },
            odd_numbers_freq=dict(all_odd_nums.most_common()),
            even_numbers_freq=dict(all_even_nums.most_common()),
        )

    # ══════════════════════════════════════════════════════════
    #  SUGESTÃO INTELIGENTE (Probabilidade + Estatística)
    # ══════════════════════════════════════════════════════════

    async def generate_smart_suggestion(self) -> SmartSuggestionResponse:
        """
        Gera um jogo inteligente baseado em múltiplos filtros estatísticos:

        1. Frequência recente (últimos 15 concursos) — "Score de Calor"
        2. Balanceamento ímpar/par (7-8 / 8-7)
        3. Padrão de repetição (8-10 números do último concurso)
        4. Faixa de soma ideal (baseada na distribuição histórica)
        5. Atraso (números que não saem há mais tempo)
        """
        async with async_session() as session:
            result = await session.execute(
                text("SELECT concurso, dezenas FROM lotomind.concursos ORDER BY data DESC LIMIT 100")
            )
            rows = result.fetchall()

        if not rows:
            game = sorted(random.sample(range(1, 26), 15))
            return SmartSuggestionResponse(
                game=game,
                filters_applied=["⚠️ Sem dados no banco — jogo aleatório"],
                metrics={
                    "odd_count": sum(1 for n in game if n % 2 != 0),
                    "even_count": sum(1 for n in game if n % 2 == 0),
                    "odd_numbers": [n for n in game if n % 2 != 0],
                    "even_numbers": [n for n in game if n % 2 == 0],
                    "sum": sum(game),
                    "sum_ideal_range": [170, 220],
                    "sum_mean": 195.0,
                    "repetitions_from_last": 0,
                    "last_contest": 0,
                    "last_contest_numbers": [],
                    "repeated_numbers": [],
                    "heat_scores": {},
                    "combined_scores": {},
                },
                explanation="Sem dados no banco. Jogo aleatório gerado.",
                confidence=0.0,
            )

        all_dezenas = [row[1] for row in rows]
        last_contest_nums = set(all_dezenas[0])
        last_contest_id = rows[0][0]

        # ── 1. Score de Calor (últimos 15 concursos) ──
        recent_15 = all_dezenas[:min(15, len(all_dezenas))]
        heat_counter = Counter()
        for dezenas in recent_15:
            for n in dezenas:
                heat_counter[n] += 1

        max_heat = max(heat_counter.values()) if heat_counter else 1
        heat_scores = {n: round(heat_counter.get(n, 0) / max_heat, 4) for n in range(1, 26)}

        # ── 2. Atraso (quantos concursos sem sair) ──
        delay = {}
        for n in range(1, 26):
            found = False
            for i, dezenas in enumerate(all_dezenas):
                if n in dezenas:
                    delay[n] = i
                    found = True
                    break
            if not found:
                delay[n] = len(all_dezenas)

        # ── 3. Soma ideal ──
        somas = [sum(d) for d in all_dezenas]
        soma_mean = float(np.mean(somas))
        soma_std = float(np.std(somas))
        soma_min_ideal = int(soma_mean - soma_std)
        soma_max_ideal = int(soma_mean + soma_std)

        # ── 4. Score combinado ──
        combined_scores = {}
        for n in range(1, 26):
            general_freq = sum(1 for d in all_dezenas if n in d) / len(all_dezenas)
            delay_score = min(delay[n] / 10, 1.0)
            score = (
                0.40 * heat_scores[n] +
                0.30 * delay_score +
                0.30 * general_freq
            )
            combined_scores[n] = round(score, 4)

        # ── 5. Gerar jogo com filtros ──
        filters_applied = []
        max_attempts = 500
        best_game = None
        best_score = -1

        for _ in range(max_attempts):
            nums = list(range(1, 26))
            weights = [combined_scores[n] + 0.01 for n in nums]
            total_w = sum(weights)
            probs = [w / total_w for w in weights]

            candidate = sorted(np.random.choice(nums, size=15, replace=False, p=probs).tolist())

            # Filtro: Balanceamento Ímpar/Par (7-8 ou 8-7)
            odds = sum(1 for n in candidate if n % 2 != 0)
            evens = 15 - odds
            if not ((odds == 7 and evens == 8) or (odds == 8 and evens == 7)):
                continue

            # Filtro: Repetição do último concurso (8-10 números)
            repetitions = len(set(candidate) & last_contest_nums)
            if not (8 <= repetitions <= 10):
                continue

            # Filtro: Soma na faixa ideal
            soma = sum(candidate)
            if not (soma_min_ideal <= soma <= soma_max_ideal):
                continue

            game_score = sum(combined_scores[n] for n in candidate)
            if game_score > best_score:
                best_score = game_score
                best_game = candidate

        # Relaxar filtros se necessário
        if best_game is None:
            filters_applied.append("⚠️ Filtros relaxados (nenhum jogo ideal encontrado)")
            for _ in range(200):
                nums = list(range(1, 26))
                weights = [combined_scores[n] + 0.01 for n in nums]
                total_w = sum(weights)
                probs = [w / total_w for w in weights]
                candidate = sorted(np.random.choice(nums, size=15, replace=False, p=probs).tolist())
                odds = sum(1 for n in candidate if n % 2 != 0)
                evens = 15 - odds
                if (odds == 7 and evens == 8) or (odds == 8 and evens == 7):
                    best_game = candidate
                    break

            if best_game is None:
                ranked = sorted(range(1, 26), key=lambda n: combined_scores[n], reverse=True)
                best_game = sorted(ranked[:15])

        game = best_game
        odds_count = sum(1 for n in game if n % 2 != 0)
        evens_count = 15 - odds_count
        game_sum = sum(game)
        repetitions = len(set(game) & last_contest_nums)
        odd_nums = sorted([n for n in game if n % 2 != 0])
        even_nums = sorted([n for n in game if n % 2 == 0])

        filters_applied.extend([
            f"✅ Balanceamento: {odds_count} Ímpares / {evens_count} Pares",
            f"✅ Repetição: {repetitions} números do concurso #{last_contest_id}",
            f"✅ Soma: {game_sum} (faixa ideal: {soma_min_ideal}-{soma_max_ideal})",
            f"✅ Score de calor (últimos 15 concursos) aplicado",
            f"✅ Fator de atraso considerado",
        ])

        confidence_score = 0.0
        if 7 <= odds_count <= 8:
            confidence_score += 0.25
        if 8 <= repetitions <= 10:
            confidence_score += 0.25
        if soma_min_ideal <= game_sum <= soma_max_ideal:
            confidence_score += 0.25
        confidence_score += 0.25

        explanation = (
            f"🧠 Jogo gerado com análise avançada de {len(all_dezenas)} concursos.\n\n"
            f"📊 **Distribuição:** {odds_count} ímpares ({', '.join(map(str, odd_nums))}) "
            f"e {evens_count} pares ({', '.join(map(str, even_nums))}).\n\n"
            f"🔁 **Repetição:** {repetitions} números do último concurso (#{last_contest_id}): "
            f"{sorted(list(set(game) & last_contest_nums))}.\n\n"
            f"➕ **Soma total:** {game_sum} (média histórica: {round(soma_mean, 1)}, "
            f"faixa ideal: {soma_min_ideal}-{soma_max_ideal}).\n\n"
            f"🔥 **Tendência recente:** Score de calor baseado nos últimos 15 concursos, "
            f"ponderado com fator de atraso e frequência geral."
        )

        return SmartSuggestionResponse(
            game=game,
            filters_applied=filters_applied,
            metrics={
                "odd_count": odds_count,
                "even_count": evens_count,
                "odd_numbers": odd_nums,
                "even_numbers": even_nums,
                "sum": game_sum,
                "sum_ideal_range": [soma_min_ideal, soma_max_ideal],
                "sum_mean": round(soma_mean, 1),
                "repetitions_from_last": repetitions,
                "last_contest": last_contest_id,
                "last_contest_numbers": sorted(list(last_contest_nums)),
                "repeated_numbers": sorted(list(set(game) & last_contest_nums)),
                "heat_scores": {str(n): heat_scores[n] for n in game},
                "combined_scores": {str(n): combined_scores[n] for n in game},
            },
            explanation=explanation,
            confidence=round(confidence_score, 2),
        )
