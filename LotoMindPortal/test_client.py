import os
import sys
import traceback
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()
app.config['TESTING'] = True
app.config['LOGIN_DISABLED'] = True

with app.test_client() as client:
    print("Testando POST /megasena/monte-carlo")
    try:
        response = client.post('/megasena/monte-carlo', json={"n": 1000})
        print("Status code:", response.status_code)
        print("Data:", response.get_data(as_text=True)[:500])
    except Exception as e:
        print("EXCEÇÃO MEGA-SENA:")
        traceback.print_exc()

    print("\nTestando POST /megasena/gerar")
    try:
        response = client.post('/megasena/gerar', json={"modo": "simples", "estrategia": "aleatorio", "qtd_dezenas": 6})
        print("Status code:", response.status_code)
        print("Data:", response.get_data(as_text=True)[:500])
    except Exception as e:
        print("EXCEÇÃO MEGA-SENA GERAR:")
        traceback.print_exc()

    print("\nTestando GET /megasena/")
    print("Status code:", client.get('/megasena/').status_code)
    print("\nTestando GET /lotofacil/")
    print("Status code:", client.get('/lotofacil/').status_code)

    print("\nTestando POST /lotofacil/gerar")
    try:
        response = client.post('/lotofacil/gerar', json={"modo": "simples", "estrategia": "aleatorio", "qtd_dezenas": 15})
        print("Status code:", response.status_code)
        print("Data:", response.get_data(as_text=True)[:500])
    except Exception as e:
        print("EXCEÇÃO LOTOFÁCIL GERAR:")
        traceback.print_exc()
