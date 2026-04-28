import sys
sys.path.insert(0, '.')
import numpy as np
import pandas as pd
from modules.megasena.quant_master import QuantMasterEngine

# Mock rapido de DataFrame
rng = np.random.default_rng(42)
rows = []
for i in range(60):
    d = sorted(rng.choice(range(1, 61), 6, replace=False).tolist())
    rows.append({
        'Concurso': 2800 - i,
        'Data': '2025-01-01',
        'Dezenas': d,
        'Soma': sum(d),
        'Pares': sum(1 for x in d if x % 2 == 0),
        'Impares': 6 - sum(1 for x in d if x % 2 == 0),
    })
df = pd.DataFrame(rows)

qm = QuantMasterEngine()
qm.carregar_historico(df)
resultado = qm.gerar_jogos(qtd=3, n_candidatos=10000)

jogos = resultado['jogos']
meta = resultado['meta']
print(f"Jogos gerados: {len(jogos)}")
print(f"Sobreviventes: {meta['n_sobreviventes']}")
print(f"Taxa aprovacao: {meta['taxa_aprovacao']}%")
print(f"Rejeicoes: {meta['rejeicoes']}")
for j in jogos:
    print(f"  Dezenas: {j['dezenas']} | Soma: {j['soma']} | SIH: {j['sih']}")
    print(f"  Justificativa: {j['justificativa'][:100]}...")
print("OK - Engine funcionando corretamente!")
