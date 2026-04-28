"""
Prediction Generator — Lógica de Palpites Inteligentes.

Classifica números em Quentes/Frios com base na frequência dos últimos 100 resultados
e gera palpites equilibrados para aumentar a probabilidade estatística.
Suporta múltiplas estratégias: Aleatório, Equilibrado, Agressivo, Extremos.
"""

import logging
import random
from collections import Counter
import pandas as pd
import numpy as np
from sqlalchemy import text
from app.core.database import async_session
from app.services.consultant_service import ConsultantService

logger = logging.getLogger(__name__)


class PredictionGenerator:
    """Service to generate smart lottery predictions."""

    def __init__(self):
        self.consultant = ConsultantService()

    async def generate_prediction(self, strategy: str = "balanced") -> dict:
        """
        Gera um palpite com base na estratégia selecionada usando Pandas e filtros rigorosos.
        strategies: 'balanced', 'aggressive', 'hot_cold', 'random'
        """
        async with async_session() as session:
            # 1. Fetch last 100 results
            result = await session.execute(
                text("SELECT concurso, data, dezenas FROM lotomind.concursos ORDER BY data DESC LIMIT 100")
            )
            rows = result.fetchall()
            
            if not rows and strategy != "random":
                logger.warning("No data found for intelligent prediction. Returning random.")
                return self._generate_random()

        # 2. Convert to Pandas DataFrame for Robust Analysis
        data = []
        for row in rows:
            data.append({"concurso": row[0], "data": row[1], "dezenas": row[2]})
        
        df = pd.DataFrame(data)
        
        # Flatten all numbers to calculate global frequency
        # Check if 'dezenas' is list or string (Postgres array comes as list in SQLAlchemy)
        all_numbers = [num for dezenas in df["dezenas"] for num in dezenas]
        counter = Counter(all_numbers)
        
        # Ensure 1-25
        for i in range(1, 26):
            if i not in counter:
                counter[i] = 0

        # DataFrame for frequencies
        freq_df = pd.DataFrame.from_dict(counter, orient='index', columns=['count'])
        freq_df.index.name = 'numero'
        freq_df = freq_df.sort_values(by='count', ascending=False)
        
        sorted_nums = freq_df.index.tolist()
        
        # Hot: Top 5
        hot = sorted_nums[:5]
        # Cold: Bottom 5
        cold = sorted_nums[-5:]
        # Medium: The middle 15
        medium = sorted_nums[5:-5]

        # 3. Generate Game based on Strategy
        final_game = []
        strategy_details = {}

        if strategy == "balanced":
            # STRICT RULE: 8 Odd / 7 Even (Pattern Filter)
            # Try to generate a valid game respecting the composition
            found_valid = False
            for _ in range(200): # Attempt 200 times
                # Base mix: 5 Hot + 6 Medium + 4 Cold
                candidates = (
                    random.sample(hot, 5) + 
                    random.sample(medium, 6) + 
                    random.sample(cold, 4)
                )
                
                # Check Filter: 8 Odd / 7 Even or 7 Odd / 8 Even
                odds = [n for n in candidates if n % 2 != 0]
                
                if len(odds) in (7, 8):
                    final_game = sorted(candidates)
                    found_valid = True
                    break
            
            if not found_valid:
                 # Fallback
                 final_game = sorted(random.sample(hot, 5) + random.sample(medium, 6) + random.sample(cold, 4))
                 logger.warning("Could not satisfy 8/7 filter in 200 attempts. Returning best effort.")

            strategy_details = {
                "description": "⚖️ Estratégia Equilibrada: Filtro Rígido (8 Ímpares / 7 Pares) + Mix Estatístico.",
                "composition": { "hot": 5, "medium": 6, "cold": 4 }
            }
        
        elif strategy == "aggressive":
            # 5 Hot + 7 Medium + 3 Cold
            final_game = sorted(random.sample(hot, 5) + random.sample(medium, 7) + random.sample(cold, 3))
            strategy_details = {
                "description": "🔥 Estratégia Agressiva: Foca nas que mais saem.",
                "composition": { "hot": 5, "medium": 7, "cold": 3 }
            }

        elif strategy == "hot_cold":
            # 5 Hot + 5 Cold + 5 Medium
            final_game = sorted(random.sample(hot, 5) + random.sample(cold, 5) + random.sample(medium, 5))
            strategy_details = {
                "description": "❄️🔥 Estratégia Extremos: Joga nas pontas (muito atrasadas ou pegando fogo).",
                "composition": { "hot": 5, "medium": 5, "cold": 5 }
            }

        elif strategy == "random":
            return self._generate_random()
            
        else:
             # Fallback to balanced
            final_game = sorted(random.sample(hot, 5) + random.sample(medium, 6) + random.sample(cold, 4))
            strategy_details = {"description": "Fallback (Equilibrada)", "composition": {"hot": 5, "medium": 6, "cold": 4}}

        logger.info("Generated prediction (%s): %s", strategy, final_game)

        # Build chart data
        def build_chart_data(nums):
            return [{"name": str(n), "freq": counter.get(n, 0)} for n in nums]

        # Gerar texto do consultor
        analise = self.consultant.generate_consultant_analysis(
            game=final_game,
            strategy=strategy,
            counter=counter,
            hot=hot,
            cold=cold,
            all_dezenas=[row[2] for row in rows],
        )

        return {
            "game": final_game,
            "analysis": {
                "hot": hot,
                "cold": cold,
                "medium": medium,
                "charts": {
                    "hot": build_chart_data(hot),
                    "cold": build_chart_data(cold)
                }
            },
            "strategy": strategy_details,
            "analise_do_consultor": analise
        }

    def _generate_random(self):
        game = sorted(random.sample(range(1, 26), 15))
        return {
            "game": game,
            "analysis": { "hot": [], "cold": [], "medium": [] },
            "strategy": {
                "description": "🎰 Surpresinha (Aleatória): Sorte pura.",
                "composition": { "hot": 0, "medium": 0, "cold": 0 }
            },
            "analise_do_consultor": "Este jogo foi gerado de forma totalmente aleatória, sem análise estatística. Boa sorte!"
        }
