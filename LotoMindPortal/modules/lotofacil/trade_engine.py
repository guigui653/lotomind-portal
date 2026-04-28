"""
LotoMind Portal — Trade Engine (Motor Analítico Trade-Finance)
==============================================================
Combina estatísticas lotéricas com conceitos do mercado financeiro:

Pilar 1 — Frequência de Curto Prazo
    • Dezenas da Semana   → Top 8 nos últimos 3 concursos
    • Dezenas da Quinzena → Top 8 nos últimos 6 concursos
    • Âncoras             → Filtragem cruzada (overlap ou Top 5 Semanal)

Pilar 2 — Validação de Trade (SMA-10 + Bollinger)
    • SMA-10              → Frequência média simples (10 concursos) por dezena
    • Bollinger da Soma   → Média ± 2σ dos últimos 20 concursos
    • Regra de Rejeição   → Palpites fora das bandas são eliminados

Pilar 3 — Backtesting (Últimos 5 Concursos)
    • Cegueira temporal   → Lógica dos Pilares 1/2 com dados disponíveis até cada ponto
    • Retorno estatístico → Acertos de 11, 12, 13, 14, 15 por concurso
"""

import random
from collections import Counter
from itertools import combinations

import numpy as np


class LotoMindTradeEngine:
    """Motor analítico trade-finance para Lotofácil."""

    UNIVERSO = 25
    DEZENAS_SORTEIO = 15

    # Faixas de soma validadas historicamente para Lotofácil
    SOMA_MIN_GLOBAL = 135
    SOMA_MAX_GLOBAL = 285

    def __init__(self):
        self.df = None
        self._carregado = False

    # ════════════════════════════════════════════════════════════
    #  CARREGAMENTO
    # ════════════════════════════════════════════════════════════

    def carregar_historico(self, df):
        """Carrega o DataFrame histórico da Lotofácil."""
        if df is None or df.empty:
            return
        # Garantir ordenação: mais recente primeiro (maior número de concurso = índice 0)
        self.df = df.sort_values('Concurso', ascending=False).reset_index(drop=True)
        self._carregado = True

    # ════════════════════════════════════════════════════════════
    #  PILAR 1 — FREQUÊNCIA DE CURTO PRAZO
    # ════════════════════════════════════════════════════════════

    def calcular_dezenas_semana(self, df_snapshot=None, n_concursos=3, top_n=8):
        """
        Analisa os últimos n_concursos (padrão 3) e retorna as top_n dezenas
        mais frequentes com suas contagens. 'Dezenas de Tendência Semanal'.
        """
        df = df_snapshot if df_snapshot is not None else self.df
        if df is None or len(df) < n_concursos:
            return []

        ultimos = df.head(n_concursos)
        todas = [n for sub in ultimos['Dezenas'] for n in sub]
        contagem = Counter(todas)

        resultado = []
        for num, freq in contagem.most_common(top_n):
            resultado.append({
                'dezena': int(num),
                'freq': int(freq),
                'max_freq': n_concursos,  # máximo possível
                'pct': round(freq / n_concursos * 100, 1),
            })
        return resultado

    def calcular_dezenas_quinzena(self, df_snapshot=None, n_concursos=6, top_n=8):
        """
        Analisa os últimos n_concursos (padrão 6) e retorna as top_n dezenas
        mais frequentes. 'Dezenas de Tendência Quinzenal'.
        """
        df = df_snapshot if df_snapshot is not None else self.df
        if df is None or len(df) < n_concursos:
            return []

        ultimos = df.head(n_concursos)
        todas = [n for sub in ultimos['Dezenas'] for n in sub]
        contagem = Counter(todas)

        resultado = []
        for num, freq in contagem.most_common(top_n):
            resultado.append({
                'dezena': int(num),
                'freq': int(freq),
                'max_freq': n_concursos,
                'pct': round(freq / n_concursos * 100, 1),
            })
        return resultado

    def calcular_ancoras(self, semana, quinzena, min_ancoras=5):
        """
        Filtragem cruzada: dezenas que aparecem em AMBAS as listas.
        Se o overlap for < min_ancoras, garante ao menos as Top min_ancoras da semanal.

        Retorna lista de dicts com flag 'overlap' (True = âncora confirmada).
        """
        nums_semana = [d['dezena'] for d in semana]
        nums_quinzena = [d['dezena'] for d in quinzena]

        overlap = set(nums_semana) & set(nums_quinzena)

        # Mapear dados de quinzena para lookup
        quinzena_map = {d['dezena']: d for d in quinzena}
        semana_map = {d['dezena']: d for d in semana}

        ancoras = []

        # Prioridade 1: dezenas em overlap (âncoras confirmadas)
        for num in nums_semana:  # mantém a ordem da semana (ranking)
            if num in overlap:
                ancoras.append({
                    'dezena': num,
                    'freq_semana': semana_map[num]['freq'],
                    'pct_semana': semana_map[num]['pct'],
                    'freq_quinzena': quinzena_map.get(num, {}).get('freq', 0),
                    'pct_quinzena': quinzena_map.get(num, {}).get('pct', 0.0),
                    'overlap': True,
                })

        # Se overlap insuficiente, completa com Top da semanal
        if len(ancoras) < min_ancoras:
            for num in nums_semana:
                if num not in overlap and len(ancoras) < min_ancoras:
                    ancoras.append({
                        'dezena': num,
                        'freq_semana': semana_map[num]['freq'],
                        'pct_semana': semana_map[num]['pct'],
                        'freq_quinzena': quinzena_map.get(num, {}).get('freq', 0),
                        'pct_quinzena': quinzena_map.get(num, {}).get('pct', 0.0),
                        'overlap': False,
                    })

        return ancoras

    # ════════════════════════════════════════════════════════════
    #  PILAR 2 — VALIDAÇÃO DE TRADE
    # ════════════════════════════════════════════════════════════

    def calcular_sma10(self, dezena, df_snapshot=None, janela=10):
        """
        Calcula a Frequência Média Simples (SMA) de uma dezena
        nos últimos `janela` concursos.
        Retorna: float (presença média por concurso, de 0.0 a 1.0)
        """
        df = df_snapshot if df_snapshot is not None else self.df
        if df is None or len(df) < janela:
            janela = len(df) if df is not None else 0

        if janela == 0:
            return 0.0

        ultimos = df.head(janela)
        freq = sum(1 for dezenas in ultimos['Dezenas'] if dezena in dezenas)
        return round(freq / janela, 4)

    def calcular_media_historica_dezena(self, dezena, df_snapshot=None):
        """Frequência histórica geral de uma dezena (0.0 a 1.0)."""
        df = df_snapshot if df_snapshot is not None else self.df
        if df is None or df.empty:
            return 0.0
        total = len(df)
        freq = sum(1 for dezenas in df['Dezenas'] if dezena in dezenas)
        return round(freq / total, 4)

    def validar_sma10_ancoras(self, ancoras, df_snapshot=None):
        """
        Para cada dezena âncora, calcula SMA-10 e compara com a
        média histórica. Emite alerta de confiabilidade.

        Status possíveis:
          'TENDÊNCIA CONFIRMADA'      → SMA-10 >= média histórica * 0.9
          'ALERTA: ANOMALIA PASSAGEIRA' → SMA-10 < média histórica * 0.9
        """
        resultado = []
        for ancora in ancoras:
            dezena = ancora['dezena']
            sma10 = self.calcular_sma10(dezena, df_snapshot)
            media_hist = self.calcular_media_historica_dezena(dezena, df_snapshot)

            # Threshold: SMA-10 >= 90% da média histórica = tendência validada
            threshold = media_hist * 0.90

            if sma10 >= threshold:
                status = 'TENDÊNCIA CONFIRMADA'
                confianca = 'alta'
                emoji = '✅'
            else:
                status = 'ALERTA: ANOMALIA PASSAGEIRA'
                confianca = 'baixa'
                emoji = '⚠️'

            # Verificação bônus: SMA está subindo (comparar SMA-10 vs SMA-5)
            sma5 = self.calcular_sma10(dezena, df_snapshot, janela=5)
            tendencia_sma = 'subindo' if sma5 > sma10 else ('estável' if abs(sma5 - sma10) < 0.05 else 'caindo')

            resultado.append({
                **ancora,
                'sma10': sma10,
                'sma5': sma5,
                'media_historica': media_hist,
                'tendencia_sma': tendencia_sma,
                'status': status,
                'confianca': confianca,
                'emoji': emoji,
            })
        return resultado

    def calcular_bollinger(self, df_snapshot=None, janela=20, desvios=2):
        """
        Calcula as Bandas de Bollinger sobre a SOMA das dezenas
        dos últimos `janela` concursos.

        Retorna: dict com media, desvio, banda_superior, banda_inferior,
                 e lista de somas para o gráfico.
        """
        df = df_snapshot if df_snapshot is not None else self.df
        if df is None or df.empty:
            return None

        n = min(janela, len(df))
        ultimos = df.head(n)
        somas = ultimos['Soma'].tolist()

        # Mais antigo primeiro para o gráfico ficar cronológico
        somas_crono = list(reversed(somas))
        concursos_crono = list(reversed(ultimos['Concurso'].tolist()))

        media = float(np.mean(somas))
        desvio = float(np.std(somas, ddof=1)) if len(somas) > 1 else 0.0

        banda_sup = round(media + desvios * desvio, 2)
        banda_inf = round(media - desvios * desvio, 2)

        # Posição do último sorteio em relação às bandas
        ultima_soma = somas[0]  # mais recente
        if ultima_soma > banda_sup:
            zona_atual = 'ACIMA (Sobrecomprado)'
            zona_emoji = '📈'
        elif ultima_soma < banda_inf:
            zona_atual = 'ABAIXO (Sobrevendido)'
            zona_emoji = '📉'
        else:
            zona_atual = 'DENTRO DAS BANDAS'
            zona_emoji = '✅'

        return {
            'media': round(media, 2),
            'desvio': round(desvio, 2),
            'banda_superior': banda_sup,
            'banda_inferior': banda_inf,
            'ultima_soma': int(ultima_soma),
            'zona_atual': zona_atual,
            'zona_emoji': zona_emoji,
            'somas_historico': [int(s) for s in somas_crono],
            'concursos_historico': [int(c) for c in concursos_crono],
            'largura_banda': round(banda_sup - banda_inf, 2),
            'janela': n,
        }

    def filtrar_por_bollinger(self, palpites, bollinger):
        """
        Filtra lista de palpites (cada um = lista de 15 dezenas).
        Rejeita automaticamente os que têm soma fora das bandas.

        Retorna: lista de dicts com palpite aceito + soma + status.
        """
        aprovados = []
        rejeitados = []

        banda_inf = bollinger['banda_inferior']
        banda_sup = bollinger['banda_superior']

        for palpite in palpites:
            soma = sum(palpite)
            if banda_inf <= soma <= banda_sup:
                aprovados.append({
                    'dezenas': sorted(palpite),
                    'soma': soma,
                    'status': 'aprovado',
                    'dentro_bollinger': True,
                })
            else:
                rejeitados.append({
                    'dezenas': sorted(palpite),
                    'soma': soma,
                    'status': 'rejeitado',
                    'dentro_bollinger': False,
                    'motivo': f'Soma {soma} fora das bandas [{banda_inf:.0f}–{banda_sup:.0f}]',
                })

        return {'aprovados': aprovados, 'rejeitados': rejeitados}

    # ════════════════════════════════════════════════════════════
    #  GERADOR DE PALPITES (baseado nas âncoras + Bollinger)
    # ════════════════════════════════════════════════════════════

    def _gerar_candidato(self, ancoras_nums, bollinger, max_tentativas=500):
        """
        Gera um palpite de 15 dezenas baseado nas dezenas âncora.
        As âncoras são incluídas; o restante é complementado com dezenas
        aleatórias dentro das restrições de Bollinger.
        """
        banda_inf = bollinger['banda_inferior']
        banda_sup = bollinger['banda_superior']

        universo = list(range(1, self.UNIVERSO + 1))

        for _ in range(max_tentativas):
            # Começa com todas as âncoras
            jogo = list(ancoras_nums)

            # Complementa até 15 dezenas com dezenas fora das âncoras
            disponiveis = [d for d in universo if d not in jogo]
            random.shuffle(disponiveis)

            faltam = self.DEZENAS_SORTEIO - len(jogo)
            jogo += disponiveis[:faltam]

            soma = sum(jogo)
            if banda_inf <= soma <= banda_sup:
                return sorted(jogo)

        return None  # não conseguiu gerar dentro das bandas

    def gerar_palpites(self, qtd=5, max_tentativas_total=2000):
        """
        Gera `qtd` palpites distintos, todos:
        1. Baseados nas dezenas âncora do Pilar 1
        2. Com soma dentro das Bandas de Bollinger (Pilar 2)

        Retorna lista de palpites com metadados.
        """
        if not self._carregado:
            return []

        semana = self.calcular_dezenas_semana()
        quinzena = self.calcular_dezenas_quinzena()
        ancoras = self.calcular_ancoras(semana, quinzena)
        bollinger = self.calcular_bollinger()

        ancoras_nums = [a['dezena'] for a in ancoras]

        # Validar que as âncoras cabem em 15 dezenas
        if len(ancoras_nums) > self.DEZENAS_SORTEIO:
            ancoras_nums = ancoras_nums[:self.DEZENAS_SORTEIO]

        palpites_gerados = []
        tentativas = 0
        jogos_vistos = set()

        while len(palpites_gerados) < qtd and tentativas < max_tentativas_total:
            candidato = self._gerar_candidato(ancoras_nums, bollinger)
            tentativas += 1

            if candidato:
                chave = tuple(candidato)
                if chave not in jogos_vistos:
                    jogos_vistos.add(chave)
                    palpites_gerados.append({
                        'dezenas': candidato,
                        'soma': sum(candidato),
                        'dentro_bollinger': True,
                        'ancoras_incluidas': sorted(set(candidato) & set(ancoras_nums)),
                        'qtd_ancoras': len(set(candidato) & set(ancoras_nums)),
                        'completares': sorted(set(candidato) - set(ancoras_nums)),
                    })

        return palpites_gerados

    # ════════════════════════════════════════════════════════════
    #  PILAR 3 — BACKTESTING
    # ════════════════════════════════════════════════════════════

    def _contar_acertos(self, jogo, sorteio):
        """Conta quantas dezenas do jogo batem com o sorteio."""
        return len(set(jogo) & set(sorteio))

    def backtest(self, n_concursos=5):
        """
        Realiza backtesting com cegueira temporal real:
        Para cada um dos últimos n_concursos:
          - Ignora os dados desse concurso e posteriores
          - Aplica Pilares 1 e 2 com dados disponíveis até antes do concurso
          - Gera 1 a 3 palpites via âncoras + Bollinger
          - Compara com o resultado real

        Retorna relatório completo por concurso.
        """
        if not self._carregado or len(self.df) < n_concursos + 10:
            return []

        relatorio = []

        # Faixas de premiação da Lotofácil
        premios_map = {
            15: '🏆 15 Pontos — PRÊMIO MÁXIMO!',
            14: '🥇 14 Pontos — Prêmio Alto',
            13: '🥈 13 Pontos — Prêmio Médio',
            12: '🥉 12 Pontos — Prêmio Pequeno',
            11: '🎖️ 11 Pontos — Prêmio Mínimo',
        }

        for i in range(n_concursos):
            # O concurso "alvo" é o i-ésimo mais recente (índice i no df ordenado desc)
            row_alvo = self.df.iloc[i]
            sorteio_real = row_alvo['Dezenas']
            concurso_num = int(row_alvo['Concurso'])
            data_concurso = row_alvo.get('Data', '-')

            # Snapshot histórico: apenas dados ANTERIORES a este concurso
            df_snapshot = self.df.iloc[i + 1:].reset_index(drop=True)

            if len(df_snapshot) < 10:
                continue

            # Criar motor temporário com snapshot
            motor_temp = LotoMindTradeEngine()
            motor_temp.carregar_historico(df_snapshot)

            # Pilar 1 no snapshot
            semana_snap = motor_temp.calcular_dezenas_semana()
            quinzena_snap = motor_temp.calcular_dezenas_quinzena()
            ancoras_snap = motor_temp.calcular_ancoras(semana_snap, quinzena_snap)
            ancoras_nums_snap = [a['dezena'] for a in ancoras_snap]

            # Pilar 2 no snapshot
            bollinger_snap = motor_temp.calcular_bollinger()
            if not bollinger_snap:
                continue

            # Gerar 3 palpites para o backtest
            palpites = []
            for _ in range(150):  # tenta até 150x para garantir 3
                candidato = motor_temp._gerar_candidato(ancoras_nums_snap, bollinger_snap)
                if candidato:
                    palpites.append(candidato)
                if len(palpites) >= 3:
                    break

            # Avaliar acertos
            resultados_palpites = []
            melhor_acerto = 0
            acertos_por_faixa = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}

            for p in palpites:
                acertos = self._contar_acertos(p, sorteio_real)
                if acertos >= 11:
                    acertos_por_faixa[acertos] = acertos_por_faixa.get(acertos, 0) + 1
                melhor_acerto = max(melhor_acerto, acertos)
                resultados_palpites.append({
                    'dezenas': p,
                    'soma': sum(p),
                    'acertos': acertos,
                    'premiado': acertos >= 11,
                    'faixa': premios_map.get(acertos, f'{acertos} pontos — Sem Prêmio'),
                })

            # Dados das âncoras usadas naquele backteste
            ancoras_usadas = ancoras_nums_snap
            acertos_ancoras = len(set(sorteio_real) & set(ancoras_usadas))

            relatorio.append({
                'concurso': concurso_num,
                'data': data_concurso,
                'sorteio_real': sorted(sorteio_real),
                'ancoras_usadas': sorted(ancoras_usadas),
                'acertos_ancoras_no_real': acertos_ancoras,
                'bollinger_info': {
                    'banda_inf': round(bollinger_snap['banda_inferior'], 1),
                    'banda_sup': round(bollinger_snap['banda_superior'], 1),
                    'media': round(bollinger_snap['media'], 1),
                    'soma_real': sum(sorteio_real),
                    'soma_dentro_bollinger': (
                        bollinger_snap['banda_inferior'] <= sum(sorteio_real) <= bollinger_snap['banda_superior']
                    ),
                },
                'palpites': resultados_palpites,
                'melhor_acerto': melhor_acerto,
                'acertos_por_faixa': acertos_por_faixa,
                'total_premiados': sum(acertos_por_faixa.values()),
            })

        # ── Resumo agregado do backtest
        total_palpites = sum(len(r['palpites']) for r in relatorio)
        total_premiados = sum(r['total_premiados'] for r in relatorio)
        dist_faixas = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
        for r in relatorio:
            for faixa, qtd in r['acertos_por_faixa'].items():
                dist_faixas[faixa] += qtd

        soma_dentro = sum(1 for r in relatorio if r['bollinger_info']['soma_dentro_bollinger'])

        return {
            'concursos': relatorio,
            'resumo': {
                'total_palpites': total_palpites,
                'total_premiados': total_premiados,
                'taxa_premiacao': round(total_premiados / max(total_palpites, 1) * 100, 1),
                'distribuicao_faixas': dist_faixas,
                'concursos_soma_dentro_bollinger': soma_dentro,
                'total_concursos': len(relatorio),
            }
        }

    # ════════════════════════════════════════════════════════════
    #  ANÁLISE COMPLETA (Todos os 3 Pilares)
    # ════════════════════════════════════════════════════════════

    def analise_completa(self):
        """
        Executa e retorna o resultado completo dos 3 Pilares:
        - Pilar 1: dezenas semana, quinzena, âncoras
        - Pilar 2: validação SMA-10 + Bollinger
        - Pilar 3: backtest dos últimos 5 concursos
        """
        if not self._carregado:
            return {'erro': 'Histórico não carregado'}

        # ── Pilar 1
        semana = self.calcular_dezenas_semana()
        quinzena = self.calcular_dezenas_quinzena()
        ancoras = self.calcular_ancoras(semana, quinzena)

        # ── Pilar 2
        ancoras_validadas = self.validar_sma10_ancoras(ancoras)
        bollinger = self.calcular_bollinger()

        # ── Pilar 3
        backtest = self.backtest(n_concursos=5)

        # ── Info do último concurso
        ultimo_row = self.df.iloc[0]
        ultimo = {
            'concurso': int(ultimo_row['Concurso']),
            'data': ultimo_row.get('Data', '-'),
            'dezenas': sorted(ultimo_row['Dezenas']),
            'soma': int(ultimo_row['Soma']),
        }

        return {
            'ultimo_concurso': ultimo,
            'pilar1': {
                'semana': semana,
                'quinzena': quinzena,
                'ancoras': ancoras,
                'n_overlap': sum(1 for a in ancoras if a['overlap']),
            },
            'pilar2': {
                'sma10': ancoras_validadas,
                'bollinger': bollinger,
                'ancoras_confirmadas': [a for a in ancoras_validadas if a['confianca'] == 'alta'],
                'ancoras_alerta': [a for a in ancoras_validadas if a['confianca'] == 'baixa'],
            },
            'pilar3': backtest,
        }
