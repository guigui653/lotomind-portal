"""
LotoMind Portal — Blueprint Mega-Sena (Rotas)
================================================
Adaptado do MegaMind original para funcionar como Blueprint.
"""

from flask import Blueprint, render_template, request, jsonify
from auth import login_required

megasena_bp = Blueprint('megasena', __name__, template_folder='../../templates/megasena')

# ── Inicialização Lazy ────────────────────────────────────

_cache = {'dados': None, 'engine': None, 'gerador': None}


def _get_engine():
    if _cache['engine'] is None:
        from modules.megasena.engine import MegaSenaEngine
        _cache['engine'] = MegaSenaEngine()
    return _cache['engine']


def _get_gerador():
    if _cache['gerador'] is None:
        from modules.megasena.generator import GeradorJogos
        _cache['gerador'] = GeradorJogos(_get_engine())
    return _cache['gerador']


def _carregar_dados(qtd=50):
    engine = _get_engine()
    from modules.megasena.statistical_filter import FiltroEstatistico

    df = engine.buscar_dados_oficiais(qtd)
    if df is None or df.empty:
        return None

    contagem, quentes, frias = engine.analisar_frequencias(df)
    fixos = engine.calcular_fixos_semana(df, top_n=10)
    probabilidades = engine.calcular_probabilidades(df)
    tendencias = engine.tendencia_numeros(df)
    quadrantes = engine.analisar_quadrantes(df)
    ciclos = engine.calcular_ciclos(df)

    filtro = FiltroEstatistico()
    filtro.carregar_historico_de_dataframe(df)

    ultimo = df.iloc[0]
    quad_ultimo = engine.quadrantes_ultimo_sorteio(ultimo['Dezenas'])

    return {
        'df': df, 'contagem': contagem, 'quentes': quentes, 'frias': frias,
        'fixos': fixos, 'probabilidades': probabilidades, 'tendencias': tendencias,
        'quadrantes': quadrantes, 'quad_ultimo': quad_ultimo, 'ciclos': ciclos,
        'filtro': filtro, 'ultimo': ultimo, 'total_jogos': len(df),
    }


def get_dados(qtd=50):
    if _cache['dados'] is None:
        _cache['dados'] = _carregar_dados(qtd)
    return _cache['dados']


# ── ROTAS ─────────────────────────────────────────────────

@megasena_bp.route('/')
@login_required
def dashboard():
    dados = get_dados()
    if dados is None:
        return render_template('megasena/dashboard.html', erro=True)

    freq_labels = list(range(1, 61))
    freq_values = [dados['contagem'].get(i, 0) for i in freq_labels]
    total_pares = dados['df']['Pares'].sum()
    total_impares = dados['df']['Impares'].sum()
    top10 = dados['contagem'].most_common(10)

    df_sorted = dados['df'].sort_values('Concurso')
    soma_concursos = df_sorted['Concurso'].tolist()
    soma_values = df_sorted['Soma'].tolist()
    media_soma = round(dados['df']['Soma'].mean(), 1)

    return render_template('megasena/dashboard.html',
        erro=False, ultimo=dados['ultimo'],
        freq_labels=freq_labels, freq_values=freq_values,
        total_pares=int(total_pares), total_impares=int(total_impares),
        quadrantes=dados['quadrantes'], quad_ultimo=dados['quad_ultimo'],
        top10=top10, quentes=sorted(dados['quentes']), frias=sorted(dados['frias']),
        total_jogos=dados['total_jogos'], fixos=dados['fixos'],
        soma_concursos=soma_concursos, soma_values=soma_values, media_soma=media_soma,
    )


@megasena_bp.route('/estatisticas')
@login_required
def estatisticas():
    dados = get_dados()
    if dados is None:
        return render_template('megasena/estatisticas.html', erro=True)

    engine = _get_engine()
    mapa_calor = dados['filtro'].get_mapa_calor_completo()
    ciclos_sorted = sorted(dados['ciclos'].items(), key=lambda x: x[1], reverse=True)[:15]
    resumo = dados['filtro'].resumo_filtros()
    paridade_det = engine.analisar_paridade_detalhada(dados['df'])

    return render_template('megasena/estatisticas.html',
        erro=False, fixos=dados['fixos'], tendencias=dados['tendencias'],
        probabilidades=dados['probabilidades'], mapa_calor=mapa_calor,
        ciclos=ciclos_sorted, quadrantes=dados['quadrantes'],
        resumo=resumo, paridade_det=paridade_det, total_jogos=dados['total_jogos'],
    )


@megasena_bp.route('/gerador')
@login_required
def gerador_page():
    dados = get_dados()
    if dados is None:
        return render_template('megasena/gerador.html', erro=True)

    return render_template('megasena/gerador.html',
        erro=False, quentes=sorted(dados['quentes']),
        frias=sorted(dados['frias']), arsenal=_get_engine().arsenal,
    )


@megasena_bp.route('/gerar', methods=['POST'])
@login_required
def gerar_jogo():
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    gerador = _get_gerador()
    modo = request.json.get('modo', 'simples')
    estrategia = request.json.get('estrategia', 'aleatorio')
    qtd_dezenas = int(request.json.get('qtd_dezenas', 6))

    if modo == 'mestre':
        melhor_jogo = request.json.get('melhor_jogo', list(_get_engine().arsenal.keys())[0])
        jogos = gerador.gerar_4_jogos_elite(
            quentes=dados['quentes'], frias=dados['frias'],
            ultimo_resultado=dados['ultimo']['Dezenas'], melhor_jogo_nome=melhor_jogo,
        )
        for j in jogos:
            valido, validacoes = gerador.validar_jogo(j['dezenas'])
            j['valido'] = valido
            j['validacoes'] = validacoes
        return jsonify({'modo': 'mestre', 'jogos': jogos})

    else:
        jogo, valido, validacoes = gerador.gerar_jogo_validado(
            estrategia=estrategia, quentes=dados['quentes'],
            frias=dados['frias'], qtd_dezenas=qtd_dezenas,
        )
        return jsonify({
            'modo': 'simples', 'jogo': jogo, 'valido': valido,
            'validacoes': validacoes, 'soma': sum(jogo),
            'paridade': gerador._calcular_paridade(jogo),
        })


@megasena_bp.route('/conferir', methods=['POST'])
@login_required
def conferir():
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
        'data': dados['ultimo']['Data'], 'sorteio': dados['ultimo']['Dezenas'],
        'seu_jogo': nums, 'acertos': acertos, 'qtd_acertos': len(acertos),
        'premio': _get_engine().calcular_premio(len(acertos)),
    })


@megasena_bp.route('/monte-carlo', methods=['POST'])
@login_required
def monte_carlo():
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    n = min(int(request.json.get('n', 100000)), 500000)
    top_k = min(int(request.json.get('top_k', 10)), 50)
    resultado = dados['filtro'].simulacao_monte_carlo(n=n, top_k=top_k)

    if resultado['status'] == 'sucesso':
        for jogo in resultado['top_jogos']:
            jogo['jogo'] = [int(x) for x in jogo['jogo']]

    return jsonify(resultado)


@megasena_bp.route('/atualizar')
@login_required
def atualizar():
    _cache['dados'] = None
    return jsonify({'status': 'ok', 'mensagem': 'Cache limpo.'})
