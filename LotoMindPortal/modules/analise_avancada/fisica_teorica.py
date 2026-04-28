"""
LotoMind Portal — Motor de Física Teórica
============================================
Simulações baseadas em modelos de física teórica aplicados
à dinâmica das bolinhas dentro do globo de sorteio.

3 Modelos:
  1. Peso da Tinta (Viés de Gravidade) — massa fictícia por dígito
  2. Termodinâmica (Resfriamento de Newton) — temperatura dinâmica
  3. Simulador de Colisão (Browniano) — energia cinética por bolinha

100% vetorizado com NumPy para performance em ambiente web.
Autor: LotoMind Engineering
"""

import math
import numpy as np
from typing import List, Dict, Optional


# ════════════════════════════════════════════════════════════
#  1. PESO DA TINTA (VIÉS DE GRAVIDADE)
# ════════════════════════════════════════════════════════════

# Área relativa de tinta para cada dígito (0-9).
# Baseado na complexidade visual do glifo:
#   '8' tem mais curvas e mais tinta que '1'.
#   Escala normalizada de 0.0 a 1.0.
AREA_TINTA_DIGITOS = {
    0: 0.72,   # '0' — oval fechado, boa área
    1: 0.30,   # '1' — traço vertical simples, mínimo de tinta
    2: 0.65,   # '2' — curva + base horizontal
    3: 0.68,   # '3' — duas semicurvas
    4: 0.55,   # '4' — linhas retas angulares
    5: 0.63,   # '5' — curva + topo reto
    6: 0.70,   # '6' — curva grande com laço
    7: 0.42,   # '7' — duas linhas simples
    8: 0.82,   # '8' — duas curvas fechadas, máxima tinta
    9: 0.70,   # '9' — espelho do 6
}

# Fator de escala base da bolinha (plástico + esfera)
MASSA_BASE_BOLINHA = 1.0  # gramas fictícias
FATOR_TINTA = 0.05        # Cada unidade de área → +0.05g


def calcular_peso_tinta(numero: int) -> dict:
    """
    Estima o peso fictício de uma bolinha baseado na quantidade de tinta
    necessária para imprimir o número nela.

    O peso total = massa_base + Σ(área_tinta_dígito × fator_tinta).

    Números com mais dígitos e dígitos mais "cheios" (como 8, 0, 6)
    são levemente mais pesados, simulando uma microdesvantagem
    gravitacional dentro do globo giratório.

    Args:
        numero: O número da bolinha (1-60).

    Returns:
        {
            numero, digitos, area_tinta_total, massa_gramas,
            penalidade_gravitacional, classificacao
        }
    """
    digitos = str(numero)
    area_total = sum(AREA_TINTA_DIGITOS.get(int(d), 0.5) for d in digitos)

    # Bônus por quantidade de dígitos (2 dígitos = mais superfície de impressão)
    fator_digitos = len(digitos) * 0.1

    massa = MASSA_BASE_BOLINHA + (area_total + fator_digitos) * FATOR_TINTA

    # Penalidade gravitacional: quanto mais pesado, mais lento o quique
    # Normalizada para [0, 1] onde 0 = sem penalidade, 1 = máxima
    # Massa mínima teórica: 1.0 + (0.30 + 0.1) × 0.05 = 1.020
    # Massa máxima teórica: 1.0 + (0.82×2 + 0.2) × 0.05 = 1.092 (num 88)
    massa_min = 1.020
    massa_max = 1.092
    penalidade = (massa - massa_min) / max(massa_max - massa_min, 0.001)
    penalidade = max(0.0, min(1.0, penalidade))

    if penalidade <= 0.25:
        classificacao = '🪶 Ultraleve — Quica com facilidade'
    elif penalidade <= 0.50:
        classificacao = '⚖️ Leve — Comportamento normal'
    elif penalidade <= 0.75:
        classificacao = '🏋️ Moderado — Leve resistência gravitacional'
    else:
        classificacao = '🧱 Pesado — Mais lento dentro do globo'

    return {
        'numero': numero,
        'digitos': digitos,
        'area_tinta_total': round(area_total, 3),
        'massa_gramas': round(massa, 4),
        'penalidade_gravitacional': round(penalidade, 4),
        'classificacao': classificacao,
    }


