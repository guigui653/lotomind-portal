"""
LotoMind Portal — Filtros de Complexidade Estrutural
=====================================================
Filtros avançados que analisam a estrutura geométrica e espacial
das combinações geradas:
  1. FiltroEspacamento — Análise de gaps entre números
  2. FiltroZonaEspacial — Análise de dispersão no grid do volante

Ambos são parametrizáveis para qualquer loteria.
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional


# ════════════════════════════════════════════════════════════
#  LAYOUTS PREDEFINIDOS DOS VOLANTES
# ════════════════════════════════════════════════════════════

# Lotofácil: Grid 5×5 (números 1 a 25)
LAYOUT_LOTOFACIL = {
    'nome': 'Lotofácil 5×5',
    'linhas': 5,
    'colunas': 5,
    'universo': 25,
}

# Mega-Sena: Grid 6×10 (números 1 a 60)
LAYOUT_MEGASENA = {
    'nome': 'Mega-Sena 6×10',
    'linhas': 6,
    'colunas': 10,
    'universo': 60,
}


def _numero_para_posicao(numero: int, colunas: int) -> Tuple[int, int]:
    """Converte número (1-indexed) para posição (linha, coluna) no grid."""
    idx = numero - 1
    linha = idx // colunas
    coluna = idx % colunas
    return (linha, coluna)


def _posicao_para_quadrante(
    linha: int, coluna: int,
    total_linhas: int, total_colunas: int,
) -> str:
    """Determina em qual quadrante espacial a posição está."""
    meio_l = total_linhas / 2
    meio_c = total_colunas / 2

    if linha < meio_l and coluna < meio_c:
        return 'TL'  # Top-Left
    elif linha < meio_l and coluna >= meio_c:
        return 'TR'  # Top-Right
    elif linha >= meio_l and coluna < meio_c:
        return 'BL'  # Bottom-Left
    else:
        return 'BR'  # Bottom-Right


# ════════════════════════════════════════════════════════════
#  1. FILTRO DE ESPAÇAMENTO (GAPS)
# ════════════════════════════════════════════════════════════

class FiltroEspacamento:
    """
    Analisa a distância entre números consecutivos ordenados
    e rejeita combinações com espaçamento atípico.

    O desvio padrão dos gaps é comparado com o desvio padrão
    histórico médio. Combinações com gaps muito irregulares
    (muito agrupadas ou muito dispersas) são rejeitadas.
    """

    def __init__(self, tolerancia_sigma: float = 1.5):
        """
        Args:
            tolerancia_sigma: Quantos sigmas de tolerância em relação
                             ao desvio padrão histórico.
        """
        self.tolerancia_sigma = tolerancia_sigma
        self.dp_historico = None
        self.gap_medio_historico = None

    def calcular_dp_historico(
        self,
        historico_sorteios: List[List[int]],
    ) -> float:
        """
        Calcula o desvio padrão médio dos gaps no histórico.
        Armazena internamente para uso posterior.
        """
        if not historico_sorteios:
            self.dp_historico = 1.0
            self.gap_medio_historico = 1.0
            return 1.0

        todos_dps = []
        todos_gaps = []

        for sorteio in historico_sorteios:
            s = sorted(sorteio)
            gaps = [s[i + 1] - s[i] for i in range(len(s) - 1)]
            if gaps:
                todos_dps.append(float(np.std(gaps)))
                todos_gaps.extend(gaps)

        self.dp_historico = float(np.mean(todos_dps)) if todos_dps else 1.0
        self.gap_medio_historico = float(np.mean(todos_gaps)) if todos_gaps else 1.0
        return self.dp_historico

    def verificar_distribuicao_espacamento(
        self,
        combinacao: List[int],
        desvio_padrao_historico: Optional[float] = None,
    ) -> dict:
        """
        Analisa os gaps de uma combinação e decide se a distribuição
        de espaçamento é estatisticamente aceitável.

        Args:
            combinacao: Lista de números do jogo.
            desvio_padrao_historico: DP médio dos gaps no histórico.
                                   Se None, usa o valor pré-calculado.

        Returns:
            {gaps, dp_gaps, dp_historico, gap_medio, gap_max, gap_min,
             desvio_relativo, aprovado, classificacao}
        """
        dp_ref = desvio_padrao_historico or self.dp_historico or 1.0
        s = sorted(combinacao)
        gaps = [s[i + 1] - s[i] for i in range(len(s) - 1)]

        if not gaps:
            return {
                'gaps': [],
                'dp_gaps': 0.0,
                'dp_historico': dp_ref,
                'gap_medio': 0.0,
                'gap_max': 0,
                'gap_min': 0,
                'desvio_relativo': 0.0,
                'aprovado': False,
                'classificacao': '❌ Inválido',
            }

        dp_gaps = float(np.std(gaps))
        gap_medio = float(np.mean(gaps))
        gap_max = int(max(gaps))
        gap_min = int(min(gaps))

        # Desvio relativo ao histórico
        desvio_relativo = abs(dp_gaps - dp_ref) / max(dp_ref, 0.01)

        # Aprovado se dentro da tolerância
        aprovado = desvio_relativo <= self.tolerancia_sigma

        # Classificação
        if desvio_relativo <= 0.5:
            classificacao = '🌟 Excelente — Espaçamento ideal'
        elif aprovado:
            classificacao = '✅ Bom — Dentro do padrão histórico'
        elif desvio_relativo <= 2.0:
            classificacao = '🟡 Moderado — Leve irregularidade'
        else:
            classificacao = '⚠️ Irregular — Espaçamento atípico'

        return {
            'gaps': gaps,
            'dp_gaps': round(dp_gaps, 3),
            'dp_historico': round(dp_ref, 3),
            'gap_medio': round(gap_medio, 2),
            'gap_max': gap_max,
            'gap_min': gap_min,
            'desvio_relativo': round(desvio_relativo, 3),
            'aprovado': aprovado,
            'classificacao': classificacao,
        }


# ════════════════════════════════════════════════════════════
#  2. FILTRO DE ZONA ESPACIAL (GRID DO VOLANTE)
# ════════════════════════════════════════════════════════════

class FiltroZonaEspacial:
    """
    Analisa como os números estão espalhados fisicamente no
    volante (grid) para evitar jogos onde todos os números
    caem em um único canto ou região.

    O grid é dividido em 4 quadrantes espaciais:
      TL (Top-Left)    | TR (Top-Right)
      BL (Bottom-Left)  | BR (Bottom-Right)
    """

    QUADRANTE_NOMES = {
        'TL': 'Superior Esquerdo',
        'TR': 'Superior Direito',
        'BL': 'Inferior Esquerdo',
        'BR': 'Inferior Direito',
    }

    def __init__(self, layout: Optional[dict] = None):
        """
        Args:
            layout: Dicionário com 'linhas', 'colunas', 'universo'.
                   Padrão: LAYOUT_LOTOFACIL.
        """
        self.layout = layout or LAYOUT_LOTOFACIL

    def verificar_distribuicao_quadrantes(
        self,
        combinacao: List[int],
        layout_volante: Optional[dict] = None,
    ) -> dict:
        """
        Analisa a dispersão espacial da combinação no grid do volante.

        Critérios de rejeição:
          - Lotofácil (15 dezenas): rejeita se algum quadrante tem 0 dezenas.
          - Mega-Sena (6 dezenas): rejeita se > 70% das dezenas estão
            em um único quadrante.

        Args:
            combinacao: Lista de números do jogo.
            layout_volante: Overrides do layout padrão.

        Returns:
            {distribuicao_quadrantes, quadrantes_vazios, quadrantes_presentes,
             concentracao_maxima, aprovado, classificacao, detalhes_por_numero}
        """
        layout = layout_volante or self.layout
        linhas = layout['linhas']
        colunas = layout['colunas']
        universo = layout['universo']
        dezenas_sorteio = len(combinacao)

        # Mapear cada número a seu quadrante
        distribuicao = {'TL': [], 'TR': [], 'BL': [], 'BR': []}
        detalhes_por_numero = {}

        for n in sorted(combinacao):
            if n < 1 or n > universo:
                continue

            linha, coluna = _numero_para_posicao(n, colunas)
            quadrante = _posicao_para_quadrante(linha, coluna, linhas, colunas)
            distribuicao[quadrante].append(n)
            detalhes_por_numero[n] = {
                'posicao': (linha, coluna),
                'quadrante': quadrante,
                'quadrante_nome': self.QUADRANTE_NOMES[quadrante],
            }

        # Contagem por quadrante
        contagem = {q: len(nums) for q, nums in distribuicao.items()}
        quadrantes_vazios = [q for q, c in contagem.items() if c == 0]
        quadrantes_presentes = 4 - len(quadrantes_vazios)
        concentracao_maxima = max(contagem.values()) / max(dezenas_sorteio, 1)

        # Critério de aprovação
        if dezenas_sorteio >= 10:
            # Jogos densos (Lotofácil): nenhum quadrante pode estar vazio
            aprovado = len(quadrantes_vazios) == 0
        else:
            # Jogos esparsos (Mega-Sena): nenhum quadrante pode ter > 70%
            aprovado = concentracao_maxima <= 0.70 and quadrantes_presentes >= 2

        # Classificação
        if quadrantes_presentes == 4 and concentracao_maxima <= 0.35:
            classificacao = '🌟 Excelente — Distribuição uniforme'
        elif aprovado:
            classificacao = '✅ Boa — Bem espalhado'
        elif quadrantes_presentes >= 3:
            classificacao = '🟡 Moderada — Leve concentração'
        else:
            classificacao = '⚠️ Fraca — Muito concentrado espacialmente'

        return {
            'distribuicao_quadrantes': {
                q: {'numeros': sorted(nums), 'quantidade': len(nums)}
                for q, nums in distribuicao.items()
            },
            'contagem': contagem,
            'quadrantes_vazios': quadrantes_vazios,
            'quadrantes_presentes': quadrantes_presentes,
            'concentracao_maxima': round(concentracao_maxima, 3),
            'aprovado': aprovado,
            'classificacao': classificacao,
            'detalhes_por_numero': detalhes_por_numero,
        }
