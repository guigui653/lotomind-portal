"""
LotoMind Portal — Testes do Motor de Física Teórica
=======================================================
Testes unitários para:
  - calcular_peso_tinta
  - calcular_temperatura_newton
  - GloboFisicoSimulator
"""

import sys
import os
import unittest
import numpy as np

# Adicionar root ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.analise_avancada.fisica_teorica import (
    calcular_peso_tinta,
    calcular_temperatura_newton,
    GloboFisicoSimulator,
    analisar_fisica_jogo,
    T_AMBIENTE,
    T_EBULICAO,
)


def _gerar_historico_lotofacil(n_jogos=100):
    np.random.seed(42)
    historico = []
    for _ in range(n_jogos):
        jogo = sorted(np.random.choice(range(1, 26), 15, replace=False).tolist())
        historico.append(jogo)
    return historico


class TestFisicaTeorica(unittest.TestCase):

    def setUp(self):
        self.historico = _gerar_historico_lotofacil(100)

    # ── 1. PESO DA TINTA ──
    def test_peso_tinta_digitos(self):
        """O número '8' (max tinta) deve ser mais pesado que '1' (min tinta)"""
        peso_8 = calcular_peso_tinta(8)
        peso_1 = calcular_peso_tinta(1)
        self.assertGreater(peso_8['massa_gramas'], peso_1['massa_gramas'])

    def test_penalidade_dois_digitos(self):
        """Números de dois dígitos devem ter penalidade maior (ex: 88 > 8)"""
        peso_88 = calcular_peso_tinta(88)
        peso_8 = calcular_peso_tinta(8)
        self.assertGreater(peso_88['penalidade_gravitacional'], peso_8['penalidade_gravitacional'])

    # ── 2. TERMODINÂMICA ──
    def test_numero_nunca_sorteado_frio(self):
        """Número que nunca saiu deve estar na temperatura ambiente"""
        # Criar histórico onde 25 nunca sai
        hist = []
        for _ in range(50):
            jogo = sorted(np.random.choice(range(1, 25), 15, replace=False).tolist())
            hist.append(jogo)
            
        temp_25 = calcular_temperatura_newton(25, hist)
        self.assertEqual(temp_25['temperatura'], T_AMBIENTE)
        self.assertIn('Frio', temp_25['fase_termica'])

    def test_numero_recente_quente(self):
        """Número recém sorteado deve estar próximo à temperatura de ebulição"""
        hist = [[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]]
        temp_1 = calcular_temperatura_newton(1, hist)
        self.assertAlmostEqual(temp_1['temperatura'], T_EBULICAO, places=1)
        self.assertEqual(temp_1['delta_t_desde_ultimo'], 0)

    # ── 3. SIMULADOR DE COLISÃO ──
    def test_simulador_retorna_jogo_valido(self):
        """O simulador deve retornar exatamente 'dezenas_sorteio' números"""
        sim = GloboFisicoSimulator(universo=25, dezenas_sorteio=15, iteracoes=10)
        res = sim.simular()
        self.assertEqual(len(res['sorteados']), 15)
        self.assertTrue(all(1 <= n <= 25 for n in res['sorteados']))

    def test_simulador_gerar_jogo_fisico(self):
        """A geração combinada deve fundir as simulações e retornar confianca_fisica"""
        sim = GloboFisicoSimulator(universo=25, dezenas_sorteio=15, iteracoes=10)
        res = sim.gerar_jogo_fisico(n_simulacoes=3)
        self.assertIn('confianca_fisica', res)
        self.assertEqual(len(res['jogo']), 15)

    # ── 4. ANÁLISE FÍSICA COMBINADA ──
    def test_analisar_fisica_jogo(self):
        """A função analisar_fisica_jogo deve retornar scores completos"""
        jogo = [1, 2, 3, 4, 5, 8, 10, 11, 15, 18, 20, 21, 23, 24, 25]
        res = analisar_fisica_jogo(jogo, self.historico, universo=25)
        
        self.assertIn('score_fisico', res)
        self.assertIn('termodinamica', res)
        self.assertIn('massa', res)
        self.assertIn('energia_cinetica', res)
        self.assertTrue(0 <= res['score_fisico'] <= 100)


if __name__ == '__main__':
    unittest.main()
