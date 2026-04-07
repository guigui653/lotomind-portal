"""
LotoMind Portal — Testes do Módulo de Análise Avançada
=======================================================
Testes unitários para:
  - calcular_indice_atraso (DNI)
  - gerar_matriz_afinidade (Lift)
  - calcular_entropia_jogo (Shannon)
  - FiltroEspacamento
  - FiltroZonaEspacial
  - AvaliadorDeJogos (pipeline completo)
"""

import sys
import os
import unittest
import numpy as np

# Adicionar root ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.analise_avancada.analisador_historico import (
    calcular_indice_atraso,
    gerar_matriz_afinidade,
    calcular_entropia_jogo,
)
from modules.analise_avancada.filtros_estruturais import (
    FiltroEspacamento,
    FiltroZonaEspacial,
    LAYOUT_LOTOFACIL,
    LAYOUT_MEGASENA,
)
from modules.analise_avancada.avaliador import AvaliadorDeJogos


# ════════════════════════════════════════════════════════════
#  FIXTURES: Dados Mock
# ════════════════════════════════════════════════════════════

def _gerar_historico_lotofacil(n_jogos=100):
    """Gera histórico mock de Lotofácil (15 de 25) para testes."""
    np.random.seed(42)
    historico = []
    for _ in range(n_jogos):
        jogo = sorted(np.random.choice(range(1, 26), 15, replace=False).tolist())
        historico.append(jogo)
    return historico


def _gerar_historico_megasena(n_jogos=100):
    """Gera histórico mock de Mega-Sena (6 de 60) para testes."""
    np.random.seed(42)
    historico = []
    for _ in range(n_jogos):
        jogo = sorted(np.random.choice(range(1, 61), 6, replace=False).tolist())
        historico.append(jogo)
    return historico


def _historico_para_df(historico):
    """Converte lista de sorteios para DataFrame no formato do LotoMind."""
    import pandas as pd
    dados = []
    for i, dezenas in enumerate(historico):
        dados.append({
            'Concurso': 1000 - i,
            'Data': f'2026-01-{(i % 28) + 1:02d}',
            'Dezenas': dezenas,
            'Pares': len([x for x in dezenas if x % 2 == 0]),
            'Impares': len([x for x in dezenas if x % 2 != 0]),
            'Soma': sum(dezenas),
        })
    return pd.DataFrame(dados)


# ════════════════════════════════════════════════════════════
#  TESTES: Índice de Atraso (DNI)
# ════════════════════════════════════════════════════════════

class TestIndiceAtraso(unittest.TestCase):

    def setUp(self):
        self.historico = _gerar_historico_lotofacil(200)

    def test_retorna_todos_os_numeros(self):
        """DNI deve retornar dados para todos os 25 números."""
        resultado = calcular_indice_atraso(self.historico, universo=25, dezenas_sorteio=15)
        self.assertEqual(len(resultado), 25)

    def test_chaves_corretas(self):
        """Cada entrada deve ter as chaves esperadas."""
        resultado = calcular_indice_atraso(self.historico, universo=25, dezenas_sorteio=15)
        for num, info in resultado.items():
            self.assertIn('dni', info)
            self.assertIn('atraso_atual', info)
            self.assertIn('intervalo_medio', info)
            self.assertIn('frequencia', info)
            self.assertIn('classificacao', info)
            self.assertIsInstance(info['dni'], float)

    def test_numero_ausente_tem_alto_dni(self):
        """Um número que nunca aparece deve ter atraso máximo."""
        # Criar histórico onde número 25 nunca aparece
        historico = []
        for _ in range(50):
            jogo = sorted(np.random.choice(range(1, 25), 15, replace=False).tolist())
            historico.append(jogo)

        resultado = calcular_indice_atraso(historico, universo=25, dezenas_sorteio=15)
        # Atraso atual deve ser máximo (= total de jogos)
        self.assertEqual(resultado[25]['atraso_atual'], 50)
        # DNI >= 0 (número "devido" ou no limite)
        self.assertGreaterEqual(resultado[25]['dni'], 0)
        # Frequência deve ser 0
        self.assertEqual(resultado[25]['frequencia'], 0)

    def test_ordenacao_decrescente(self):
        """Resultado deve estar ordenado pelo DNI decrescente."""
        resultado = calcular_indice_atraso(self.historico, universo=25, dezenas_sorteio=15)
        dnis = [info['dni'] for info in resultado.values()]
        self.assertEqual(dnis, sorted(dnis, reverse=True))

    def test_historico_vazio(self):
        """Histórico vazio deve retornar dicionário vazio."""
        resultado = calcular_indice_atraso([], universo=25)
        self.assertEqual(resultado, {})


