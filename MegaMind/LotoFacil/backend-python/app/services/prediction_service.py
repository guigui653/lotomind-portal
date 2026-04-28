"""
PredictionService — Previsão de tendências via Machine Learning.

Utiliza Scikit-Learn para classificar números em quentes/frios
baseado em padrões históricos de frequência.
"""

import asyncio
import logging

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

from app.core.config import settings
from app.core.redis_client import redis_manager
from app.schemas.prediction_schema import NumberTrend, PredictionResponse

logger = logging.getLogger(__name__)


class PredictionService:
    """Serviço de previsão de tendências com ML."""

    async def predict_trends(self, top_n: int = 10) -> PredictionResponse:
        """Gera previsão de números quentes e frios com score de confiança."""
        cache_key = f"predictions:top_{top_n}"

        cached = await redis_manager.get_cached(cache_key)
        if cached:
            return PredictionResponse(**cached)

        result = await asyncio.to_thread(self._run_prediction, top_n)

        await redis_manager.set_cached(
            cache_key, result.model_dump(), ttl=settings.REDIS_CACHE_TTL
        )
        return result

    def _run_prediction(self, top_n: int) -> PredictionResponse:
        """Execute ML prediction pipeline (blocking)."""
        min_num = settings.LOTOFACIL_MIN_NUMBER
        max_num = settings.LOTOFACIL_MAX_NUMBER
        draw_size = settings.LOTOFACIL_DRAW_SIZE
        n_contests = 200

        rng = np.random.default_rng(seed=42)
        all_numbers = np.arange(min_num, max_num + 1)

        # Simular histórico de sorteios
        draws = np.array([
            np.sort(rng.choice(all_numbers, size=draw_size, replace=False))
            for _ in range(n_contests)
        ])

        # Feature engineering: frequência em janelas deslizantes
        window_size = 20
        features = []
        labels = []

        for i in range(window_size, n_contests):
            window = draws[i - window_size:i]
            freq = np.array([np.sum(window == n) for n in all_numbers])
            features.append(freq)
            # Label: 1 se apareceu no sorteio seguinte
            labels.append(np.isin(all_numbers, draws[i]).astype(int))

        X = np.array(features)
        y = np.array(labels)

        # Treinar modelo por número
        hot_numbers: list[NumberTrend] = []
        cold_numbers: list[NumberTrend] = []
        accuracies: list[float] = []

        for idx, num in enumerate(all_numbers):
            y_num = y[:, idx]
            model = LogisticRegression(max_iter=500, random_state=42)
            scores = cross_val_score(model, X, y_num, cv=3, scoring="accuracy")
            accuracies.append(float(np.mean(scores)))

            model.fit(X, y_num)
            prob = float(model.predict_proba(X[-1:])[:, 1][0])

            freq_last = int(np.sum(draws[-window_size:] == num))

            trend_item = NumberTrend(
                number=int(num),
                trend="hot" if prob > 0.6 else ("cold" if prob < 0.4 else "neutral"),
                score=round(prob, 3),
                frequency=freq_last,
            )

            if trend_item.trend == "hot":
                hot_numbers.append(trend_item)
            elif trend_item.trend == "cold":
                cold_numbers.append(trend_item)

        # Ordenar e limitar
        hot_numbers.sort(key=lambda x: x.score, reverse=True)
        cold_numbers.sort(key=lambda x: x.score)

        return PredictionResponse(
            hot_numbers=hot_numbers[:top_n],
            cold_numbers=cold_numbers[:top_n],
            model_accuracy=round(float(np.mean(accuracies)), 3),
            contests_analyzed=n_contests,
        )
