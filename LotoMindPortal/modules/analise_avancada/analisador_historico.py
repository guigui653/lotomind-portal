"""
LotoMind Portal — Analisador Histórico Avançado
=================================================
Funções de análise profunda do histórico de sorteios:
  1. Índice de Atraso Normalizado (DNI)
  2. Matriz de Afinidade (Lift de pares)
  3. Entropia de Shannon para combinações

100% vetorizado com NumPy para performance em ambiente web.
"""

import math
import numpy as np
from typing import List, Dict, Tuple


# ════════════════════════════════════════════════════════════
#  1. ÍNDICE DE ATRASO NORMALIZADO (DNI)
# ════════════════════════════════════════════════════════════

def calcular_indice_atraso(
    historico_sorteios: List[List[int]],
    universo: int = 25,
    dezenas_sorteio: int = 15,
) -> Dict[int, dict]:
    """
    Calcula o Delay Normalized Index (DNI) para cada número do universo.

    O DNI mede a diferença entre o intervalo médio esperado de aparição
    e o atraso atual (concursos consecutivos sem sair).

    DNI > 0  →  número "devido" (atraso acima da média esperada)
    DNI < 0  →  número "recente" (apareceu antes do intervalo médio)
    DNI ≈ 0  →  número no ritmo normal

    Args:
        historico_sorteios: Lista de sorteios (do mais recente ao mais antigo),
                           cada sorteio é uma lista de inteiros.
        universo: Total de números possíveis (25 para Lotofácil, 60 para Mega-Sena).
        dezenas_sorteio: Quantidade de dezenas por sorteio.

    Returns:
        Dicionário ordenado pelo DNI decrescente:
        {numero: {dni, atraso_atual, intervalo_medio, frequencia, classificacao}}
    """
    n_jogos = len(historico_sorteios)
    if n_jogos == 0:
        return {}

    # ── Converter para matriz binária (N, UNIVERSO) ──
    hist_binary = np.zeros((n_jogos, universo), dtype=np.int8)
    for i, sorteio in enumerate(historico_sorteios):
        indices = np.array(sorteio, dtype=int) - 1
        indices = indices[(indices >= 0) & (indices < universo)]
        hist_binary[i, indices] = 1

    resultado = {}
    for d in range(universo):
        coluna = hist_binary[:, d]
        frequencia = int(coluna.sum())

        # Atraso atual: quantos concursos desde a última aparição
        if frequencia == 0:
            atraso_atual = n_jogos
        else:
            # hist_binary[0] = mais recente
            primeira_ocorrencia = int(np.argmax(coluna))
            # Se argmax retorna 0 mas coluna[0] == 0, o número nunca apareceu
            if coluna[primeira_ocorrencia] == 0:
                atraso_atual = n_jogos
            else:
                atraso_atual = primeira_ocorrencia

        # Intervalo médio esperado
        if frequencia > 0:
            intervalo_medio = n_jogos / frequencia
        else:
            # Nunca apareceu: intervalo "infinito", usamos n_jogos + 1
            # para que DNI = n_jogos - (n_jogos + 1) = -1 ... não.
            # Na verdade, se nunca apareceu, atraso = n_jogos e intervalo = inf
            # Definimos como n_jogos para que DNI = 0 (neutro) mas
            # classificação = "Muito Devido" via atraso_atual alto
            intervalo_medio = float(n_jogos)

        # DNI = atraso_atual - intervalo_medio
        dni = round(atraso_atual - intervalo_medio, 2)

        # Classificação
        if dni > intervalo_medio * 0.5:
            classificacao = '🔴 Muito Devido'
        elif dni > 0:
            classificacao = '🟡 Devido'
        elif dni > -intervalo_medio * 0.3:
            classificacao = '🟢 Normal'
        else:
            classificacao = '🔵 Recente'

        numero = d + 1
        resultado[numero] = {
            'dni': dni,
            'atraso_atual': atraso_atual,
            'intervalo_medio': round(intervalo_medio, 2),
            'frequencia': frequencia,
            'classificacao': classificacao,
        }

    # Ordenar pelo DNI decrescente (mais "devidos" primeiro)
    resultado_ordenado = dict(
        sorted(resultado.items(), key=lambda x: x[1]['dni'], reverse=True)
    )
    return resultado_ordenado


# ════════════════════════════════════════════════════════════
#  2. MATRIZ DE AFINIDADE (LIFT DE PARES)
# ════════════════════════════════════════════════════════════