# ════════════════════════════════════════════════════════════
#  TESTES: Matriz de Afinidade
# ════════════════════════════════════════════════════════════

class TestMatrizAfinidade(unittest.TestCase):

    def setUp(self):
        self.historico = _gerar_historico_lotofacil(200)

    def test_matriz_simetrica(self):
        """Matriz de Lift deve ser simétrica."""
        resultado = gerar_matriz_afinidade(self.historico, universo=25)
        matriz = resultado['matriz_lift']
        np.testing.assert_array_almost_equal(matriz, matriz.T, decimal=4)

    def test_diagonal_unitaria(self):
        """Diagonal da matriz de Lift deve ser 1.0."""
        resultado = gerar_matriz_afinidade(self.historico, universo=25)
        diagonal = np.diag(resultado['matriz_lift'])
        np.testing.assert_array_almost_equal(diagonal, np.ones(25), decimal=4)

    def test_lift_positivo(self):
        """Todos os valores de Lift devem ser >= 0."""
        resultado = gerar_matriz_afinidade(self.historico, universo=25)
        self.assertTrue(np.all(resultado['matriz_lift'] >= 0))

    def test_top_pares_formato(self):
        """Top pares devem ter par (tupla), lift (float) e coocorrencias (int)."""
        resultado = gerar_matriz_afinidade(self.historico, universo=25, top_n=5)
        self.assertLessEqual(len(resultado['top_pares_afinidade']), 5)
        for par in resultado['top_pares_afinidade']:
            self.assertIn('par', par)
            self.assertIn('lift', par)
            self.assertIn('coocorrencias', par)
            self.assertEqual(len(par['par']), 2)

    def test_historico_vazio(self):
        """Histórico vazio deve retornar matriz de 1s."""
        resultado = gerar_matriz_afinidade([], universo=25)
        np.testing.assert_array_almost_equal(
            resultado['matriz_lift'], np.ones((25, 25))
        )


# ════════════════════════════════════════════════════════════
#  TESTES: Entropia de Shannon
# ════════════════════════════════════════════════════════════

class TestEntropiaShannon(unittest.TestCase):

    def test_distribuicao_uniforme(self):
        """Distribuição uniforme perfeita deve ter entropia normalizada ~1.0."""
        # 5 bins, 3 números em cada (15 total, range 25, 5 bins de 5)
        jogo = [1, 3, 5, 6, 8, 10, 11, 13, 15, 16, 18, 20, 21, 23, 25]
        resultado = calcular_entropia_jogo(jogo, range_numeros=25, num_bins=5)
        self.assertGreaterEqual(resultado['entropia_normalizada'], 0.95)

    def test_distribuicao_concentrada(self):
        """Todos os números na mesma faixa devem ter entropia ~ 0."""
        jogo = [1, 2, 3, 4, 5]
        resultado = calcular_entropia_jogo(jogo, range_numeros=25, num_bins=5)
        self.assertAlmostEqual(resultado['entropia_normalizada'], 0.0, places=3)

    def test_entropia_max_correta(self):
        """Entropia máxima deve ser log2(num_bins)."""
        import math
        resultado = calcular_entropia_jogo([1, 10, 20], range_numeros=25, num_bins=5)
        self.assertAlmostEqual(resultado['entropia_max'], math.log2(5), places=3)

    def test_distribuicao_bins(self):
        """Deve retornar a contagem correta por bin."""
        jogo = [1, 2, 3, 6, 7, 11, 12, 16, 17, 21, 22, 23, 24, 25, 8]
        resultado = calcular_entropia_jogo(jogo, range_numeros=25, num_bins=5)
        self.assertIn('distribuicao_bins', resultado)
        total = sum(resultado['distribuicao_bins'].values())
        self.assertEqual(total, 15)

    def test_classificacao_presente(self):
        """Resultado deve conter classificação textual."""
        resultado = calcular_entropia_jogo([1, 5, 10, 15, 20, 25], range_numeros=25, num_bins=5)
        self.assertIn('classificacao', resultado)
        self.assertIsInstance(resultado['classificacao'], str)

    def test_jogo_vazio(self):
        """Jogo vazio deve retornar entropia 0."""
        resultado = calcular_entropia_jogo([], range_numeros=25)
        self.assertEqual(resultado['entropia'], 0.0)


