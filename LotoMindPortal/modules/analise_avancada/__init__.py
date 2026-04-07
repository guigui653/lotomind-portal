"""
LotoMind Portal — Módulo de Análise Avançada
=============================================
Análises matemáticas, estatísticas e probabilísticas avançadas.
Genérico para Lotofácil (25/15) e Mega-Sena (60/6).
"""

from modules.analise_avancada.analisador_historico import (
    calcular_indice_atraso,
    gerar_matriz_afinidade,
    calcular_entropia_jogo,
)
from modules.analise_avancada.filtros_estruturais import (
    FiltroEspacamento,
    FiltroZonaEspacial,
)
from modules.analise_avancada.avaliador import AvaliadorDeJogos
