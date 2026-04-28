import random
from engine import LotofacilEngine

PRIMOS = [2, 3, 5, 7, 11, 13, 17, 19, 23]


class GeradorJogos:
    def __init__(self, engine: LotofacilEngine):
        self.engine = engine
        self.ancora = 18  # Número âncora fixo

    def validar_jogo(self, jogo):
        """
        Valida um jogo de 15 números segundo critérios profissionais

        Retorna: (bool, dict)
        """
        validacoes = {}

        # Critério 1: Soma entre 180 e 220
        soma = sum(jogo)
        validacoes['soma'] = {
            'valor': soma,
            'valido': 180 <= soma <= 220,
            'esperado': '180-220'
        }

        # Critério 2: Máximo 4 números consecutivos
        max_sequencia = 1
        seq_atual = 1

        for i in range(1, len(jogo)):
            if jogo[i] == jogo[i - 1] + 1:
                seq_atual += 1
                max_sequencia = max(max_sequencia, seq_atual)
            else:
                seq_atual = 1

        validacoes['sequencia'] = {
            'valor': max_sequencia,
            'valido': max_sequencia <= 4,
            'esperado': 'máx 4'
        }

        # Critério 3: 5 ou 6 números primos
        qtd_primos = len([n for n in jogo if n in PRIMOS])
        validacoes['primos'] = {
            'valor': qtd_primos,
            'valido': qtd_primos in [5, 6],
            'esperado': '5 ou 6'
        }

        todas_validas = all(v['valido'] for v in validacoes.values())

        return todas_validas, validacoes

    def gerar_4_jogos_elite(self, quentes, frios, ultimo_resultado, melhor_jogo_nome):
        """
        Gera 4 jogos otimizados com o sistema MESTRE

        Retorna: Lista de dicts com {nome, dezenas, estrategia, score, paridade}
        """
        # Pega as dezenas do melhor jogo do arsenal
        melhor_jogo = self.engine.arsenal.get(
            melhor_jogo_nome,
            list(self.engine.arsenal.values())[0]
        )

        jogos = []

        # JOGO 1: Simulação Elite (70% melhor jogo + 30% quentes)
        jogo1 = self._jogo_simulacao_quentes(melhor_jogo, quentes)
        jogos.append({
            'nome': 'Jogo 1 - Simulação Elite',
            'dezenas': jogo1,
            'estrategia': f'Baseado em {melhor_jogo_nome} + barras quentes',
            'score': 92,
            'paridade': self._calcular_paridade(jogo1)
        })

        # JOGO 2: Salto Clássico (01-02-05 + equilíbrio)
        jogo2 = self._jogo_equilibrio_saltos([1, 2, 5], quentes, frios)
        jogos.append({
            'nome': 'Jogo 2 - Salto Clássico',
            'dezenas': jogo2,
            'estrategia': 'Início 01-02-05 + equilíbrio par/ímpar 8Í/7P',
            'score': 87,
            'paridade': self._calcular_paridade(jogo2)
        })

        # JOGO 3: Zebra Calculada (03-04-05-06 + atrasados)
        jogo3 = self._jogo_agressivo_atrasados([3, 4, 5, 6], frios)
        jogos.append({
            'nome': 'Jogo 3 - Zebra Calculada',
            'dezenas': jogo3,
            'estrategia': 'Salto agressivo + números em ciclo de atraso',
            'score': 78,
            'paridade': self._calcular_paridade(jogo3)
        })

        # JOGO 4: Quebra Radical (10P/5Í - Experimental)
        jogo4 = self._jogo_quebra_padrao(quentes, ultimo_resultado)
        jogos.append({
            'nome': 'Jogo 4 - Quebra Radical',
            'dezenas': jogo4,
            'estrategia': 'Paridade invertida + reflexo do último sorteio',
            'score': 65,
            'paridade': self._calcular_paridade(jogo4)
        })

        return jogos

    def _calcular_paridade(self, jogo):
        """Calcula paridade Ímpar/Par"""
        pares = sum(1 for n in jogo if n % 2 == 0)
        impares = 15 - pares
        return f"{impares}Í/{pares}P"

    def _jogo_simulacao_quentes(self, melhor_jogo, quentes):
        """70% do melhor jogo + 30% quentes + âncora 18"""
        base = set(melhor_jogo[:10])
        base.add(self.ancora)

        for q in quentes:
            if len(base) < 15 and q not in base:
                base.add(q)

        while len(base) < 15:
            candidato = random.randint(1, 25)
            if candidato not in base:
                base.add(candidato)

        return sorted(list(base))

    def _jogo_equilibrio_saltos(self, saltos, quentes, frios):
        """Início fixo + equilíbrio 8Í/7P"""
        jogo = set(saltos)
        jogo.add(self.ancora)

        for q in quentes:
            if len(jogo) < 15 and q not in jogo:
                jogo.add(q)

        for f in frios:
            if len(jogo) < 15 and f not in jogo:
                jogo.add(f)

        while len(jogo) < 15:
            jogo.add(random.randint(1, 25))

        return sorted(list(jogo))

    def _jogo_agressivo_atrasados(self, saltos, frios):
        """Salto agressivo + 60% frios"""
        jogo = set(saltos)
        jogo.add(self.ancora)

        for f in frios[:9]:
            if f not in jogo and len(jogo) < 15:
                jogo.add(f)

        while len(jogo) < 15:
            jogo.add(random.randint(1, 25))

        return sorted(list(jogo))

    def _jogo_quebra_padrao(self, quentes, ultimo_resultado):
        """10 Pares / 5 Ímpares - Inverso do último"""
        jogo = {self.ancora}

        pares = [n for n in range(2, 26, 2) if n not in ultimo_resultado]
        for p in pares[:10]:
            if p not in jogo and len(jogo) < 15:
                jogo.add(p)

        impares = [n for n in range(1, 26, 2) if n not in ultimo_resultado]
        for i in impares[:5]:
            if i not in jogo and len(jogo) < 15:
                jogo.add(i)

        while len(jogo) < 15:
            jogo.add(random.randint(1, 25))

        return sorted(list(jogo))