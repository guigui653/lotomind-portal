"""
LotoMind Portal — AvaliadorDeJogos (IA Explicável)
====================================================
Classe orquestradora que avalia uma combinação de jogo contra
8 critérios (filtros + análise histórica) e gera um boletim
JSON completo com nota final e justificativas textuais.

Fluxo:
  1. carregar_historico(df, ...) → pré-calcula DNI, Afinidade, etc.
  2. avaliar_e_pontuar_jogo(combinacao) → aplica 8 critérios
  3. gerar_relatorio_jogo() → retorna boletim JSON explicável

Genérico: funciona para Lotofácil (25/15) e Mega-Sena (60/6).
"""

import math
import numpy as np
from typing import List, Dict, Optional

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


# ════════════════════════════════════════════════════════════
#  CONFIGURAÇÕES PADRÃO POR LOTERIA
# ════════════════════════════════════════════════════════════

CONFIGS = {
    'lotofacil': {
        'universo': 25,
        'dezenas_sorteio': 15,
        'layout': LAYOUT_LOTOFACIL,
        'soma_min': 166,
        'soma_max': 220,
        'paridade_min_impares': 7,
        'paridade_max_impares': 9,
        'primos': {2, 3, 5, 7, 11, 13, 17, 19, 23},
        'primos_min': 5,
        'primos_max': 6,
        'entropia_bins': 5,
    },
    'megasena': {
        'universo': 60,
        'dezenas_sorteio': 6,
        'layout': LAYOUT_MEGASENA,
        'soma_min': 100,
        'soma_max': 250,
        'paridade_min_impares': 2,
        'paridade_max_impares': 4,
        'primos': {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59},
        'primos_min': 2,
        'primos_max': 3,
        'entropia_bins': 6,
    },
}