def calcular_pesos_tinta_batch(universo: int = 25) -> Dict[int, dict]:
    """Calcula peso de tinta para todos os números do universo."""
    return {n: calcular_peso_tinta(n) for n in range(1, universo + 1)}


# ════════════════════════════════════════════════════════════
#  2. TERMODINÂMICA (RESFRIAMENTO DE NEWTON)
# ════════════════════════════════════════════════════════════

# Constantes do modelo termodinâmico
T_AMBIENTE = 20.0       # Temperatura ambiente (°C fictícios)
T_EBULICAO = 100.0      # Temperatura ao ser sorteado
K_RESFRIAMENTO = 0.15   # Constante de resfriamento (taxa de decaimento)
T_PONTO_IDEAL_MIN = 55.0  # Faixa do "ponto de ebulição" ideal
T_PONTO_IDEAL_MAX = 75.0


def calcular_temperatura_newton(
    numero: int,
    historico_sorteios: List[List[int]],
    t_ambiente: float = T_AMBIENTE,
    t_ebulicao: float = T_EBULICAO,
    k: float = K_RESFRIAMENTO,
) -> dict:
    """
    Aplica a Lei de Resfriamento de Newton para calcular a "temperatura"
    atual de um número baseado em seu histórico de aparições.

    Fórmula: T(t) = T_env + (T_0 - T_env) × e^{-kt}

    Onde:
      - T_env = temperatura ambiente (20°C)
      - T_0 = temperatura inicial ao ser sorteado (100°C)
      - k = constante de resfriamento (0.15)
      - t = concursos desde a última aparição

    Um número "esquenta" instantaneamente quando é sorteado e vai
    perdendo calor exponencialmente a cada concurso que fica de fora.

    O sistema prioriza números no "ponto de ebulição" (55-75°C):
    quentes o suficiente para indicar tendência, mas prestes a esfriar.

    Args:
        numero: O número a analisar.
        historico_sorteios: Lista de sorteios (do mais recente ao mais antigo).
        t_ambiente: Temperatura ambiente.
        t_ebulicao: Temperatura de "aquecimento" ao sair.
        k: Constante de resfriamento.

    Returns:
        {
            numero, temperatura, delta_t_desde_ultimo,
            fase_termica, no_ponto_ebulicao, historico_termico
        }
    """
    n_jogos = len(historico_sorteios)
    if n_jogos == 0:
        return {
            'numero': numero,
            'temperatura': t_ambiente,
            'delta_t_desde_ultimo': n_jogos,
            'fase_termica': '❄️ Congelado',
            'no_ponto_ebulicao': False,
            'historico_termico': [],
        }

    # Encontrar todas as aparições (índices, do mais recente=0 ao mais antigo)
    aparicoes = []
    for i, sorteio in enumerate(historico_sorteios):
        if numero in sorteio:
            aparicoes.append(i)

    if not aparicoes:
        # Número nunca apareceu no histórico analisado
        temperatura = t_ambiente
        delta_t = n_jogos
    else:
        # A temperatura é determinada pela ÚLTIMA aparição
        ultimo_sorteio = aparicoes[0]  # Mais recente (índice 0 = último concurso)
        delta_t = ultimo_sorteio       # t = concursos desde a última aparição

        # T(t) = T_env + (T_0 - T_env) × e^{-kt}
        temperatura = t_ambiente + (t_ebulicao - t_ambiente) * math.exp(-k * delta_t)

    # Calcular curva térmica recente (últimos 20 concursos para visualização)
    historico_termico = []
    # Recalcular temperatura em cada ponto do tempo
    for t_ponto in range(min(20, n_jogos)):
        # Verificar se o número apareceu no concurso t_ponto ou antes
        atraso_no_ponto = None
        for i in range(t_ponto, n_jogos):
            if numero in historico_sorteios[i]:
                atraso_no_ponto = i - t_ponto
                break

        if atraso_no_ponto is not None:
            temp_ponto = t_ambiente + (t_ebulicao - t_ambiente) * math.exp(-k * atraso_no_ponto)
        else:
            temp_ponto = t_ambiente

        historico_termico.append(round(temp_ponto, 1))

    # Classificação da fase térmica
    if temperatura >= 85:
        fase = '🔴 Superaquecido — Acabou de sair'
    elif temperatura >= T_PONTO_IDEAL_MAX:
        fase = '🟠 Muito Quente — Esfriando rapidamente'
    elif temperatura >= T_PONTO_IDEAL_MIN:
        fase = '🟡 Ponto de Ebulição — Momento IDEAL'
    elif temperatura >= 35:
        fase = '🔵 Morno — Tendência de retorno'
    else:
        fase = '❄️ Frio — Longa ausência'

    no_ponto = T_PONTO_IDEAL_MIN <= temperatura <= T_PONTO_IDEAL_MAX

    return {
        'numero': numero,
        'temperatura': round(temperatura, 2),
        'delta_t_desde_ultimo': delta_t,
        'fase_termica': fase,
        'no_ponto_ebulicao': no_ponto,
        'historico_termico': historico_termico,
    }


