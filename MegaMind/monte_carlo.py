import numpy as np
import time
from collections import Counter

class MonteCarloEngine:
    """
    Motor Estocástico para Simulação de Monte Carlo na Mega-Sena.
    Utiliza amostragem com base no peso histórico das frequências.
    """

    def __init__(self, engine):
        self.engine = engine

    def simular_cenarios(self, df, jogo, num_simulacoes=1000000):
        """
        Executa `num_simulacoes` sorteios utilizando 'Gumbel-max trick' otimizado via NumPy,
        aplicando os pesos históricos relativos de cada dezena.
        """
        start_time = time.time()
        
        # 1. Obter frequências
        todas = [n for sub in df['Dezenas'] for n in sub]
        contagem = Counter(todas)
        
        # Array de 60 posições (0 a 59), mapeando dezenas 1 a 60
        freqs = np.array([contagem.get(i, 1) for i in range(1, 61)], dtype=np.float64)
        
        # Normalizar para obter as probabilidades
        probs = freqs / freqs.sum()

        # 2. Truque de Gumbel-Max para amostragem ponderada sem reposição em grande escala
        # Evita log(0) adicionando um eps ínfimo
        log_probs = np.log(probs + 1e-10)
        
        # Ruído de Gumbel
        # shape = (1_000_000, 60)
        u = np.random.rand(num_simulacoes, 60)
        gumbel_noise = -np.log(-np.log(u))
        
        # Scores de propensão
        scores = log_probs + gumbel_noise
        
        # Obter os 6 maiores índices de cada simulação (axis=1)
        sorteios_idx = np.argpartition(scores, -6, axis=1)[:, -6:]
        sorteios = sorteios_idx + 1  # converter índice 0-59 para dezenas 1-60
        
        # 3. Avaliar acertos do jogo do usuário contra a matriz simulada
        jogo_array = np.array(jogo)
        
        # Verifica quais números do sorteio estão no jogo
        # Retorna uma matriz booleana (num_simulacoes, 6)
        acertos_matriz = np.isin(sorteios, jogo_array)
        
        # Soma os acertos por simulação
        acertos_por_simulacao = acertos_matriz.sum(axis=1)
        
        # 4. Compilar Resultados
        quadras = np.sum(acertos_por_simulacao == 4)
        quinas = np.sum(acertos_por_simulacao == 5)
        senas = np.sum(acertos_por_simulacao == 6)
        
        tempo_execucao = time.time() - start_time
        
        # Calcular Probabilidades Empíricas
        prob_quadra = (quadras / num_simulacoes) * 100
        prob_quina = (quinas / num_simulacoes) * 100
        prob_sena = (senas / num_simulacoes) * 100
        
        # Formatar ROI Esperado Numérico Teórico (Apenas visualização)
        # Assumindo Qdr(R$ 1.000), Qin(R$ 50.000), Sna(R$ 30.000.000)
        retorno_estimado = (quadras * 1000) + (quinas * 50000) + (senas * 30000000)
        investimento = num_simulacoes * 5.00 # Custo de R$ 5,00 por aposta simulada
        roi = ((retorno_estimado - investimento) / investimento) * 100 if investimento > 0 else 0

        return {
            'simulacoes': num_simulacoes,
            'tempo_segundos': round(tempo_execucao, 2),
            'jogo': jogo,
            'acertos': {
                'quadras': int(quadras),
                'quinas': int(quinas),
                'senas': int(senas)
            },
            'probabilidades': {
                'quadra_pct': prob_quadra,
                'quina_pct': prob_quina,
                'sena_pct': prob_sena
            },
            'financeiro_teorico': {
                'investimento': investimento,
                'retorno': retorno_estimado,
                'roi_pct': round(roi, 2)
            }
        }
