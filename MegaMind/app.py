"""
MegaMind — Aplicação Flask para Análise da Mega-Sena
=====================================================
Dashboard, estatísticas, gerador de jogos, conferidor
e Motor de Inteligência LotoMind v2.0.
"""

from flask import Flask, render_template, request, jsonify
from engine import MegaSenaEngine
from generator import GeradorJogos
from statistical_filter import FiltroEstatistico
from intelligence_engine import LotoMindEngine
from monte_carlo import MonteCarloEngine

app = Flask(__name__)

# ── Inicialização ─────────────────────────────────────────
engine = MegaSenaEngine()
gerador = GeradorJogos(engine)
simulador = MonteCarloEngine(engine)

def carregar_dados(qtd=200):
    """Busca dados e prepara todas as análises (200 concursos para Rolling Windows)."""
    df = engine.buscar_dados_oficiais(qtd)
    if df is None or df.empty:
        return None

    contagem, quentes, frias = engine.analisar_frequencias(df)
    fixos = engine.calcular_fixos_semana(df)
    probabilidades = engine.calcular_probabilidades(df)
    tendencias = engine.tendencia_numeros(df)
    quadrantes = engine.analisar_quadrantes(df)
    mapa_calor_quad = engine.mapa_calor_quadrantes(df)
    ciclos = engine.calcular_ciclos(df)

    filtro = FiltroEstatistico()
    filtro.carregar_historico_de_dataframe(df)

    # Motor de Inteligência v2.0
    lotomind = LotoMindEngine()
    lotomind.carregar_historico(df)

    ultimo = df.iloc[0]
    quad_ultimo = engine.quadrantes_ultimo_sorteio(ultimo['Dezenas'])

    return {
        'df': df,
        'contagem': contagem,
        'quentes': quentes,
        'frias': frias,
        'fixos': fixos,
        'probabilidades': probabilidades,
        'tendencias': tendencias,
        'quadrantes': quadrantes,
        'mapa_calor_quads': mapa_calor_quad,
        'quad_ultimo': quad_ultimo,
        'ciclos': ciclos,
        'filtro': filtro,
        'lotomind': lotomind,
        'ultimo': ultimo,
        'total_jogos': len(df),
    }


# ── Cache simples em memória ──────────────────────────────
_cache = {'dados': None}


def get_dados(qtd=200):
    if _cache['dados'] is None:
        _cache['dados'] = carregar_dados(qtd)
    return _cache['dados']


# ── ROTAS ─────────────────────────────────────────────────

@app.route('/')
def dashboard():
    """Dashboard principal."""
    dados = get_dados()
    if dados is None:
        return render_template('dashboard.html', erro=True)

    # Preparar dados de frequência para Chart.js
    freq_labels = list(range(1, 61))
    freq_values = [dados['contagem'].get(i, 0) for i in freq_labels]

    # Dados par/ímpar
    total_pares = dados['df']['Pares'].sum()
    total_impares = dados['df']['Impares'].sum()

    # Top 10 mais frequentes
    top10 = dados['contagem'].most_common(10)

    # Dados de evolução da soma para gráfico de linha
    df_sorted = dados['df'].sort_values('Concurso')
    soma_concursos = df_sorted['Concurso'].tolist()
    soma_values = df_sorted['Soma'].tolist()
    media_soma = round(dados['df']['Soma'].mean(), 1)

    return render_template('dashboard.html',
        erro=False,
        ultimo=dados['ultimo'],
        freq_labels=freq_labels,
        freq_values=freq_values,
        total_pares=int(total_pares),
        total_impares=int(total_impares),
        quadrantes=dados['quadrantes'],
        quad_ultimo=dados['quad_ultimo'],
        top10=top10,
        quentes=sorted(dados['quentes']),
        frias=sorted(dados['frias']),
        total_jogos=dados['total_jogos'],
        fixos=dados['fixos'],
        soma_concursos=soma_concursos,
        soma_values=soma_values,
        media_soma=media_soma,
    )


@app.route('/estatisticas')
def estatisticas():
    """Estatísticas detalhadas."""
    dados = get_dados()
    if dados is None:
        return render_template('estatisticas.html', erro=True)

    # Mapa de calor
    mapa_calor = dados['filtro'].get_mapa_calor_completo()

    # Ciclos (top 15 mais atrasados)
    ciclos_sorted = sorted(dados['ciclos'].items(), key=lambda x: x[1], reverse=True)[:15]

    # Resumo filtros
    resumo = dados['filtro'].resumo_filtros()

    # Paridade detalhada
    paridade_det = engine.analisar_paridade_detalhada(dados['df'])

    return render_template('estatisticas.html',
        erro=False,
        fixos=dados['fixos'],
        tendencias=dados['tendencias'],
        probabilidades=dados['probabilidades'],
        mapa_calor=mapa_calor,
        mapa_calor_quads=dados['mapa_calor_quads'],
        ciclos=ciclos_sorted,
        quadrantes=dados['quadrantes'],
        resumo=resumo,
        paridade_det=paridade_det,
        total_jogos=dados['total_jogos'],
    )


