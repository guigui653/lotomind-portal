"""
GeradorJogos — Refatorado e otimizado.

✅ Código limpo & tipado
✅ Validação centralizada
✅ Independente do Streamlit
"""
import random

from app.core.engine import LotofacilEngine

PRIMOS = frozenset({2, 3, 5, 7, 11, 13, 17, 19, 23})


class GeradorJogos:
    """Gerador de jogos validados para a Lotofácil."""

    def __init__(self, engine: LotofacilEngine):
        self.engine = engine
        self.ancora = 18  # Número âncora fixo

    # ── Validação ─────────────────────────────────────────────────
    @staticmethod
    def validar_jogo(jogo: list[int]) -> tuple[bool, dict]:
        """
        Valida um jogo de 15 números.
        Retorna (valido, detalhes_validacao).
        """
        validacoes: dict = {}

        # 1) Soma entre 180-220
        soma = sum(jogo)
        validacoes["soma"] = {
            "valor": soma,
            "valido": 180 <= soma <= 220,
            "esperado": "180-220",
        }

        # 2) Máximo 4 números consecutivos
        max_seq = 1
        seq_atual = 1
        for i in range(1, len(jogo)):
            if jogo[i] == jogo[i - 1] + 1:
                seq_atual += 1
                max_seq = max(max_seq, seq_atual)
            else:
                seq_atual = 1

        validacoes["sequencia"] = {
            "valor": max_seq,
            "valido": max_seq <= 4,
            "esperado": "máx 4",
        }

        # 3) 5 ou 6 números primos
        qtd_primos = sum(1 for n in jogo if n in PRIMOS)
        validacoes["primos"] = {
            "valor": qtd_primos,
            "valido": qtd_primos in (5, 6),
            "esperado": "5 ou 6",
        }

        valido = all(v["valido"] for v in validacoes.values())
        return valido, validacoes

    # ── Gerador validado (Pro) ────────────────────────────────────
    def gerar_jogo_validado(
        self,
        estrategia: str,
        quentes: list[int],
        frias: list[int],
        max_tentativas: int = 200,
    ) -> tuple[list[int], bool, dict]:
        """Gera um jogo otimizado com validação profissional."""
        melhor_jogo = None
        melhor_score = -1
        melhor_val = {}

        for _ in range(max_tentativas):
            jogo = self._montar_jogo_por_estrategia(estrategia, quentes, frias)
            valido, validacoes = self.validar_jogo(jogo)

            if valido:
                return jogo, True, validacoes

            score = sum(1 for v in validacoes.values() if v["valido"])
            if score > melhor_score:
                melhor_score = score
                melhor_jogo = jogo
                melhor_val = validacoes

        return melhor_jogo or sorted(random.sample(range(1, 26), 15)), False, melhor_val

    def _montar_jogo_por_estrategia(
        self, estrategia: str, quentes: list[int], frias: list[int]
    ) -> list[int]:
        if estrategia == "quente":
            pool = quentes[:20] if len(quentes) >= 15 else list(range(1, 26))
            return sorted(random.sample(pool, 15))
        elif estrategia == "fria":
            n_frias = min(10, len(frias))
            n_quentes = 15 - n_frias
            selecionados = random.sample(frias, n_frias) + random.sample(quentes, min(n_quentes, len(quentes)))
            while len(selecionados) < 15:
                c = random.randint(1, 25)
                if c not in selecionados:
                    selecionados.append(c)
            return sorted(selecionados[:15])
        elif estrategia == "equilibrado":
            n_q = min(9, len(quentes))
            n_f = min(6, len(frias))
            selecionados = random.sample(quentes, n_q) + random.sample(frias, n_f)
            # Remover duplicatas e completar
            selecionados = list(set(selecionados))
            while len(selecionados) < 15:
                c = random.randint(1, 25)
                if c not in selecionados:
                    selecionados.append(c)
            return sorted(selecionados[:15])
        else:
            return sorted(random.sample(range(1, 26), 15))

    # ── Gerador MESTRE (4 Jogos Elite) ────────────────────────────
    def gerar_4_jogos_elite(
        self,
        quentes: list[int],
        frios: list[int],
        ultimo_resultado: list[int],
        melhor_jogo_nome: str,
    ) -> list[dict]:
        """Gera 4 jogos elite com estratégias diferentes."""
        melhor_jogo = self.engine.arsenal.get(
            melhor_jogo_nome, list(self.engine.arsenal.values())[0]
        )

        jogos: list[dict] = []

        # JOGO 1 — Simulação Elite
        j1 = self._jogo_simulacao_quentes(melhor_jogo, quentes)
        v1, val1 = self.validar_jogo(j1)
        jogos.append(self._build_elite_response(
            "Jogo 1 - Simulação Elite", j1, f"Baseado em {melhor_jogo_nome} + quentes", 92, val1
        ))

        # JOGO 2 — Salto Clássico
        j2 = self._jogo_equilibrio_saltos([1, 2, 5], quentes, frios)
        _, val2 = self.validar_jogo(j2)
        jogos.append(self._build_elite_response(
            "Jogo 2 - Salto Clássico", j2, "Início 01-02-05 + equilíbrio 8Í/7P", 87, val2
        ))

        # JOGO 3 — Zebra Calculada
        j3 = self._jogo_agressivo_atrasados([3, 4, 5, 6], frios)
        _, val3 = self.validar_jogo(j3)
        jogos.append(self._build_elite_response(
            "Jogo 3 - Zebra Calculada", j3, "Salto agressivo + números atrasados", 78, val3
        ))

        # JOGO 4 — Quebra Radical
        j4 = self._jogo_quebra_padrao(quentes, ultimo_resultado)
        _, val4 = self.validar_jogo(j4)
        jogos.append(self._build_elite_response(
            "Jogo 4 - Quebra Radical", j4, "Paridade invertida + reflexo último sorteio", 65, val4
        ))

        return jogos

    # ── Helpers ────────────────────────────────────────────────────
    def _build_elite_response(
        self, nome: str, dezenas: list[int], estrategia: str, score: int, validacoes: dict
    ) -> dict:
        pares = sum(1 for n in dezenas if n % 2 == 0)
        impares = 15 - pares
        return {
            "nome": nome,
            "dezenas": dezenas,
            "estrategia": estrategia,
            "score": score,
            "paridade": f"{impares}Í/{pares}P",
            "validacao": {
                "valido": all(v["valido"] for v in validacoes.values()),
                "soma": validacoes["soma"],
                "sequencia": validacoes["sequencia"],
                "primos": validacoes["primos"],
            },
        }

    def _jogo_simulacao_quentes(self, melhor_jogo: list[int], quentes: list[int]) -> list[int]:
        base = set(melhor_jogo[:10])
        base.add(self.ancora)
        for q in quentes:
            if len(base) >= 15:
                break
            base.add(q)
        while len(base) < 15:
            base.add(random.randint(1, 25))
        return sorted(base)

    def _jogo_equilibrio_saltos(
        self, saltos: list[int], quentes: list[int], frios: list[int]
    ) -> list[int]:
        jogo = set(saltos)
        jogo.add(self.ancora)
        for q in quentes:
            if len(jogo) >= 15:
                break
            jogo.add(q)
        for f in frios:
            if len(jogo) >= 15:
                break
            jogo.add(f)
        while len(jogo) < 15:
            jogo.add(random.randint(1, 25))
        return sorted(jogo)

    def _jogo_agressivo_atrasados(self, saltos: list[int], frios: list[int]) -> list[int]:
        jogo = set(saltos)
        jogo.add(self.ancora)
        for f in frios[:9]:
            if len(jogo) >= 15:
                break
            jogo.add(f)
        while len(jogo) < 15:
            jogo.add(random.randint(1, 25))
        return sorted(jogo)

    def _jogo_quebra_padrao(self, quentes: list[int], ultimo_resultado: list[int]) -> list[int]:
        jogo = {self.ancora}
        ult_set = set(ultimo_resultado)
        pares = [n for n in range(2, 26, 2) if n not in ult_set]
        for p in pares[:10]:
            if len(jogo) >= 15:
                break
            jogo.add(p)
        impares = [n for n in range(1, 26, 2) if n not in ult_set]
        for i in impares[:5]:
            if len(jogo) >= 15:
                break
            jogo.add(i)
        while len(jogo) < 15:
            jogo.add(random.randint(1, 25))
        return sorted(jogo)