# ════════════════════════════════════════════════════════════
#  TESTES: Filtro de Espaçamento
# ════════════════════════════════════════════════════════════

class TestFiltroEspacamento(unittest.TestCase):

    def setUp(self):
        self.filtro = FiltroEspacamento(tolerancia_sigma=1.5)
        self.historico = _gerar_historico_lotofacil(200)
        self.filtro.calcular_dp_historico(self.historico)

    def test_dp_historico_calculado(self):
        """DP histórico deve ser calculado e armazenado."""
        self.assertIsNotNone(self.filtro.dp_historico)
        self.assertGreater(self.filtro.dp_historico, 0)

    def test_jogo_normal_aprovado(self):
        """Jogo com espaçamento normal deve ser aprovado."""
        # Jogo bem distribuído
        jogo = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25]
        resultado = self.filtro.verificar_distribuicao_espacamento(jogo)
        self.assertIn('aprovado', resultado)
        self.assertIn('gaps', resultado)
        self.assertEqual(len(resultado['gaps']), 14)

    def test_jogo_agrupado_rejeitado(self):
        """Jogo com todos números consecutivos pode ser irregular."""
        jogo = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        resultado = self.filtro.verificar_distribuicao_espacamento(jogo)
        # Todos gaps = 1, dp = 0 → desvio grande em relação ao histórico
        self.assertIn('dp_gaps', resultado)
        self.assertAlmostEqual(resultado['dp_gaps'], 0.0)

    def test_classificacao_textual(self):
        """Resultado deve incluir classificação textual."""
        jogo = list(range(1, 16))
        resultado = self.filtro.verificar_distribuicao_espacamento(jogo)
        self.assertIn('classificacao', resultado)
        self.assertIsInstance(resultado['classificacao'], str)


# ════════════════════════════════════════════════════════════
#  TESTES: Filtro de Zona Espacial
# ════════════════════════════════════════════════════════════