@app.route('/gerador')
def gerador_page():
    """Página do gerador de jogos."""
    dados = get_dados()
    if dados is None:
        return render_template('gerador.html', erro=True)

    return render_template('gerador.html',
        erro=False,
        quentes=sorted(dados['quentes']),
        frias=sorted(dados['frias']),
        arsenal=engine.arsenal,
    )


@app.route('/inteligencia')
def inteligencia_page():
    """Página do Motor de Inteligência LotoMind v2.0."""
    dados = get_dados()
    if dados is None:
        return render_template('inteligencia.html', erro=True)

    lotomind = dados['lotomind']

    # Dados pré-calculados para a página
    resumo = lotomind.resumo_diretrizes()
    benford = lotomind.analise_benford()
    chi2_info = lotomind.chi_quadrado_geral()
    atrasados = lotomind.dezenas_atraso_critico(15)
    maturados = lotomind.dezenas_com_vies_maturacao(15)
    pares_pos = lotomind.top_pares_positivos(10)
    pares_neg = lotomind.top_pares_negativos(10)
    hiper = lotomind.pico_hipergeometrico(20)
    rolling = lotomind.analise_rolling_window(100)

    return render_template('inteligencia.html',
        erro=False,
        resumo=resumo,
        benford=benford,
        chi2_info=chi2_info,
        atrasados=atrasados,
        maturados=maturados,
        pares_pos=pares_pos,
        pares_neg=pares_neg,
        hiper=hiper,
        rolling=rolling,
        entropia_media=lotomind.entropia_media_historica,
        total_jogos=dados['total_jogos'],
    )


@app.route('/gerar', methods=['POST'])
def gerar_jogo():
    """Endpoint para gerar jogos via AJAX."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    modo = request.json.get('modo', 'simples')
    estrategia = request.json.get('estrategia', 'aleatorio')
    qtd_dezenas = int(request.json.get('qtd_dezenas', 6))

    if modo == 'mestre':
        jogos = gerador.gerar_5_jogos_mestre(
            lotomind=dados['lotomind'],
            quentes=dados['quentes'],
            frias=dados['frias'],
            ultimo_resultado=dados['ultimo']['Dezenas']
        )
        # Adicionar formatação ao JS caso precise validacoes
        for j in jogos:
            valido, validacoes = gerador.validar_jogo(j['dezenas'])
            j['valido'] = valido
            j['validacoes'] = validacoes
        return jsonify({'modo': 'mestre', 'jogos': jogos})

    else:
        jogo, valido, validacoes = gerador.gerar_jogo_validado(
            estrategia=estrategia,
            quentes=dados['quentes'],
            frias=dados['frias'],
            qtd_dezenas=qtd_dezenas,
        )
        return jsonify({
            'modo': 'simples',
            'jogo': jogo,
            'valido': valido,
            'validacoes': validacoes,
            'soma': sum(jogo),
            'paridade': gerador._calcular_paridade(jogo),
        })


@app.route('/gerar-inteligente', methods=['POST'])
def gerar_inteligente():
    """Gera jogos usando o Motor de Inteligência LotoMind v2.0."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    qtd = int(request.json.get('qtd', 5))
    qtd = min(qtd, 10)  # Máximo 10 jogos por vez

    lotomind = dados['lotomind']
    jogos = lotomind.gerar_multiplos_jogos(qtd=qtd)

    # Serializar numpy types
    resultados = []
    for j in jogos:
        resultados.append({
            'jogo': [int(x) for x in j['jogo']],
            'score_final': int(j['score_final']),
            'classificacao': j['classificacao'],
            'diretrizes_aprovadas': j['diretrizes_aprovadas'],
            'total_diretrizes': j['total_diretrizes'],
            'detalhes': _serializar_detalhes(j['detalhes']),
        })

    return jsonify({
        'status': 'sucesso',
        'jogos': resultados,
        'total': len(resultados),
    })


def _serializar_detalhes(detalhes):
    """Converte tipos numpy para JSON serializable."""
    resultado = {}
    for key, val in detalhes.items():
        if isinstance(val, dict):
            clean = {}
            for k, v in val.items():
                if hasattr(v, 'item'):
                    clean[k] = v.item()
                elif isinstance(v, list):
                    clean[k] = [x.item() if hasattr(x, 'item') else x for x in v]
                else:
                    clean[k] = v
            resultado[key] = clean
        else:
            resultado[key] = val
    return resultado


