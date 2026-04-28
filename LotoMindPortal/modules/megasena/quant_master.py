"""
LotoMind Quant-Master — Motor de Geração Elite (Mega-Sena)
==========================================================
Baseado no "Prompt Mestre" — Foco em Maximização do EV via
redução de colisão com apostas humanas.

AXIOMA FUNDAMENTAL
  p(qualquer combo) = 1 / 50.063.860  →  constante e imutável.
  Objetivo: maximizar EV = Prêmio / N_Ganhadores.
  Estratégia: gerar apostas com baixíssima probabilidade de
  serem escolhidas por outros apostadores (SIH alto).

Pilares
  1. Filtro de Viés Comportamental (Behavioral Bias Filter)
      • Viés de Calendário (≥ 4 números ≤ 31)
      • Viés de Geometria (linhas/colunas/aglomerações no volante 6×10)
      • Viés de Progressão (sequências aritméticas óbvias)

  2. Otimização de Soma e Entropia
      • Alvo: soma entre 170 e 230 (cauda direita da distribuição)
      • Maximizar dispersão nos 4 quadrantes
      • Priorizar primos obscuros e pares altos

  3. Teoria do Jogo Contrário (Contrarian Trading)
      • Mapa de calor: top 10 quentes e top 10 atrasadas
      • Rejeitar combos onde todos os 6 números estão no cluster da manada

  4. Monte Carlo Elite (vetorizado com NumPy)
      • Gera N candidatos aleatórios em batch
      • Aplica filtros como máscaras vetorizadas
      • Seleciona os K com maior SIH
"""

from __future__ import annotations

import math
from collections import Counter
from itertools import combinations
from typing import Dict, List, Tuple

import numpy as np

# ─── Constantes ────────────────────────────────────────────────────────────────

UNIVERSO: int = 60            # dezenas da Mega-Sena
DEZENAS_SORTEIO: int = 6      # bolas sorteadas
PROBABILIDADE: float = 1 / 50_063_860  # p exata de qualquer combo

# Soma média teórica de 6 números de 1–60: (1+60)/2 * 6 = 183
SOMA_MEDIA_TEORICA: float = 183.0
SOMA_META_MIN: int = 170      # cauda direita onde há menos apostadores
SOMA_META_MAX: int = 230

# Matriz do volante físico (6 linhas × 10 colunas)
# VOLANTE[linha][coluna] = número
VOLANTE: np.ndarray = np.arange(1, 61).reshape(6, 10)  # (6, 10)

# Quadrantes (mesmo padrão do trade_engine.py existente)
QUADRANTES: Dict[str, List[int]] = {
    'Q1': list(range(1, 16)),
    'Q2': list(range(16, 31)),
    'Q3': list(range(31, 46)),
    'Q4': list(range(46, 61)),
}

# Primos obscuros e pares altos (alta entropia)
PRIMOS_ALTOS: set = {37, 41, 43, 47, 53, 59}
PARES_ALTOS: set = {46, 48, 50, 52, 54, 56, 58, 60}
ALTA_ENTROPIA: set = PRIMOS_ALTOS | PARES_ALTOS


# ─── Motor Principal ───────────────────────────────────────────────────────────