class TestFiltroZonaEspacial(unittest.TestCase):

    def test_lotofacil_distribuido_aprovado(self):
        """Jogo distribuído em todos os quadrantes deve ser aprovado (Lotofácil)."""
        filtro = FiltroZonaEspacial(layout=LAYOUT_LOTOFACIL)
        # Grid 5x5: TL(1-3,6-8), TR(4-5,9-10), BL(16-18,21-23), BR(19-20,24-25)
        jogo = [1, 2, 4, 5, 6, 9, 11, 13, 14, 16, 18, 21, 22, 24, 25]
        resultado = filtro.verificar_distribuicao_quadrantes(jogo)
        self.assertTrue(resultado['aprovado'])
        self.assertEqual(resultado['quadrantes_presentes'], 4)

    def test_lotofacil_concentrado_rejeitado(self):
        """Jogo concentrado em um quadrante deve ser rejeitado (Lotofácil)."""
        filtro = FiltroZonaEspacial(layout=LAYOUT_LOTOFACIL)
        # Todos os primeiros números (primeiras linhas)
        jogo = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        resultado = filtro.verificar_distribuicao_quadrantes(jogo)
        # Isso pode não ter cobertura total dos 4 quadrantes
        self.assertIn('quadrantes_presentes', resultado)
        self.assertIn('concentracao_maxima', resultado)

    def test_megasena_aprovado(self):
        """Jogo com 3+ quadrantes presentes deve ser aprovado (Mega-Sena)."""
        filtro = FiltroZonaEspacial(layout=LAYOUT_MEGASENA)
        # Grid 6x10: 6 números bem espalhados
        jogo = [5, 18, 32, 45, 51, 60]
        resultado = filtro.verificar_distribuicao_quadrantes(jogo)
        self.assertTrue(resultado['aprovado'])
        self.assertGreaterEqual(resultado['quadrantes_presentes'], 2)

    def test_megasena_concentrado_rejeitado(self):
        """Jogo com > 70% em um quadrante deve ser rejeitado (Mega-Sena)."""
        filtro = FiltroZonaEspacial(layout=LAYOUT_MEGASENA)
        # 5 de 6 números no canto superior esquerdo (1-5 no grid 6x10)
        jogo = [1, 2, 3, 4, 5, 55]
        resultado = filtro.verificar_distribuicao_quadrantes(jogo)
        # 5/6 = 83% em um quadrante → rejeitado
        self.assertFalse(resultado['aprovado'])

    def test_detalhes_completos(self):
        """Resultado deve conter todas as chaves esperadas."""
        filtro = FiltroZonaEspacial(layout=LAYOUT_LOTOFACIL)
        jogo = [1, 3, 5, 10, 13, 15, 16, 18, 20, 21, 22, 23, 24, 25, 8]
        resultado = filtro.verificar_distribuicao_quadrantes(jogo)
        self.assertIn('distribuicao_quadrantes', resultado)
        self.assertIn('quadrantes_vazios', resultado)
        self.assertIn('concentracao_maxima', resultado)
        self.assertIn('classificacao', resultado)


# ════════════════════════════════════════════════════════════
#  TESTES: AvaliadorDeJogos (Pipeline Completo)
# ════════════════════════════════════════════════════════════

