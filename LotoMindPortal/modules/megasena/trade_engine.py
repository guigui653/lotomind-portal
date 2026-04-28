"""
MegaMind — Trade Engine (Motor Analítico Quantitativo) v2 — OTIMIZADO
=======================================================
Versao vetorizada com NumPy para alta performance.

Pilar 1 — Momentum e Ciclos
    • Trend Quinzenal  : dezenas nos ultimos 5 concursos
    • Consolidacao     : dezenas com > 2 ocorrencias nos ultimos 10
    • Filtro Quadrantes: max 3 numeros por quadrante

Pilar 2 — Indicadores de Trade
    • SMA-50           : frequencia media nos ultimos 50 concursos
    • Oversold         : dezenas mais atrasadas (reversao de tendencia)
    • Bollinger Soma   : valida soma no canal 150-220

Pilar 3 — Backtesting
    • Simula ultimos 10 concursos com cegueira temporal
    • Mapa Quadras, Quinas e Senas (Sharpe Ratio adaptado)
"""

import random
from collections import Counter

import numpy as np

QUADRANTES_DEF = {
    'Q1 (01-15)': list(range(1, 16)),
    'Q2 (16-30)': list(range(16, 31)),
    'Q3 (31-45)': list(range(31, 46)),
    'Q4 (46-60)': list(range(46, 61)),
}

PREMIOS_MAP = {
    6: 'SENA - PREMIO MAXIMO!',
    5: 'Quina',
    4: 'Quadra',
    3: 'Terno',
}