def calcular_temperaturas_batch(
    historico_sorteios: List[List[int]],
    universo: int = 25,
    **kwargs,
) -> Dict[int, dict]:
    """Calcula temperaturas para todos os números do universo."""
    return {
        n: calcular_temperatura_newton(n, historico_sorteios, **kwargs)
        for n in range(1, universo + 1)
    }


def ranking_temperatura(
    historico_sorteios: List[List[int]],
    universo: int = 25,
    **kwargs,
) -> List[dict]:
    """
    Retorna ranking de números ordenados pela proximidade ao
    ponto de ebulição ideal (55-75°C).
    """
    temps = calcular_temperaturas_batch(historico_sorteios, universo, **kwargs)
    ranking = []
    for n, info in temps.items():
        t = info['temperatura']
        # Distância ao centro do ponto ideal
        centro_ideal = (T_PONTO_IDEAL_MIN + T_PONTO_IDEAL_MAX) / 2
        distancia = abs(t - centro_ideal)
        ranking.append({**info, 'distancia_ideal': round(distancia, 2)})

    return sorted(ranking, key=lambda x: x['distancia_ideal'])


# ════════════════════════════════════════════════════════════
#  3. SIMULADOR DE COLISÃO (MOVIMENTO BROWNIANO)
# ════════════════════════════════════════════════════════════

