import random
import numpy as np

class LotofacilMonteCarlo:
    """Motor de Simulação Monte Carlo para Lotofácil - Otimizado com NumPy."""

    def __init__(self, engine, df):
        self.engine = engine
        self.df = df
        self.contagem, _, _ = engine.analisar_frequencias(df)
        
        # Guardar histórico para multiplicações matriciais futuras (Top 500 para rapidez)
        self.historico_matrix = np.zeros((min(500, len(df)), 25), dtype=int)
        for i, dezenas in enumerate(df['Dezenas'].head(500)):
            for d in dezenas:
                self.historico_matrix[i, d - 1] = 1

    def simular(self, num_simulacoes=5000, top_n=5):
        """
        Gera milhares de jogos de forma vetorial, filtra e avalia matricialmente.
        """
        # Numerações de segurança para web
        num_simulacoes = min(num_simulacoes, 50000)
        top_n = min(top_n, 20)
        
        # 1. Geração Vetorial de Jogos (N, 15)
        # Random rand (N, 25) -> argsort dá a ordem (sem repetição) -> Pega 15
        random_matrix = np.random.rand(num_simulacoes, 25)
        jogos_gerados = np.sort(random_matrix.argsort(axis=1)[:, :15] + 1, axis=1)

        # 2. Eliminar Duplicados (se houver) na geração
        jogos_gerados = np.unique(jogos_gerados, axis=0)
        
        # 3. Filtro Estatístico Vetorizado
        pares = np.sum(jogos_gerados % 2 == 0, axis=1)
        somas = np.sum(jogos_gerados, axis=1)
        validos_mask = (pares >= 5) & (pares <= 9) & (somas >= 160) & (somas <= 230)
        jogos_validos = jogos_gerados[validos_mask]
        
        if len(jogos_validos) == 0:
            return []

        # 4. Avaliação Matricial do Histórico e Frequências
        # Converter jogos_validos (M, 15) para One-Hot-Encoding (M, 25)
        N_validos = len(jogos_validos)
        jogos_one_hot = np.zeros((N_validos, 25), dtype=int)
        np.put_along_axis(jogos_one_hot, jogos_validos - 1, 1, axis=1)

        # Acertos via Multiplicação de Matrizes (M, 500)
        acertos_historico = np.dot(jogos_one_hot, self.historico_matrix.T)
        
        # Contar prêmios 14 e 15 na matriz de acertos
        premios_14 = np.sum(acertos_historico == 14, axis=1)
        premios_15 = np.sum(acertos_historico == 15, axis=1)
        
        # 5. Score de Frequência Vetorizado
        freq_weights = np.array([self.contagem.get(i, 0) for i in range(1, 26)])
        scores_freq = np.dot(jogos_one_hot, freq_weights)
        
        # 6. Score Total
        scores_totais = (scores_freq * 0.1) + (premios_14 * 50) + (premios_15 * 500)

        # 7. Separar os melhores jogos
        melhores_indices = np.argsort(scores_totais)[::-1][:top_n]
        
        melhores = []
        for idx in melhores_indices:
            melhores.append({
                'dezenas': jogos_validos[idx].tolist(),
                'score': float(scores_totais[idx])
            })

        return melhores
