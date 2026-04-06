"""
MegaMind — Módulo de Filtragem Estatística
============================================
Análise de normalidade estatística para jogos da Mega-Sena.
Monte Carlo, mapa de calor, quadrantes e pontuação composta.
"""

import numpy as np
import pandas as pd
from collections import Counter
from typing import List, Dict, Optional
import time


class FiltroEstatistico:
    DEZENAS_TOTAL = 60
    DEZENAS_POR_JOGO = 6

    # Faixas para 6 dezenas (1-60)
    SOMA_MIN = 100
    SOMA_MAX = 250
    SOMA_MEDIA = 183       # Soma média teórica: 6 × 30.5 = 183
    DESVIO_MIN = 14.0
    DESVIO_MAX = 22.0
    IMPARES_MIN = 2
    IMPARES_MAX = 4

    # Primos no universo 1-60
    PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}

    # Quadrantes
    QUADRANTES = {
        'Q1': list(range(1, 16)),
        'Q2': list(range(16, 31)),
        'Q3': list(range(31, 46)),
        'Q4': list(range(46, 61)),
    }

    def __init__(self):
        self.historico_df: Optional[pd.DataFrame] = None
        self.mapa_calor: Dict[int, float] = {}

    # ── FILTROS ────────────────────────────────────────────

    def filtrar_por_soma(self, jogos: List[List[int]]) -> List[List[int]]:
        if not jogos:
            return []
        jogos_np = np.array(jogos)
        somas = jogos_np.sum(axis=1)
        mascara = (somas >= self.SOMA_MIN) & (somas <= self.SOMA_MAX)
        return jogos_np[mascara].tolist()

    def calcular_soma(self, jogo: List[int]) -> Dict:
        soma = sum(jogo)
        return {
            'valor': soma,
            'valido': self.SOMA_MIN <= soma <= self.SOMA_MAX,
            'faixa': f'{self.SOMA_MIN}–{self.SOMA_MAX}',
            'desvio_da_media': soma - self.SOMA_MEDIA,
            'posicao': 'centro' if 160 <= soma <= 210 else ('acima' if soma > 210 else 'abaixo'),
        }

    def calcular_desvio_padrao(self, jogo: List[int]) -> Dict:
        sigma = float(np.std(jogo))
        return {
            'valor': round(sigma, 3),
            'valido': self.DESVIO_MIN <= sigma <= self.DESVIO_MAX,
            'faixa': f'{self.DESVIO_MIN}–{self.DESVIO_MAX}',
            'classificacao': (
                '✅ Equilibrada' if self.DESVIO_MIN <= sigma <= self.DESVIO_MAX
                else ('⚠️ Agrupado' if sigma < self.DESVIO_MIN else '⚠️ Espalhado')
            ),
        }

    def filtrar_por_desvio_padrao(self, jogos: List[List[int]]) -> List[List[int]]:
        if not jogos:
            return []
        jogos_np = np.array(jogos, dtype=np.float64)
        desvios = np.std(jogos_np, axis=1)
        mascara = (desvios >= self.DESVIO_MIN) & (desvios <= self.DESVIO_MAX)
        return jogos_np[mascara].astype(int).tolist()

    def filtrar_por_paridade(self, jogos: List[List[int]]) -> List[List[int]]:
        if not jogos:
            return []
        jogos_np = np.array(jogos)
        impares = np.sum(jogos_np % 2 != 0, axis=1)
        mascara = (impares >= self.IMPARES_MIN) & (impares <= self.IMPARES_MAX)
        return jogos_np[mascara].tolist()

    def calcular_paridade(self, jogo: List[int]) -> Dict:
        impares = sum(1 for n in jogo if n % 2 != 0)
        pares = len(jogo) - impares
        return {
            'impares': impares,
            'pares': pares,
            'formato': f'{impares}Í/{pares}P',
            'valido': self.IMPARES_MIN <= impares <= self.IMPARES_MAX,
            'faixa': f'{self.IMPARES_MIN}–{self.IMPARES_MAX} ímpares',
        }

    # ── Quadrantes ────────────────────────────────────────

    def analisar_quadrantes_jogo(self, jogo: List[int]) -> Dict:
        resultado = {}
        for nome, faixa in self.QUADRANTES.items():
            nums = [n for n in jogo if n in faixa]
            resultado[nome] = {'numeros': nums, 'quantidade': len(nums)}
        quads_presentes = sum(1 for v in resultado.values() if v['quantidade'] > 0)
        return {
            'distribuicao': resultado,
            'quadrantes_presentes': quads_presentes,
            'equilibrado': quads_presentes >= 3,
        }

    # ── CALOR HISTÓRICO ───────────────────────────────────

    def carregar_historico_de_dataframe(self, df: pd.DataFrame) -> None:
        self.historico_df = df
        todas_dezenas = []
        for dezenas in df['Dezenas']:
            if isinstance(dezenas, list):
                todas_dezenas.extend(dezenas)
            elif isinstance(dezenas, str):
                nums = [int(n.strip()) for n in dezenas.strip('[]').split(',')]
                todas_dezenas.extend(nums)

        contagem = Counter(todas_dezenas)
        max_freq = max(contagem.values()) if contagem else 1
        min_freq = min(contagem.values()) if contagem else 0

        for dezena in range(1, self.DEZENAS_TOTAL + 1):
            freq = contagem.get(dezena, 0)
            if max_freq > min_freq:
                self.mapa_calor[dezena] = round(((freq - min_freq) / (max_freq - min_freq)) * 100, 1)
            else:
                self.mapa_calor[dezena] = 50.0

    def calcular_pontuacao_calor(self, dezena: int) -> float:
        return self.mapa_calor.get(dezena, 50.0)

    def calor_do_jogo(self, jogo: List[int]) -> Dict:
        scores = [self.calcular_pontuacao_calor(n) for n in jogo]
        return {
            'media': float(round(np.mean(scores), 1)),
            'mediana': float(round(np.median(scores), 1)),
            'min': float(round(min(scores), 1)),
            'max': float(round(max(scores), 1)),
            'dezenas_quentes': int(sum(1 for s in scores if s >= 70)),
            'dezenas_frias': int(sum(1 for s in scores if s <= 30)),
            'scores_por_dezena': {int(n): float(s) for n, s in zip(jogo, scores)},
        }

    def get_mapa_calor_completo(self) -> List[Dict]:
        resultado = []
        for dezena in range(1, self.DEZENAS_TOTAL + 1):
            score = self.mapa_calor.get(dezena, 50.0)
            if score >= 70:
                cat = '🔥 Quente'
            elif score >= 40:
                cat = '🟡 Morna'
            else:
                cat = '❄️ Fria'
            resultado.append({'dezena': dezena, 'calor': score, 'categoria': cat})
        return sorted(resultado, key=lambda x: x['calor'], reverse=True)

    # ── PONTUAÇÃO COMPOSTA ────────────────────────────────

    def pontuar_jogo(self, jogo: List[int]) -> Dict:
        score = 0.0
        detalhes = {}

        # Soma (30 pts max)
        info_soma = self.calcular_soma(jogo)
        detalhes['soma'] = info_soma
        if info_soma['valido']:
            soma_score = max(0, 30 - (abs(info_soma['valor'] - self.SOMA_MEDIA) * 0.3))
            score += soma_score
            detalhes['soma']['pontos'] = round(soma_score, 1)
        else:
            detalhes['soma']['pontos'] = 0

        # Desvio padrão (20 pts max)
        info_dp = self.calcular_desvio_padrao(jogo)
        detalhes['desvio_padrao'] = info_dp
        if info_dp['valido']:
            dp_score = max(0, 20 - (abs(info_dp['valor'] - 18.0) * 3))
            score += dp_score
            detalhes['desvio_padrao']['pontos'] = round(dp_score, 1)
        else:
            detalhes['desvio_padrao']['pontos'] = 0

        # Paridade (15 pts max)
        info_par = self.calcular_paridade(jogo)
        detalhes['paridade'] = info_par
        if info_par['valido']:
            par_score = max(0, 15 - (abs(info_par['impares'] - 3) * 7))
            score += par_score
            detalhes['paridade']['pontos'] = round(par_score, 1)
        else:
            detalhes['paridade']['pontos'] = 0

        # Calor (20 pts max)
        if self.mapa_calor:
            info_calor = self.calor_do_jogo(jogo)
            detalhes['calor'] = info_calor
            calor_score = min(20, info_calor['media'] * 0.2)
            score += calor_score
            detalhes['calor']['pontos'] = round(calor_score, 1)
        else:
            detalhes['calor'] = {'pontos': 10, 'media': 50}
            score += 10

        # Primos (10 pts max)
        qtd_primos = sum(1 for n in jogo if n in self.PRIMOS)
        primos_valido = 2 <= qtd_primos <= 3
        primos_score = 10 if primos_valido else max(0, 10 - abs(qtd_primos - 2.5) * 4)
        score += primos_score
        detalhes['primos'] = {
            'quantidade': qtd_primos,
            'valido': primos_valido,
            'esperado': '2 a 3',
            'pontos': round(primos_score, 1),
        }

        # Quadrantes (5 pts extra)
        info_quad = self.analisar_quadrantes_jogo(jogo)
        quad_score = min(5, info_quad['quadrantes_presentes'] * 1.5)
        score += quad_score
        detalhes['quadrantes'] = {
            'presentes': info_quad['quadrantes_presentes'],
            'equilibrado': info_quad['equilibrado'],
            'pontos': round(quad_score, 1),
        }

        classificacao = (
            '🏆 Elite' if score >= 85 else
            '🥇 Ótimo' if score >= 70 else
            '🥈 Bom' if score >= 55 else
            '🥉 Regular' if score >= 40 else
            '⚠️ Fraco'
        )

        return {
            'jogo': jogo,
            'score': round(score, 1),
            'max_score': 100,
            'classificacao': classificacao,
            'aprovado': score >= 55,
            'detalhes': detalhes,
        }

    # ── MONTE CARLO ───────────────────────────────────────

    def simulacao_monte_carlo(self, n: int = 100_000, top_k: int = 10) -> Dict:
        inicio = time.time()

        todos_jogos = np.array([
            np.sort(np.random.choice(range(1, 61), size=6, replace=False))
            for _ in range(n)
        ])

        somas = todos_jogos.sum(axis=1)
        mask_soma = (somas >= self.SOMA_MIN) & (somas <= self.SOMA_MAX)
        aprovados_soma = int(mask_soma.sum())

        impares = np.sum(todos_jogos % 2 != 0, axis=1)
        mask_par = (impares >= self.IMPARES_MIN) & (impares <= self.IMPARES_MAX)

        desvios = np.std(todos_jogos.astype(np.float64), axis=1)
        mask_dp = (desvios >= self.DESVIO_MIN) & (desvios <= self.DESVIO_MAX)

        mask_final = mask_soma & mask_par & mask_dp
        aprovados_total = int(mask_final.sum())

        sobreviventes = todos_jogos[mask_final].tolist()
        if not sobreviventes:
            return {
                'status': 'sem_resultados',
                'total_gerado': n,
                'total_aprovado': 0,
                'top_jogos': [],
                'tempo_segundos': round(time.time() - inicio, 2),
            }

        pontuados = [self.pontuar_jogo(jogo) for jogo in sobreviventes]
        pontuados.sort(key=lambda x: x['score'], reverse=True)

        return {
            'status': 'sucesso',
            'total_gerado': n,
            'estatisticas': {
                'aprovados_soma': aprovados_soma,
                'taxa_soma': round(aprovados_soma / n * 100, 2),
                'aprovados_desvio': aprovados_total,
                'taxa_final': round(aprovados_total / n * 100, 2),
            },
            'top_jogos': pontuados[:top_k],
            'tempo_segundos': round(time.time() - inicio, 2),
        }

    # ── UTILITÁRIOS ───────────────────────────────────────

    def validar_jogo_completo(self, jogo: List[int]) -> Dict:
        if len(jogo) != 6:
            return {'erro': f'Jogo deve ter 6 números, recebeu {len(jogo)}'}
        if any(n < 1 or n > 60 for n in jogo):
            return {'erro': 'Todos os números devem estar entre 1 e 60'}
        if len(set(jogo)) != 6:
            return {'erro': 'Jogo contém números repetidos'}
        return self.pontuar_jogo(sorted(jogo))

    def resumo_filtros(self) -> Dict:
        return {
            'soma': {'min': self.SOMA_MIN, 'max': self.SOMA_MAX, 'media_ideal': self.SOMA_MEDIA},
            'desvio_padrao': {'min': self.DESVIO_MIN, 'max': self.DESVIO_MAX, 'ideal': 18.0},
            'paridade': {'impares_min': self.IMPARES_MIN, 'impares_max': self.IMPARES_MAX},
            'primos': {'ideal': [2, 3], 'numeros_primos': sorted(self.PRIMOS)},
            'historico_carregado': self.historico_df is not None,
            'dezenas_no_mapa': len(self.mapa_calor),
        }
