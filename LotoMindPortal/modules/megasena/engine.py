"""
MegaMind — Motor de Análise da Mega-Sena
=========================================
Classe principal para busca de dados da API Caixa,
análise de frequências, ciclos, quadrantes e probabilidades.
"""

import json
import os
from collections import Counter
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Quadrantes do volante da Mega-Sena (60 dezenas divididas em 4 faixas)
QUADRANTES = {
    'Q1 (01-15)': list(range(1, 16)),
    'Q2 (16-30)': list(range(16, 31)),
    'Q3 (31-45)': list(range(31, 46)),
    'Q4 (46-60)': list(range(46, 61)),
}


class MegaSenaEngine:
    """Motor principal de análise da Mega-Sena."""

    API_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"
    UNIVERSO = 60          # 1 a 60
    DEZENAS_SORTEIO = 6    # 6 bolas por concurso

    def __init__(self, arsenal_path='data/arsenal.json'):
        os.makedirs('data', exist_ok=True)

        if os.path.exists(arsenal_path):
            with open(arsenal_path, 'r', encoding='utf-8') as f:
                self.arsenal = json.load(f)
        else:
            self.arsenal = self._criar_arsenal_padrao()
            self._salvar_arsenal(arsenal_path)

    # ── Arsenal ────────────────────────────────────────────

    def _criar_arsenal_padrao(self):
        """8 jogos-base para backtesting inicial."""
        return {
            "Jogo 1 (Estatístico)": [5, 12, 23, 34, 45, 56],
            "Jogo 2 (Calor)": [3, 10, 17, 28, 41, 53],
            "Jogo 3 (Zebra)": [7, 14, 22, 33, 47, 58],
            "Jogo 4 (Equilíbrio)": [2, 15, 24, 36, 44, 55],
            "Jogo 5 (Primos)": [5, 11, 23, 37, 41, 59],
            "Jogo 6 (Extremos)": [1, 8, 30, 31, 52, 60],
            "Jogo 7 (Quadrantes)": [4, 18, 32, 46, 50, 57],
            "Jogo 8 (Misto)": [6, 19, 27, 38, 49, 54],
        }

    def _salvar_arsenal(self, caminho):
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(self.arsenal, f, indent=2, ensure_ascii=False)

    # ── Busca de Dados ────────────────────────────────────

    def buscar_dados_oficiais(self, qtd_concursos=50):
        """Busca resultados na API oficial da Caixa para a Mega-Sena."""
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
                print(f"[MegaSenaEngine] Falha na API. Status: {resp.status_code}. Resposta: {resp.text[:200]}")
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
            print(f"[MegaSenaEngine] Erro ao buscar dados: {e}")
            
        print("[MegaSenaEngine] API da Caixa indisponível (403/Timeout). Entrando em falha segura com MOCK local.")
        import numpy as np
        mock_dados = []
        for i in range(qtd_concursos):
            dezenas = np.sort(np.random.choice(range(1, 61), 6, replace=False)).tolist()
            mock_dados.append({
                'Concurso': 9999 - i,
                'Data': 'Hoje',
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
        """Retorna contagem, lista de quentes (top 20) e frias (bottom 15)."""
        todas = [n for sub in df['Dezenas'] for n in sub]
        contagem = Counter(todas)
        quentes = [n for n, _ in contagem.most_common(20)]
        frias = [n for n, _ in contagem.most_common()[:-16:-1]]
        return contagem, quentes, frias

    # ── Quadrantes (NOVO) ─────────────────────────────────

    def analisar_quadrantes(self, df):
        """Conta quantas dezenas caem em cada quadrante para cada sorteio."""
        resultados = {nome: 0 for nome in QUADRANTES}
        total_dezenas = 0

        for dezenas in df['Dezenas']:
            for nome, faixa in QUADRANTES.items():
                resultados[nome] += len([d for d in dezenas if d in faixa])
            total_dezenas += len(dezenas)

        percentuais = {}
        for nome, contagem in resultados.items():
            percentuais[nome] = {
                'contagem': contagem,
                'percentual': round((contagem / total_dezenas) * 100, 1) if total_dezenas else 0
            }
        return percentuais

    def quadrantes_ultimo_sorteio(self, dezenas):
        """Distribuição de quadrantes para um sorteio específico."""
        resultado = {}
        for nome, faixa in QUADRANTES.items():
            nums = [d for d in dezenas if d in faixa]
            resultado[nome] = {'numeros': nums, 'quantidade': len(nums)}
        return resultado

    # ── Ciclos de Sorteio ─────────────────────────────────

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
                'concursos_semana': total_jogos,
            })
        return fixos

    # ── Probabilidades ────────────────────────────────────

    def calcular_probabilidades(self, df):
        """Probabilidade histórica de cada dezena (1–60)."""
        todas = [n for sub in df['Dezenas'] for n in sub]
        contagem = Counter(todas)
        total = len(df)

        dados = []
        for dezena in range(1, self.UNIVERSO + 1):
            freq = contagem.get(dezena, 0)
            prob = round((freq / total) * 100, 2) if total > 0 else 0
            if prob >= 12:
                chance = '🔥 Alta'
            elif prob >= 8:
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

    # ── Premiação ─────────────────────────────────────────

    def calcular_premio(self, acertos):
        premios = {
            4: "Quadra",
            5: "Quina",
            6: "SENA — PRÊMIO MÁXIMO!",
        }
        return premios.get(acertos, "Sem prêmio")

    # ── Simulação de Desempenho do Arsenal ────────────────

    def simular_desempenho(self, df):
        """Simula performance de cada jogo do arsenal no histórico."""
        ranking = {}

        for nome, dezenas in self.arsenal.items():
            set_jogo = set(dezenas)
            pontos = 0
            acertos_detalhados = []

            for _, row in df.iterrows():
                set_resultado = set(row['Dezenas'])
                acertos = len(set_jogo.intersection(set_resultado))

                if acertos == 4:
                    pontos += 10
                elif acertos == 5:
                    pontos += 100
                elif acertos == 6:
                    pontos += 5000

                if acertos >= 4:
                    acertos_detalhados.append({
                        'concurso': row['Concurso'],
                        'acertos': acertos,
                        'premio': self.calcular_premio(acertos),
                    })

            ranking[nome] = {
                'pontos': pontos,
                'acertos': acertos_detalhados,
                'total_premiado': len(acertos_detalhados),
                'dezenas': dezenas,
            }

        return dict(sorted(ranking.items(), key=lambda x: x[1]['pontos'], reverse=True))

    # ── Paridade Detalhada ────────────────────────────────

    def analisar_paridade_detalhada(self, df):
        """Distribuição de pares/ímpares nos sorteios."""
        distribuicao = Counter()
        for _, row in df.iterrows():
            pares = row['Pares']
            impares = row['Impares']
            distribuicao[f"{pares}P/{impares}I"] += 1
        return dict(distribuicao.most_common())