def gerar_matriz_afinidade(
    historico_sorteios: List[List[int]],
    universo: int = 25,
    top_n: int = 15,
) -> dict:
    """
    Gera a Matriz de Afinidade baseada no conceito de Lift estatístico.

    Para cada par (A, B):
      - coocorrencia_real = quantas vezes A e B saíram juntos
      - P(A) = freq(A) / total_jogos
      - P(B) = freq(B) / total_jogos
      - coocorrencia_esperada = P(A) × P(B) × total_jogos
      - Lift(A,B) = coocorrencia_real / coocorrencia_esperada

    Lift > 1.0  →  A e B saem juntos mais que o esperado (afinidade)
    Lift < 1.0  →  A e B evitam sair juntos (repulsão)
    Lift ≈ 1.0  →  independentes

    Args:
        historico_sorteios: Lista de sorteios (listas de inteiros).
        universo: Total de números possíveis.
        top_n: Quantidade de pares top a retornar.

    Returns:
        {
            'matriz_lift': ndarray (UNIVERSO × UNIVERSO),
            'top_pares_afinidade': [{par: (A,B), lift: float, coocorrencias: int}],
            'top_pares_repulsao': [{par: (A,B), lift: float, coocorrencias: int}],
        }
    """
    n_jogos = len(historico_sorteios)
    if n_jogos == 0:
        return {
            'matriz_lift': np.ones((universo, universo)),
            'top_pares_afinidade': [],
            'top_pares_repulsao': [],
        }

    # ── Matriz binária (N, UNIVERSO) ──
    hist_binary = np.zeros((n_jogos, universo), dtype=np.float64)
    for i, sorteio in enumerate(historico_sorteios):
        indices = np.array(sorteio, dtype=int) - 1
        indices = indices[(indices >= 0) & (indices < universo)]
        hist_binary[i, indices] = 1.0

    # ── Matriz de coocorrência via multiplicação matricial ──
    # (UNIVERSO, N) @ (N, UNIVERSO) → (UNIVERSO, UNIVERSO)
    cooc_matrix = hist_binary.T @ hist_binary

    # ── Frequências individuais ──
    freqs = hist_binary.sum(axis=0)  # (UNIVERSO,)

    # ── Matriz de coocorrência esperada ──
    # P(A) × P(B) × N = (freq_A / N) × (freq_B / N) × N = freq_A × freq_B / N
    freq_outer = np.outer(freqs, freqs)
    esperada = freq_outer / max(n_jogos, 1)

    # ── Lift = real / esperada ──
    # Evitar divisão por zero
    esperada_safe = np.where(esperada == 0, 1.0, esperada)
    matriz_lift = cooc_matrix / esperada_safe

    # Diagonal = 1.0 (auto-afinidade não faz sentido)
    np.fill_diagonal(matriz_lift, 1.0)

    # ── Extrair top pares ──
    pares_dados = []
    for i in range(universo):
        for j in range(i + 1, universo):
            lift = float(matriz_lift[i, j])
            cooc = int(cooc_matrix[i, j])
            pares_dados.append({
                'par': (i + 1, j + 1),
                'lift': round(lift, 4),
                'coocorrencias': cooc,
            })

    # Top afinidade (Lift mais alto)
    pares_dados_sorted_asc = sorted(pares_dados, key=lambda x: x['lift'])
    top_afinidade = sorted(pares_dados, key=lambda x: x['lift'], reverse=True)[:top_n]

    # Top repulsão (Lift mais baixo, excluindo zeros por falta de dados)
    top_repulsao = [p for p in pares_dados_sorted_asc if p['coocorrencias'] > 0][:top_n]

    return {
        'matriz_lift': matriz_lift,
        'top_pares_afinidade': top_afinidade,
        'top_pares_repulsao': top_repulsao,
    }


# ════════════════════════════════════════════════════════════
#  3. ENTROPIA DE SHANNON PARA COMBINAÇÕES
# ════════════════════════════════════════════════════════════

def calcular_entropia_jogo(
    combinacao: List[int],
    range_numeros: int = 25,
    num_bins: int = 5,
) -> dict:
    """
    Calcula a Entropia de Shannon normalizada de uma combinação,
    medindo quão uniformemente os números estão distribuídos
    ao longo do espaço numérico.

    Divide o range [1, range_numeros] em `num_bins` faixas iguais
    e conta quantas dezenas caem em cada faixa.

    H_norm → 1.0  =  distribuição uniforme perfeita (ideal)
    H_norm → 0.0  =  todas as dezenas na mesma faixa (péssimo)

    Args:
        combinacao: Lista de números do jogo.
        range_numeros: Número máximo possível (25 ou 60).
        num_bins: Quantidade de faixas para dividir o range.

    Returns:
        {entropia, entropia_max, entropia_normalizada, distribuicao_bins, classificacao}
    """
    if not combinacao or num_bins <= 0:
        return {
            'entropia': 0.0,
            'entropia_max': 0.0,
            'entropia_normalizada': 0.0,
            'distribuicao_bins': {},
            'classificacao': '❌ Inválido',
        }

    # Calcular limites dos bins
    bin_size = range_numeros / num_bins
    bins = np.zeros(num_bins, dtype=int)

    for n in combinacao:
        # Determinar em qual bin o número cai (0-indexed)
        bin_idx = min(int((n - 1) / bin_size), num_bins - 1)
        bins[bin_idx] += 1

    total = len(combinacao)

    # Distribuição de probabilidades
    probs = bins / total

    # Entropia de Shannon
    entropia = 0.0
    for p in probs:
        if p > 0:
            entropia -= p * math.log2(p)

    # Entropia máxima (distribuição uniforme perfeita)
    entropia_max = math.log2(num_bins)

    # Normalização [0, 1]
    if entropia_max > 0:
        entropia_normalizada = entropia / entropia_max
    else:
        entropia_normalizada = 0.0

    # Labels das faixas para o relatório
    distribuicao_bins = {}
    for i in range(num_bins):
        inicio = int(i * bin_size) + 1
        fim = int((i + 1) * bin_size)
        if i == num_bins - 1:
            fim = range_numeros
        label = f'{inicio:02d}-{fim:02d}'
        distribuicao_bins[label] = int(bins[i])

    # Classificação
    if entropia_normalizada >= 0.90:
        classificacao = '🌟 Excelente — Distribuição quase perfeita'
    elif entropia_normalizada >= 0.75:
        classificacao = '✅ Boa — Bem distribuído'
    elif entropia_normalizada >= 0.55:
        classificacao = '🟡 Moderada — Leve concentração'
    else:
        classificacao = '⚠️ Fraca — Muito concentrado'

    return {
        'entropia': round(entropia, 4),
        'entropia_max': round(entropia_max, 4),
        'entropia_normalizada': round(entropia_normalizada, 4),
        'distribuicao_bins': distribuicao_bins,
        'classificacao': classificacao,
    }
