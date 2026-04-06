"""
test_stats.py — TDD para o módulo LotteryPredictor (Markov + Poisson)
=====================================================================
Escrito ANTES da implementação, seguindo o Framework Superpowers.
Execução: python test_stats.py   (da raiz do LotoMindPortal)
"""

import os
import sys
import json
import time
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from modules.lotofacil.engine import LotofacilEngine
from modules.lotofacil.advanced_stats import LotteryPredictor


class TestLotteryPredictor(unittest.TestCase):
    """Suíte de testes para o LotteryPredictor."""

    @classmethod
    def setUpClass(cls):
        """Carrega dados UMA vez para todos os testes (economia de rede)."""
        cls.app = create_app()
        with cls.app.app_context():
            engine = LotofacilEngine()
            cls.df = engine.buscar_dados_oficiais(200)

        cls.predictor = LotteryPredictor()
        cls.predictor.carregar_historico(cls.df)

        # Bilhete de teste válido (15 dezenas, 1 a 25)
        cls.bilhete = [1, 2, 3, 5, 7, 9, 11, 13, 15, 17, 19, 20, 22, 24, 25]

    # ════════════════════════════════════════════════════════
    #  TESTE 1: Formato da Matriz de Markov
    # ════════════════════════════════════════════════════════

    def test_markov_matrix_shape(self):
        """A matriz de transição deve ser 25x25 e cada linha deve somar ≈ 1.0."""
        M = self.predictor.markov_matrix
        self.assertEqual(M.shape, (25, 25), "Markov matrix shape deve ser (25, 25)")

        # Cada linha deve somar aproximadamente 1.0 (tolerância para linhas com zero)
        row_sums = M.sum(axis=1)
        for i, s in enumerate(row_sums):
            if s > 0:  # Ignora linhas que nunca apareceram (improvável, mas seguro)
                self.assertAlmostEqual(s, 1.0, places=5,
                    msg=f"Linha {i} da Markov soma {s}, esperado ≈ 1.0")

    # ════════════════════════════════════════════════════════
    #  TESTE 2: Tipos Nativos (JSON-safe)
    # ════════════════════════════════════════════════════════

    def test_markov_matrix_dtype(self):
        """Todos os valores da matriz devem ser float Python (não np.float64)."""
        M = self.predictor.markov_matrix
        # A matriz interna pode ser numpy, mas o output de confidence_score
        # deve converter para primitivos. Testar que a conversão funciona:
        result = self.predictor.confidence_score(self.bilhete)
        # Todos os valores numéricos no dict devem ser int/float nativos
        for key, val in result.items():
            if isinstance(val, (int, float)):
                self.assertNotIsInstance(val, (np.integer, np.floating),
                    msg=f"Campo '{key}' é tipo numpy ({type(val)}), não primitivo Python")

    # ════════════════════════════════════════════════════════
    #  TESTE 3: Lambda (Poisson) dentro do Range
    # ════════════════════════════════════════════════════════

    def test_poisson_lambda_range(self):
        """λ de cada dezena deve estar entre 0 e o tamanho da janela (100)."""
        lambdas = self.predictor.poisson_lambdas
        self.assertEqual(len(lambdas), 25, "Deve haver 25 lambdas (uma por dezena)")
        for i, lam in enumerate(lambdas):
            self.assertGreaterEqual(lam, 0,
                msg=f"λ da dezena {i+1} é negativo: {lam}")
            self.assertLessEqual(lam, 100,
                msg=f"λ da dezena {i+1} excede 100: {lam}")

    # ════════════════════════════════════════════════════════
    #  TESTE 4: Probabilidades Poisson em [0, 1]
    # ════════════════════════════════════════════════════════

    def test_poisson_probability_range(self):
        """P(retorno) de cada dezena deve estar entre 0.0 e 1.0."""
        probs = self.predictor.poisson_probs
        self.assertEqual(len(probs), 25, "Deve haver 25 probabilidades Poisson")
        for i, p in enumerate(probs):
            self.assertGreaterEqual(p, 0.0,
                msg=f"P(retorno) da dezena {i+1} é negativa: {p}")
            self.assertLessEqual(p, 1.0,
                msg=f"P(retorno) da dezena {i+1} > 1.0: {p}")

    # ════════════════════════════════════════════════════════
    #  TESTE 5: Score Final entre 0 e 100
    # ════════════════════════════════════════════════════════

    def test_confidence_score_range(self):
        """confidence_score deve retornar valor entre 0 e 100."""
        result = self.predictor.confidence_score(self.bilhete)
        score = result['confidence_score']
        self.assertGreaterEqual(score, 0, f"Score {score} < 0")
        self.assertLessEqual(score, 100, f"Score {score} > 100")

        # Sub-scores também
        self.assertGreaterEqual(result['score_markov'], 0)
        self.assertLessEqual(result['score_markov'], 100)
        self.assertGreaterEqual(result['score_poisson'], 0)
        self.assertLessEqual(result['score_poisson'], 100)

    # ════════════════════════════════════════════════════════
    #  TESTE 6: Serialização JSON sem Erros
    # ════════════════════════════════════════════════════════

    def test_confidence_score_json_safe(self):
        """json.dumps() no resultado não deve lançar exceção."""
        result = self.predictor.confidence_score(self.bilhete)
        try:
            json_str = json.dumps(result, ensure_ascii=False)
            self.assertIsInstance(json_str, str)
            # Valida ida e volta
            parsed = json.loads(json_str)
            self.assertIn('confidence_score', parsed)
        except (TypeError, ValueError) as e:
            self.fail(f"json.dumps falhou: {e}")

    # ════════════════════════════════════════════════════════
    #  TESTE 7: Funciona com Dados Mockados (Fallback)
    # ════════════════════════════════════════════════════════

    def test_confidence_score_with_mock_data(self):
        """O predictor deve funcionar mesmo com dados mockados/aleatórios."""
        # Simular dados mock (igual ao fallback do LotofacilEngine)
        import pandas as pd
        mock_dados = []
        for i in range(100):
            dezenas = np.sort(np.random.choice(range(1, 26), 15, replace=False)).tolist()
            mock_dados.append({
                'Concurso': 9999 - i,
                'Data': 'Mock',
                'Dezenas': dezenas,
                'Pares': len([x for x in dezenas if x % 2 == 0]),
                'Impares': len([x for x in dezenas if x % 2 != 0]),
                'Soma': sum(dezenas),
            })
        df_mock = pd.DataFrame(mock_dados)

        predictor_mock = LotteryPredictor()
        predictor_mock.carregar_historico(df_mock)

        result = predictor_mock.confidence_score(self.bilhete)
        self.assertIn('confidence_score', result)
        self.assertGreaterEqual(result['confidence_score'], 0)
        self.assertLessEqual(result['confidence_score'], 100)

    # ════════════════════════════════════════════════════════
    #  TESTE 8: Performance < 1 segundo
    # ════════════════════════════════════════════════════════

    def test_performance_under_1_second(self):
        """Construção dos modelos + scoring deve levar < 1 segundo para 500 concursos."""
        import pandas as pd

        # Gerar 500 concursos mock para stress test
        mock_dados = []
        for i in range(500):
            dezenas = np.sort(np.random.choice(range(1, 26), 15, replace=False)).tolist()
            mock_dados.append({
                'Concurso': 9999 - i,
                'Data': 'Perf-Test',
                'Dezenas': dezenas,
                'Pares': len([x for x in dezenas if x % 2 == 0]),
                'Impares': len([x for x in dezenas if x % 2 != 0]),
                'Soma': sum(dezenas),
            })
        df_perf = pd.DataFrame(mock_dados)

        t0 = time.time()
        p = LotteryPredictor()
        p.carregar_historico(df_perf)
        _ = p.confidence_score(self.bilhete)
        elapsed = time.time() - t0

        self.assertLess(elapsed, 1.0,
            f"Performance: {elapsed:.4f}s — deveria ser < 1.0s")
        print(f"\n⚡ Performance: {elapsed:.4f}s para 500 concursos (OK)")


if __name__ == '__main__':
    print("=" * 60)
    print("  TDD — LotteryPredictor (Markov + Poisson)")
    print("=" * 60)
    unittest.main(verbosity=2)
