"""
LotoMind Enterprise — Módulo de Filtragem Estatística
=====================================================
Classe modular para análise de normalidade estatística de jogos da Lotofácil.
"""

import numpy as np
import pandas as pd
from collections import Counter
from typing import List, Dict, Optional
import time


class FiltroEstatistico:
    DEZENAS_TOTAL = 25
    DEZENAS_POR_JOGO = 15
    SOMA_MIN = 166
    SOMA_MAX = 220
    DESVIO_MIN = 6.5
    DESVIO_MAX = 8.5
    IMPARES_MIN = 7
    IMPARES_MAX = 9
    PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}

    def __init__(self, historico_path: Optional[str] = None):
        self.historico_df: Optional[pd.DataFrame] = None
        self.mapa_calor: Dict[int, float] = {}
        if historico_path:
            self.carregar_historico(historico_path)

    # ── FILTROS ────────────────────────────────────────────

    def filtrar_por_soma(self, jogos: List[List[int]]) -> List[List[int]]:
        if not jogos: return []
        jogos_np = np.array(jogos)
        somas = jogos_np.sum(axis=1)
        mascara = (somas >= self.SOMA_MIN) & (somas <= self.SOMA_MAX)
        return jogos_np[mascara].tolist()

    def calcular_soma(self, jogo: List[int]) -> Dict:
        soma = sum(jogo)
        return {
            'valor': soma, 'valido': self.SOMA_MIN <= soma <= self.SOMA_MAX,
            'faixa': f'{self.SOMA_MIN}–{self.SOMA_MAX}',
            'desvio_da_media': soma - 195,
            'posicao': 'centro' if 185 <= soma <= 205 else ('acima' if soma > 205 else 'abaixo')
        }

    def calcular_desvio_padrao(self, jogo: List[int]) -> Dict:
        sigma = float(np.std(jogo))
        return {
            'valor': round(sigma, 3), 'valido': self.DESVIO_MIN <= sigma <= self.DESVIO_MAX,
            'faixa': f'{self.DESVIO_MIN}–{self.DESVIO_MAX}',
            'classificacao': '✅ Equilibrada' if self.DESVIO_MIN <= sigma <= self.DESVIO_MAX
                             else ('⚠️ Agrupado' if sigma < self.DESVIO_MIN else '⚠️ Espalhado')
        }

    def filtrar_por_desvio_padrao(self, jogos: List[List[int]]) -> List[List[int]]:
        if not jogos: return []
        jogos_np = np.array(jogos, dtype=np.float64)
        desvios = np.std(jogos_np, axis=1)
        mascara = (desvios >= self.DESVIO_MIN) & (desvios <= self.DESVIO_MAX)
        return jogos_np[mascara].astype(int).tolist()

    def filtrar_por_paridade(self, jogos: List[List[int]]) -> List[List[int]]:
        if not jogos: return []
        jogos_np = np.array(jogos)
        impares = np.sum(jogos_np % 2 != 0, axis=1)
        mascara = (impares >= self.IMPARES_MIN) & (impares <= self.IMPARES_MAX)
        return jogos_np[mascara].tolist()

    def calcular_paridade(self, jogo: List[int]) -> Dict:
        impares = sum(1 for n in jogo if n % 2 != 0)
        pares = 15 - impares
        return {
            'impares': impares, 'pares': pares, 'formato': f'{impares}Í/{pares}P',
            'valido': self.IMPARES_MIN <= impares <= self.IMPARES_MAX,
            'faixa': f'{self.IMPARES_MIN}–{self.IMPARES_MAX} ímpares'
        }

    # ── CALOR HISTÓRICO ────────────────────────────────────

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
        for dezena in range(1, 26):
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
            'media': round(np.mean(scores), 1),
            'mediana': round(float(np.median(scores)), 1),
            'min': round(min(scores), 1), 'max': round(max(scores), 1),
            'dezenas_quentes': sum(1 for s in scores if s >= 70),
            'dezenas_frias': sum(1 for s in scores if s <= 30),
            'scores_por_dezena': {n: s for n, s in zip(jogo, scores)}
        }

    def get_mapa_calor_completo(self) -> List[Dict]:
        resultado = []
        for dezena in range(1, 26):
            score = self.mapa_calor.get(dezena, 50.0)
            categoria = '🔥 Quente' if score >= 70 else ('🟡 Morna' if score >= 40 else '❄️ Fria')
            resultado.append({'dezena': dezena, 'calor': score, 'categoria': categoria})
        return sorted(resultado, key=lambda x: x['calor'], reverse=True)

    # ── PONTUAÇÃO COMPOSTA ────────────────────────────────

    def pontuar_jogo(self, jogo: List[int]) -> Dict:
        score = 0.0
        detalhes = {}

        info_soma = self.calcular_soma(jogo)
        detalhes['soma'] = info_soma
        if info_soma['valido']:
            soma_score = max(0, 30 - (abs(info_soma['valor'] - 195) * 0.8))
            score += soma_score
            detalhes['soma']['pontos'] = round(soma_score, 1)
        else:
            detalhes['soma']['pontos'] = 0

        info_dp = self.calcular_desvio_padrao(jogo)
        detalhes['desvio_padrao'] = info_dp
        if info_dp['valido']:
            dp_score = max(0, 20 - (abs(info_dp['valor'] - 7.5) * 8))
            score += dp_score
            detalhes['desvio_padrao']['pontos'] = round(dp_score, 1)
        else:
            detalhes['desvio_padrao']['pontos'] = 0

        info_par = self.calcular_paridade(jogo)
        detalhes['paridade'] = info_par
        if info_par['valido']:
            par_score = max(0, 20 - (abs(info_par['impares'] - 8) * 10))
            score += par_score
            detalhes['paridade']['pontos'] = round(par_score, 1)
        else:
            detalhes['paridade']['pontos'] = 0

        if self.mapa_calor:
            info_calor = self.calor_do_jogo(jogo)
            detalhes['calor'] = info_calor
            calor_score = min(20, info_calor['media'] * 0.2)
            score += calor_score
            detalhes['calor']['pontos'] = round(calor_score, 1)
        else:
            detalhes['calor'] = {'pontos': 10, 'media': 50}
            score += 10

        qtd_primos = sum(1 for n in jogo if n in self.PRIMOS)
        primos_valido = qtd_primos in [5, 6]
        primos_score = 10 if primos_valido else max(0, 10 - abs(qtd_primos - 5.5) * 3)
        score += primos_score
        detalhes['primos'] = {
            'quantidade': qtd_primos, 'valido': primos_valido,
            'esperado': '5 ou 6', 'pontos': round(primos_score, 1)
        }

        classificacao = ('🏆 Elite (excelente)' if score >= 85 else
                         '🥇 Ótimo' if score >= 70 else
                         '🥈 Bom' if score >= 60 else
                         '🥉 Regular' if score >= 45 else '⚠️ Fraco')

        return {
            'jogo': jogo, 'score': round(score, 1), 'max_score': 100,
            'classificacao': classificacao, 'aprovado': score >= 60, 'detalhes': detalhes
        }

    # ── PIPELINE + MONTE CARLO ────────────────────────────

    def filtrar_jogos(self, jogos: List[List[int]]) -> List[Dict]:
        jogos = self.filtrar_por_soma(jogos)
        jogos = self.filtrar_por_paridade(jogos)
        jogos = self.filtrar_por_desvio_padrao(jogos)
        resultados = [self.pontuar_jogo(jogo) for jogo in jogos]
        resultados.sort(key=lambda x: x['score'], reverse=True)
        return resultados

    def simulacao_monte_carlo(self, n: int = 100_000, top_k: int = 10, verbose: bool = False) -> Dict:
        inicio = time.time()
        todos_jogos = np.array([
            np.sort(np.random.choice(range(1, 26), size=15, replace=False))
            for _ in range(n)
        ])

        somas = todos_jogos.sum(axis=1)
        mask_soma = (somas >= self.SOMA_MIN) & (somas <= self.SOMA_MAX)
        aprovados_soma = int(mask_soma.sum())

        impares = np.sum(todos_jogos % 2 != 0, axis=1)
        mask_paridade = (impares >= self.IMPARES_MIN) & (impares <= self.IMPARES_MAX)
        aprovados_paridade = int((mask_soma & mask_paridade).sum())

        desvios = np.std(todos_jogos.astype(np.float64), axis=1)
        mask_dp = (desvios >= self.DESVIO_MIN) & (desvios <= self.DESVIO_MAX)
        mask_final = mask_soma & mask_paridade & mask_dp
        aprovados_total = int(mask_final.sum())

        sobreviventes = todos_jogos[mask_final].tolist()
        if not sobreviventes:
            return {
                'status': 'sem_resultados', 'total_gerado': n, 'total_aprovado': 0,
                'top_jogos': [], 'tempo_segundos': round(time.time() - inicio, 2)
            }

        pontuados = [self.pontuar_jogo(jogo) for jogo in sobreviventes]
        pontuados.sort(key=lambda x: x['score'], reverse=True)

        return {
            'status': 'sucesso', 'total_gerado': n,
            'estatisticas': {
                'aprovados_soma': aprovados_soma,
                'taxa_soma': round(aprovados_soma / n * 100, 2),
                'aprovados_paridade': aprovados_paridade,
                'aprovados_desvio': aprovados_total,
                'taxa_final': round(aprovados_total / n * 100, 2),
            },
            'top_jogos': pontuados[:top_k],
            'tempo_segundos': round(time.time() - inicio, 2)
        }

    # ── UTILITÁRIOS ────────────────────────────────────────

    def validar_jogo_completo(self, jogo: List[int]) -> Dict:
        if len(jogo) != 15:
            return {'erro': f'Jogo deve ter 15 números, recebeu {len(jogo)}'}
        if any(n < 1 or n > 25 for n in jogo):
            return {'erro': 'Todos os números devem estar entre 1 e 25'}
        if len(set(jogo)) != 15:
            return {'erro': 'Jogo contém números repetidos'}
        return self.pontuar_jogo(sorted(jogo))

    def resumo_filtros(self) -> Dict:
        return {
            'soma': {'min': self.SOMA_MIN, 'max': self.SOMA_MAX, 'media_ideal': 195},
            'desvio_padrao': {'min': self.DESVIO_MIN, 'max': self.DESVIO_MAX, 'ideal': 7.5},
            'paridade': {'impares_min': self.IMPARES_MIN, 'impares_max': self.IMPARES_MAX},
            'primos': {'ideal': [5, 6], 'numeros_primos': sorted(self.PRIMOS)},
            'historico_carregado': self.historico_df is not None,
            'dezenas_no_mapa': len(self.mapa_calor)
        }