class GloboFisicoSimulator:
    """
    Simula o comportamento físico de bolinhas dentro de um globo
    de sorteio usando um modelo simplificado de colisões brownianas.

    Em vez de usar random.sample, o simulador:
      1. Inicializa N bolinhas com energia cinética aleatória
      2. Aplica viés gravitacional (peso da tinta)
      3. Simula colisões em pares durante X iterações
      4. Os números com maior energia cinética ao final são "sorteados"

    O modelo é simplificado para executar em < 100ms via NumPy vetorizado.
    """

    def __init__(
        self,
        universo: int = 25,
        dezenas_sorteio: int = 15,
        iteracoes: int = 200,
        fator_colisao: float = 0.3,
        fator_atrito: float = 0.02,
    ):
        """
        Args:
            universo: Total de bolinhas no globo.
            dezenas_sorteio: Quantas bolinhas saem do globo.
            iteracoes: Número de ciclos de simulação.
            fator_colisao: Fração de energia transferida em colisões (0-1).
            fator_atrito: Perda de energia por iteração (resistência do ar).
        """
        self.universo = universo
        self.dezenas_sorteio = dezenas_sorteio
        self.iteracoes = iteracoes
        self.fator_colisao = fator_colisao
        self.fator_atrito = fator_atrito

        # Pesos de tinta pré-calculados
        self._pesos = np.array([
            calcular_peso_tinta(n)['massa_gramas']
            for n in range(1, universo + 1)
        ], dtype=np.float64)

        # Penalidades gravitacionais
        self._penalidades = np.array([
            calcular_peso_tinta(n)['penalidade_gravitacional']
            for n in range(1, universo + 1)
        ], dtype=np.float64)

    def simular(
        self,
        energia_inicial: Optional[np.ndarray] = None,
        temperaturas: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
    ) -> dict:
        """
        Executa a simulação do globo físico.

        Args:
            energia_inicial: Array (UNIVERSO,) com energia cinética inicial
                            para cada bolinha. Se None, gera aleatoriamente.
            temperaturas: Array (UNIVERSO,) com temperaturas de Newton para
                         cada bolinha (usado como boost de energia).
            seed: Seed para reprodutibilidade.

        Returns:
            {
                sorteados: list[int],
                energias_finais: dict[int, float],
                log_simulacao: {iteracoes, colisoes_totais, energia_media_final},
                detalhes_por_bolinha: [{numero, energia_final, rank, sorteado}]
            }
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = np.random.default_rng()

        N = self.universo

        # ── 1. Energia cinética inicial ──
        if energia_inicial is not None:
            E = energia_inicial.copy().astype(np.float64)
        else:
            # Distribuição Maxwell-Boltzmann simplificada (chi-squared com 3 DoF)
            E = rng.chisquare(df=3, size=N).astype(np.float64)

        # ── 2. Boost de temperatura (se fornecido) ──
        if temperaturas is not None:
            # Normalizar temperaturas para [0, 1] e aplicar como boost
            t_norm = (temperaturas - T_AMBIENTE) / max(T_EBULICAO - T_AMBIENTE, 1)
            t_norm = np.clip(t_norm, 0, 1)
            # Boost: números "quentes" ganham até 30% mais energia
            E *= (1.0 + t_norm * 0.3)

        # ── 3. Aplicar viés gravitacional ──
        # Bolinhas mais pesadas perdem uma fração de energia proporcional
        # à sua penalidade gravitacional (simula quique mais lento)
        E *= (1.0 - self._penalidades * 0.15)

        # ── 4. Loop de colisões ──
        colisoes_totais = 0
        for _ in range(self.iteracoes):
            # Selecionar pares aleatórios de bolinhas que colidem
            # ~30% das bolinhas colidem em cada iteração
            n_colisoes = max(1, N // 3)
            idx_a = rng.integers(0, N, size=n_colisoes)
            idx_b = rng.integers(0, N, size=n_colisoes)

            # Evitar auto-colisão
            mask_valido = idx_a != idx_b
            idx_a = idx_a[mask_valido]
            idx_b = idx_b[mask_valido]

            if len(idx_a) == 0:
                continue

            colisoes_totais += len(idx_a)

            # Transferência parcial de energia (colisão inelástica simplificada)
            # A bolinha mais energética transfere uma fração para a menos energética
            E_a = E[idx_a]
            E_b = E[idx_b]

            # Quem tem mais energia perde, quem tem menos ganha
            delta = (E_a - E_b) * self.fator_colisao

            # Fator de massa: bolinhas mais pesadas transferem menos energia
            peso_a = self._pesos[idx_a]
            peso_b = self._pesos[idx_b]
            fator_massa = peso_b / (peso_a + peso_b)  # Conservation-like

            transferencia = delta * fator_massa

            E[idx_a] -= transferencia
            E[idx_b] += transferencia

            # ── Perturbação browniana (ruído térmico) ──
            E += rng.normal(0, 0.1, size=N)

            # ── Atrito (perda de energia por resistência do ar) ──
            E *= (1.0 - self.fator_atrito)

            # ── Garantir energia não-negativa ──
            E = np.maximum(E, 0.01)

        # ── 5. Selecionar os "sorteados" (maior energia cinética) ──
        ranking_indices = np.argsort(E)[::-1]
        sorteados_indices = ranking_indices[:self.dezenas_sorteio]
        sorteados = sorted((sorteados_indices + 1).tolist())

        # ── 6. Compilar resultados ──
        detalhes = []
        for rank, idx in enumerate(ranking_indices):
            numero = int(idx + 1)
            detalhes.append({
                'numero': numero,
                'energia_final': round(float(E[idx]), 4),
                'rank': rank + 1,
                'sorteado': numero in sorteados,
            })

        # Ordenar detalhes por número
        detalhes.sort(key=lambda x: x['numero'])

        energias_dict = {int(i + 1): round(float(E[i]), 4) for i in range(N)}

        return {
            'sorteados': sorteados,
            'energias_finais': energias_dict,
            'log_simulacao': {
                'iteracoes': self.iteracoes,
                'colisoes_totais': colisoes_totais,
                'energia_media_final': round(float(np.mean(E)), 4),
                'energia_max_final': round(float(np.max(E)), 4),
                'energia_min_final': round(float(np.min(E)), 4),
                'desvio_padrao_energia': round(float(np.std(E)), 4),
            },
            'detalhes_por_bolinha': detalhes,
        }

    def gerar_jogo_fisico(
        self,
        historico_sorteios: Optional[List[List[int]]] = None,
        n_simulacoes: int = 5,
        seed: Optional[int] = None,
    ) -> dict:
        """
        Gera um jogo usando a média de múltiplas simulações físicas.

        Executa N simulações independentes e conta a frequência com que
        cada número aparece como "sorteado". Os mais frequentes são escolhidos.

        Args:
            historico_sorteios: Histórico para calcular temperaturas.
            n_simulacoes: Quantidade de simulações a executar.
            seed: Seed base para reprodutibilidade.

        Returns:
            {jogo, confianca_fisica, frequencia_simulacoes, simulacao_detalhada}
        """
        # Limitar para não travar backend
        n_simulacoes = min(n_simulacoes, 20)

        # Calcular temperaturas se houver histórico
        temperaturas = None
        if historico_sorteios:
            temps_data = calcular_temperaturas_batch(
                historico_sorteios, universo=self.universo
            )
            temperaturas = np.array([
                temps_data[n]['temperatura']
                for n in range(1, self.universo + 1)
            ], dtype=np.float64)

        # Executar múltiplas simulações
        contagem = np.zeros(self.universo, dtype=int)
        ultima_simulacao = None

        for i in range(n_simulacoes):
            s = seed + i if seed is not None else None
            resultado = self.simular(temperaturas=temperaturas, seed=s)
            for num in resultado['sorteados']:
                contagem[num - 1] += 1
            if i == n_simulacoes - 1:
                ultima_simulacao = resultado

        # Selecionar os mais frequentes entre as simulações
        ranking = np.argsort(contagem)[::-1]
        jogo = sorted((ranking[:self.dezenas_sorteio] + 1).tolist())

        # Confiança física: proporção média de aparições
        max_aparicoes = n_simulacoes
        confianca = float(np.mean(np.sort(contagem)[::-1][:self.dezenas_sorteio]))
        confianca_pct = round((confianca / max_aparicoes) * 100, 1)

        frequencia = {
            int(i + 1): int(contagem[i])
            for i in range(self.universo)
        }

        return {
            'jogo': jogo,
            'confianca_fisica': confianca_pct,
            'n_simulacoes': n_simulacoes,
            'frequencia_simulacoes': frequencia,
            'simulacao_detalhada': ultima_simulacao,
        }


# ════════════════════════════════════════════════════════════
#  ANÁLISE FÍSICA COMPLETA (Para integração no Avaliador)
# ════════════════════════════════════════════════════════════

def analisar_fisica_jogo(
    combinacao: List[int],
    historico_sorteios: List[List[int]],
    universo: int = 25,
) -> dict:
    """
    Função de conveniência que executa toda a análise física para
    uma combinação e retorna os resultados formatados para o boletim.

    Args:
        combinacao: Dezenas do jogo a analisar.
        historico_sorteios: Histórico de sorteios.
        universo: Tamanho do universo numérico.

    Returns:
        {
            massa: {media, min, max, classificacao},
            termodinamica: {temp_media, no_ponto_ebulicao, fase_dominante},
            energia_cinetica: {simulacao, energia_media_sorteados},
            score_fisico: float (0-100),
        }
    """
    jogo = sorted(combinacao)

    # ── 1. Análise de Massa ──
    massas = [calcular_peso_tinta(n) for n in jogo]
    massa_valores = [m['massa_gramas'] for m in massas]
    penalidades = [m['penalidade_gravitacional'] for m in massas]
    penalidade_media = float(np.mean(penalidades))

    # Score de massa: penalidade baixa = bom (bolinhas leves quicam mais)
    score_massa = max(0, 10.0 * (1.0 - penalidade_media))

    massa_info = {
        'media': round(float(np.mean(massa_valores)), 4),
        'min': round(float(np.min(massa_valores)), 4),
        'max': round(float(np.max(massa_valores)), 4),
        'penalidade_media': round(penalidade_media, 4),
        'score': round(score_massa, 1),
        'detalhes': massas,
    }

    # ── 2. Análise Termodinâmica ──
    if historico_sorteios:
        temps = [
            calcular_temperatura_newton(n, historico_sorteios)
            for n in jogo
        ]
    else:
        temps = [{'temperatura': T_AMBIENTE, 'no_ponto_ebulicao': False,
                  'fase_termica': '❄️ Frio'} for _ in jogo]

    temp_valores = [t['temperatura'] for t in temps]
    no_ponto = sum(1 for t in temps if t.get('no_ponto_ebulicao', False))
    temp_media = float(np.mean(temp_valores))

    # Fase dominante
    fases = [t['fase_termica'] for t in temps]
    from collections import Counter
    fase_contagem = Counter(fases)
    fase_dominante = fase_contagem.most_common(1)[0][0] if fase_contagem else '—'

    # Score termodinâmico: mais números no "ponto de ebulição" = melhor
    proporcao_ideal = no_ponto / max(len(jogo), 1)
    score_termo = 10.0 * proporcao_ideal

    # Bônus se temperatura média estiver perto do ideal (55-75°C)
    centro_ideal = (T_PONTO_IDEAL_MIN + T_PONTO_IDEAL_MAX) / 2
    dist_ideal = abs(temp_media - centro_ideal)
    bonus_temp = max(0, 5.0 * (1 - dist_ideal / centro_ideal))
    score_termo = min(15.0, score_termo + bonus_temp)

    termo_info = {
        'temperatura_media': round(temp_media, 2),
        'numeros_no_ponto_ebulicao': no_ponto,
        'total_numeros': len(jogo),
        'fase_dominante': fase_dominante,
        'score': round(score_termo, 1),
        'detalhes': temps,
    }

    # ── 3. Energia Cinética (mini-simulação rápida) ──
    dezenas_sorteio = len(jogo)
    sim = GloboFisicoSimulator(
        universo=universo,
        dezenas_sorteio=dezenas_sorteio,
        iteracoes=100,  # Reduzido para velocidade
    )
    resultado_sim = sim.simular()

    # Verificar quantos números do jogo teriam sido "sorteados" pela simulação
    sorteados_sim = set(resultado_sim['sorteados'])
    coincidencias = len(set(jogo) & sorteados_sim)
    proporcao_coincidencia = coincidencias / max(dezenas_sorteio, 1)

    # Energia média dos números DO JOGO na simulação
    energias_jogo = [
        resultado_sim['energias_finais'].get(n, 0)
        for n in jogo
    ]
    energia_media_jogo = float(np.mean(energias_jogo)) if energias_jogo else 0

    score_energia = min(10.0, 10.0 * proporcao_coincidencia + 2.0)

    energia_info = {
        'energia_media_jogo': round(energia_media_jogo, 4),
        'energia_media_global': resultado_sim['log_simulacao']['energia_media_final'],
        'coincidencias_com_simulacao': coincidencias,
        'total_sorteados_simulacao': dezenas_sorteio,
        'score': round(score_energia, 1),
        'log': resultado_sim['log_simulacao'],
    }

    # ── Score Físico Combinado (0-35 pts → normalizado para 0-100) ──
    score_bruto = score_massa + score_termo + score_energia
    score_normalizado = round(min(100, score_bruto / 35.0 * 100))

    # Classificação física
    if score_normalizado >= 75:
        classif = '⚛️ QUÂNTICO — Dinâmica física excepcional'
    elif score_normalizado >= 55:
        classif = '🔬 NEWTONIANO — Boa consistência física'
    elif score_normalizado >= 35:
        classif = '🌡️ TERMODINÂMICO — Física moderada'
    else:
        classif = '🪨 INERTE — Baixa energia física'

    return {
        'massa': massa_info,
        'termodinamica': termo_info,
        'energia_cinetica': energia_info,
        'score_fisico': score_normalizado,
        'score_bruto': round(score_bruto, 1),
        'classificacao_fisica': classif,
    }
