import pandas as pd
import numpy as np

class FeatureEngineer:
    """
    Engine para engenharia de atributos avançada para a Lotofácil.
    Foca em extrair padrões matemáticos e estatísticos de cada sorteio.
    """

    @staticmethod
    def is_prime(n: int) -> bool:
        if n < 2: return False
        for i in range(2, int(np.sqrt(n)) + 1):
            if n % i == 0: return False
        return True

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma a base bruta de concursos em uma base com features enriquecidas.
        Assume que df['dezenas'] contém uma lista de 15 inteiros.
        """
        # Expandir dezenas em colunas individuais
        dezenas_cols = [f'd_{i+1}' for i in range(15)]
        df[dezenas_cols] = pd.DataFrame(df['dezenas'].tolist(), index=df.index)

        # 1. Soma das Dezenas
        df['soma'] = df['dezenas'].apply(sum)

        # 2. Proporção Par/Ímpar
        df['pares'] = df['dezenas'].apply(lambda x: len([n for n in x if n % 2 == 0]))
        df['impares'] = 15 - df['pares']
        df['prop_par_impar'] = df['pares'] / 15

        # 3. Números Primos
        df['primos_count'] = df['dezenas'].apply(lambda x: len([n for n in x if self.is_prime(n)]))

        # 4. Repetições do Concurso Anterior
        # Ordenar por concurso para calcular shift
        df = df.sort_values('concurso')
        df['dezenas_set'] = df['dezenas'].apply(set)
        df['dezenas_prev_set'] = df['dezenas_set'].shift(1)
        
        df['repetidos_anterior'] = df.apply(
            lambda row: len(row['dezenas_set'].intersection(row['dezenas_prev_set'])) 
            if row['dezenas_prev_set'] is not None and isinstance(row['dezenas_prev_set'], set) else 0, 
            axis=1
        )

        # Limpeza
        df = df.drop(columns=['dezenas_set', 'dezenas_prev_set'])
        return df.fillna(0)
