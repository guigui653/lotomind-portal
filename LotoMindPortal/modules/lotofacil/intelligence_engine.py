"""
LotoMind Portal — Motor de Inteligência Lotofácil v2.0
========================================================
8 Diretrizes Técnicas Avançadas para análise estatística
e probabilística do espaço amostral C(25,15).

Diretrizes:
  1. Distribuição Hipergeométrica Crítica (11-15 pontos)
  2. Entropia de Shannon (gaps e sequências)
  3. Resíduos de Pearson (χ²) — regressão à média
  4. Filtro de Simetria / Moldura do Volante
  5. Ciclos de Fechamento
  6. Matriz de Coocorrência (Pares de Ouro)
  7. Proporção Áurea de Paridade e Primos
  8. Filtro de Soma (166–220)
"""

import math
import random
from collections import Counter
import numpy as np
from scipy import stats


class LotofacilIntelligenceEngine:
    """Motor de Inteligência avançado para Lotofácil (25 dezenas, 15 sorteadas)."""

    UNIVERSO = 25
    DEZENAS_SORTEIO = 15
    PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}

    # Moldura do volante da Lotofácil (5x5):
    # [01][02][03][04][05]
    # [06]            [10]
    # [11]            [15]
    # [16]            [20]
    # [21][22][23][24][25]
    MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    MIOLO = {7, 8, 9, 12, 13, 14, 17, 18, 19}

    def __init__(self):
        self.historico = None
        self.frequencias = None
        self.total_jogos = 0
        self.entropia_media = 0.0
        self.chi2_resultado = {}
        self.benford = {}
        self.coocorrencia = None
        self.ciclos = {}
        self.decaimento = {}
        self.rolling = {}
        self.residuos = {}
        self.moldura_stats = {}

    # ════════════════════════════════════════════════════════════
    #  CARREGAMENTO E PREPARAÇÃO
    # ════════════════════════════════════════════════════════════

    def carregar_historico(self, df):
        """Carrega DataFrame e dispara todos os cálculos."""
        if df is None or df.empty:
            return

        self.historico = df
        self.total_jogos = len(df)
        self._calcular_frequencias()
        self._calcular_chi2()
        self._calcular_coocorrencia()
        self._calcular_ciclos_fechamento()
        self._calcular_decaimento()
        self._calcular_rolling_windows()
        self._calcular_moldura_stats()
        self._calcular_entropia_media()
        self._calcular_benford()

    def _calcular_frequencias(self):
        """Frequência absoluta de cada dezena no histórico."""
        todas = [n for sub in self.historico['Dezenas'] for n in sub]
        self.frequencias = Counter(todas)

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 1: DISTRIBUIÇÃO HIPERGEOMÉTRICA CRÍTICA
    # ════════════════════════════════════════════════════════════

    def probabilidade_hipergeometrica(self, num_quentes=15):
        """
        Calcula P(X=k) para k=11..15 acertos, dado que o jogo
        contém 'num_quentes' dezenas da Zona de Alta Frequência.
        Retorna distribuição + zona de retorno.
        """
        N = self.UNIVERSO       # população total (25)
        K = num_quentes         # nº de "quentes" na população
        n = self.DEZENAS_SORTEIO  # sorteadas por concurso (15)

        distribuicao = {}
        for k in range(max(0, n + K - N), min(n, K) + 1):
            prob = stats.hypergeom.pmf(k, N, K, n)
            distribuicao[k] = round(float(prob), 6)

        pico_k = max(distribuicao, key=distribuicao.get)

        # Zona de Retorno: 11-12 pontos (premiação secundária)
        zona_retorno = {k: v for k, v in distribuicao.items() if 11 <= k <= 12}
        prob_zona_retorno = sum(zona_retorno.values())

        # Zona Premium: 13-15 pontos
        zona_premium = {k: v for k, v in distribuicao.items() if 13 <= k <= 15}
        prob_zona_premium = sum(zona_premium.values())

        return {
            'distribuicao': distribuicao,
            'pico_k': pico_k,
            'pico_probabilidade': distribuicao[pico_k],
            'zona_retorno': zona_retorno,
            'prob_zona_retorno': round(prob_zona_retorno, 6),
            'zona_premium': zona_premium,
            'prob_zona_premium': round(prob_zona_premium, 6),
        }

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 2: ENTROPIA DE SHANNON (GAPS E SEQUÊNCIAS)
    # ════════════════════════════════════════════════════════════

    def calcular_entropia(self, jogo):
        """
        Entropia de Shannon do jogo baseada nas frequências históricas.
        Penaliza gaps excessivos (>4 números consecutivos ausentes)
        e sequências longas (>4 números em sequência).
        """
        total = sum(self.frequencias.values())
        if total == 0:
            return {'entropia': 0, 'aprovado': False, 'gaps': 0, 'max_sequencia': 0}

        probs = []
        for n in jogo:
            freq = self.frequencias.get(n, 1)
            p = freq / total
            probs.append(p)

        # Entropia de Shannon
        entropia = -sum(p * math.log2(p) for p in probs if p > 0)

        # Análise de gaps (buracos entre números)
        jogo_sorted = sorted(jogo)
        gaps = [jogo_sorted[i+1] - jogo_sorted[i] for i in range(len(jogo_sorted) - 1)]
        max_gap = max(gaps) if gaps else 0
        gaps_excessivos = sum(1 for g in gaps if g > 4)

        # Análise de sequências longas
        max_seq = 1
        seq_atual = 1
        for i in range(1, len(jogo_sorted)):
            if jogo_sorted[i] == jogo_sorted[i-1] + 1:
                seq_atual += 1
                max_seq = max(max_seq, seq_atual)
            else:
                seq_atual = 1

        # Aprovado se: entropia >= média, gap máx <= 4, sequência máx <= 4
        aprovado = (
            entropia >= self.entropia_media * 0.95 and
            max_gap <= 5 and
            max_seq <= 4
        )

        return {
            'entropia': round(entropia, 3),
            'media_historica': round(self.entropia_media, 3),
            'aprovado': aprovado,
            'max_gap': max_gap,
            'gaps_excessivos': gaps_excessivos,
            'max_sequencia': max_seq,
        }

    def _calcular_entropia_media(self):
        """Calcula entropia média histórica."""
        total = sum(self.frequencias.values())
        if total == 0:
            self.entropia_media = 0
            return

        entropias = []
        for _, row in self.historico.iterrows():
            probs = []
            for n in row['Dezenas']:
                freq = self.frequencias.get(n, 1)
                p = freq / total
                probs.append(p)
            h = -sum(p * math.log2(p) for p in probs if p > 0)
            entropias.append(h)

        self.entropia_media = np.mean(entropias) if entropias else 0

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 3: RESÍDUOS DE PEARSON (χ²)
    # ════════════════════════════════════════════════════════════

    def _calcular_chi2(self):
        """Teste chi-quadrado das frequências observadas vs esperadas."""
        esperado = self.total_jogos * self.DEZENAS_SORTEIO / self.UNIVERSO
        observados = [self.frequencias.get(d, 0) for d in range(1, self.UNIVERSO + 1)]
        esperados = [esperado] * self.UNIVERSO

        chi2, p_valor = stats.chisquare(observados, f_exp=esperados)

        # Resíduos de Pearson individuais
        residuos = {}
        for d in range(1, self.UNIVERSO + 1):
            obs = self.frequencias.get(d, 0)
            r = (obs - esperado) / math.sqrt(esperado) if esperado > 0 else 0
            residuos[d] = round(r, 3)

        self.chi2_resultado = {
            'chi2': round(float(chi2), 1),
            'p_valor': round(float(p_valor), 6),
        }
        self.residuos = residuos

    def calcular_maturacao(self):
        """
        Identifica dezenas com viés de maturação (regressão à média).
        Dezenas muito abaixo da média tendem a retornar.
        """
        esperado = self.total_jogos * self.DEZENAS_SORTEIO / self.UNIVERSO
        maturados = []

        # Frequência recente (últimos 50 concursos)
        recentes = self.historico.head(50)
        freq_recente = Counter([n for sub in recentes['Dezenas'] for n in sub])
        esperado_recente = len(recentes) * self.DEZENAS_SORTEIO / self.UNIVERSO

        for d in range(1, self.UNIVERSO + 1):
            obs = self.frequencias.get(d, 0)
            obs_rec = freq_recente.get(d, 0)
            residuo = self.residuos.get(d, 0)

            # Viés de maturação: desvio entre freq recente e histórica
            maturacao = round((esperado_recente - obs_rec) / max(esperado_recente, 1), 3)

            if maturacao > 0.3:
                classificacao = '🔴 Atrasada (alta maturação)'
            elif maturacao > 0:
                classificacao = '🟡 Levemente atrasada'
            elif maturacao < -0.3:
                classificacao = '🟢 Acima da média'
            else:
                classificacao = '⚪ Normal'

            maturados.append({
                'dezena': d,
                'residuo_pearson': residuo,
                'freq_historica': obs,
                'freq_recente': obs_rec,
                'maturacao': maturacao,
                'classificacao': classificacao,
            })

        return sorted(maturados, key=lambda x: x['maturacao'], reverse=True)

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 4: FILTRO DE SIMETRIA / MOLDURA DO VOLANTE
    # ════════════════════════════════════════════════════════════

    def _calcular_moldura_stats(self):
        """Estatísticas históricas de moldura vs miolo."""
        moldura_counts = []
        for _, row in self.historico.iterrows():
            jogo_set = set(row['Dezenas'])
            moldura_count = len(jogo_set & self.MOLDURA)
            moldura_counts.append(moldura_count)

        self.moldura_stats = {
            'media': round(np.mean(moldura_counts), 1),
            'min': int(np.min(moldura_counts)),
            'max': int(np.max(moldura_counts)),
            'faixa_ideal': '8 a 11',
        }

    def validar_moldura(self, jogo):
        """
        Verifica se o jogo tem 8-11 números na moldura do volante.
        Retorna status de aprovação e detalhes.
        """
        jogo_set = set(jogo)
        na_moldura = jogo_set & self.MOLDURA
        no_miolo = jogo_set & self.MIOLO

        aprovado = 8 <= len(na_moldura) <= 11

        return {
            'moldura': sorted(na_moldura),
            'miolo': sorted(no_miolo),
            'qtd_moldura': len(na_moldura),
            'qtd_miolo': len(no_miolo),
            'aprovado': aprovado,
            'media_historica': self.moldura_stats.get('media', 0),
        }

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 5: CLUSTERIZAÇÃO EUCLIDIANA
    # ════════════════════════════════════════════════════════════

    def analisar_clusterizacao(self, jogo):
        """
        Calcula o Desvio Padrão (σ) do jogo.
        Para Lotofácil (alta densidade, 15 de 25), espera-se um σ baixo e estável
        para refletir a ocupação massiva do volante (sem grandes gaps não mapeados).
        """
        sigma = float(np.std(jogo))

        # Na Lotofácil típica: a média agrupada gera um σ médio de ~7.2 a 7.5
        # Valores aceitos focam na densidade
        aprovado = 6.5 <= sigma <= 8.0

        return {
            'sigma': round(sigma, 3),
            'aprovado': aprovado,
            'faixa_ideal': '6.5 a 8.0',
            'classificacao': (
                '✅ Ocupação Massiva e Estável' if aprovado
                else ('⚠️ Muito Agrupado' if sigma < 6.5 else '⚠️ Dispersão Atípica')
            ),
        }

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 6: LEI DE BENFORD
    # ════════════════════════════════════════════════════════════

    def _calcular_benford(self):
        """Calcula distribuição de Benford baseada no primeiro dígito."""
        # Dezenas 01 a 25 -> Dígitos 1 e 2 dominam (de 10-19 e 20-25) e 0 (01-09)
        # Lotofácil tem limite curto, então a adaptação do primeiro dígito
        # considerando d in [0, 1, 2]. Benford tradicional adapta log10(1 + 1/d)
        self.benford_esperado = {
            # Probabilidade teórica de primeiros dígitos num limite estrito de 25
            1: round(math.log10(1 + 1 / 1), 4),
            2: round(math.log10(1 + 1 / 2), 4),
            3: round(math.log10(1 + 1 / 3), 4),
        }
        
        if self.historico is None:
            return

        recentes = self.historico.head(100)
        primeiros_digitos = []
        for _, row in recentes.iterrows():
            for d in row['Dezenas']:
                primeiro = int(str(d)[0])
                if primeiro in [1, 2, 3]:
                    primeiros_digitos.append(primeiro)

        total = len(primeiros_digitos)
        contagem = Counter(primeiros_digitos)

        self.benford = {}
        for d in [1, 2, 3]:
            self.benford[d] = round(contagem.get(d, 0) / max(total, 1), 4)

    def analise_benford(self):
        """Compara a conformidade com a distribuição esperada."""
        desvio_total = sum(abs(self.benford.get(d, 0) - self.benford_esperado.get(d, 0)) for d in [1, 2, 3])
        conformidade = max(0, 1.0 - desvio_total)
        return {
            'distribuicao_real': {d: round(v * 100, 2) for d, v in self.benford.items()},
            'distribuicao_esperada': {d: round(v * 100, 2) for d, v in self.benford_esperado.items()},
            'conformidade': round(conformidade * 100, 1),
            'aprovado': conformidade >= 0.70,
        }

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 7: CICLOS DE FECHAMENTO
    # ════════════════════════════════════════════════════════════

    def _calcular_ciclos_fechamento(self):
        """
        Monitora ciclos de fechamento: quando todas as 25 dezenas
        já saíram pelo menos uma vez. Identifica dezenas que faltam
        para fechar o ciclo atual.
        """
        apareceu = set()
        ciclo_jogos = 0
        ciclos_completos = 0
        historico_ciclos = []

        for _, row in self.historico.sort_values('Concurso').iterrows():
            for d in row['Dezenas']:
                apareceu.add(d)
            ciclo_jogos += 1

            if len(apareceu) == self.UNIVERSO:
                historico_ciclos.append(ciclo_jogos)
                apareceu.clear()
                ciclo_jogos = 0
                ciclos_completos += 1

        # Dezenas que faltam no ciclo atual (do mais recente para trás)
        apareceu_recente = set()
        jogos_no_ciclo = 0
        for _, row in self.historico.iterrows():
            for d in row['Dezenas']:
                apareceu_recente.add(d)
            jogos_no_ciclo += 1
            if len(apareceu_recente) == self.UNIVERSO:
                break

        faltam = set(range(1, self.UNIVERSO + 1)) - apareceu_recente
        # Se o ciclo já fechou recentemente, recalcular a partir de concursos recentes
        if not faltam:
            apareceu_recente = set()
            jogos_no_ciclo = 0
            for _, row in self.historico.head(20).iterrows():
                for d in row['Dezenas']:
                    apareceu_recente.add(d)
                jogos_no_ciclo += 1
            faltam = set(range(1, self.UNIVERSO + 1)) - apareceu_recente

        media_ciclo = round(np.mean(historico_ciclos), 1) if historico_ciclos else 0

        self.ciclos = {
            'faltam': sorted(faltam),
            'apareceu': sorted(apareceu_recente),
            'jogos_no_ciclo': jogos_no_ciclo,
            'ciclos_completos': ciclos_completos,
            'media_ciclo': media_ciclo,
            'progresso': round(len(apareceu_recente) / self.UNIVERSO * 100, 1),
        }

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 8: MATRIZ DE COOCORRÊNCIA (PARES E TRIOS INTELIGENTES)
    # ════════════════════════════════════════════════════════════

    def _calcular_coocorrencia(self):
        """Gera a matriz 25×25 de coocorrência de pares."""
        self.coocorrencia = np.zeros((self.UNIVERSO, self.UNIVERSO), dtype=int)

        for _, row in self.historico.iterrows():
            dezenas = row['Dezenas']
            for i in range(len(dezenas)):
                for j in range(i + 1, len(dezenas)):
                    a, b = dezenas[i] - 1, dezenas[j] - 1
                    self.coocorrencia[a][b] += 1
                    self.coocorrencia[b][a] += 1

    def pares_de_ouro(self, top_n=10):
        """
        Retorna os top N pares de dezenas que mais saem juntas
        e os top N pares que menos saem juntas.
        """
        pares_pos = []
        pares_neg = []

        for i in range(self.UNIVERSO):
            for j in range(i + 1, self.UNIVERSO):
                count = int(self.coocorrencia[i][j])
                pares_pos.append({'par': (i + 1, j + 1), 'coocorrencias': count})
                pares_neg.append({'par': (i + 1, j + 1), 'coocorrencias': count})

        pares_pos = sorted(pares_pos, key=lambda x: x['coocorrencias'], reverse=True)[:top_n]
        pares_neg = sorted(pares_neg, key=lambda x: x['coocorrencias'])[:top_n]

        return pares_pos, pares_neg

    def trios_de_ouro(self, top_n=5):
        """Calcula os trios de ouro usando freqüência conjunta (pseudo-correlação > 0.7)."""
        trios = Counter()
        for _, row in self.historico.iterrows():
            dezenas = sorted(row['Dezenas'])
            for i in range(len(dezenas)):
                for j in range(i + 1, len(dezenas)):
                    for k in range(j + 1, len(dezenas)):
                        trios[(dezenas[i], dezenas[j], dezenas[k])] += 1
        
        # Correlação teórica esperada em N jogos = N * (15/25) * (14/24) * (13/23)
        esperado_trio = self.total_jogos * (15/25) * (14/24) * (13/23)
        res_trios = []
        for trio, count in trios.most_common(top_n * 3):
            corr = count / esperado_trio
            if corr > 1.2: # > 20% acima do esperado
                res_trios.append({'trio': list(trio), 'coocorrencias': count, 'correlacao_idx': round(corr, 2)})
                if len(res_trios) >= top_n:
                    break
        return res_trios

    def score_coocorrencia(self, jogo):
        """Score de coocorrência: soma normalizada dos pares do jogo."""
        if self.coocorrencia is None:
            return 0

        total = 0
        pares_count = 0
        for i in range(len(jogo)):
            for j in range(i + 1, len(jogo)):
                a, b = jogo[i] - 1, jogo[j] - 1
                total += self.coocorrencia[a][b]
                pares_count += 1

        media_global = np.mean(self.coocorrencia[self.coocorrencia > 0]) if np.any(self.coocorrencia > 0) else 1
        score = round(total / max(pares_count, 1) / max(media_global, 1) * 10, 2)
        return min(score, 15)

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 9: PROPORÇÃO ÁUREA DE PARIDADE E PRIMOS
    # ════════════════════════════════════════════════════════════

    def validar_paridade_primos(self, jogo):
        """
        Verifica restrições:
        - 7 a 9 ímpares
        - 5 a 6 primos
        """
        pares = [x for x in jogo if x % 2 == 0]
        impares = [x for x in jogo if x % 2 != 0]
        primos = [x for x in jogo if x in self.PRIMOS]

        paridade_ok = 7 <= len(impares) <= 9
        primos_ok = 5 <= len(primos) <= 6
        aprovado = paridade_ok and primos_ok

        return {
            'pares': len(pares),
            'impares': len(impares),
            'primos': len(primos),
            'lista_primos': sorted(primos),
            'paridade_ok': paridade_ok,
            'primos_ok': primos_ok,
            'aprovado': aprovado,
        }

    # ════════════════════════════════════════════════════════════
    #  DIRETRIZ 10: FILTRO DE SOMA (166–220)
    # ════════════════════════════════════════════════════════════

    def validar_soma(self, jogo):
        """Verifica se a soma total está entre 166 e 220."""
        soma = sum(jogo)
        aprovado = 166 <= soma <= 220
        return {
            'soma': soma,
            'faixa': '166 a 220',
            'aprovado': aprovado,
        }

    # ════════════════════════════════════════════════════════════
    #  ROLLING WINDOWS
    # ════════════════════════════════════════════════════════════

    def _calcular_rolling_windows(self, janela=100):
        """Tendências de curto/médio prazo via janela deslizante."""
        recentes = self.historico.head(janela)
        freq_recente = Counter([n for sub in recentes['Dezenas'] for n in sub])

        esperado_recente = len(recentes) * self.DEZENAS_SORTEIO / self.UNIVERSO
        total_hist = self.total_jogos * self.DEZENAS_SORTEIO / self.UNIVERSO

        subindo = []
        caindo = []

        for d in range(1, self.UNIVERSO + 1):
            fh = self.frequencias.get(d, 0) / max(total_hist, 1)
            fr = freq_recente.get(d, 0) / max(esperado_recente, 1)

            if fr > fh * 1.15:
                subindo.append(d)
            elif fr < fh * 0.85:
                caindo.append(d)

        self.rolling = {
            'janela': len(recentes),
            'dezenas_subindo': sorted(subindo),
            'dezenas_caindo': sorted(caindo),
        }

    # ════════════════════════════════════════════════════════════
    #  DECAIMENTO TEMPORAL
    # ════════════════════════════════════════════════════════════

    def _calcular_decaimento(self):
        """Atraso de cada dezena e peso exponencial."""
        atrasos = {}
        for d in range(1, self.UNIVERSO + 1):
            atraso = 0
            for _, row in self.historico.iterrows():
                if d in row['Dezenas']:
                    break
                atraso += 1
            atrasos[d] = atraso

        media = np.mean(list(atrasos.values()))
        resultado = []
        for d, atraso in atrasos.items():
            peso = round(1.0 + (atraso / max(media, 1)) * 0.5, 2)
            if atraso > media * 2:
                zona = '🔴 Crítico'
            elif atraso > media:
                zona = '🟡 Alerta'
            else:
                zona = '🟢 Normal'

            resultado.append({
                'dezena': d,
                'atraso': atraso,
                'peso': peso,
                'zona': zona,
            })

        self.decaimento = sorted(resultado, key=lambda x: x['atraso'], reverse=True)

    # ════════════════════════════════════════════════════════════
    #  PIPELINE COMPLETO DE ANÁLISE
    # ════════════════════════════════════════════════════════════

    def analise_completa_jogo(self, jogo):
        """
        Aplica todas as 8 diretrizes a um jogo.
        Retorna score final, classificação e detalhes.
        """
        if self.historico is None:
            return {'erro': 'Histórico não carregado'}

        detalhes = {}
        score = 0
        aprovadas = 0
        total_dir = 8

        # 1. Hipergeométrica
        quentes = [n for n, _ in self.frequencias.most_common(15)]
        acertos_quentes = len(set(jogo) & set(quentes))
        hiper = self.probabilidade_hipergeometrica()
        prob = hiper['distribuicao'].get(acertos_quentes, 0)
        na_zona_retorno = 11 <= acertos_quentes <= 12
        hiper_score = 15 if na_zona_retorno else (10 if prob > 0.1 else 5)
        if na_zona_retorno or prob > 0.05:
            aprovadas += 1
        detalhes['hipergeometrica'] = {
            'acertos_quentes': acertos_quentes,
            'probabilidade': round(prob, 4),
            'na_zona_retorno': na_zona_retorno,
            'score': hiper_score,
            'aprovado': na_zona_retorno or prob > 0.05,
        }
        score += hiper_score

        # 2. Entropia
        entropia = self.calcular_entropia(jogo)
        e_score = 12 if entropia['aprovado'] else 4
        if entropia['aprovado']:
            aprovadas += 1
        detalhes['entropia'] = entropia
        detalhes['entropia']['score'] = e_score
        score += e_score

        # 3. Pearson / Maturação
        nums_maturados = [d['dezena'] for d in self.calcular_maturacao()[:8]]
        acertos_mat = len(set(jogo) & set(nums_maturados))
        p_score = min(acertos_mat * 3, 12)
        pearson_aprovado = acertos_mat >= 3
        if pearson_aprovado:
            aprovadas += 1
        detalhes['pearson'] = {
            'acertos_maturados': acertos_mat,
            'score': p_score,
            'aprovado': pearson_aprovado,
        }
        score += p_score

        # 4. Moldura
        moldura = self.validar_moldura(jogo)
        m_score = 13 if moldura['aprovado'] else 4
        if moldura['aprovado']:
            aprovadas += 1
        detalhes['moldura'] = moldura
        detalhes['moldura']['score'] = m_score
        score += m_score

        # 5. Clusterização Euclidiana
        cluster = self.analisar_clusterizacao(jogo)
        c_score_eucl = 10 if cluster['aprovado'] else 4
        if cluster['aprovado']:
            aprovadas += 1
        detalhes['clusterizacao'] = cluster
        detalhes['clusterizacao']['score'] = c_score_eucl
        score += c_score_eucl

        # 6. Lei de Benford
        benford = self.analise_benford()
        b_score = 10 if benford['aprovado'] else 5
        if benford['aprovado']:
            aprovadas += 1
        detalhes['benford'] = benford
        detalhes['benford']['score'] = b_score
        score += b_score

        # 7. Ciclos de Fechamento
        faltam = set(self.ciclos.get('faltam', []))
        acertos_ciclo = len(set(jogo) & faltam)
        c_score = min(acertos_ciclo * 4, 12) if faltam else 8
        ciclo_aprovado = acertos_ciclo >= 2 if faltam else True
        if ciclo_aprovado:
            aprovadas += 1
        detalhes['ciclos'] = {
            'dezenas_faltando': sorted(faltam),
            'acertos_no_ciclo': acertos_ciclo,
            'score': c_score,
            'aprovado': ciclo_aprovado,
        }
        score += c_score

        # 8. Coocorrência (Pares e Trios)
        cooc_score = self.score_coocorrencia(jogo)
        cooc_aprovado = cooc_score >= 7
        if cooc_aprovado:
            aprovadas += 1
        detalhes['coocorrencia'] = {
            'score': round(cooc_score, 1),
            'aprovado': cooc_aprovado,
        }
        score += cooc_score

        # 9. Paridade / Primos
        pp = self.validar_paridade_primos(jogo)
        pp_score = 12 if pp['aprovado'] else (6 if pp['paridade_ok'] or pp['primos_ok'] else 2)
        if pp['aprovado']:
            aprovadas += 1
        detalhes['paridade_primos'] = pp
        detalhes['paridade_primos']['score'] = pp_score
        score += pp_score

        # 10. Soma
        soma = self.validar_soma(jogo)
        s_score = 10 if soma['aprovado'] else 2
        if soma['aprovado']:
            aprovadas += 1
        detalhes['soma'] = soma
        detalhes['soma']['score'] = s_score
        score += s_score

        # Score final (normalizado para 100)
        max_score = 15 + 12 + 12 + 13 + 10 + 10 + 12 + 15 + 12 + 10  # = 121
        score_final = round(score / max_score * 100)

        if score_final >= 80:
            classificacao = '⭐ ELITE — Jogo Excepcional'
        elif score_final >= 65:
            classificacao = '🏆 OURO — Alta Qualidade'
        elif score_final >= 50:
            classificacao = '🥈 PRATA — Jogo Sólido'
        else:
            classificacao = '🥉 BRONZE — Jogo Regular'

        return {
            'jogo': sorted(jogo),
            'score_final': score_final,
            'classificacao': classificacao,
            'diretrizes_aprovadas': aprovadas,
            'total_diretrizes': 10,
            'detalhes': detalhes,
        }

    # ════════════════════════════════════════════════════════════
    #  GERADOR INTELIGENTE
    # ════════════════════════════════════════════════════════════

    def gerar_jogo_inteligente(self, tentativas=300):
        """
        Gera um jogo otimizado usando pool ponderado
        e validação por todas as 8 diretrizes.
        """
        # Pool ponderado
        pesos = {}
        for d in range(1, self.UNIVERSO + 1):
            peso = self.frequencias.get(d, 0) / max(self.total_jogos, 1) * 100
            # Bônus por decaimento
            for item in self.decaimento:
                if item['dezena'] == d:
                    peso *= item['peso']
                    break
            # Bônus por ciclo faltando
            if d in self.ciclos.get('faltam', []):
                peso *= 1.5
            pesos[d] = max(peso, 0.1)

        pool = list(range(1, self.UNIVERSO + 1))
        weights = [pesos[d] for d in pool]

        melhor_jogo = None
        melhor_score = 0

        for _ in range(tentativas):
            # Seleção ponderada sem repetição
            jogo = []
            pool_temp = pool.copy()
            weights_temp = weights.copy()
            for _ in range(self.DEZENAS_SORTEIO):
                total_w = sum(weights_temp)
                if total_w == 0:
                    break
                r = random.uniform(0, total_w)
                cumulative = 0
                for idx, w in enumerate(weights_temp):
                    cumulative += w
                    if r <= cumulative:
                        jogo.append(pool_temp[idx])
                        pool_temp.pop(idx)
                        weights_temp.pop(idx)
                        break

            jogo = sorted(jogo)
            if len(jogo) != self.DEZENAS_SORTEIO:
                continue

            resultado = self.analise_completa_jogo(jogo)
            if resultado['score_final'] > melhor_score:
                melhor_score = resultado['score_final']
                melhor_jogo = resultado

        return melhor_jogo

    def gerar_multiplos_jogos(self, qtd=5, tentativas_por_jogo=200):
        """Gera múltiplos jogos inteligentes únicos."""
        jogos = []
        jogos_set = set()

        for _ in range(qtd * 3):
            resultado = self.gerar_jogo_inteligente(tentativas=tentativas_por_jogo)
            if resultado is None:
                continue
            jogo_tuple = tuple(resultado['jogo'])
            if jogo_tuple not in jogos_set:
                jogos_set.add(jogo_tuple)
                jogos.append(resultado)

            if len(jogos) >= qtd:
                break

        return sorted(jogos, key=lambda x: x['score_final'], reverse=True)

    # ════════════════════════════════════════════════════════════
    #  RESUMO DAS DIRETRIZES
    # ════════════════════════════════════════════════════════════

    def resumo_diretrizes(self):
        """Retorna status de cada diretriz para o frontend."""
        hiper = self.probabilidade_hipergeometrica()

        return {
            'hipergeometrica': {
                'nome': 'Distribuição Hipergeométrica',
                'icon': '📊',
                'descricao': f'Zona de Retorno (11-12 pts): P={hiper["prob_zona_retorno"]:.2%}',
            },
            'entropia': {
                'nome': 'Entropia de Shannon',
                'icon': '🔀',
                'descricao': f'Média histórica: H={self.entropia_media:.3f}',
            },
            'pearson': {
                'nome': 'Resíduos de Pearson (χ²)',
                'icon': '📐',
                'descricao': f'χ²={self.chi2_resultado.get("chi2", 0)} | p={self.chi2_resultado.get("p_valor", 0)}',
            },
            'clusterizacao': {
                'nome': 'Clusterização Euclidiana',
                'icon': '🎯',
                'descricao': 'σ baixo e estável para ocupação massiva do volante',
            },
            'benford': {
                'nome': 'Lei de Benford',
                'icon': '📈',
                'descricao': 'Validação logarítmica contra vieses mecânicos',
            },
            'moldura': {
                'nome': 'Simetria / Moldura do Volante',
                'icon': '🔲',
                'descricao': f'Faixa ideal: {self.moldura_stats.get("faixa_ideal", "8-11")} na moldura',
            },
            'ciclos': {
                'nome': 'Ciclos de Fechamento',
                'icon': '🔄',
                'descricao': f'{len(self.ciclos.get("faltam", []))} dezenas faltando no ciclo atual',
            },
            'coocorrencia': {
                'nome': 'Coocorrência (Pares de Ouro)',
                'icon': '🔗',
                'descricao': f'{len(self.pares_de_ouro()[0])} pares correlatos identificados',
            },
            'paridade_primos': {
                'nome': 'Paridade e Primos (Ouro)',
                'icon': '⚖️',
                'descricao': '7-9 ímpares + 5-6 primos por jogo',
            },
            'soma': {
                'nome': 'Filtro de Soma',
                'icon': '➕',
                'descricao': 'Soma ideal: 166 a 220',
            },
        }
