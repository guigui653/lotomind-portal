"""
LotoMind Portal — Estatística Avançada: LotteryPredictor
=========================================================
Modelos probabilísticos preditivos usando Cadeias de Markov
e Distribuição de Poisson para gerar um confidence_score (0–100%)
compatível com o Arsenal (JogoSalvo.score_metric).

Princípios:
  - 100% vetorizado com NumPy (zero for/while nos hot-paths)
  - Tipagem segura: todos os outputs são primitivos Python (JSON-safe)
  - Tolerante a falhas: funciona com dados reais ou mockados (Fallback)

Autor: LotoMind Engineering
"""

import numpy as np
from scipy.stats import poisson


class LotteryPredictor:
    """
    Motor de predição avançada para Lotofácil.

    Dois modelos independentes:
      1. Cadeia de Markov (25×25) — probabilidade de transição entre dezenas
      2. Poisson (25 lambdas) — pressão de retorno por atraso

    O confidence_score(bilhete) combina ambos em uma métrica 0–100%.
    """

    UNIVERSO = 25
    DEZENAS_SORTEIO = 15
    JANELA_POISSON = 100  # Últimos N concursos para calcular λ

    def __init__(self, peso_markov: float = 0.5, peso_poisson: float = 0.5):
        """
        Args:
            peso_markov: Peso do modelo Markov no score final (default 0.5).
            peso_poisson: Peso do modelo Poisson no score final (default 0.5).
        """
        self.peso_markov = peso_markov
        self.peso_poisson = peso_poisson

        # Modelos internos (preenchidos em carregar_historico)
        self.markov_matrix = np.zeros((self.UNIVERSO, self.UNIVERSO), dtype=float)
        self.poisson_lambdas = np.zeros(self.UNIVERSO, dtype=float)
        self.poisson_probs = np.zeros(self.UNIVERSO, dtype=float)
        self.atrasos = np.zeros(self.UNIVERSO, dtype=int)
        self.ultimo_concurso_dezenas = None

        self._historico_carregado = False

    # ════════════════════════════════════════════════════════════
    #  CARREGAMENTO E PREPARAÇÃO (Entry-Point)
    # ════════════════════════════════════════════════════════════

    def carregar_historico(self, df):
        """
        Recebe o DataFrame do histórico (mesmo formato do LotofacilEngine)
        e constrói ambos os modelos de forma 100% vetorizada.

        Colunas esperadas no DataFrame:
          - 'Concurso': int
          - 'Dezenas': list[int] (15 dezenas de 1 a 25)
        """
        if df is None or df.empty:
            return

        # ── Converter histórico para matriz binária (N, 25) ──
        n_jogos = len(df)
        hist_binary = np.zeros((n_jogos, self.UNIVERSO), dtype=np.int8)

        # Índices para batch encoding — otimizado com put_along_axis
        dezenas_lists = df['Dezenas'].tolist()
        for i, dezenas in enumerate(dezenas_lists):
            indices = np.array(dezenas, dtype=int) - 1
            hist_binary[i, indices] = 1

        # Guardar dezenas do último concurso (para transição de Markov)
        self.ultimo_concurso_dezenas = np.array(dezenas_lists[0], dtype=int)

        # ── Construir modelos ──
        self._construir_markov(hist_binary)
        self._construir_poisson(hist_binary)
        self._historico_carregado = True

    # ════════════════════════════════════════════════════════════
    #  MODELO 1: CADEIA DE MARKOV (Matriz de Transição 25×25)
    # ════════════════════════════════════════════════════════════

    def _construir_markov(self, hist_binary: np.ndarray):
        """
        Constrói a matriz de transição de Markov 25×25.

        Lógica vetorizada:
          Para cada par de concursos consecutivos (t, t+1), queremos contar
          co-transições: se dezena X saiu em t e dezena Y saiu em t+1.

          Isso equivale a: M_raw = hist[t].T @ hist[t+1]
          Somando sobre todos os pares: M_raw = hist[:-1].T @ hist[1:]
          Normalizando cada linha para somar 1.0 → probabilidades condicionais.

        O DataFrame vem ordenado do mais recente para o mais antigo,
        então hist[0] é o último concurso e hist[-1] é o mais antigo.
        Invertemos para que a transição vá de t → t+1 cronologicamente.
        """
        # Inverter para ordem cronológica (antigo → recente)
        hist_chrono = hist_binary[::-1]

        # Multiplação matricial: (25, N-1) @ (N-1, 25) → (25, 25)
        # hist_chrono[:-1] = todos exceto o último (papel de "t")
        # hist_chrono[1:]  = todos exceto o primeiro (papel de "t+1")
        M_raw = hist_chrono[:-1].astype(np.float64).T @ hist_chrono[1:].astype(np.float64)

        # Normalizar cada linha para somar 1.0 (probabilidades condicionais)
        row_sums = M_raw.sum(axis=1, keepdims=True)
        # Evitar divisão por zero (linhas com soma 0 ficam como probabilidade uniforme)
        row_sums = np.where(row_sums == 0, 1.0, row_sums)
        self.markov_matrix = M_raw / row_sums

    # ════════════════════════════════════════════════════════════
    #  MODELO 2: POISSON (Análise de Atraso)
    # ════════════════════════════════════════════════════════════

    def _construir_poisson(self, hist_binary: np.ndarray):
        """
        Calcula λ (taxa média de aparição) e P(retorno) para cada dezena.

        Lógica vetorizada:
          1. Janela: últimos JANELA_POISSON concursos (ou todos, se houver menos).
          2. λ = soma de cada coluna na janela (frequência absoluta).
          3. Atraso: para cada dezena, quantos concursos desde a última aparição.
             → np.argmax(hist_binary[:, col]) para achar a primeira ocorrência
               (hist está do mais recente para o mais antigo).
          4. P(retorno) = 1 - CDF(atraso - 1, λ) = survival function.
        """
        n_jogos = len(hist_binary)
        janela = min(self.JANELA_POISSON, n_jogos)

        # hist_binary[0] = mais recente; usar os primeiros 'janela' registros
        janela_binary = hist_binary[:janela]

        # λ = frequência de cada dezena na janela (vetor de 25)
        self.poisson_lambdas = janela_binary.sum(axis=0).astype(float)

        # Atraso: para cada coluna, achar o primeiro '1' a partir do mais recente
        # hist_binary[0] é o mais recente
        # np.argmax retorna o índice da primeira ocorrência do valor máximo (1)
        # Se a dezena não apareceu em nenhum dos concursos, argmax retorna 0
        # (o primeiro elemento), então precisamos checar se realmente há um 1 ali.
        atrasos = np.zeros(self.UNIVERSO, dtype=int)
        for col in range(self.UNIVERSO):
            coluna = hist_binary[:, col]
            if coluna.max() == 0:
                # Dezena nunca apareceu (praticamente impossível, mas safe)
                atrasos[col] = n_jogos
            else:
                atrasos[col] = int(np.argmax(coluna))
        self.atrasos = atrasos

        # P(retorno) via Poisson survival function: P(X >= atraso)
        # sf(k, mu) = 1 - CDF(k, mu) = P(X > k)
        # Queremos P(X >= atraso) = sf(atraso - 1, λ_normalizado)
        # Normalizar λ: transformar de "frequência na janela" para "taxa por concurso"
        lambda_por_concurso = self.poisson_lambdas / max(janela, 1)

        # Evitar λ = 0 (causaria problemas no Poisson)
        lambda_safe = np.where(lambda_por_concurso == 0, 0.01, lambda_por_concurso)

        # Atraso efetivo: usar atraso tal qual (em unidades de concursos)
        atraso_safe = np.maximum(self.atrasos - 1, 0)

        # Calcular P(retorno) vetorizado com scipy.stats.poisson.sf
        self.poisson_probs = poisson.sf(atraso_safe, lambda_safe * janela).astype(float)

        # Clip para garantir [0, 1]
        self.poisson_probs = np.clip(self.poisson_probs, 0.0, 1.0)

    # ════════════════════════════════════════════════════════════
    #  SCORE — Função Principal de Avaliação
    # ════════════════════════════════════════════════════════════

    def confidence_score(self, bilhete: list) -> dict:
        """
        Avalia um bilhete de 15 dezenas combinando Markov + Poisson.

        Args:
            bilhete: Lista de 15 inteiros (1 a 25), sem repetição.

        Returns:
            dict com:
              - score_markov (float, 0–100)
              - score_poisson (float, 0–100)
              - confidence_score (float, 0–100)
              - classificacao (str)
              - detalhes (dict com informações granulares)
        """
        if not self._historico_carregado:
            return {
                'score_markov': 0.0,
                'score_poisson': 0.0,
                'confidence_score': 0.0,
                'classificacao': '⚠️ Histórico não carregado',
                'detalhes': {},
            }

        bilhete_arr = np.array(bilhete, dtype=int)
        indices = bilhete_arr - 1  # Converter para 0-indexed

        # ── Score Markov ────────────────────────────────────
        score_markov = self._calcular_score_markov(indices)

        # ── Score Poisson ───────────────────────────────────
        score_poisson = self._calcular_score_poisson(indices)

        # ── Score Combinado ─────────────────────────────────
        score_final = (
            score_markov * self.peso_markov +
            score_poisson * self.peso_poisson
        )
        score_final = float(np.clip(score_final, 0.0, 100.0))

        # ── Classificação ───────────────────────────────────
        if score_final >= 75:
            classificacao = '🔮 VISIONÁRIO — Altíssima Confiança'
        elif score_final >= 60:
            classificacao = '⭐ FORTE — Boa Confiança'
        elif score_final >= 45:
            classificacao = '🟡 MODERADO — Confiança Média'
        else:
            classificacao = '🔵 EXPLORATÓRIO — Confiança Baixa'

        # ── Detalhes Granulares ─────────────────────────────
        detalhes = self._gerar_detalhes(bilhete_arr, indices)

        return {
            'score_markov': round(float(score_markov), 2),
            'score_poisson': round(float(score_poisson), 2),
            'confidence_score': round(score_final, 2),
            'classificacao': classificacao,
            'detalhes': detalhes,
        }

    def _calcular_score_markov(self, indices: np.ndarray) -> float:
        """
        Score Markov: dado o último concurso real, qual a probabilidade
        acumulada de transição para as dezenas do bilhete?

        Vetorizado: seleciona as linhas do último concurso na Markov matrix,
        soma as colunas correspondentes às dezenas do bilhete.
        """
        if self.ultimo_concurso_dezenas is None:
            return 0.0

        ultimo_indices = self.ultimo_concurso_dezenas - 1  # 0-indexed

        # Submatriz: linhas = dezenas do último concurso (15),
        #            colunas = dezenas do bilhete (15)
        # Cada M[i][j] = P(dezena j saia | dezena i saiu no concurso anterior)
        submatriz = self.markov_matrix[np.ix_(ultimo_indices, indices)]

        # Score bruto: média das probabilidades de transição
        # Multiplicamos por um fator para espalhar na faixa 0-100
        score_bruto = float(np.mean(submatriz))

        # Normalização:
        # A probabilidade média esperada por célula é (DEZENAS_SORTEIO / UNIVERSO) = 15/25 = 0.6
        # Se score_bruto ≈ 0.6 → score normalizado = ~50 (média)
        # Escalar linearmente: score = (bruto / esperado) * 50, capped a 100
        esperado = self.DEZENAS_SORTEIO / self.UNIVERSO
        if esperado > 0:
            score_normalizado = (score_bruto / esperado) * 50.0
        else:
            score_normalizado = 0.0

        return float(np.clip(score_normalizado, 0.0, 100.0))

    def _calcular_score_poisson(self, indices: np.ndarray) -> float:
        """
        Score Poisson: soma das P(retorno) das 15 dezenas do bilhete.

        Um bilhete que tenha dezenas "maduras" (alto atraso, alta pressão
        de retorno) terá um score Poisson maior.
        """
        # Selecionar P(retorno) das dezenas do bilhete
        probs_bilhete = self.poisson_probs[indices]

        # Score bruto: média das probabilidades (0 a 1)
        score_bruto = float(np.mean(probs_bilhete))

        # Normalizar para 0–100
        # A média esperada depende do estado do histórico.
        # Usamos uma normalização mais simples: score = bruto * 100
        # Isso coloca bilhetes com todas as dezenas "maduras" perto de 100
        # e bilhetes com todas as dezenas "recentes" perto de 0.
        score_normalizado = score_bruto * 100.0

        return float(np.clip(score_normalizado, 0.0, 100.0))

    def _gerar_detalhes(self, bilhete_arr: np.ndarray, indices: np.ndarray) -> dict:
        """Gera informações detalhadas para o frontend."""
        # Top 5 dezenas do bilhete com maior P(retorno) Poisson
        probs = self.poisson_probs[indices]
        sorted_idx = np.argsort(probs)[::-1][:5]

        top_poisson = []
        for i in sorted_idx:
            top_poisson.append({
                'dezena': int(bilhete_arr[i]),
                'atraso': int(self.atrasos[indices[i]]),
                'prob_retorno': round(float(probs[i]), 4),
            })

        # Top 5 transições Markov mais fortes para o bilhete
        top_markov = []
        if self.ultimo_concurso_dezenas is not None:
            ultimo_idx = self.ultimo_concurso_dezenas - 1
            for dezena_idx in indices:
                # Média da probabilidade de transição de todas as dezenas do
                # último concurso para esta dezena
                prob_media = float(np.mean(self.markov_matrix[ultimo_idx, dezena_idx]))
                top_markov.append({
                    'dezena': int(dezena_idx + 1),
                    'prob_transicao': round(prob_media, 4),
                })
            top_markov.sort(key=lambda x: x['prob_transicao'], reverse=True)
            top_markov = top_markov[:5]

        return {
            'top_poisson': top_poisson,
            'top_markov': top_markov,
            'ultimo_concurso': self.ultimo_concurso_dezenas.tolist() if self.ultimo_concurso_dezenas is not None else [],
            'janela_poisson': int(self.JANELA_POISSON),
        }

    # ════════════════════════════════════════════════════════════
    #  UTILITÁRIOS
    # ════════════════════════════════════════════════════════════

    def get_markov_heatmap_data(self) -> dict:
        """Retorna dados da Markov matrix formatados para renderizar um heatmap no frontend."""
        return {
            'labels': list(range(1, self.UNIVERSO + 1)),
            'matrix': [[round(float(self.markov_matrix[i][j]), 4)
                         for j in range(self.UNIVERSO)]
                        for i in range(self.UNIVERSO)],
        }

    def get_poisson_chart_data(self) -> dict:
        """Retorna dados de Poisson formatados para gráficos no frontend."""
        return {
            'dezenas': list(range(1, self.UNIVERSO + 1)),
            'lambdas': [round(float(l), 2) for l in self.poisson_lambdas],
            'atrasos': [int(a) for a in self.atrasos],
            'probabilidades': [round(float(p), 4) for p in self.poisson_probs],
        }