class MegaMindTradeEngine:
    """Motor analítico trade-quantitativo para Mega-Sena (60 dezenas, 6 sorteadas)."""

    UNIVERSO        = 60
    DEZENAS_SORTEIO = 6
    SOMA_MIN_BOL    = 150
    SOMA_MAX_BOL    = 220

    def __init__(self):
        self.df         = None
        self._carregado = False
        # Cache pre-computado
        self._matriz    = None  # shape (n_concursos, 60) — presenca de cada dezena
        self._somas_arr = None
        self._ciclos_vec= None

    # ════════════════════════════════════════════════════════════
    #  CARREGAMENTO E PRE-COMPUTACAO VETORIZADA
    # ════════════════════════════════════════════════════════════

    def carregar_historico(self, df):
        if df is None or df.empty:
            return
        self.df = df.sort_values('Concurso', ascending=False).reset_index(drop=True)
        self._carregado = True
        self._pre_computar()

    def _pre_computar(self):
        """Pre-computa a matriz binaria dezenas x concursos (vetorizado)."""
        n = len(self.df)
        # Matriz binaria: linha=concurso (mais recente=0), coluna=dezena (0-indexed => dezena-1)
        self._matriz = np.zeros((n, self.UNIVERSO), dtype=np.int8)
        for i, row in self.df.iterrows():
            for d in row['Dezenas']:
                self._matriz[i, d - 1] = 1
        self._somas_arr = self.df['Soma'].values.astype(float)
        # Ciclos: para cada dezena, quantos concursos desde a ultima aparicao
        # (percorre da linha 0 em diante ate encontrar 1)
        ciclos = np.zeros(self.UNIVERSO, dtype=int)
        for d_idx in range(self.UNIVERSO):
            col = self._matriz[:, d_idx]
            pos = np.argmax(col)  # primeira ocorrencia
            if col[pos] == 0:
                ciclos[d_idx] = len(col)
            else:
                ciclos[d_idx] = int(pos)
        self._ciclos_vec = ciclos

    # ════════════════════════════════════════════════════════════
    #  UTILITARIOS
    # ════════════════════════════════════════════════════════════

    def _get_quadrante(self, dezena):
        if dezena <= 15: return 'Q1 (01-15)'
        if dezena <= 30: return 'Q2 (16-30)'
        if dezena <= 45: return 'Q3 (31-45)'
        return 'Q4 (46-60)'

    def _distribuicao_quadrante(self, dezenas):
        dist = {q: [] for q in QUADRANTES_DEF}
        for d in dezenas:
            dist[self._get_quadrante(d)].append(d)
        return dist

    # ════════════════════════════════════════════════════════════
    #  PILAR 1 — MOMENTUM E CICLOS (vetorizado)
    # ════════════════════════════════════════════════════════════

    def calcular_trend_quinzenal(self, n=5, offset=0):
        """Top dezenas nos ultimos n concursos a partir do offset (para backtest)."""
        if self._matriz is None or len(self._matriz) <= offset:
            return []
        janela = self._matriz[offset:offset + n, :]
        freq = janela.sum(axis=0)  # shape (60,)
        # Apenas dezenas que apareceram ao menos 1 vez
        idxs = np.where(freq > 0)[0]
        resultado = sorted(
            [{'dezena': int(i+1), 'freq': int(freq[i]), 'max_freq': n,
              'pct': round(float(freq[i]) / n * 100, 1),
              'quadrante': self._get_quadrante(i+1)}
             for i in idxs],
            key=lambda x: x['freq'], reverse=True
        )
        return resultado

    def calcular_consolidacao_mensal(self, n=10, min_ocorrencias=2, offset=0):
        """Dezenas com > min_ocorrencias nos ultimos n concursos."""
        if self._matriz is None or len(self._matriz) <= offset:
            return []
        janela = self._matriz[offset:offset + n, :]
        freq = janela.sum(axis=0)
        idxs = np.where(freq >= min_ocorrencias)[0]
        resultado = sorted(
            [{'dezena': int(i+1), 'freq': int(freq[i]), 'max_freq': n,
              'pct': round(float(freq[i]) / n * 100, 1),
              'quadrante': self._get_quadrante(i+1)}
             for i in idxs],
            key=lambda x: x['freq'], reverse=True
        )
        return resultado

    # ════════════════════════════════════════════════════════════
    #  PILAR 2 — SMA-50 e BOLLINGER (vetorizado)
    # ════════════════════════════════════════════════════════════

    def calcular_sma50_todas(self, janela=50, offset=0):
        """Retorna SMA-50 para todas as 60 dezenas em um array shape (60,)."""
        if self._matriz is None:
            return np.zeros(self.UNIVERSO)
        n = min(janela, len(self._matriz) - offset)
        if n <= 0:
            return np.zeros(self.UNIVERSO)
        janela_mat = self._matriz[offset:offset + n, :]
        return janela_mat.mean(axis=0)  # frequencia media por dezena

    def calcular_sma50_dezena(self, dezena, janela=50, offset=0):
        """SMA-50 para uma dezena especifica."""
        smas = self.calcular_sma50_todas(janela, offset)
        idx = dezena - 1
        hist_total = self._matriz.shape[0]
        freq_hist = float(self._matriz[:, idx].mean()) if hist_total > 0 else 0.0
        sma_val = float(smas[idx])
        esperado = self.DEZENAS_SORTEIO / self.UNIVERSO
        if sma_val >= freq_hist * 1.1:
            status = 'acima_sma'
        elif sma_val < esperado * 0.7:
            status = 'oversold'
        else:
            status = 'neutro'
        return {
            'dezena': dezena,
            'freq_50': int(round(sma_val * min(janela, self._matriz.shape[0]))),
            'sma50': round(sma_val, 4),
            'media_hist': round(freq_hist, 4),
            'esperado': round(esperado, 4),
            'pct_sma50': round(sma_val * 100, 1),
            'pct_hist': round(freq_hist * 100, 1),
            'status': status,
        }

    def identificar_oversold(self, top_n=8, offset=0):
        """Top dezenas mais atrasadas (oversold) — candidatas a reversao."""
        smas = self.calcular_sma50_todas(offset=offset)
        esperado = self.DEZENAS_SORTEIO / self.UNIVERSO
        ciclos = self._ciclos_vec if offset == 0 else self._calcular_ciclos_offset(offset)

        resultado = []
        for idx in range(self.UNIVERSO):
            dezena = idx + 1
            sma_val = float(smas[idx])
            freq_hist = float(self._matriz[:, idx].mean())
            atraso = int(ciclos[idx])
            if sma_val < esperado * 0.7:
                status = 'oversold'
            elif sma_val >= freq_hist * 1.1:
                status = 'acima_sma'
            else:
                status = 'neutro'
            resultado.append({
                'dezena': dezena,
                'sma50': round(sma_val, 4),
                'media_hist': round(freq_hist, 4),
                'esperado': round(esperado, 4),
                'pct_sma50': round(sma_val * 100, 1),
                'pct_hist': round(freq_hist * 100, 1),
                'atraso': atraso,
                'status': status,
                'quadrante': self._get_quadrante(dezena),
            })

        # Ordenar: mais atrasadas primeiro, depois menor SMA
        resultado.sort(key=lambda x: (x['atraso'], -x['sma50']), reverse=True)
        return resultado[:top_n]

    def _calcular_ciclos_offset(self, offset):
        """Calcula ciclos a partir de um offset (para backtest)."""
        mat = self._matriz[offset:, :]
        if mat.shape[0] == 0:
            return np.zeros(self.UNIVERSO, dtype=int)
        ciclos = np.zeros(self.UNIVERSO, dtype=int)
        for d_idx in range(self.UNIVERSO):
            col = mat[:, d_idx]
            pos = np.argmax(col)
            ciclos[d_idx] = 0 if col[pos] == 1 else len(col)
        return ciclos

    def calcular_bollinger_soma(self, janela=50, desvios=2, offset=0):
        """Bandas de Bollinger sobre a soma das dezenas (50 concursos por padrao)."""
        if self._somas_arr is None or len(self._somas_arr) <= offset:
            return None
        n = min(janela, len(self._somas_arr) - offset)
        if n < 2:
            return None

        somas = self._somas_arr[offset:offset + n]
        somas_crono = list(reversed(somas.tolist()))

        concursos = (self.df['Concurso'].values[offset:offset + n]).tolist()
        concursos_crono = list(reversed(concursos))

        media = float(np.mean(somas))
        desvio = float(np.std(somas, ddof=1))

        banda_sup = round(min(media + desvios * desvio, self.SOMA_MAX_BOL), 2)
        banda_inf = round(max(media - desvios * desvio, self.SOMA_MIN_BOL), 2)

        ultima_soma = float(somas[0])
        if ultima_soma > banda_sup:
            zona = 'ACIMA'; zona_emoji = 'SOBRC'
        elif ultima_soma < banda_inf:
            zona = 'ABAIXO'; zona_emoji = 'SOBRV'
        else:
            zona = 'DENTRO DO CANAL'; zona_emoji = 'OK'

        return {
            'media': round(media, 2),
            'desvio': round(desvio, 2),
            'banda_superior': banda_sup,
            'banda_inferior': banda_inf,
            'ultima_soma': int(ultima_soma),
            'zona': zona,
            'zona_emoji': zona_emoji,
            'somas_historico': [int(s) for s in somas_crono],
            'concursos_historico': [int(c) for c in concursos_crono],
            'largura_banda': round(banda_sup - banda_inf, 2),
            'janela': n,
        }

    # ════════════════════════════════════════════════════════════
    #  GERADOR DE PALPITES
    # ════════════════════════════════════════════════════════════

    def gerar_palpites(self, qtd=5, max_tentativas=1000, offset=0):
        """Gera palpites respeitando Bollinger, quadrantes (max 3) e oversold."""
        if not self._carregado:
            return []

        bol = self.calcular_bollinger_soma(offset=offset)
        if not bol:
            return []

        banda_inf = bol['banda_inferior']
        banda_sup = bol['banda_superior']

        # Scores: trend quinzenal * 3 + consolidacao * 2 + oversold bonus
        smas = self.calcular_sma50_todas(offset=offset)
        ciclos = self._ciclos_vec if offset == 0 else self._calcular_ciclos_offset(offset)
        esperado = self.DEZENAS_SORTEIO / self.UNIVERSO

        trend = self.calcular_trend_quinzenal(offset=offset)
        consol = self.calcular_consolidacao_mensal(offset=offset)

        scores = np.zeros(self.UNIVERSO)
        for t in trend:
            scores[t['dezena'] - 1] += t['freq'] * 3
        for c in consol:
            scores[c['dezena'] - 1] += c['freq'] * 2
        # bonus oversold (SMA muito abaixo do esperado)
        oversold_mask = smas < esperado * 0.7
        scores[oversold_mask] += 5

        # Identificar oversold nums
        oversold_idxs = set(np.where(oversold_mask)[0].tolist())
        oversold_nums = {idx + 1 for idx in oversold_idxs}

        universo_arr = np.arange(1, self.UNIVERSO + 1)
        palpites = []
        vistos = set()

        for _ in range(max_tentativas):
            if len(palpites) >= qtd:
                break

            # Selecao ponderada sem repeticao respeitando quadrante max=3
            contagem_quad = {'Q1 (01-15)': 0, 'Q2 (16-30)': 0, 'Q3 (31-45)': 0, 'Q4 (46-60)': 0}
            escolhidos = []

            # Candidatos ordenados por score decrescente + aleatoriedade
            noise = np.random.uniform(0, 0.5, self.UNIVERSO)
            order = np.argsort(-(scores + noise))

            for idx in order:
                dezena = int(idx + 1)
                q = self._get_quadrante(dezena)
                if contagem_quad[q] < 3:
                    escolhidos.append(dezena)
                    contagem_quad[q] += 1
                if len(escolhidos) >= self.DEZENAS_SORTEIO:
                    break

            if len(escolhidos) < self.DEZENAS_SORTEIO:
                continue

            soma = sum(escolhidos)
            if not (banda_inf <= soma <= banda_sup):
                continue

            chave = tuple(sorted(escolhidos))
            if chave in vistos:
                continue
            vistos.add(chave)

            dist_quad = self._distribuicao_quadrante(escolhidos)
            ov_incl = sorted([d for d in escolhidos if d in oversold_nums])

            palpites.append({
                'dezenas': sorted(escolhidos),
                'soma': soma,
                'dentro_bollinger': True,
                'distribuicao_quadrantes': {q: v for q, v in dist_quad.items()},
                'oversold_incluidos': ov_incl,
                'qtd_oversold': len(ov_incl),
                'sma_medio': round(float(np.mean([smas[d-1] for d in escolhidos])), 4),
            })

        return palpites

    # ════════════════════════════════════════════════════════════
    #  PILAR 3 — BACKTESTING (10 concursos — vetorizado)
    # ════════════════════════════════════════════════════════════

    def backtest(self, n_concursos=10):
        """
        Backtest com cegueira temporal usando offset na matriz vetorizada.
        Muito mais rapido que criar instancias temporarias.
        """
        if not self._carregado or len(self.df) < n_concursos + 15:
            return {'concursos': [], 'resumo': {}}

        relatorio = []
        acertos_dist = {3: 0, 4: 0, 5: 0, 6: 0}

        for i in range(n_concursos):
            row_alvo = self.df.iloc[i]
            sorteio_real = set(row_alvo['Dezenas'])
            num_concurso = int(row_alvo['Concurso'])
            data_conc = row_alvo.get('Data', '-')
            soma_real = int(row_alvo['Soma'])

            offset = i + 1  # usa dados a partir do concurso seguinte
            if offset >= len(self.df) - 10:
                continue

            bol_snap = self.calcular_bollinger_soma(offset=offset)
            if not bol_snap:
                continue

            # Gera 2 palpites com offset
            palpites_bt = self.gerar_palpites(qtd=2, max_tentativas=300, offset=offset)
            if not palpites_bt:
                # fallback: gerar sem restricoes de bollinger (dados insuficientes)
                palpites_bt = [{'dezenas': random.sample(range(1,61), 6), 'soma': 0,
                                'oversold_incluidos': [], 'distribuicao_quadrantes': {}}]

            resultados = []
            for p in palpites_bt:
                ac = len(set(p['dezenas']) & sorteio_real)
                if ac >= 3:
                    acertos_dist[ac] = acertos_dist.get(ac, 0) + 1
                resultados.append({
                    'dezenas': p['dezenas'],
                    'soma': p['soma'],
                    'acertos': ac,
                    'premiado': ac >= 4,
                    'faixa': PREMIOS_MAP.get(ac, str(ac) + ' pontos'),
                    'distribuicao_quadrantes': p.get('distribuicao_quadrantes', {}),
                    'oversold_incluidos': p.get('oversold_incluidos', []),
                })

            trend_offset = self.calcular_trend_quinzenal(offset=offset)
            trend_nums = [t['dezena'] for t in trend_offset[:10]]
            acertos_trend = len(sorteio_real & set(trend_nums))
            dentro_bol = bol_snap['banda_inferior'] <= soma_real <= bol_snap['banda_superior']

            relatorio.append({
                'concurso': num_concurso,
                'data': data_conc,
                'sorteio_real': sorted(sorteio_real),
                'soma_real': soma_real,
                'bollinger': {
                    'banda_inf': round(bol_snap['banda_inferior'], 1),
                    'banda_sup': round(bol_snap['banda_superior'], 1),
                    'media': round(bol_snap['media'], 1),
                    'soma_dentro': dentro_bol,
                },
                'trend_nums_usados': trend_nums,
                'acertos_trend_no_real': acertos_trend,
                'palpites': resultados,
                'melhor_acerto': max((r['acertos'] for r in resultados), default=0),
            })

        total_palpites = sum(len(r['palpites']) for r in relatorio)
        total_premiados = acertos_dist.get(4, 0) + acertos_dist.get(5, 0) + acertos_dist.get(6, 0)
        sharpe = round(total_premiados / max(total_palpites, 1) * 100, 2)
        somas_dentro = sum(1 for r in relatorio if r['bollinger']['soma_dentro'])

        return {
            'concursos': relatorio,
            'resumo': {
                'total_palpites': total_palpites,
                'total_premiados': total_premiados,
                'quadras': acertos_dist.get(4, 0),
                'quinas': acertos_dist.get(5, 0),
                'senas': acertos_dist.get(6, 0),
                'ternos': acertos_dist.get(3, 0),
                'taxa_premiacao': round(total_premiados / max(total_palpites, 1) * 100, 1),
                'sharpe_ratio': sharpe,
                'somas_dentro_bollinger': somas_dentro,
                'total_concursos': len(relatorio),
                'distribuicao_acertos': {str(k): v for k, v in acertos_dist.items()},
            }
        }

    # ════════════════════════════════════════════════════════════
    #  ANALISE COMPLETA
    # ════════════════════════════════════════════════════════════

    def analise_completa(self):
        if not self._carregado:
            return {'erro': 'Historico nao carregado'}

        # Pilar 1
        trend = self.calcular_trend_quinzenal()
        consol = self.calcular_consolidacao_mensal()

        # Pilar 2
        oversold = self.identificar_oversold(top_n=8)
        bollinger = self.calcular_bollinger_soma()

        # Pilar 3
        backtest = self.backtest(n_concursos=10)

        # Info ultimo concurso
        row = self.df.iloc[0]
        dezenas_ult = sorted(row['Dezenas'])
        ultimo = {
            'concurso': int(row['Concurso']),
            'data': row.get('Data', '-'),
            'dezenas': dezenas_ult,
            'soma': int(row['Soma']),
            'quadrantes': self._distribuicao_quadrante(dezenas_ult),
        }

        return {
            'ultimo_concurso': ultimo,
            'pilar1': {
                'trend_quinzenal': trend,
                'consolidacao_mensal': consol,
                'n_trend': len(trend),
                'n_consolidados': len(consol),
            },
            'pilar2': {
                'oversold': oversold,
                'bollinger': bollinger,
            },
            'pilar3': backtest,
        }
