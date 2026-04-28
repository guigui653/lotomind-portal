import json
import os
from collections import Counter
import requests
import pandas as pd
import streamlit as st
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LotofacilEngine:
    def __init__(self, arsenal_path='data/arsenal.json'):
        """Motor principal de análise da Lotofácil"""

        # Cria diretório data se não existir
        os.makedirs('data', exist_ok=True)

        # Carrega arsenal se existir
        if os.path.exists(arsenal_path):
            with open(arsenal_path, 'r', encoding='utf-8') as f:
                self.arsenal = json.load(f)
        else:
            # Cria arsenal padrão
            self.arsenal = self._criar_arsenal_padrao()
            self._salvar_arsenal(arsenal_path)

    def _criar_arsenal_padrao(self):
        """Cria os 8 jogos do arsenal"""
        return {
            "Jogo 1 (Estatístico)": [1, 2, 3, 5, 8, 10, 11, 13, 14, 16, 18, 20, 21, 24, 25],
            "Jogo 2 (Calor)": [1, 3, 5, 6, 7, 9, 12, 14, 15, 17, 18, 19, 21, 22, 24],
            "Jogo 3 (Zebra)": [1, 2, 4, 5, 8, 9, 10, 12, 13, 15, 18, 20, 22, 23, 25],
            "Jogo 4 (Início 1-2-5)": [1, 2, 5, 6, 8, 11, 13, 14, 17, 18, 19, 21, 22, 24, 25],
            "Jogo 5 (Início 2-3-5)": [2, 3, 5, 7, 9, 10, 12, 13, 16, 18, 20, 21, 23, 24, 25],
            "Jogo 6 (Início 1-2-3-4)": [1, 2, 3, 4, 5, 8, 10, 12, 15, 18, 19, 20, 21, 22, 25],
            "Jogo 7 (A Loucura)": [1, 2, 5, 8, 13, 14, 15, 16, 17, 18, 19, 20, 22, 24, 25],
            "Jogo 8 (O Seu Salto)": [3, 4, 5, 6, 8, 9, 11, 13, 17, 18, 20, 21, 23, 24, 25]
        }

    def _salvar_arsenal(self, caminho):
        """Salva o arsenal em JSON"""
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(self.arsenal, f, indent=2, ensure_ascii=False)

    def buscar_dados_oficiais(self, qtd_concursos=50):
        """Busca dados da API da Caixa"""
        url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
        dados = []
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            resp = requests.get(url, headers=headers, verify=False, timeout=10)
            if resp.status_code != 200:
                return None

            ultimo = resp.json()
            num_atual = ultimo['numero']
            dados.append(self._processar_jogo(ultimo))

            progress_bar = st.progress(0)

            for i in range(1, qtd_concursos):
                try:
                    r = requests.get(f"{url}/{num_atual - i}", headers=headers, verify=False, timeout=5)
                    if r.status_code == 200:
                        dados.append(self._processar_jogo(r.json()))
                except:
                    pass
                progress_bar.progress((i + 1) / qtd_concursos)

            progress_bar.empty()
            return pd.DataFrame(dados)

        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
            return None

    def _processar_jogo(self, jogo):
        """Processa um jogo retornado pela API"""
        dezenas = sorted([int(d) for d in jogo['listaDezenas']])
        return {
            'Concurso': jogo['numero'],
            'Data': jogo['dataApuracao'],
            'Dezenas': dezenas,
            'Pares': len([x for x in dezenas if x % 2 == 0]),
            'Impares': len([x for x in dezenas if x % 2 != 0]),
            'Soma': sum(dezenas)
        }

    def analisar_frequencias(self, df):
        """Analisa frequências de dezenas"""
        todas_dezenas = [num for sublist in df['Dezenas'] for num in sublist]
        contagem = Counter(todas_dezenas)
        quentes = [num for num, freq in contagem.most_common(15)]
        frias = [num for num, freq in contagem.most_common()[:-11:-1]]
        return contagem, quentes, frias

    def simular_desempenho(self, resultados_historico):
        """Simula performance de cada jogo do arsenal"""
        ranking = {}

        for nome, dezenas in self.arsenal.items():
            set_jogo = set(dezenas)
            pontos = 0
            acertos_detalhados = []

            for idx, row in resultados_historico.iterrows():
                concurso = row['Concurso']
                resultado = row['Dezenas']
                set_resultado = set(resultado)
                acertos = len(set_jogo.intersection(set_resultado))

                if acertos == 11:
                    pontos += 5
                elif acertos == 12:
                    pontos += 15
                elif acertos == 13:
                    pontos += 50
                elif acertos == 14:
                    pontos += 200
                elif acertos == 15:
                    pontos += 1000

                if acertos >= 11:
                    acertos_detalhados.append({
                        'concurso': concurso,
                        'acertos': acertos,
                        'premio': self._calcular_premio(acertos)
                    })

            ranking[nome] = {
                'pontos': pontos,
                'acertos': acertos_detalhados,
                'total_premiado': len(acertos_detalhados),
                'dezenas': dezenas
            }

        return dict(sorted(ranking.items(), key=lambda x: x[1]['pontos'], reverse=True))

    def _calcular_premio(self, acertos):
        """Calcula o prêmio baseado no número de acertos"""
        premios = {
            11: "R$ 7,00",
            12: "R$ 14,00",
            13: "R$ 35,00",
            14: "R$ 800,00+",
            15: "JACKPOT!"
        }
        return premios.get(acertos, "Sem prêmio")

    def identificar_atrasados(self, df, limite=3):
        """Identifica dezenas que não saem há X concursos"""
        ultimos = df.head(limite)['Dezenas'].tolist()
        todas_ultimas = set([num for resultado in ultimos for num in resultado])
        return [n for n in range(1, 26) if n not in todas_ultimas]

    def calcular_fixos_semana(self, df, top_n=10):
        """Calcula os N números mais frequentes nos últimos 7 concursos"""
        ultimos_7 = df.head(7)
        todas = [num for sublist in ultimos_7['Dezenas'] for num in sublist]
        contagem = Counter(todas)
        total_jogos = len(ultimos_7)

        fixos = []
        for num, freq in contagem.most_common(top_n):
            fixos.append({
                'numero': num,
                'frequencia': freq,
                'percentual': round((freq / total_jogos) * 100, 1),
                'concursos_semana': total_jogos
            })
        return fixos

    def calcular_probabilidades(self, df):
        """Calcula a probabilidade histórica de cada dezena (1-25)"""
        todas = [num for sublist in df['Dezenas'] for num in sublist]
        contagem = Counter(todas)
        total = len(df)

        dados = []
        for dezena in range(1, 26):
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
                'Frequência': freq,
                'Probabilidade (%)': prob,
                'Chance': chance
            })
        return pd.DataFrame(dados)

    def tendencia_numeros(self, df):
        """Compara frequência recente (7 jogos) vs histórica para determinar tendência"""
        recentes = df.head(7)
        todas_recentes = [num for sublist in recentes['Dezenas'] for num in sublist]
        cont_recente = Counter(todas_recentes)

        todas_hist = [num for sublist in df['Dezenas'] for num in sublist]
        cont_hist = Counter(todas_hist)

        tendencias = {}
        total_recente = len(recentes)
        total_hist = len(df)

        for dezena in range(1, 26):
            freq_rec = cont_recente.get(dezena, 0) / max(total_recente, 1)
            freq_hist = cont_hist.get(dezena, 0) / max(total_hist, 1)
            if freq_rec > freq_hist * 1.2:
                tendencias[dezena] = '📈 Alta'
            elif freq_rec < freq_hist * 0.8:
                tendencias[dezena] = '📉 Queda'
            else:
                tendencias[dezena] = '➡️ Estável'
        return tendencias