@app.route('/api/analise-inteligente', methods=['POST'])
def api_analise_inteligente():
    """Analisa um jogo específico com todas as 9 diretrizes."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    numeros = request.json.get('numeros', [])
    try:
        nums = sorted(list(set([int(n) for n in numeros])))
    except (ValueError, TypeError):
        return jsonify({'erro': 'Números inválidos'}), 400

    if len(nums) != 6:
        return jsonify({'erro': 'Digite exatamente 6 números'}), 400
    if any(n < 1 or n > 60 for n in nums):
        return jsonify({'erro': 'Números devem estar entre 1 e 60'}), 400

    lotomind = dados['lotomind']
    resultado = lotomind.analise_completa_jogo(nums, dados['quentes'])

    # Serializar
    resultado['jogo'] = [int(x) for x in resultado['jogo']]
    resultado['detalhes'] = _serializar_detalhes(resultado['detalhes'])

    return jsonify(resultado)


@app.route('/validar', methods=['POST'])
def validar_jogo():
    """Valida um jogo individual."""
    dados = get_dados()
    numeros = request.json.get('numeros', [])

    try:
        nums = sorted(list(set([int(n) for n in numeros])))
    except (ValueError, TypeError):
        return jsonify({'erro': 'Números inválidos'}), 400

    if len(nums) != 6:
        return jsonify({'erro': 'Digite exatamente 6 números'}), 400
    if any(n < 1 or n > 60 for n in nums):
        return jsonify({'erro': 'Números devem estar entre 1 e 60'}), 400

    resultado = dados['filtro'].validar_jogo_completo(nums)
    valido_gen, validacoes_gen = gerador.validar_jogo(nums)
    resultado['validacoes_gerador'] = validacoes_gen

    return jsonify(resultado)


@app.route('/conferir', methods=['POST'])
def conferir_jogo():
    """Confere um jogo contra o último sorteio."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    numeros = request.json.get('numeros', [])
    try:
        nums = sorted(list(set([int(n) for n in numeros])))
    except (ValueError, TypeError):
        return jsonify({'erro': 'Números inválidos'}), 400

    real = set(dados['ultimo']['Dezenas'])
    acertos = sorted(set(nums).intersection(real))

    return jsonify({
        'concurso': int(dados['ultimo']['Concurso']),
        'data': dados['ultimo']['Data'],
        'sorteio': dados['ultimo']['Dezenas'],
        'seu_jogo': nums,
        'acertos': acertos,
        'qtd_acertos': len(acertos),
        'premio': engine.calcular_premio(len(acertos)),
    })


@app.route('/monte-carlo', methods=['POST'])
def monte_carlo():
    """Executa simulação de Monte Carlo."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    n = int(request.json.get('n', 100000))
    top_k = int(request.json.get('top_k', 10))

    # Limitar para segurança
    n = min(n, 500000)
    top_k = min(top_k, 50)

    resultado = dados['filtro'].simulacao_monte_carlo(n=n, top_k=top_k)

    # Converter numpy types para JSON
    if resultado['status'] == 'sucesso':
        for jogo in resultado['top_jogos']:
            jogo['jogo'] = [int(x) for x in jogo['jogo']]

# ── ROTA MONTE CARLO ──────────────────────────────────────

@app.route('/montecarlo', methods=['GET', 'POST'])
def montecarlo():
    """Página e processamento da Simulação de Monte Carlo."""
    dados = get_dados()
    if dados is None:
        return render_template('montecarlo.html', erro=True)
        
    if request.method == 'POST':
        try:
            jogo_str = request.form.get('jogo', '')
            num_simulacoes = int(request.form.get('qtd_simulacoes', 1000000))
            
            # Formatar jogo (ex: 5 12 23 34 45 56)
            dezenas = sorted([int(x.strip()) for x in jogo_str.replace(',', ' ').split() if x.strip()])
            
            if len(dezenas) != 6:
                return render_template('montecarlo.html', erro=False, req_erro="Você deve informar exatamente 6 dezenas.")
            
            if not all(1 <= d <= 60 for d in dezenas):
                return render_template('montecarlo.html', erro=False, req_erro="Valores devem ser entre 1 e 60.")
            if len(set(dezenas)) != 6:
                return render_template('montecarlo.html', erro=False, req_erro="Não pode haver dezenas repetidas.")
                
            # Executar Simulação!
            resultado = simulador.simular_cenarios(dados['df'], dezenas, num_simulacoes)
            
            return render_template('montecarlo.html', erro=False, resultado=resultado, jogo=dezenas)
            
        except Exception as e:
            return render_template('montecarlo.html', erro=False, req_erro=f"Ocorreu um erro: {str(e)}")

    # GET RENDER
    return render_template('montecarlo.html', erro=False)


@app.route('/atualizar')
def atualizar():
    """Força atualização dos dados."""
    _cache['dados'] = None
    return jsonify({'status': 'ok', 'mensagem': 'Cache limpo. Dados serão recarregados.'})


@app.route('/api/dados')
def api_dados():
    """API JSON com dados resumidos."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    return jsonify({
        'ultimo_concurso': int(dados['ultimo']['Concurso']),
        'data': dados['ultimo']['Data'],
        'ultimo_sorteio': dados['ultimo']['Dezenas'],
        'quentes': sorted(dados['quentes']),
        'frias': sorted(dados['frias']),
        'total_jogos': dados['total_jogos'],
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
