import os
import sys
import time
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from modules.lotofacil.engine import LotofacilEngine
from modules.lotofacil.monte_carlo import LotofacilMonteCarlo
from modules.megasena.engine import MegaSenaEngine
from modules.megasena.statistical_filter import FiltroEstatistico

app = create_app()

with app.app_context():
    print("=== Testando MEGA-SENA ===")
    me = MegaSenaEngine()
    df_mega = me.buscar_dados_oficiais(50)
    filtro_mega = FiltroEstatistico()
    filtro_mega.carregar_historico_de_dataframe(df_mega)
    
    t0 = time.time()
    res_mega = filtro_mega.simulacao_monte_carlo(n=1000, top_k=2) # Teste rápido
    t1 = time.time()
    print(f"Mega-Sena levou: {t1 - t0:.4f} segundos")
    
    import json
    try:
        print("Testando JSON dumps Mega-Sena:")
        json.dumps(res_mega)
        print("JSON dumps OK!")
    except Exception as e:
        print("Erro de JSON dumps Mega-Sena:", e)

    print("\n=== Testando LOTOFÁCIL ===")
    le = LotofacilEngine()
    df_loto = le.buscar_dados_oficiais(50)
    mc_loto = LotofacilMonteCarlo(le, df_loto)
    
    t0 = time.time()
    res_loto = mc_loto.simular(num_simulacoes=1000, top_n=2)
    t1 = time.time()
    print(f"Lotofácil levou: {t1 - t0:.4f} segundos")
    try:
        print("Testando JSON dumps Lotofacil:")
        json.dumps(res_loto)
        print("JSON dumps OK!")
    except Exception as e:
        print("Erro de JSON dumps Lotofacil:", e)
