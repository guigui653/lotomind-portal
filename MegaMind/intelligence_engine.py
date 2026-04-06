"""
LotoMind — Motor de Inteligência v2.0 (Mega-Sena)
=====================================================
Modelagem Matemática e Teoria das Probabilidades aplicadas
à análise do histórico da Mega-Sena para redução do espaço
amostral de 60 dezenas.

Diretrizes Técnicas Implementadas:
1. Filtro de Probabilidade Hipergeométrica
2. Entropia de Shannon
3. Resíduos de Pearson (χ²)
4. Clusterização e Distância Euclidiana
5. Lei de Benford (Primeiro Dígito)
6. Matriz de Correlação e Coocorrência
7. Janelas Deslizantes (Rolling Windows)
8. Decaimento Temporal (Lag Time)
9. Restrição Dimensional (Paridade / Primos)
"""

import numpy as np
import pandas as pd
from collections import Counter
from itertools import combinations
from typing import List, Dict, Tuple, Optional
from scipy.stats import hypergeom, chi2
import math
import random
import time


# ── Constantes ──────────────────────────────────────────────
UNIVERSO = 60
DEZENAS_POR_JOGO = 6
PRIMOS_1_60 = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}


class LotoMindEngine:
    """Motor de Inteligência Artificial para a Mega-Sena."""

    def __init__(self):
        self.historico: Optional[pd.DataFrame] = None
        self.frequencias: Dict[int, int] = {}
        self.freq_recente: Dict[int, int] = {}
        self.matriz_coocorrencia: Optional[np.ndarray] = None
        self.correlacoes_pares: Dict[Tuple[int, int], float] = {}
        self.correlacoes_trios: Dict[Tuple[int, int, int], float] = {}
        self.atraso_dezenas: Dict[int, int] = {}
        self.benford_real: Dict[int, float] = {}
        self.benford_esperado: Dict[int, float] = {}
        self.entropia_media_historica: float = 0.0
        self.janela_curta: int = 100
        self.janela_longa: int = 200

    # ═══════════════════════════════════════════════════════
    # CARREGAMENTO DE DADOS
    # ═══════════════════════════════════════════════════════

    def carregar_historico(self, df: pd.DataFrame) -> None:
        """Carrega o DataFrame de histórico e pré-calcula todas as análises."""
        self.historico = df.copy()
        self._calcular_frequencias()
        self._calcular_frequencias_recentes()
        self._calcular_matriz_coocorrencia()
        self._calcular_atrasos()
        self._calcular_benford()
        self._calcular_entropia_media()

    def _calcular_frequencias(self) -> None:
        """Frequência absoluta de cada dezena no histórico completo."""
        todas = [n for sub in self.historico['Dezenas'] for n in sub]
        self.frequencias = dict(Counter(todas))

    def _calcular_frequencias_recentes(self) -> None:
        """Frequência nas últimas `janela_curta` jogos (rolling window)."""
        recentes = self.historico.head(self.janela_curta)
        todas = [n for sub in recentes['Dezenas'] for n in sub]
        self.freq_recente = dict(Counter(todas))

    # ═══════════════════════════════════════════════════════
    # 1. FILTRO DE PROBABILIDADE HIPERGEOMÉTRICA
    # ═══════════════════════════════════════════════════════

    def probabilidade_hipergeometrica(self, k: int, n_quentes: int = 20) -> float:
        """
        Calcula P(X=k) pela distribuição hipergeométrica.
        M = UNIVERSO (60), n = dezenas_quentes (20), N = DEZENAS_POR_JOGO (6)
        k = quantas quentes queremos acertar.
        """
        return float(hypergeom.pmf(k, UNIVERSO, n_quentes, DEZENAS_POR_JOGO))

    def pico_hipergeometrico(self, n_quentes: int = 20) -> Dict:
        """
        Retorna a distribuição hipergeométrica completa e identifica o pico
        (valor de k com maior probabilidade).
        """
        distribuicao = {}
        for k in range(DEZENAS_POR_JOGO + 1):
            distribuicao[k] = round(self.probabilidade_hipergeometrica(k, n_quentes), 6)

        pico_k = max(distribuicao, key=distribuicao.get)
        return {
            'distribuicao': distribuicao,
            'pico_k': pico_k,
            'pico_probabilidade': distribuicao[pico_k],
            'faixa_ideal': [k for k, p in distribuicao.items() if p >= distribuicao[pico_k] * 0.5],
            'n_quentes': n_quentes,
        }

    def filtro_hipergeometrico(self, jogo: List[int], quentes: List[int]) -> Dict:
        """
        Verifica se o jogo está dentro do pico da curva hipergeométrica.
        """
        n_quentes = len(quentes)
        k_acertos = len(set(jogo).intersection(set(quentes)))
        prob = self.probabilidade_hipergeometrica(k_acertos, n_quentes)
        pico = self.pico_hipergeometrico(n_quentes)

        no_pico = k_acertos in pico['faixa_ideal']
        return {
            'k_quentes_no_jogo': k_acertos,
            'probabilidade': round(prob, 6),
            'pico_k': pico['pico_k'],
            'faixa_ideal': pico['faixa_ideal'],
            'no_pico': no_pico,
            'score': round(prob * 100, 2),
        }

    # ═══════════════════════════════════════════════════════
    # 2. ENTROPIA DE SHANNON
    # ═══════════════════════════════════════════════════════

    def calcular_entropia(self, jogo: List[int]) -> float:
        """
        H = -Σ p(x_i) * log₂(p(x_i))
        onde p(x_i) é a probabilidade de cada dezena baseada na frequência histórica.
        """
        total = sum(self.frequencias.values()) if self.frequencias else 1
        probs = []
        for n in jogo:
            freq = self.frequencias.get(n, 1)
            p = freq / total
            probs.append(p)

        # Normalizar para somar 1 dentro do jogo
        soma_probs = sum(probs)
        if soma_probs == 0:
            return 0.0

        probs_norm = [p / soma_probs for p in probs]
        H = -sum(p * math.log2(p) for p in probs_norm if p > 0)
        return round(H, 4)

    def _calcular_entropia_media(self) -> None:
        """Calcula a entropia média do histórico para referência."""
        if self.historico is None or self.historico.empty:
            self.entropia_media_historica = 2.5
            return

        entropias = []
        for dezenas in self.historico['Dezenas']:
            if isinstance(dezenas, list) and len(dezenas) == DEZENAS_POR_JOGO:
                H = self.calcular_entropia(dezenas)
                entropias.append(H)

        self.entropia_media_historica = round(float(np.mean(entropias)), 4) if entropias else 2.5

    def filtro_entropia(self, jogo: List[int]) -> Dict:
        """
        Verifica se a entropia do jogo está acima da média histórica.
        Jogos com H abaixo da média = muito previsíveis / ordenados → eliminados.
        """
        H = self.calcular_entropia(jogo)
        acima_media = H >= self.entropia_media_historica

        return {
            'entropia': H,
            'media_historica': self.entropia_media_historica,
            'aprovado': acima_media,
            'classificacao': (
                '✅ Alta Entropia' if H > self.entropia_media_historica * 1.05
                else ('🟡 Normal' if acima_media else '❌ Baixa Entropia')
            ),
        }

    # ═══════════════════════════════════════════════════════
    # 3. RESÍDUOS DE PEARSON (χ²)
    # ═══════════════════════════════════════════════════════

    def calcular_residuos_pearson(self) -> Dict[int, Dict]:
        """
        Para cada dezena, calcula o resíduo de Pearson:
        R_i = (O_i - E_i) / √E_i
        onde O_i = freq observada, E_i = freq esperada.
        Prioriza dezenas com viés de maturação positiva.
        """
        if self.historico is None:
            return {}

        total_jogos = len(self.historico)
        # Frequência esperada ~ total_jogos * (6/60) = total_jogos * 0.1
        freq_esperada = total_jogos * (DEZENAS_POR_JOGO / UNIVERSO)

        residuos = {}
        for dezena in range(1, UNIVERSO + 1):
            obs = self.frequencias.get(dezena, 0)
            obs_rec = self.freq_recente.get(dezena, 0)
            residuo = (obs - freq_esperada) / math.sqrt(freq_esperada) if freq_esperada > 0 else 0

            # Viés de maturação: compara freq recente vs histórica
            freq_esperada_rec = min(len(self.historico), self.janela_curta) * (DEZENAS_POR_JOGO / UNIVERSO)
            residuo_recente = (obs_rec - freq_esperada_rec) / math.sqrt(freq_esperada_rec) if freq_esperada_rec > 0 else 0

            # Maturação = dezena abaixo do esperado recentemente mas acima no histórico
            maturacao = residuo - residuo_recente

            residuos[dezena] = {
                'frequencia_observada': obs,
                'frequencia_esperada': round(freq_esperada, 2),
                'residuo_pearson': round(residuo, 3),
                'residuo_recente': round(residuo_recente, 3),
                'maturacao': round(maturacao, 3),
                'classificacao': (
                    '🔥 Sobrefrequente' if residuo > 1.5
                    else ('❄️ Subfrequente' if residuo < -1.5
                          else '➡️ Normal')
                ),
            }

        return residuos

    def dezenas_com_vies_maturacao(self, top_n: int = 15) -> List[Dict]:
        """Retorna as dezenas com maior viés de maturação (prontas para retornar)."""
        residuos = self.calcular_residuos_pearson()
        maturadas = sorted(residuos.items(), key=lambda x: x[1]['maturacao'], reverse=True)

        return [
            {'dezena': d, **info}
            for d, info in maturadas[:top_n]
        ]

    def chi_quadrado_geral(self) -> Dict:
        """Teste χ² geral para avaliar se a distribuição é significativamente diferente do esperado."""
        if self.historico is None:
            return {'chi2': 0, 'p_valor': 1, 'significativo': False}

        total_jogos = len(self.historico)
        freq_esperada = total_jogos * (DEZENAS_POR_JOGO / UNIVERSO)

        chi2_stat = sum(
            ((self.frequencias.get(d, 0) - freq_esperada) ** 2) / freq_esperada
            for d in range(1, UNIVERSO + 1)
        )

        graus_liberdade = UNIVERSO - 1
        p_valor = 1 - chi2.cdf(chi2_stat, graus_liberdade)

        return {
            'chi2': round(chi2_stat, 3),
            'graus_liberdade': graus_liberdade,
            'p_valor': round(p_valor, 6),
            'significativo': p_valor < 0.05,
            'interpretacao': (
                '⚠️ Distribuição NÃO uniforme (p < 0.05)' if p_valor < 0.05
                else '✅ Distribuição próxima da uniforme'
            ),
        }

    # ═══════════════════════════════════════════════════════
    # 4. CLUSTERIZAÇÃO E DISTÂNCIA EUCLIDIANA
    # ═══════════════════════════════════════════════════════

    def analisar_clusterizacao(self, jogo: List[int]) -> Dict:
        """
        Analisa a distribuição espacial do jogo:
        - σ normalizado deve estar entre 1.5 e 2.5
        - Verifica gaps (distâncias entre números consecutivos)
        """
        jogo_sorted = sorted(jogo)
        sigma = float(np.std(jogo_sorted))

        # Normalizar σ para escala comparável
        sigma_normalizado = sigma / (UNIVERSO / DEZENAS_POR_JOGO)  # σ / 10

        # Gaps entre números consecutivos
        gaps = [jogo_sorted[i + 1] - jogo_sorted[i] for i in range(len(jogo_sorted) - 1)]
        gap_medio = float(np.mean(gaps))
        gap_std = float(np.std(gaps))

        # Distância euclidiana da distribuição ideal (uniforme)
        ideal = np.linspace(1, 60, DEZENAS_POR_JOGO)
        dist_euclidiana = float(np.sqrt(np.sum((np.array(jogo_sorted) - ideal) ** 2)))

        # Validação de decenais (não pode ter >= 4 no mesmo decenal)
        decenais = [((n - 1) // 10) for n in jogo]
        contagem_decenais = Counter(decenais)
        max_no_decenal = max(contagem_decenais.values()) if contagem_decenais else 0
        aglomeracao_decenal = max_no_decenal >= 4

        aprovado = 1.5 <= sigma_normalizado <= 2.5 and not aglomeracao_decenal

        return {
            'sigma': round(sigma, 3),
            'sigma_normalizado': round(sigma_normalizado, 3),
            'aprovado': aprovado,
            'faixa_ideal': '1.5 – 2.5 e max 3 por decenal',
            'gaps': gaps,
            'gap_medio': round(gap_medio, 2),
            'gap_desvio': round(gap_std, 2),
            'distancia_euclidiana': round(dist_euclidiana, 2),
            'max_mesmo_decenal': max_no_decenal,
            'classificacao': (
                '❌ Aglomeração em Decenal' if aglomeracao_decenal
                else ('✅ Dispersão Ampla' if aprovado
                else ('⚠️ Muito Agrupado (σ baixo)' if sigma_normalizado < 1.5
                      else '⚠️ Muito Espalhado (σ alto)'))
            ),
        }

    # ═══════════════════════════════════════════════════════
    # 5. FILTRO GEOMÉTRICO DE QUADRANTES
    # ═══════════════════════════════════════════════════════

    def filtro_geometrico_quadrantes(self, jogo: List[int]) -> Dict:
        """
        O volante (60 dezenas) é dividido em 4 quadrantes.
        Exige-se que as dezenas estejam distribuídas em pelo menos 3 dos 4 quadrantes.
        Q1 (1-15), Q2 (16-30), Q3 (31-45), Q4 (46-60) simplificado para fins de distribuição
        geométrica, comumente definido como:
        Q1 (1-5, 11-15, 21-25) - Superior Esquerdo
        Q2 (6-10, 16-20, 26-30) - Superior Direito
        Q3 (31-35, 41-45, 51-55) - Inferior Esquerdo
        Q4 (36-40, 46-50, 56-60) - Inferior Direito
        """
        quadrantes_jogo = set()
        for n in jogo:
            linha = (n - 1) // 10
            coluna = (n - 1) % 10

            is_esquerda = coluna <= 4
            is_superior = linha <= 2

            if is_superior and is_esquerda: q = 1
            elif is_superior and not is_esquerda: q = 2
            elif not is_superior and is_esquerda: q = 3
            else: q = 4

            quadrantes_jogo.add(q)

        qtd_quadrantes = len(quadrantes_jogo)
        aprovado = qtd_quadrantes >= 3

        return {
            'quadrantes_sorteados': sorted(list(quadrantes_jogo)),
            'qtd_quadrantes': qtd_quadrantes,
            'aprovado': aprovado,
            'descricao': f'{qtd_quadrantes} de 4 quadrantes',
        }

    # ═══════════════════════════════════════════════════════
    # 6. LEI DE BENFORD (PRIMEIRO DÍGITO)
    # ═══════════════════════════════════════════════════════

    def _calcular_benford(self) -> None:
        """Calcula distribuição de Benford real vs esperada."""
        # Distribuição esperada pela Lei de Benford
        self.benford_esperado = {
            d: round(math.log10(1 + 1 / d), 4) for d in range(1, 7)
            # Dígitos 1-6 (dezenas 01-60, primeiro dígito pode ser 1-6)
        }

        if self.historico is None:
            return

        # Coletar primeiros dígitos das últimas janela_longa dezenas
        recentes = self.historico.head(self.janela_longa)
        primeiros_digitos = []
        for dezenas in recentes['Dezenas']:
            for d in dezenas:
                primeiro = int(str(d)[0])
                if primeiro > 0:
                    primeiros_digitos.append(primeiro)

        total = len(primeiros_digitos)
        contagem = Counter(primeiros_digitos)

        self.benford_real = {}
        for d in range(1, 7):
            self.benford_real[d] = round(contagem.get(d, 0) / total, 4) if total > 0 else 0

    def analise_benford(self) -> Dict:
        """Retorna a análise completa de Benford com anomalias detectadas."""
        anomalias = []
        for d in range(1, 7):
            real = self.benford_real.get(d, 0)
            esperado = self.benford_esperado.get(d, 0)
            desvio = abs(real - esperado)
            if desvio > 0.05:
                anomalias.append({
                    'digito': d,
                    'real': round(real * 100, 2),
                    'esperado': round(esperado * 100, 2),
                    'desvio': round(desvio * 100, 2),
                    'tipo': 'Excesso' if real > esperado else 'Deficit',
                })

        conformidade = 1.0 - (sum(
            abs(self.benford_real.get(d, 0) - self.benford_esperado.get(d, 0))
            for d in range(1, 7)
        ) / 2)

        return {
            'distribuicao_real': {d: round(v * 100, 2) for d, v in self.benford_real.items()},
            'distribuicao_esperada': {d: round(v * 100, 2) for d, v in self.benford_esperado.items()},
            'anomalias': anomalias,
            'conformidade': round(max(0, conformidade) * 100, 1),
            'has_anomalias': len(anomalias) > 0,
        }

    # ═══════════════════════════════════════════════════════
    # 6. MATRIZ DE CORRELAÇÃO E COOCORRÊNCIA
    # ═══════════════════════════════════════════════════════

    def _calcular_matriz_coocorrencia(self) -> None:
        """Constrói a matriz de coocorrência 60x60."""
        if self.historico is None:
            return

        mat = np.zeros((UNIVERSO, UNIVERSO), dtype=int)

        for dezenas in self.historico['Dezenas']:
            if isinstance(dezenas, list):
                for i, j in combinations(dezenas, 2):
                    mat[i - 1][j - 1] += 1
                    mat[j - 1][i - 1] += 1

        self.matriz_coocorrencia = mat
        self._extrair_correlacoes()

    def _extrair_correlacoes(self) -> None:
        """Extrai os pares e trios com maior/menor correlação."""
        if self.matriz_coocorrencia is None:
            return

        total_jogos = len(self.historico)
        prob_esperada = (DEZENAS_POR_JOGO / UNIVERSO) ** 2 * total_jogos

        pares = {}
        for i in range(UNIVERSO):
            for j in range(i + 1, UNIVERSO):
                obs = self.matriz_coocorrencia[i][j]
                corr = (obs - prob_esperada) / max(1, math.sqrt(prob_esperada))
                pares[(i + 1, j + 1)] = round(corr, 3)

        self.correlacoes_pares = pares

    def top_pares_positivos(self, top_n: int = 15) -> List[Dict]:
        """Pares que mais saem juntos."""
        ranked = sorted(self.correlacoes_pares.items(), key=lambda x: x[1], reverse=True)
        return [
            {'par': list(p), 'correlacao': c, 'coocorrencias': int(self.matriz_coocorrencia[p[0]-1][p[1]-1])}
            for p, c in ranked[:top_n]
        ]

    def top_pares_negativos(self, top_n: int = 15) -> List[Dict]:
        """Pares que raramente saem juntos."""
        ranked = sorted(self.correlacoes_pares.items(), key=lambda x: x[1])
        return [
            {'par': list(p), 'correlacao': c, 'coocorrencias': int(self.matriz_coocorrencia[p[0]-1][p[1]-1])}
            for p, c in ranked[:top_n]
        ]

    def score_coocorrencia_jogo(self, jogo: List[int]) -> Dict:
        """Avalia o jogo com base na matriz de coocorrência."""
        pares_jogo = list(combinations(sorted(jogo), 2))
        scores = []
        detalhes = []

        for par in pares_jogo:
            corr = self.correlacoes_pares.get(par, 0)
            scores.append(corr)
            detalhes.append({'par': list(par), 'correlacao': corr})

        media = float(np.mean(scores)) if scores else 0
        return {
            'score_medio': round(media, 3),
            'pares_positivos': sum(1 for s in scores if s > 0.5),
            'pares_negativos': sum(1 for s in scores if s < -0.5),
            'total_pares': len(pares_jogo),
            'top_pares': sorted(detalhes, key=lambda x: x['correlacao'], reverse=True)[:5],
        }

    # ═══════════════════════════════════════════════════════
    # 7. JANELAS DESLIZANTES (ROLLING WINDOWS)
    # ═══════════════════════════════════════════════════════

    def analise_rolling_window(self, janela: int = 100) -> Dict:
        """
        Análise com janela deslizante dos últimos `janela` concursos.
        Compara tendências de curto prazo com o histórico geral.
        """
        if self.historico is None:
            return {}

        recentes = self.historico.head(min(janela, len(self.historico)))
        todas_rec = [n for sub in recentes['Dezenas'] for n in sub]
        freq_rec = Counter(todas_rec)
        total_rec = len(recentes)

        total_geral = len(self.historico)

        tendencias = {}
        for dezena in range(1, UNIVERSO + 1):
            fr_rec = freq_rec.get(dezena, 0) / max(total_rec, 1)
            fr_hist = self.frequencias.get(dezena, 0) / max(total_geral, 1)

            # Taxa de variação
            if fr_hist > 0:
                variacao = (fr_rec - fr_hist) / fr_hist * 100
            else:
                variacao = 0

            # Peso triplicado para últimos 50 (Master Prompt exige foco recente mais forte)
            # A 'janela' pode ser até 100, mas vamos triplicar o peso se a variação for muito forte
            peso_trend = 1.0
            if variacao > 30:
                trend = '📈 Alta Tendência'
                peso_trend = 3.0
            elif variacao > 15:
                trend = '↗️ Subindo'
                peso_trend = 2.0
            elif variacao < -20:
                trend = '📉 Caindo'
                peso_trend = 0.5
            else:
                trend = '➡️ Estável'

            tendencias[dezena] = {
                'freq_recente': freq_rec.get(dezena, 0),
                'freq_percentual_rec': round(fr_rec * 100, 2),
                'freq_percentual_hist': round(fr_hist * 100, 2),
                'variacao': round(variacao, 1),
                'tendencia': trend,
            }

        # Resumo
        subindo = [d for d, t in tendencias.items() if '📈' in t['tendencia'] or '↗️' in t['tendencia']]
        caindo = [d for d, t in tendencias.items() if '📉' in t['tendencia']]

        return {
            'janela': janela,
            'total_concursos': total_rec,
            'tendencias': tendencias,
            'dezenas_subindo': sorted(subindo),
            'dezenas_caindo': sorted(caindo),
            'dezenas_estaveis': sorted([d for d in range(1, 61) if d not in subindo and d not in caindo]),
        }

    # ═══════════════════════════════════════════════════════
    # 8. DECAIMENTO TEMPORAL (LAG TIME)
    # ═══════════════════════════════════════════════════════

    def _calcular_atrasos(self) -> None:
        """Calcula o atraso (lag) de cada dezena."""
        if self.historico is None:
            return

        for dezena in range(1, UNIVERSO + 1):
            atraso = 0
            for _, row in self.historico.iterrows():
                if dezena in row['Dezenas']:
                    break
                atraso += 1
            self.atraso_dezenas[dezena] = atraso

    def decaimento_temporal(self) -> List[Dict]:
        """
        Retorna dezenas ordenadas por urgência de retorno.
        O peso cresce conforme o atraso supera a média esperada.
        """
        # Média esperada de atraso: UNIVERSO / DEZENAS_POR_JOGO = 10 concursos
        media_esperada = UNIVERSO / DEZENAS_POR_JOGO

        resultado = []
        for dezena in range(1, UNIVERSO + 1):
            atraso = self.atraso_dezenas.get(dezena, 0)
            # Peso exponencial de decaimento
            if atraso > media_esperada:
                peso = 1.0 + (atraso - media_esperada) / media_esperada
                peso = min(peso, 3.0)  # Cap em 3x
            else:
                peso = atraso / media_esperada

            # Classificação
            if atraso >= media_esperada * 2:
                zona = '🔴 Atraso Crítico'
            elif atraso >= media_esperada * 1.5:
                zona = '🟡 Atraso Moderado'
            elif atraso >= media_esperada:
                zona = '🟢 Normal'
            else:
                zona = '🔵 Recente'

            resultado.append({
                'dezena': dezena,
                'atraso': atraso,
                'media_esperada': round(media_esperada, 1),
                'peso': round(peso, 3),
                'zona': zona,
            })

        return sorted(resultado, key=lambda x: x['atraso'], reverse=True)

    def dezenas_atraso_critico(self, top_n: int = 15) -> List[Dict]:
        """Top N dezenas em atraso crítico."""
        return self.decaimento_temporal()[:top_n]

    # ═══════════════════════════════════════════════════════
    # 9. RESTRIÇÃO DIMENSIONAL (PARIDADE / PRIMOS)
    # ═══════════════════════════════════════════════════════

    def validar_restricao_dimensional(self, jogo: List[int]) -> Dict:
        """
        Verifica restrições:
        - Paridade: 3:3 ou 4:2 (pares/ímpares)
        - Primos: entre 1 e 3 números primos
        """
        pares = sum(1 for n in jogo if n % 2 == 0)
        impares = len(jogo) - pares

        # Distribuições aceitas
        paridade_ok = (pares, impares) in [(3, 3), (4, 2), (2, 4)]

        # Primos
        qtd_primos = sum(1 for n in jogo if n in PRIMOS_1_60)
        lista_primos = [n for n in jogo if n in PRIMOS_1_60]
        primos_ok = 0 <= qtd_primos <= 2  # Mega-Sena: max 2 primos (Master Prompt)

        # Soma total
        soma = sum(jogo)
        soma_ok = 150 <= soma <= 270

        return {
            'paridade': {
                'pares': pares,
                'impares': impares,
                'formato': f'{pares}P/{impares}I',
                'aprovado': paridade_ok,
                'distribuicoes_aceitas': ['3P/3I', '4P/2I', '2P/4I'],
            },
            'primos': {
                'quantidade': qtd_primos,
                'numeros': lista_primos,
                'aprovado': primos_ok,
                'faixa_aceita': '0 a 2',
            },
            'soma': {
                'valor': soma,
                'aprovado': soma_ok,
                'faixa_aceita': '150 a 270',
            },
            'aprovado': paridade_ok and primos_ok and soma_ok,
        }

    # ═══════════════════════════════════════════════════════
    # PIPELINE COMPLETO DE ANÁLISE
    # ═══════════════════════════════════════════════════════

    def analise_completa_jogo(self, jogo: List[int], quentes: List[int] = None) -> Dict:
        """
        Executa TODAS as 9 diretrizes sobre um jogo.
        Retorna score final e detalhamento por diretriz.
        """
        if quentes is None:
            # Calcular quentes do histórico
            quentes = sorted(self.frequencias, key=self.frequencias.get, reverse=True)[:20]

        resultado = {}
        score_total = 0
        total_aprovados = 0

        # 1. Hipergeométrica (peso 15)
        hiper = self.filtro_hipergeometrico(jogo, quentes)
        resultado['hipergeometrica'] = hiper
        if hiper['no_pico']:
            score_total += 15
            total_aprovados += 1

        # 2. Entropia de Shannon (peso 12)
        entropia = self.filtro_entropia(jogo)
        resultado['entropia'] = entropia
        if entropia['aprovado']:
            score_total += 12
            total_aprovados += 1

        # 3. Resíduos de Pearson — avalia se as dezenas do jogo têm bom viés (peso 10)
        residuos = self.calcular_residuos_pearson()
        score_pearson = 0
        for n in jogo:
            mat = residuos.get(n, {}).get('maturacao', 0)
            score_pearson += max(0, mat)
        score_pearson = min(10, score_pearson)
        resultado['pearson'] = {
            'score': round(score_pearson, 2),
            'aprovado': score_pearson >= 3,
            'dezenas_maturadas': [n for n in jogo if residuos.get(n, {}).get('maturacao', 0) > 0.5],
        }
        if score_pearson >= 3:
            score_total += 10
            total_aprovados += 1

        # 4. Clusterização (peso 11)
        cluster = self.analisar_clusterizacao(jogo)
        resultado['clusterizacao'] = cluster
        if cluster['aprovado']:
            score_total += 11
            total_aprovados += 1

        # 5. Quadrantes (peso 6)
        quad = self.filtro_geometrico_quadrantes(jogo)
        resultado['quadrantes'] = quad
        if quad['aprovado']:
            score_total += 6
            total_aprovados += 1

        # 6. Lei de Benford — score baseado em conformidade (peso 8)
        benford = self.analise_benford()
        benford_score = min(8, benford['conformidade'] * 0.08)
        resultado['benford'] = {
            'conformidade': benford['conformidade'],
            'score': round(benford_score, 2),
            'aprovado': benford['conformidade'] >= 70,
        }
        if benford['conformidade'] >= 70:
            score_total += 8
            total_aprovados += 1

        # 7. Coocorrência (peso 12)
        cooc = self.score_coocorrencia_jogo(jogo)
        cooc_score = min(12, max(0, (cooc['score_medio'] + 2) * 3))
        resultado['coocorrencia'] = {
            **cooc,
            'score': round(cooc_score, 2),
            'aprovado': cooc['pares_positivos'] >= 3,
        }
        if cooc['pares_positivos'] >= 3:
            score_total += round(cooc_score)
            total_aprovados += 1

        # 8. Rolling Windows — verifica se o jogo usa dezenas em tendência (peso 10)
        rolling = self.analise_rolling_window(self.janela_curta)
        dezenas_subindo = set(rolling.get('dezenas_subindo', []))
        n_subindo = len(set(jogo).intersection(dezenas_subindo))
        rolling_score = min(10, n_subindo * 3)
        resultado['rolling_windows'] = {
            'dezenas_subindo_no_jogo': n_subindo,
            'total_subindo': len(dezenas_subindo),
            'score': rolling_score,
            'aprovado': n_subindo >= 2,
        }
        if n_subindo >= 2:
            score_total += rolling_score
            total_aprovados += 1

        # 9. Decaimento Temporal (peso 10)
        atrasados = {d['dezena']: d['peso'] for d in self.decaimento_temporal()}
        peso_atraso = sum(atrasados.get(n, 0) for n in jogo)
        decay_score = min(10, peso_atraso * 1.5)
        n_criticos = sum(1 for n in jogo if atrasados.get(n, 0) >= 1.5)
        resultado['decaimento'] = {
            'peso_total_atraso': round(peso_atraso, 2),
            'dezenas_atrasadas': n_criticos,
            'score': round(decay_score, 2),
            'aprovado': n_criticos >= 1,
        }
        if n_criticos >= 1:
            score_total += round(decay_score)
            total_aprovados += 1

        # 10. Restrição Dimensional (peso 6)
        restricao = self.validar_restricao_dimensional(jogo)
        resultado['restricao_dimensional'] = restricao
        if restricao['aprovado']:
            score_total += 6
            total_aprovados += 1

        # Score final
        score_final = min(100, score_total)
        classificacao = (
            '🏆 Elite LotoMind' if score_final >= 85 else
            '🥇 Excelente' if score_final >= 70 else
            '🥈 Bom' if score_final >= 55 else
            '🥉 Regular' if score_final >= 40 else
            '⚠️ Fraco'
        )

        return {
            'jogo': sorted(jogo),
            'score_final': score_final,
            'max_score': 100,
            'classificacao': classificacao,
            'diretrizes_aprovadas': total_aprovados,
            'total_diretrizes': 10,
            'detalhes': resultado,
        }

    # ═══════════════════════════════════════════════════════
    # GERADOR INTELIGENTE
    # ═══════════════════════════════════════════════════════

    def gerar_jogo_inteligente(self, max_tentativas: int = 500) -> Dict:
        """
        Gera um jogo usando pipeline completo das 9 diretrizes.
        Usa pool ponderado por decaimento temporal + frequências.
        """
        quentes = sorted(self.frequencias, key=self.frequencias.get, reverse=True)[:20]
        atrasados = {d['dezena']: d['peso'] for d in self.decaimento_temporal()}
        rolling = self.analise_rolling_window(self.janela_curta)
        subindo = set(rolling.get('dezenas_subindo', []))

        # Pool ponderado
        pesos = {}
        for d in range(1, UNIVERSO + 1):
            peso_base = self.frequencias.get(d, 1) / max(sum(self.frequencias.values()), 1)
            peso_atraso = atrasados.get(d, 0.5)
            peso_trend = 1.3 if d in subindo else 1.0
            pesos[d] = peso_base * (1 + peso_atraso) * peso_trend

        dezenas_pool = list(pesos.keys())
        pesos_pool = np.array([pesos[d] for d in dezenas_pool])
        pesos_pool = pesos_pool / pesos_pool.sum()

        melhor = None
        melhor_score = 0

        for _ in range(max_tentativas):
            jogo = sorted(np.random.choice(dezenas_pool, size=DEZENAS_POR_JOGO, replace=False, p=pesos_pool).tolist())
            analise = self.analise_completa_jogo(jogo, quentes)

            if analise['score_final'] > melhor_score:
                melhor_score = analise['score_final']
                melhor = analise

            if melhor_score >= 75:
                break

        return melhor

    def gerar_multiplos_jogos(self, qtd: int = 5, max_tentativas_por_jogo: int = 500) -> List[Dict]:
        """Gera múltiplos jogos otimizados, sem repetições."""
        jogos = []
        jogos_gerados = set()

        for _ in range(qtd):
            for tentativa in range(3):  # Máximo 3 tentativas por jogo
                resultado = self.gerar_jogo_inteligente(max_tentativas_por_jogo)
                if resultado:
                    jogo_key = tuple(resultado['jogo'])
                    if jogo_key not in jogos_gerados:
                        jogos_gerados.add(jogo_key)
                        jogos.append(resultado)
                        break

        return sorted(jogos, key=lambda x: x['score_final'], reverse=True)

    # ═══════════════════════════════════════════════════════
    # RESUMO GERAL DAS DIRETRIZES
    # ═══════════════════════════════════════════════════════

    def resumo_diretrizes(self) -> Dict:
        """Retorna o status de todas as 9 diretrizes com dados calculados."""
        chi2_info = self.chi_quadrado_geral()
        benford_info = self.analise_benford()
        rolling_info = self.analise_rolling_window(self.janela_curta)
        atrasados = self.dezenas_atraso_critico(10)
        maturados = self.dezenas_com_vies_maturacao(10)
        pares_pos = self.top_pares_positivos(10)
        pares_neg = self.top_pares_negativos(10)
        hiper = self.pico_hipergeometrico(20)

        return {
            'hipergeometrica': {
                'nome': 'Probabilidade Hipergeométrica',
                'icon': '📊',
                'descricao': f'Pico em k={hiper["pico_k"]} quentes (faixa: {hiper["faixa_ideal"]})',
                'dados': hiper,
            },
            'entropia': {
                'nome': 'Entropia de Shannon',
                'icon': '🔀',
                'descricao': f'Média histórica: H={self.entropia_media_historica}',
                'dados': {'media': self.entropia_media_historica},
            },
            'pearson': {
                'nome': 'Resíduos de Pearson (χ²)',
                'icon': '📐',
                'descricao': chi2_info['interpretacao'],
                'dados': {**chi2_info, 'top_maturados': maturados[:5]},
            },
            'clusterizacao': {
                'nome': 'Clusterização / Distância Euclidiana',
                'icon': '🎯',
                'descricao': 'σ normalizado (1.5–2.5) sem aglomeração decenal',
                'dados': {},
            },
            'quadrantes': {
                'nome': 'Distribuição em Quadrantes',
                'icon': '🧭',
                'descricao': 'Presença em no mínimo 3 dos 4 quadrantes',
                'dados': {},
            },
            'benford': {
                'nome': 'Lei de Benford',
                'icon': '📈',
                'descricao': f'Conformidade: {benford_info["conformidade"]}%',
                'dados': benford_info,
            },
            'coocorrencia': {
                'nome': 'Correlação e Coocorrência',
                'icon': '🔗',
                'descricao': f'{len(pares_pos)} pares correlatos identificados',
                'dados': {
                    'top_positivos': pares_pos[:5],
                    'top_negativos': pares_neg[:5],
                },
            },
            'rolling_windows': {
                'nome': 'Janelas Deslizantes',
                'icon': '📉',
                'descricao': f'{len(rolling_info.get("dezenas_subindo", []))} dezenas em alta (janela {self.janela_curta})',
                'dados': {
                    'subindo': rolling_info.get('dezenas_subindo', []),
                    'caindo': rolling_info.get('dezenas_caindo', []),
                },
            },
            'decaimento': {
                'nome': 'Decaimento Temporal',
                'icon': '⏳',
                'descricao': f'{sum(1 for a in atrasados if "Crítico" in a["zona"])} dezenas em atraso crítico',
                'dados': {'top_atrasados': atrasados[:5]},
            },
            'restricao_dimensional': {
                'nome': 'Restrição Dimensional',
                'icon': '⚖️',
                'descricao': 'Soma entre 150-270, 0-2 primos, paridade aceita',
                'dados': {
                    'paridade_aceita': ['3P/3I', '4P/2I', '2P/4I'],
                    'primos_range': '0-2',
                    'primos_1_60': sorted(PRIMOS_1_60),
                },
            },
        }
