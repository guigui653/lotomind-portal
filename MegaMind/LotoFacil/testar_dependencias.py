# Script de Teste - Lotofácil Pro 2.0

import sys

print("🔍 Verificando dependências...")

# Lista de bibliotecas obrigatórias
dependencias = [
    'streamlit',
    'pandas',
    'requests',
    'plotly',
    'urllib3'
]

faltando = []

for lib in dependencias:
    try:
        __import__(lib)
        print(f"✅ {lib}")
    except ImportError:
        print(f"❌ {lib} - NÃO INSTALADO")
        faltando.append(lib)

print("\n" + "="*50)

if faltando:
    print("\n⚠️ ATENÇÃO: Bibliotecas faltando!")
    print("\nInstale com:")
    print(f"pip install {' '.join(faltando)}")
    sys.exit(1)
else:
    print("\n✅ Todas as dependências estão instaladas!")
    print("\n🚀 Execute o app com:")
    print("streamlit run app.py")
    sys.exit(0)
