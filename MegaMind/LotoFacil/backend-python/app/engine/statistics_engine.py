"""
StatisticsEngine — Motor de cálculos estatísticos da Lotofácil.

Centraliza operações matemáticas reutilizáveis:
frequência, desvio, ciclos, atraso e correlações.
"""

import numpy as np
import pandas as pd


class StatisticsEngine:
    """Encapsula cálculos estatísticos sobre sorteios da Lotofácil."""

    @staticmethod
    def calculate_frequency(draws: np.ndarray, number: int) -> int:
        """Conta quantas vezes `number` apareceu nos sorteios."""
        return int(np.sum(draws == number))

    @staticmethod
    def calculate_delay(draws: np.ndarray, number: int) -> int:
        """Calcula há quantos concursos o número não é sorteado (atraso)."""
        for i in range(len(draws) - 1, -1, -1):
            if number in draws[i]:
                return len(draws) - 1 - i
        return len(draws)

    @staticmethod
    def frequency_distribution(draws: np.ndarray, min_num: int, max_num: int) -> pd.Series:
        """Retorna a distribuição de frequência de todos os números."""
        flat = draws.flatten()
        counts = pd.Series(flat).value_counts().reindex(
            range(min_num, max_num + 1), fill_value=0
        )
        return counts.sort_index()

    @staticmethod
    def detect_cycles(draws: np.ndarray, number: int) -> list[int]:
        """Calcula os intervalos entre aparições consecutivas de um número."""
        appearances = [i for i, draw in enumerate(draws) if number in draw]
        if len(appearances) < 2:
            return []
        return [appearances[i + 1] - appearances[i] for i in range(len(appearances) - 1)]