class QuantMasterEngine:
    """
    Motor de geração elite para Mega-Sena.
    Maximiza o EV via SIH (Score de Improbabilidade Humana).
    """

    N_CANDIDATOS: int = 50_000   # candidatos Monte Carlo por execução
    SIH_MINIMO: int = 72         # threshold mínimo de qualidade

    def __init__(self) -> None:
        self._historico: List[List[int]] = []   # lista de sorteios [[n1..n6], ...]
        self._quentes: List[int] = []           # top 10 mais frequentes
        self._atrasadas: List[int] = []         # top 10 mais atrasadas
        self._soma_media_hist: float = SOMA_MEDIA_TEORICA
        self._soma_std_hist: float = 25.0
        self._carregado: bool = False

    # ─── Carregamento ──────────────────────────────────────────────────────────

    def carregar_historico(self, df) -> None:
        """Carrega DataFrame histórico (mesma estrutura do MegaSenaEngine)."""
        if df is None or df.empty:
            return

        df_ord = df.sort_values('Concurso', ascending=False).reset_index(drop=True)
        self._historico = [list(row['Dezenas']) for _, row in df_ord.iterrows()]

        # Estatísticas de soma
        somas = df_ord['Soma'].values.astype(float)
        self._soma_media_hist = float(np.mean(somas))
        self._soma_std_hist = float(np.std(somas, ddof=1)) if len(somas) > 1 else 25.0

        # Top 10 quentes (mais frequentes no histórico total)
        todas = [n for sorteio in self._historico for n in sorteio]
        contagem = Counter(todas)
        self._quentes = [n for n, _ in contagem.most_common(10)]

        # Top 10 mais atrasadas (maior ciclo sem aparecer)
        ciclos = self._calcular_ciclos()
        self._atrasadas = sorted(ciclos, key=ciclos.get, reverse=True)[:10]

        self._carregado = True

    def _calcular_ciclos(self) -> Dict[int, int]:
        """Calcula atraso de cada dezena (concursos sem aparecer)."""
        ciclos: Dict[int, int] = {}
        for dezena in range(1, UNIVERSO + 1):
            atraso = 0
            for sorteio in self._historico:
                if dezena in sorteio:
                    break
                atraso += 1
            ciclos[dezena] = atraso
        return ciclos

    # ─── Pilar 1 — Filtros de Viés Comportamental ─────────────────────────────

    def _filtro_calendario(self, combo: np.ndarray) -> bool:
        """
        Rejeita se ≥ 4 números ≤ 31 (viés de datas de aniversário/calendário).
        Retorna True se APROVADO (sem viés).
        """
        return int(np.sum(combo <= 31)) < 4

    def _filtro_geometria(self, combo: np.ndarray) -> bool:
        """
        Rejeita padrões geométricos no volante físico 6×10.
        Retorna True se APROVADO (sem viés geométrico).
        """
        # Mapear cada dezena para (linha, coluna) no VOLANTE
        linhas = (combo - 1) // 10   # 0-indexed
        colunas = (combo - 1) % 10   # 0-indexed

        # Regra 1: todos os 6 na mesma linha (linha reta horizontal)
        if len(set(linhas)) == 1:
            return False

        # Regra 2: 5+ na mesma linha (quase linha perfeita)
        linha_contagem = Counter(linhas.tolist())
        if max(linha_contagem.values()) >= 5:
            return False

        # Regra 3: 4+ na mesma coluna (vertical)
        col_contagem = Counter(colunas.tolist())
        if max(col_contagem.values()) >= 4:
            return False

        # Regra 4: 5+ em apenas 2 linhas adjacentes (aglomeração)
        linhas_unicas = sorted(set(linhas.tolist()))
        if len(linhas_unicas) <= 2:
            return False

        # Regra 5: todos no mesmo quadrante
        for _, nums_q in QUADRANTES.items():
            if all(int(n) in nums_q for n in combo):
                return False

        return True

    def _filtro_progressao(self, combo: np.ndarray) -> bool:
        """
        Rejeita sequências aritméticas óbvias.
        Ex: 5,10,15,20,25,30 (passo 5) ou 10,20,30,40,50,60 (passo 10).
        Retorna True se APROVADO.
        """
        arr = np.sort(combo)
        diffs = np.diff(arr)

        # Se todas as diferenças são iguais = progressão aritmética pura
        if len(set(diffs.tolist())) == 1:
            return False

        # Progressão óbvia com passo 5 ou 10: ≥ 4 múltiplos do mesmo passo
        for passo in [5, 10, 15]:
            multiplos = np.sum(arr % passo == 0)
            if multiplos >= 4:
                return False

        return True

    def _filtro_contrarian(self, combo: np.ndarray) -> bool:
        """
        Rejeita combos onde TODOS os 6 estão nas top-10 quentes OU top-10 atrasadas
        (onde a manada está apostando, ativada pela Falácia do Apostador).
        Retorna True se APROVADO.
        """
        if not self._carregado:
            return True

        set_combo = set(combo.tolist())
        set_quentes = set(self._quentes)
        set_atrasadas = set(self._atrasadas)

        # Rejeita se todos os 6 no cluster quente
        if set_combo.issubset(set_quentes):
            return False

        # Rejeita se todos os 6 no cluster atrasado
        if set_combo.issubset(set_atrasadas):
            return False

        return True

    # ─── Pilar 2 — Score de Improbabilidade Humana (SIH) ──────────────────────

    def calcular_sih(self, combo: np.ndarray) -> Tuple[float, Dict]:
        """
        Calcula o SIH (0–100) de uma combinação.
        Quanto maior, mais "feia" e improvável para o cérebro humano.
        """
        arr = np.sort(combo)
        soma = int(arr.sum())
        detalhe: Dict = {}

        # ── Componente 1: Calendário (max 30 pts)
        n_abaixo_31 = int(np.sum(arr <= 31))
        # Normalizado: 0 abaixo=31 → 0 abaixo=5 (teto) → razão invertida
        ratio_cal = n_abaixo_31 / DEZENAS_SORTEIO
        score_cal = round(30 * (1 - ratio_cal), 2)
        detalhe['calendario'] = {'n_abaixo_31': n_abaixo_31, 'score': score_cal}

        # ── Componente 2: Geometria / Dispersão Quadrantes (max 25 pts)
        contagem_q = {}
        for q, nums in QUADRANTES.items():
            contagem_q[q] = sum(1 for n in arr if n in nums)
        max_q = max(contagem_q.values())
        # Aglomeração máxima em 1 quadrante → penalizar; dispersão ideal = ≤ 2 por quadrante
        aglom = max_q / DEZENAS_SORTEIO
        score_geo = round(25 * (1 - aglom), 2)
        detalhe['geometria'] = {'distribuicao_quad': contagem_q, 'max_num_quad': max_q, 'score': score_geo}

        # ── Componente 3: Soma na Cauda Direita (max 20 pts)
        # Soma ideal: entre 170 e 230. Penaliza quem fica próximo da média 183 (onde a manada está)
        if SOMA_META_MIN <= soma <= SOMA_META_MAX:
            # Dentro da zona target: premia quem está mais alto (mais distante da média humana)
            dist_normalizada = (soma - SOMA_META_MIN) / (SOMA_META_MAX - SOMA_META_MIN)
            score_soma = round(10 + 10 * dist_normalizada, 2)
        else:
            score_soma = 0.0
        detalhe['soma'] = {'valor': soma, 'meta_min': SOMA_META_MIN, 'meta_max': SOMA_META_MAX, 'score': score_soma}

        # ── Componente 4: Dispersão de Quadrantes (max 15 pts)
        # Premia cobertura de múltiplos quadrantes
        quad_cobertos = sum(1 for v in contagem_q.values() if v > 0)
        score_disp = round(15 * (quad_cobertos / 4), 2)
        detalhe['dispersao_quadrantes'] = {'quadrantes_cobertos': quad_cobertos, 'score': score_disp}

        # ── Componente 5: Primos Altos e Pares Altos (max 10 pts)
        n_alta_entropia = sum(1 for n in arr if int(n) in ALTA_ENTROPIA)
        score_entropia = round(10 * min(n_alta_entropia / 2, 1.0), 2)
        detalhe['alta_entropia'] = {'n_alta_entropia': n_alta_entropia, 'score': score_entropia}

        sih_total = min(100.0, score_cal + score_geo + score_soma + score_disp + score_entropia)
        sih_total = round(sih_total, 1)

        return sih_total, detalhe

    # ─── Pilar 3 — Justificativa Quantitativa ─────────────────────────────────

    def _gerar_justificativa(self, combo: np.ndarray, sih: float, detalhe: Dict) -> str:
        """Gera texto de justificativa quantitativa para cada jogo."""
        arr = sorted(combo.tolist())
        soma = sum(arr)
        dist_q = detalhe['geometria']['distribuicao_quad']
        n_alta = detalhe['alta_entropia']['n_alta_entropia']
        n_cal = detalhe['calendario']['n_abaixo_31']

        # Sigma da soma em relação ao histórico
        sigma = (soma - self._soma_media_hist) / max(self._soma_std_hist, 1)

        # Quadrantes cobertos
        q_cobertos = [f"{q}:{v}" for q, v in dist_q.items() if v > 0]
        quad_str = ", ".join(q_cobertos)

        # Itens de alta entropia presentes
        alta_presentes = [str(n) for n in arr if n in ALTA_ENTROPIA]
        entropia_str = (
            f"Alta entropia: {', '.join(alta_presentes)}. "
            if alta_presentes else "Sem primos/pares altos. "
        )

        return (
            f"Soma {soma} ({sigma:+.1f} dp acima da media historica de {self._soma_media_hist:.0f}). "
            f"Dispersao quadrantes: [{quad_str}]. "
            f"Apenas {n_cal} numero(s) <= 31 - vies de calendario minimo. "
            f"{entropia_str}"
            f"SIH {sih}/100 - combinacao estatisticamente improvavel para o apostador medio. "
            f"EV maximizado: baixa colisao com padroes humanos."
        )

    # ─── Pilar 4 — Monte Carlo Elite (Vetorizado) ─────────────────────────────

    def gerar_jogos(self, qtd: int = 5, n_candidatos: int = None) -> Dict:
        """
        Executa o Gerador MESTRE:
        1. Gera n_candidatos combinações aleatórias (NumPy vectorizado)
        2. Aplica os 3 filtros de viés como stop-loss
        3. Calcula SIH de cada sobrevivente
        4. Retorna os qtd melhores

        Returns dict com jogos gerados + metadados de execução.
        """
        if n_candidatos is None:
            n_candidatos = self.N_CANDIDATOS

        n_candidatos = int(n_candidatos)
        qtd = max(1, min(qtd, 10))

        # ── Geração em batch (vetorizado) ──────────────────────────────────────
        # Gerar todos os candidatos de uma vez usando vetorização NumPy
        rng = np.random.default_rng()

        # Batch de candidatos: cada linha é um combo de 6 dezenas únicas
        # Usamos permutação de colunas em linhas de arange para garantia de unicidade
        candidatos_raw: List[np.ndarray] = []
        batch_size = min(n_candidatos, 10_000)  # processa em batches de 10k
        n_batches = math.ceil(n_candidatos / batch_size)

        for _ in range(n_batches):
            # Gera batch_size × 60, depois pega os 6 primeiros de cada linha
            indices = np.argsort(rng.random((batch_size, UNIVERSO)), axis=1)[:, :DEZENAS_SORTEIO]
            batch = indices + 1  # dezenas 1-60
            candidatos_raw.append(batch)

        candidatos = np.vstack(candidatos_raw)  # shape: (n_candidatos, 6)

        # ── Aplicar filtros (Stop-Loss de Viés) ───────────────────────────────
        aprovados: List[Dict] = []
        rejeitados_stats = {'calendario': 0, 'geometria': 0, 'progressao': 0, 'contrarian': 0}

        for row in candidatos:
            combo = np.sort(row)

            # Filtro 1: Calendário
            if not self._filtro_calendario(combo):
                rejeitados_stats['calendario'] += 1
                continue

            # Filtro 2: Geometria
            if not self._filtro_geometria(combo):
                rejeitados_stats['geometria'] += 1
                continue

            # Filtro 3: Progressão
            if not self._filtro_progressao(combo):
                rejeitados_stats['progressao'] += 1
                continue

            # Filtro 4: Contrarian
            if not self._filtro_contrarian(combo):
                rejeitados_stats['contrarian'] += 1
                continue

            # ── Calcular SIH e filtrar soma alvo
            soma = int(combo.sum())
            if not (SOMA_META_MIN <= soma <= SOMA_META_MAX):
                continue

            sih, detalhe = self.calcular_sih(combo)

            if sih < self.SIH_MINIMO:
                continue

            aprovados.append({
                'combo': combo,
                'soma': soma,
                'sih': sih,
                'detalhe': detalhe,
            })

        n_sobreviventes = len(aprovados)

        # ── Selecionar os K melhores por SIH ───────────────────────────────────
        aprovados.sort(key=lambda x: x['sih'], reverse=True)

        # Garantir diversidade: remover combos muito similares
        selecionados = self._selecionar_diversos(aprovados, qtd)

        # ── Formatar output ────────────────────────────────────────────────────
        jogos_output = []
        for item in selecionados:
            combo = item['combo']
            sih = item['sih']
            detalhe = item['detalhe']
            dezenas = sorted(combo.tolist())

            # Distribuição por quadrante
            dist_q = {q: [n for n in dezenas if n in nums]
                      for q, nums in QUADRANTES.items()}

            # Presença nas listas de quentes/atrasadas
            n_quentes = sum(1 for n in dezenas if n in self._quentes)
            n_atrasadas = sum(1 for n in dezenas if n in self._atrasadas)

            jogos_output.append({
                'dezenas': dezenas,
                'soma': item['soma'],
                'sih': sih,
                'distribuicao_quadrantes': dist_q,
                'filtros_passados': {
                    'calendario': True,
                    'geometria': True,
                    'progressao': True,
                    'contrarian': True,
                },
                'analise': {
                    'n_abaixo_31': detalhe['calendario']['n_abaixo_31'],
                    'max_por_quadrante': detalhe['geometria']['max_num_quad'],
                    'quadrantes_cobertos': detalhe['dispersao_quadrantes']['quadrantes_cobertos'],
                    'n_alta_entropia': detalhe['alta_entropia']['n_alta_entropia'],
                    'n_quentes': n_quentes,
                    'n_atrasadas': n_atrasadas,
                    'sigma_soma': round(
                        (item['soma'] - self._soma_media_hist) / max(self._soma_std_hist, 1), 2
                    ),
                },
                'scores': {
                    'calendario': detalhe['calendario']['score'],
                    'geometria': detalhe['geometria']['score'],
                    'soma': detalhe['soma']['score'],
                    'dispersao': detalhe['dispersao_quadrantes']['score'],
                    'entropia': detalhe['alta_entropia']['score'],
                    'total_sih': sih,
                },
                'justificativa': self._gerar_justificativa(combo, sih, detalhe),
            })

        return {
            'jogos': jogos_output,
            'meta': {
                'n_candidatos_gerados': n_candidatos,
                'n_sobreviventes': n_sobreviventes,
                'taxa_aprovacao': round(n_sobreviventes / max(n_candidatos, 1) * 100, 2),
                'rejeicoes': rejeitados_stats,
                'soma_media_historica': round(self._soma_media_hist, 1),
                'soma_std_historica': round(self._soma_std_hist, 1),
                'quentes_referencia': self._quentes,
                'atrasadas_referencia': self._atrasadas,
                'sih_minimo_aplicado': self.SIH_MINIMO,
                'axioma': (
                    f"p = 1 / {50_063_860:,} para QUALQUER combinação. "
                    "Objetivo: minimizar colisão com apostadores humanos."
                ),
            },
        }

    def _selecionar_diversos(self, aprovados: List[Dict], qtd: int) -> List[Dict]:
        """
        Seleciona 'qtd' jogos garantindo diversidade mínima
        (evita combos que compartilhem 5+ dezenas entre si).
        """
        if len(aprovados) <= qtd:
            return aprovados

        selecionados: List[Dict] = []
        for item in aprovados:
            if len(selecionados) >= qtd:
                break
            combo_set = set(item['combo'].tolist())
            # Verificar se já temos um jogo muito parecido
            muito_similar = any(
                len(combo_set & set(s['combo'].tolist())) >= 5
                for s in selecionados
            )
            if not muito_similar:
                selecionados.append(item)

        # Se ainda não chegou em qtd, preenche sem critério de diversidade
        if len(selecionados) < qtd:
            for item in aprovados:
                if item not in selecionados:
                    selecionados.append(item)
                if len(selecionados) >= qtd:
                    break

        return selecionados[:qtd]

    # ─── Informações Estáticas ─────────────────────────────────────────────────

    def info_axioma(self) -> Dict:
        """Retorna o Axioma Fundamental e as métricas de referência."""
        return {
            'probabilidade_exata': PROBABILIDADE,
            'probabilidade_fmt': f"1 / {50_063_860:,}",
            'soma_media_teorica': SOMA_MEDIA_TEORICA,
            'soma_alvo_min': SOMA_META_MIN,
            'soma_alvo_max': SOMA_META_MAX,
            'universo': UNIVERSO,
            'dezenas_sorteio': DEZENAS_SORTEIO,
            'alta_entropia': sorted(ALTA_ENTROPIA),
            'n_combinacoes_totais': 50_063_860,
        }