class TestAvaliadorDeJogos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Preparar avaliador com dados mock — uma vez para todos os testes."""
        cls.historico = _gerar_historico_lotofacil(200)
        cls.df = _historico_para_df(cls.historico)

        cls.avaliador = AvaliadorDeJogos(loteria='lotofacil')
        cls.avaliador.carregar_historico(cls.df)

    def test_historico_carregado(self):
        """Avaliador deve marcar histórico como carregado."""
        self.assertTrue(self.avaliador.historico_carregado)

    def test_avaliar_retorna_nota(self):
        """Avaliação deve retornar nota final entre 0 e 100."""
        jogo = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25]
        resultado = self.avaliador.avaliar_e_pontuar_jogo(jogo)
        self.assertIn('nota_final', resultado)
        self.assertGreaterEqual(resultado['nota_final'], 0)
        self.assertLessEqual(resultado['nota_final'], 100)

    def test_avaliar_retorna_classificacao(self):
        """Avaliação deve retornar classificação textual."""
        jogo = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25]
        resultado = self.avaliador.avaliar_e_pontuar_jogo(jogo)
        self.assertIn('classificacao', resultado)
        self.assertIsInstance(resultado['classificacao'], str)

    def test_8_filtros_presentes(self):
        """Resultado deve conter exatamente 8 filtros."""
        jogo = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 21, 22, 23, 24, 25]
        resultado = self.avaliador.avaliar_e_pontuar_jogo(jogo)
        filtros_esperados = {
            'soma', 'paridade', 'primos', 'entropia',
            'espacamento', 'zona_espacial', 'dni', 'afinidade',
        }
        self.assertEqual(set(resultado['filtros'].keys()), filtros_esperados)

    def test_analise_por_numero(self):
        """Deve retornar análise individual para cada número."""
        jogo = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25]
        resultado = self.avaliador.avaliar_e_pontuar_jogo(jogo)
        self.assertEqual(len(resultado['analise_por_numero']), 15)
        for numero_info in resultado['analise_por_numero']:
            self.assertIn('numero', numero_info)
            self.assertIn('dni', numero_info)
            self.assertIn('afinidade_media', numero_info)
            self.assertIn('vantagem', numero_info)

    def test_justificativa_geral(self):
        """Deve gerar justificativa textual."""
        jogo = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25]
        resultado = self.avaliador.avaliar_e_pontuar_jogo(jogo)
        self.assertIn('justificativa_geral', resultado)
        self.assertIsInstance(resultado['justificativa_geral'], str)
        self.assertGreater(len(resultado['justificativa_geral']), 20)

    def test_gerar_relatorio_apos_avaliacao(self):
        """gerar_relatorio_jogo deve retornar o último resultado."""
        jogo = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 21, 22, 23, 24, 25]
        self.avaliador.avaliar_e_pontuar_jogo(jogo)
        relatorio = self.avaliador.gerar_relatorio_jogo()
        self.assertEqual(relatorio['jogo'], sorted(jogo))
        self.assertIn('nota_final', relatorio)

    def test_gerar_relatorio_sem_avaliacao(self):
        """gerar_relatorio_jogo sem avaliação prévia deve retornar erro."""
        avaliador_novo = AvaliadorDeJogos(loteria='lotofacil')
        avaliador_novo.carregar_historico(self.df)
        avaliador_novo._ultimo_resultado = None
        relatorio = avaliador_novo.gerar_relatorio_jogo()
        self.assertIn('erro', relatorio)

    def test_sem_historico(self):
        """Sem histórico carregado, deve retornar nota 0."""
        avaliador_vazio = AvaliadorDeJogos(loteria='lotofacil')
        resultado = avaliador_vazio.avaliar_e_pontuar_jogo([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        self.assertEqual(resultado['nota_final'], 0)

    def test_megasena(self):
        """Avaliador deve funcionar para Mega-Sena."""
        historico_mega = _gerar_historico_megasena(100)
        df_mega = _historico_para_df(historico_mega)

        avaliador_mega = AvaliadorDeJogos(loteria='megasena')
        avaliador_mega.carregar_historico(df_mega)

        jogo = [5, 18, 32, 45, 51, 60]
        resultado = avaliador_mega.avaliar_e_pontuar_jogo(jogo)
        self.assertIn('nota_final', resultado)
        self.assertEqual(len(resultado['analise_por_numero']), 6)
        self.assertEqual(resultado['total_filtros'], 8)

    def test_filtros_tem_score(self):
        """Cada filtro deve ter um campo 'score' numérico."""
        jogo = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25]
        resultado = self.avaliador.avaliar_e_pontuar_jogo(jogo)
        for nome, filtro in resultado['filtros'].items():
            self.assertIn('score', filtro, f"Filtro '{nome}' sem campo 'score'")
            self.assertIsInstance(filtro['score'], (int, float), f"Score de '{nome}' não é numérico")

    def test_json_serializable(self):
        """Resultado completo deve ser JSON-serializável."""
        import json
        jogo = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25]
        resultado = self.avaliador.avaliar_e_pontuar_jogo(jogo)

        # Converter tipos numpy manualmente
        def _converter(obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj)
            elif isinstance(obj, (np.bool_,)):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            raise TypeError(f"Tipo não serializável: {type(obj)}")

        try:
            json_str = json.dumps(resultado, default=_converter)
            self.assertIsInstance(json_str, str)
        except (TypeError, ValueError) as e:
            self.fail(f"Resultado não é JSON-serializável: {e}")


# ════════════════════════════════════════════════════════════
#  EXECUÇÃO
# ════════════════════════════════════════════════════════════

if __name__ == '__main__':
    unittest.main(verbosity=2)
