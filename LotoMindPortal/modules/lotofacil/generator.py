import random
from collections import Counter

class LotofacilGenerator:
    """Gerador de Jogos da Lotofácil (Pro e Mestre)."""

    def __init__(self, engine, df):
        self.engine = engine
        self.df = df
        self.contagem, self.quentes, self.frias = engine.analisar_frequencias(df)

    def is_valid(self, jogo):
        """Aplica filtros estatísticos comuns."""
        pares = len([x for x in jogo if x % 2 == 0])
        impares = len(jogo) - pares
        # Paridade ideal: 7P/8I ou 8P/7I ou 6P/9I
        if pares < 6 or pares > 8:
            return False

        soma = sum(jogo)
        # Soma ideal: entre 170 e 220
        if soma < 170 or soma > 220:
            return False

        # Primos ideal: entre 4 e 6
        primos = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        qtd_primos = len([x for x in jogo if x in primos])
        if qtd_primos < 4 or qtd_primos > 6:
            return False

        # Moldura ideal: entre 8 e 11
        moldura = [1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25]
        qtd_moldura = len([x for x in jogo if x in moldura])
        if qtd_moldura < 8 or qtd_moldura > 11:
            return False

        return True

    def _gerar_aleatorio_validado(self):
        universo = list(range(1, 26))
        while True:
            jogo = sorted(random.sample(universo, 15))
            if self.is_valid(jogo):
                return jogo

    def _gerar_estrategia_quentes_frias(self):
        """Seleciona 9 das top 15 quentes e 6 das frias/médias."""
        todas_frias = self.frias + [n for n in range(1, 26) if n not in self.quentes and n not in self.frias]
        # Remove duplicatas mantendo ordem
        todas_frias = list(dict.fromkeys(todas_frias))

        for _ in range(500):
            base = random.sample(self.quentes, 9)
            resto = random.sample(todas_frias, 6)
            jogo = sorted(base + resto)
            if self.is_valid(jogo):
                return jogo
        return self._gerar_aleatorio_validado()  # fallback

    def _gerar_jogo_mestre(self, repetidas_ultimo_concurso=9):
        """Estratégia Mestre: Pega N dezenas do último concurso, completa com as restantes validadas."""
        ultimo_jogo = sorted([int(d) for d in self.df.iloc[0]['Dezenas']])
        dezenas_fora = [d for d in range(1, 26) if d not in ultimo_jogo]

        for _ in range(500):
            base = random.sample(ultimo_jogo, repetidas_ultimo_concurso)
            resto = random.sample(dezenas_fora, 15 - repetidas_ultimo_concurso)
            jogo = sorted(base + resto)
            if self.is_valid(jogo):
                return jogo
        return self._gerar_aleatorio_validado()  # fallback

    def gerar_jogo(self, estrategia="padrao"):
        """Gera um único jogo (lista de inteiros) baseado na estratégia."""
        estrategia = estrategia.lower()
        if estrategia == 'quentes':
            return self._gerar_estrategia_quentes_frias()
        elif estrategia == 'mestre':
            # Em média repetem 9 do anterior
            return self._gerar_jogo_mestre(repetidas_ultimo_concurso=9)
        elif estrategia == 'aleatorio_pro':
            return self._gerar_aleatorio_validado()
        else:
            return sorted(random.sample(range(1, 26), 15))