class AvaliadorDeJogos:
    """
    Motor de avaliação e pontuação de jogos com justificativas explicáveis.

    8 Critérios de Avaliação (max = 100 pts):
      1. Soma             → 0 a 15 pts
      2. Par/Ímpar         → 0 a 10 pts
      3. Primos            → 0 a 10 pts
      4. Entropia Shannon  → 0 a 15 pts
      5. Espaçamento Gaps  → 0 a 15 pts
      6. Zona Espacial     → 0 a 10 pts
      7. DNI (Atraso)      → 0 a 15 pts
      8. Afinidade Pares   → 0 a 10 pts
                            ─────────
                     TOTAL:  100 pts
    """

    MAX_SCORE = 100

    def __init__(self, loteria: str = 'lotofacil'):
        """
        Args:
            loteria: 'lotofacil' ou 'megasena'.
        """
        if loteria not in CONFIGS:
            raise ValueError(f"Loteria '{loteria}' não suportada. Use 'lotofacil' ou 'megasena'.")

        self.loteria = loteria
        self.config = CONFIGS[loteria]
        self.universo = self.config['universo']
        self.dezenas_sorteio = self.config['dezenas_sorteio']

        # Componentes de análise
        self.filtro_espacamento = FiltroEspacamento(tolerancia_sigma=1.5)
        self.filtro_zona = FiltroZonaEspacial(layout=self.config['layout'])

        # Dados pré-calculados (preenchidos em carregar_historico)
        self.indices_atraso = {}
        self.matriz_afinidade = {}
        self.historico_carregado = False

        # Cache do último relatório
        self._ultimo_resultado = None

    # ════════════════════════════════════════════════════════
    #  CARREGAMENTO (Entry-Point)
    # ════════════════════════════════════════════════════════

    def carregar_historico(self, df) -> None:
        """
        Carrega o DataFrame do histórico e pré-calcula todas as análises.

        Args:
            df: DataFrame com colunas 'Concurso' e 'Dezenas' (lista de ints).
        """
        if df is None or df.empty:
            return

        historico_listas = df['Dezenas'].tolist()

        # 1. Índice de Atraso (DNI)
        self.indices_atraso = calcular_indice_atraso(
            historico_listas,
            universo=self.universo,
            dezenas_sorteio=self.dezenas_sorteio,
        )

        # 2. Matriz de Afinidade
        self.matriz_afinidade = gerar_matriz_afinidade(
            historico_listas,
            universo=self.universo,
            top_n=15,
        )

        # 3. Desvio Padrão Histórico dos Gaps (para filtro de espaçamento)
        self.filtro_espacamento.calcular_dp_historico(historico_listas)

        self.historico_carregado = True

    # ════════════════════════════════════════════════════════
    #  AVALIAÇÃO PRINCIPAL
    # ════════════════════════════════════════════════════════

    def avaliar_e_pontuar_jogo(self, combinacao: List[int]) -> dict:
        """
        Método principal: passa a combinação por todos os 8 filtros
        e gera uma pontuação matemática com justificativas.

        Args:
            combinacao: Lista de inteiros (dezenas do jogo).

        Returns:
            Dicionário com nota final, classificação, detalhes por filtro
            e análise individual de cada número.
        """
        if not self.historico_carregado:
            return {
                'nota_final': 0,
                'classificacao': '⚠️ Histórico não carregado',
                'filtros': {},
                'analise_por_numero': [],
                'justificativa_geral': 'Histórico de sorteios não foi carregado.',
            }

        jogo = sorted(combinacao)
        filtros = {}
        score_total = 0.0

        # ── 1. Filtro de Soma (0-15 pts) ──────────────────
        soma = sum(jogo)
        soma_min = self.config['soma_min']
        soma_max = self.config['soma_max']
        soma_ideal = (soma_min + soma_max) / 2
        soma_ok = soma_min <= soma <= soma_max

        if soma_ok:
            # Score proporcional à proximidade do centro
            distancia = abs(soma - soma_ideal)
            amplitude = (soma_max - soma_min) / 2
            score_soma = 15.0 * max(0, 1 - distancia / amplitude)
        else:
            score_soma = 0.0

        filtros['soma'] = {
            'valor': soma,
            'faixa': f'{soma_min}-{soma_max}',
            'ideal': round(soma_ideal),
            'aprovado': soma_ok,
            'score': round(score_soma, 1),
        }
        score_total += score_soma

        # ── 2. Filtro Par/Ímpar (0-10 pts) ────────────────
        impares = sum(1 for n in jogo if n % 2 != 0)
        pares = len(jogo) - impares
        par_min = self.config['paridade_min_impares']
        par_max = self.config['paridade_max_impares']
        paridade_ok = par_min <= impares <= par_max

        if paridade_ok:
            ideal_impares = (par_min + par_max) / 2
            score_paridade = 10.0 * max(0, 1 - abs(impares - ideal_impares) / max(ideal_impares, 1))
        else:
            score_paridade = 2.0  # Pontuação mínima

        filtros['paridade'] = {
            'pares': pares,
            'impares': impares,
            'formato': f'{impares}Í/{pares}P',
            'faixa_impares': f'{par_min}-{par_max}',
            'aprovado': paridade_ok,
            'score': round(score_paridade, 1),
        }
        score_total += score_paridade

        # ── 3. Filtro de Primos (0-10 pts) ────────────────
        primos_no_jogo = [n for n in jogo if n in self.config['primos']]
        qtd_primos = len(primos_no_jogo)
        primos_min = self.config['primos_min']
        primos_max = self.config['primos_max']
        primos_ok = primos_min <= qtd_primos <= primos_max

        if primos_ok:
            ideal_primos = (primos_min + primos_max) / 2
            score_primos = 10.0 * max(0, 1 - abs(qtd_primos - ideal_primos) / max(ideal_primos, 1))
        else:
            score_primos = 2.0

        filtros['primos'] = {
            'quantidade': qtd_primos,
            'numeros': sorted(primos_no_jogo),
            'faixa': f'{primos_min}-{primos_max}',
            'aprovado': primos_ok,
            'score': round(score_primos, 1),
        }
        score_total += score_primos

        # ── 4. Entropia de Shannon (0-15 pts) ─────────────
        entropia_result = calcular_entropia_jogo(
            jogo,
            range_numeros=self.universo,
            num_bins=self.config['entropia_bins'],
        )
        h_norm = entropia_result['entropia_normalizada']
        score_entropia = 15.0 * h_norm  # Linear: 1.0 → 15 pts, 0.0 → 0 pts

        filtros['entropia'] = {
            **entropia_result,
            'aprovado': h_norm >= 0.70,
            'score': round(score_entropia, 1),
        }
        score_total += score_entropia

        # ── 5. Espaçamento / Gaps (0-15 pts) ──────────────
        gaps_result = self.filtro_espacamento.verificar_distribuicao_espacamento(jogo)
        if gaps_result['aprovado']:
            # Quanto menor o desvio relativo, maior o score
            desvio = gaps_result['desvio_relativo']
            score_gaps = 15.0 * max(0, 1 - desvio / self.filtro_espacamento.tolerancia_sigma)
        else:
            score_gaps = max(0, 5.0 * (1 - gaps_result['desvio_relativo'] / 3.0))

        filtros['espacamento'] = {
            **gaps_result,
            'score': round(score_gaps, 1),
        }
        score_total += score_gaps

        # ── 6. Zona Espacial (0-10 pts) ───────────────────
        zona_result = self.filtro_zona.verificar_distribuicao_quadrantes(jogo)
        if zona_result['aprovado']:
            # Score baseado na quantidade de quadrantes presentes
            score_zona = min(10.0, zona_result['quadrantes_presentes'] * 2.5)
            # Bônus por baixa concentração
            if zona_result['concentracao_maxima'] <= 0.35:
                score_zona = 10.0
        else:
            score_zona = zona_result['quadrantes_presentes'] * 1.5

        # Remover detalhes por número (muito verboso para o JSON principal)
        zona_resumo = {k: v for k, v in zona_result.items() if k != 'detalhes_por_numero'}
        filtros['zona_espacial'] = {
            **zona_resumo,
            'score': round(score_zona, 1),
        }
        score_total += score_zona

        # ── 7. DNI — Índice de Atraso (0-15 pts) ─────────
        score_dni, analise_dni = self._avaliar_dni(jogo)
        filtros['dni'] = {
            'score': round(score_dni, 1),
            'numeros_devidos': analise_dni['devidos'],
            'numeros_recentes': analise_dni['recentes'],
            'dni_medio': analise_dni['dni_medio'],
            'aprovado': score_dni >= 7.0,
        }
        score_total += score_dni

        # ── 8. Afinidade de Pares (0-10 pts) ─────────────
        score_afinidade, analise_afinidade = self._avaliar_afinidade(jogo)
        filtros['afinidade'] = {
            'score': round(score_afinidade, 1),
            'lift_medio': analise_afinidade['lift_medio'],
            'pares_fortes': analise_afinidade['pares_fortes'],
            'pares_fracos': analise_afinidade['pares_fracos'],
            'aprovado': score_afinidade >= 5.0,
        }
        score_total += score_afinidade

        # ── Score Final ───────────────────────────────────
        nota_final = round(min(score_total, self.MAX_SCORE))

        # Classificação
        if nota_final >= 80:
            classificacao = '⭐ ELITE — Jogo Excepcional'
        elif nota_final >= 65:
            classificacao = '🏆 FORTE — Alta Qualidade'
        elif nota_final >= 50:
            classificacao = '🥈 SÓLIDO — Jogo Competitivo'
        elif nota_final >= 35:
            classificacao = '🥉 REGULAR — Pode Melhorar'
        else:
            classificacao = '🔵 FRACO — Baixa Qualidade'

        # Contagem de filtros aprovados
        aprovados = sum(1 for f in filtros.values() if f.get('aprovado', False))

        # Análise individual por número
        analise_por_numero = self._analisar_numeros_individuais(jogo)

        # Justificativa textual
        justificativa = self._gerar_justificativa_textual(
            jogo, nota_final, filtros, analise_por_numero
        )

        self._ultimo_resultado = {
            'jogo': jogo,
            'nota_final': nota_final,
            'classificacao': classificacao,
            'filtros_aprovados': aprovados,
            'total_filtros': 8,
            'filtros': filtros,
            'analise_por_numero': analise_por_numero,
            'justificativa_geral': justificativa,
        }

        return self._ultimo_resultado

    # ════════════════════════════════════════════════════════
    #  RELATÓRIO JSON (Saída)
    # ════════════════════════════════════════════════════════

    def gerar_relatorio_jogo(self) -> dict:
        """
        Retorna o boletim completo do último jogo avaliado.
        """
        if self._ultimo_resultado is None:
            return {'erro': 'Nenhum jogo foi avaliado ainda.'}
        return self._ultimo_resultado

    # ════════════════════════════════════════════════════════
    #  MÉTODOS INTERNOS
    # ════════════════════════════════════════════════════════

    def _avaliar_dni(self, jogo: List[int]) -> tuple:
        """Avalia o score baseado no DNI dos números do jogo."""
        if not self.indices_atraso:
            return 0.0, {'devidos': 0, 'recentes': 0, 'dni_medio': 0.0}

        dnis = []
        devidos = 0
        recentes = 0

        for n in jogo:
            info = self.indices_atraso.get(n, {})
            dni = info.get('dni', 0)
            dnis.append(dni)
            if dni > 0:
                devidos += 1
            elif dni < -1:
                recentes += 1

        dni_medio = float(np.mean(dnis)) if dnis else 0.0

        # Score: ter uma mistura saudável de números devidos é bom
        # Ideal: 40-60% dos números com DNI > 0
        proporcao_devidos = devidos / max(len(jogo), 1)
        if 0.3 <= proporcao_devidos <= 0.7:
            score = 15.0 * (1 - abs(proporcao_devidos - 0.5) / 0.5)
        elif proporcao_devidos > 0.7:
            score = 10.0  # Muitos devidos: bom mas não ideal
        else:
            score = 5.0 * proporcao_devidos / 0.3 if proporcao_devidos > 0 else 3.0

        return min(score, 15.0), {
            'devidos': devidos,
            'recentes': recentes,
            'dni_medio': round(dni_medio, 2),
        }

    def _avaliar_afinidade(self, jogo: List[int]) -> tuple:
        """Avalia o score baseado na afinidade entre pares do jogo."""
        matriz_lift = self.matriz_afinidade.get('matriz_lift')
        if matriz_lift is None:
            return 0.0, {'lift_medio': 1.0, 'pares_fortes': 0, 'pares_fracos': 0}

        lifts = []
        pares_fortes = 0
        pares_fracos = 0

        for i in range(len(jogo)):
            for j in range(i + 1, len(jogo)):
                a, b = jogo[i] - 1, jogo[j] - 1
                if 0 <= a < self.universo and 0 <= b < self.universo:
                    lift = float(matriz_lift[a, b])
                    lifts.append(lift)
                    if lift > 1.15:
                        pares_fortes += 1
                    elif lift < 0.85:
                        pares_fracos += 1

        lift_medio = float(np.mean(lifts)) if lifts else 1.0

        # Score: lift médio próximo de 1.0 a 1.2 é ideal
        # Lift muito alto pode indicar viés
        if 1.0 <= lift_medio <= 1.20:
            score = 10.0
        elif 0.90 <= lift_medio < 1.0 or 1.20 < lift_medio <= 1.35:
            score = 7.0
        elif lift_medio >= 0.80:
            score = 4.0
        else:
            score = 2.0

        return score, {
            'lift_medio': round(lift_medio, 4),
            'pares_fortes': pares_fortes,
            'pares_fracos': pares_fracos,
        }

    def _analisar_numeros_individuais(self, jogo: List[int]) -> List[dict]:
        """Gera análise individual de cada número do jogo."""
        resultado = []

        for n in sorted(jogo):
            info_dni = self.indices_atraso.get(n, {})
            dni = info_dni.get('dni', 0)
            atraso = info_dni.get('atraso_atual', 0)
            classificacao_dni = info_dni.get('classificacao', '—')

            # Afinidade média deste número com os demais do jogo
            afins = []
            matriz_lift = self.matriz_afinidade.get('matriz_lift')
            if matriz_lift is not None:
                for m in jogo:
                    if m != n:
                        a, b = n - 1, m - 1
                        if 0 <= a < self.universo and 0 <= b < self.universo:
                            afins.append(float(matriz_lift[a, b]))

            afinidade_media = round(float(np.mean(afins)), 4) if afins else 1.0

            # Gerar texto de vantagem/desvantagem
            vantagens = []
            if dni > 2:
                vantagens.append(f'Alto atraso histórico (DNI +{dni:.1f})')
            elif dni > 0:
                vantagens.append(f'Levemente devido (DNI +{dni:.1f})')
            elif dni < -2:
                vantagens.append(f'Saiu recentemente (DNI {dni:.1f})')

            if afinidade_media > 1.10:
                vantagens.append(f'Boa afinidade com o grupo (Lift {afinidade_media:.2f})')
            elif afinidade_media < 0.90:
                vantagens.append(f'Baixa afinidade com o grupo (Lift {afinidade_media:.2f})')

            if not vantagens:
                vantagens.append('Sem destaque (padrão neutro)')

            resultado.append({
                'numero': n,
                'dni': dni,
                'atraso_atual': atraso,
                'classificacao_dni': classificacao_dni,
                'afinidade_media': afinidade_media,
                'vantagem': '; '.join(vantagens),
            })

        return resultado

    def _gerar_justificativa_textual(
        self,
        jogo: List[int],
        nota_final: int,
        filtros: dict,
        analise_por_numero: List[dict],
    ) -> str:
        """Constrói texto human-readable para o frontend."""
        partes = []

        # Nota geral
        partes.append(f'Nota final: {nota_final}/100.')

        # Soma
        f_soma = filtros.get('soma', {})
        if f_soma.get('aprovado'):
            partes.append(f'Soma {f_soma["valor"]} dentro da faixa ideal ({f_soma["faixa"]}).')
        else:
            partes.append(f'⚠️ Soma {f_soma.get("valor", "?")} fora da faixa {f_soma.get("faixa", "?")}.')

        # Entropia
        f_ent = filtros.get('entropia', {})
        h_norm = f_ent.get('entropia_normalizada', 0)
        if h_norm >= 0.85:
            partes.append(f'Entropia normalizada {h_norm:.2f} (excelente distribuição).')
        elif h_norm >= 0.70:
            partes.append(f'Entropia normalizada {h_norm:.2f} (boa distribuição).')
        else:
            partes.append(f'⚠️ Entropia normalizada {h_norm:.2f} (concentração detectada).')

        # Espaçamento
        f_gap = filtros.get('espacamento', {})
        if f_gap.get('aprovado'):
            partes.append('Espaçamento entre números dentro do padrão histórico.')
        else:
            partes.append('⚠️ Espaçamento irregular entre os números.')

        # Zona Espacial
        f_zona = filtros.get('zona_espacial', {})
        qp = f_zona.get('quadrantes_presentes', 0)
        partes.append(f'Cobertura espacial: {qp}/4 quadrantes do volante.')

        # DNI
        f_dni = filtros.get('dni', {})
        devidos = f_dni.get('numeros_devidos', 0)
        if devidos > 0:
            nums_dev = [
                str(a['numero']) for a in analise_por_numero
                if a['dni'] > 1.5
            ][:4]
            if nums_dev:
                partes.append(
                    f'{devidos} números com alto atraso histórico '
                    f'(destaque: {", ".join(nums_dev)}).'
                )

        # Afinidade
        f_afin = filtros.get('afinidade', {})
        pf = f_afin.get('pares_fortes', 0)
        if pf > 0:
            partes.append(f'{pf} pares com afinidade acima da média.')

        return ' '.join(partes)
