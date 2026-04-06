"""
MegaMind — Gerador de Jogos da Mega-Sena
==========================================
Geração com validação profissional e sistema MESTRE de 4 jogos elite.
"""

import random

# Primos no universo 1-60
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}

# Faixas ideais para 6 dezenas no range 1-60 (Conforme Master Prompt)
SOMA_MIN = 150
SOMA_MAX = 270
PRIMOS_IDEAL = (0, 2)  # 0 a 2 primos
SEQ_MAX = 2             # Máximo de números consecutivos


class GeradorJogos:
    """Gerador de jogos validados para a Mega-Sena."""

    def __init__(self, engine):
        self.engine = engine

    # ── Validação ─────────────────────────────────────────

    def validar_jogo(self, jogo):
        """
        Valida um jogo de 6 dezenas segundo critérios profissionais.
        Retorna: (bool, dict)
        """
        validacoes = {}

        # 1) Soma
        soma = sum(jogo)
        validacoes['soma'] = {
            'valor': soma,
            'valido': SOMA_MIN <= soma <= SOMA_MAX,
            'esperado': f'{SOMA_MIN}-{SOMA_MAX}',
        }

        # 2) Sequência máxima
        max_seq = 1
        seq = 1
        for i in range(1, len(jogo)):
            if jogo[i] == jogo[i - 1] + 1:
                seq += 1
                max_seq = max(max_seq, seq)
            else:
                seq = 1
        validacoes['sequencia'] = {
            'valor': max_seq,
            'valido': max_seq <= SEQ_MAX,
            'esperado': f'máx {SEQ_MAX}',
        }

        # 3) Primos
        qtd_primos = len([n for n in jogo if n in PRIMOS])
        validacoes['primos'] = {
            'valor': qtd_primos,
            'valido': PRIMOS_IDEAL[0] <= qtd_primos <= PRIMOS_IDEAL[1],
            'esperado': f'{PRIMOS_IDEAL[0]} a {PRIMOS_IDEAL[1]}',
        }

        # 4) Quadrantes — deve ter pelo menos 3 quadrantes representados (Master Prompt)
        from engine import QUADRANTES
        quads_presentes = 0
        for faixa in QUADRANTES.values():
            if any(n in faixa for n in jogo):
                quads_presentes += 1
        validacoes['quadrantes'] = {
            'valor': quads_presentes,
            'valido': quads_presentes >= 3,
            'esperado': '≥ 3 quadrantes',
        }
        
        # 5) Paridade (3:3 ou 4:2, ou seja, pares entre 2 e 4)
        pares = sum(1 for n in jogo if n % 2 == 0)
        validacoes['paridade'] = {
            'valor': pares,
            'valido': 2 <= pares <= 4,
            'esperado': '3P/3I ou 4P/2I (Pares 2 a 4)',
        }

        todas_validas = all(v['valido'] for v in validacoes.values())
        return todas_validas, validacoes

    # ── Gerador Simples Validado ──────────────────────────

    def gerar_jogo_validado(self, estrategia, quentes, frias, qtd_dezenas=6, max_tentativas=200):
        """
        Gera um jogo com `qtd_dezenas` números (6-15) usando a estratégia escolhida.
        Retorna: (jogo, valido, validacoes)
        """
        melhor_jogo = None
        melhor_score = 0

        for _ in range(max_tentativas):
            if estrategia == 'quente':
                pool = quentes[:max(qtd_dezenas + 5, 20)]
                jogo = sorted(random.sample(pool, min(qtd_dezenas, len(pool))))
            elif estrategia == 'fria':
                n_frias = min(qtd_dezenas - 2, len(frias))
                n_quentes = qtd_dezenas - n_frias
                jogo = sorted(
                    random.sample(frias, n_frias) +
                    random.sample(quentes, min(n_quentes, len(quentes)))
                )
            elif estrategia == 'equilibrado':
                metade = qtd_dezenas // 2
                resto = qtd_dezenas - metade
                jogo = sorted(
                    random.sample(quentes, min(metade, len(quentes))) +
                    random.sample(frias, min(resto, len(frias)))
                )
            else:  # aleatório
                jogo = sorted(random.sample(range(1, 61), qtd_dezenas))

            # Garante tamanho correto (caso pool seja pequeno)
            jogo_set = set(jogo)
            while len(jogo_set) < qtd_dezenas:
                jogo_set.add(random.randint(1, 60))
            jogo = sorted(jogo_set)[:qtd_dezenas]

            valido, validacoes = self.validar_jogo(jogo)
            if valido:
                return jogo, True, validacoes

            score = sum(1 for v in validacoes.values() if v['valido'])
            if score > melhor_score:
                melhor_score = score
                melhor_jogo = jogo
                melhor_validacoes = validacoes

        return melhor_jogo, False, melhor_validacoes

    # ── Paridade ──────────────────────────────────────────

    def _calcular_paridade(self, jogo):
        pares = sum(1 for n in jogo if n % 2 == 0)
        impares = len(jogo) - pares
        return f"{impares}Í/{pares}P"

    # ── Gerador MESTRE — 5 Jogos Elite > 85% ─────────────

    def gerar_5_jogos_mestre(self, lotomind, quentes, frias, ultimo_resultado):
        """Gera 5 jogos EXTREMAMENTE OTIMIZADOS que quebram o score de 85% no LotoMind."""
        
        jogos_aprovados = []
        tentativas = 0
        max_tentativas = 10000  # Evitar loop infinito
        
        while len(jogos_aprovados) < 5 and tentativas < max_tentativas:
            tentativas += 1
            
            # Estratégia rotativa de geração bruta
            tipo = tentativas % 4
            if tipo == 0:
                # Quase aleatório
                jogo = sorted(random.sample(range(1, 61), 6))
            elif tipo == 1:
                # Equilíbrio quente/fria
                q = random.sample(quentes, min(3, len(quentes)))
                f = random.sample(frias, min(3, len(frias)))
                jogo = sorted(set(q + f))
            elif tipo == 2:
                # Reflexo invertido
                excluidos = set(ultimo_resultado)
                pool = [n for n in range(1, 61) if n not in excluidos]
                jogo = sorted(random.sample(pool, 6))
            else:
                # Total quentes
                jogo = sorted(random.sample(quentes, min(6, len(quentes))))
                
            # Verifica tamanho (pode faltar)
            while len(set(jogo)) < 6:
                jogo.append(random.randint(1, 60))
            jogo = sorted(set(jogo))[:6]
            
            # Filtro Rígido Dimensional Mestre (Obrigatório)
            valido_abs, _ = self.validar_jogo(jogo)
            if not valido_abs:
                continue
                
            # Filtro Inteligente LotoMind v2 (Score > 85)
            # Analise completa usa o motor
            analise = lotomind.analise_completa_jogo(jogo)
            
            if analise['score_final'] > 85:
                # Já não pode ser duplicado
                if jogo not in [j['dezenas'] for j in jogos_aprovados]:
                    jogos_aprovados.append({
                        'nome': f'Jogo Mestre #{len(jogos_aprovados) + 1}',
                        'dezenas': jogo,
                        'estrategia': f'Score LotoMind: {analise["score_final"]:.1f}%',
                        'score': round(analise['score_final'], 1),
                        'paridade': self._calcular_paridade(jogo)
                    })
                    
        return jogos_aprovados

        # JOGO 1: Simulação Elite — 60% melhor jogo + 40% quentes
        j1 = self._jogo_simulacao_quentes(melhor_jogo, quentes)
        jogos.append({
            'nome': 'Jogo 1 — Simulação Elite',
            'dezenas': j1,
            'estrategia': f'Base: {melhor_jogo_nome} + quentes',
            'score': 92,
            'paridade': self._calcular_paridade(j1),
        })

        # JOGO 2: Equilíbrio — Mix quentes + frias
        j2 = self._jogo_equilibrio(quentes, frias)
        jogos.append({
            'nome': 'Jogo 2 — Equilíbrio',
            'dezenas': j2,
            'estrategia': 'Mix 3 quentes + 3 frias',
            'score': 87,
            'paridade': self._calcular_paridade(j2),
        })

        # JOGO 3: Zebra Calculada — Frias + Atrasados
        j3 = self._jogo_agressivo_frias(frias)
        jogos.append({
            'nome': 'Jogo 3 — Zebra Calculada',
            'dezenas': j3,
            'estrategia': 'Números em ciclo de atraso',
            'score': 75,
            'paridade': self._calcular_paridade(j3),
        })

        # JOGO 4: Reflexo Invertido
        j4 = self._jogo_reflexo(ultimo_resultado)
        jogos.append({
            'nome': 'Jogo 4 — Reflexo Invertido',
            'dezenas': j4,
            'estrategia': 'Reflexo do último sorteio (complementares)',
            'score': 68,
            'paridade': self._calcular_paridade(j4),
        })

        return jogos

    def _jogo_simulacao_quentes(self, base, quentes):
        jogo = set(base[:4])
        for q in quentes:
            if len(jogo) >= 6:
                break
            if q not in jogo:
                jogo.add(q)
        while len(jogo) < 6:
            jogo.add(random.randint(1, 60))
        return sorted(jogo)[:6]

    def _jogo_equilibrio(self, quentes, frias):
        jogo = set()
        for q in random.sample(quentes, min(3, len(quentes))):
            jogo.add(q)
        for f in random.sample(frias, min(3, len(frias))):
            jogo.add(f)
        while len(jogo) < 6:
            jogo.add(random.randint(1, 60))
        return sorted(jogo)[:6]

    def _jogo_agressivo_frias(self, frias):
        jogo = set()
        for f in frias[:6]:
            jogo.add(f)
        while len(jogo) < 6:
            jogo.add(random.randint(1, 60))
        return sorted(jogo)[:6]

    def _jogo_reflexo(self, ultimo_resultado):
        """Complementar ao último sorteio — pega números que NÃO saíram."""
        excluidos = set(ultimo_resultado)
        pool = [n for n in range(1, 61) if n not in excluidos]
        return sorted(random.sample(pool, 6))
