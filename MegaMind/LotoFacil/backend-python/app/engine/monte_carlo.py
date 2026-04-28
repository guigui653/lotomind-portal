import numpy as np
import logging

logger = logging.getLogger(__name__)

class MonteCarloValidator:
    """
    Motor de simulação de Monte Carlo para validar a viabilidade de jogos gerados.
    """

    def __init__(self, simulations: int = 10000):
        self.simulations = simulations

    def simulate_game_viability(self, numbers: list[int], prob_dist: np.ndarray) -> float:
        """
        Simula o desempenho do jogo contra N sorteios virtuais baseados na distribuição de probabilidade.
        Retorna um score de viabilidade (0 a 1).
        """
        if len(numbers) < 15:
            return 0.0

        my_game = set(numbers)
        hits_distribution = []

        # Criar sorteios simulados baseados na prob_dist (que deve ter tamanho 25)
        # Assumindo que prob_dist são probabilidades normalizadas para cada número de 1 a 25
        available_numbers = np.arange(1, 26)
        
        # Normalizar se necessário para garantir que somem para o sorteio de 15 números
        p = prob_dist / prob_dist.sum()

        for _ in range(self.simulations):
            simulated_draw = set(np.random.choice(available_numbers, size=15, replace=False, p=p))
            hits = len(my_game.intersection(simulated_draw))
            hits_distribution.append(hits)

        # Cálculo de viabilidade: probabilidade de obter 11 ou mais acertos na simulação
        success_count = len([h for h in hits_distribution if h >= 11])
        viability_score = success_count / self.simulations

        logger.info(f"Monte Carlo simulation complete. Viability Score (P>=11): {viability_score:.4f}")
        return viability_score
