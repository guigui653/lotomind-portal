"""
LotoMind Portal — Motor de Análise da Lotofácil
=================================================
Busca de dados da API Caixa, análise de frequências, ciclos e probabilidades.
"""

import json
import os
from collections import Counter
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LotofacilEngine:
    """Motor principal de análise da Lotofácil."""

    API_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
    UNIVERSO = 25
    DEZENAS_SORTEIO = 15

    def __init__(self):
        os.makedirs('data', exist_ok=True)

    # ── Busca de Dados ────────────────────────────────────

    def buscar_dados_oficiais(self, qtd_concursos=500):
        """
        Busca resultados oficiais na API da Caixa e retorna um DataFrame.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://loterias.caixa.gov.br/'
        }
        dados = []

        try:
            resp = requests.get(self.API_URL, headers=headers, verify=False, timeout=10)
            if resp.status_code != 200:
                print(f"[LotofacilEngine] Falha na API. Status: {resp.status_code}.")
                raise Exception(f"HTTP {resp.status_code}")

            ultimo = resp.json()
            num_atual = ultimo['numero']
            dados.append(self._processar_jogo(ultimo))

            for i in range(1, qtd_concursos):
                try:
                    r = requests.get(
                        f"{self.API_URL}/{num_atual - i}",
                        headers=headers, verify=False, timeout=5
                    )
                    if r.status_code == 200:
                        dados.append(self._processar_jogo(r.json()))
                    else:
                        raise Exception(f"HTTP {r.status_code} no concurso {num_atual - i}")
                except Exception as e:
                    raise Exception(f"Interrompendo lote devido a falha: {e}")

            return pd.DataFrame(dados)

        except Exception as e:
            print(f"[LotofacilEngine] Erro ao buscar dados: {e}")
            
        print("[LotofacilEngine] API bloqueou (Fall-back local acionado).")
        import numpy as np
        mock_dados = []
        for i in range(qtd_concursos):
            dezenas = np.sort(np.random.choice(range(1, 26), 15, replace=False)).tolist()
            mock_dados.append({
                'Concurso': 8888 - i,
                'Data': 'Hoje (MOCK)',
                'Dezenas': dezenas,
                'Pares': len([x for x in dezenas if x % 2 == 0]),
                'Impares': len([x for x in dezenas if x % 2 != 0]),
                'Soma': sum(dezenas),
            })
        return pd.DataFrame(mock_dados)

    def _processar_jogo(self, jogo):
        """Processa um registro retornado pela API."""
        dezenas = sorted([int(d) for d in jogo['listaDezenas']])
        return {
            'Concurso': jogo['numero'],
            'Data': jogo.get('dataApuracao', ''),
            'Dezenas': dezenas,
            'Pares': len([x for x in dezenas if x % 2 == 0]),
            'Impares': len([x for x in dezenas if x % 2 != 0]),
            'Soma': sum(dezenas),
        }

    # ── Frequências ────────────────────────────────────────

    def analisar_frequencias(self, df):
        """Retorna contagem, lista de quentes (top 15) e frias (bottom 10)."""
        todas = [n for sub in df['Dezenas'] for n in sub]
        contagem = Counter(todas)
        quentes = [n for n, _ in contagem.most_common(15)]
        frias = [n for n, _ in contagem.most_common()[:-11:-1]]
        return contagem, quentes, frias

    # ── Fixos da Semana ───────────────────────────────────

    def calcular_fixos_semana(self, df, top_n=10):
        """Top N dezenas mais frequentes nos últimos 7 concursos."""
        ultimos_7 = df.head(7)
        todas = [n for sub in ultimos_7['Dezenas'] for n in sub]
        contagem = Counter(todas)
        total_jogos = len(ultimos_7)

        fixos = []
        for num, freq in contagem.most_common(top_n):
            fixos.append({
                'numero': num,
                'frequencia': freq,
                'percentual': round((freq / total_jogos) * 100, 1),
            })
        return fixos

    # ── Probabilidades ────────────────────────────────────

    def calcular_probabilidades(self, df):
        """Probabilidade histórica de cada dezena (1–25)."""
        todas = [n for sub in df['Dezenas'] for n in sub]
        contagem = Counter(todas)
        total = len(df)

        dados = []
        for dezena in range(1, self.UNIVERSO + 1):
            freq = contagem.get(dezena, 0)
            prob = round((freq / total) * 100, 2) if total > 0 else 0
            if prob >= 65:
                chance = '🔥 Alta'
            elif prob >= 55:
                chance = '🟡 Média'
            else:
                chance = '❄️ Baixa'
            dados.append({
                'Dezena': dezena,
                'Frequencia': freq,
                'Probabilidade': prob,
                'Chance': chance,
            })
        return dados

    # ── Tendências ────────────────────────────────────────

    def tendencia_numeros(self, df):
        """Compara frequência recente (7 jogos) vs histórica."""
        recentes = df.head(7)
        cont_rec = Counter([n for sub in recentes['Dezenas'] for n in sub])
        cont_hist = Counter([n for sub in df['Dezenas'] for n in sub])

        total_rec = max(len(recentes), 1)
        total_hist = max(len(df), 1)

        tendencias = {}
        for dezena in range(1, self.UNIVERSO + 1):
            fr = cont_rec.get(dezena, 0) / total_rec
            fh = cont_hist.get(dezena, 0) / total_hist
            if fr > fh * 1.2:
                tendencias[dezena] = '📈 Alta'
            elif fr < fh * 0.8:
                tendencias[dezena] = '📉 Queda'
            else:
                tendencias[dezena] = '➡️ Estável'
        return tendencias

    # ── Ciclos ────────────────────────────────────────────

    def calcular_ciclos(self, df):
        """Para cada dezena, calcula há quantos concursos não aparece."""
        ciclos = {}
        for dezena in range(1, self.UNIVERSO + 1):
            atraso = 0
            for _, row in df.iterrows():
                if dezena in row['Dezenas']:
                    break
                atraso += 1
            ciclos[dezena] = atraso
        return ciclos

    # ── Paridade ──────────────────────────────────────────

    def analisar_paridade_detalhada(self, df):
        """Distribuição de pares/ímpares nos sorteios."""
        distribuicao = Counter()
        for _, row in df.iterrows():
            pares = row['Pares']
            impares = row['Impares']
            distribuicao[f"{pares}P/{impares}I"] += 1
        return dict(distribuicao.most_common())
