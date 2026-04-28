"""
LotoMind Portal — Blueprint Mega-Sena (Rotas)
================================================
Adaptado do MegaMind original para funcionar como Blueprint.
"""

from flask import Blueprint, render_template, request, jsonify
from auth import login_required

megasena_bp = Blueprint('megasena', __name__, template_folder='../../templates/megasena')

# ── Inicialização Lazy ────────────────────────────────────

_cache = {'dados': None, 'engine': None, 'gerador': None, 'avaliador': None, 'trade_engine': None, 'quant_master': None}


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


def _get_avaliador():
    if _cache['avaliador'] is None:
        from modules.analise_avancada.avaliador import AvaliadorDeJogos
        _cache['avaliador'] = AvaliadorDeJogos(loteria='megasena')
    avaliador = _cache['avaliador']
    if not avaliador.historico_carregado:
        dados = get_dados()
        if dados:
            avaliador.carregar_historico(dados['df'])
    return avaliador


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
    _cache['avaliador'] = None
    _cache['trade_engine'] = None
    _cache['quant_master'] = None
    return jsonify({'status': 'ok', 'mensagem': 'Cache limpo.'})


def _get_trade_engine_mega():
    """Retorna (ou inicializa) o MegaMindTradeEngine com historico carregado."""
    if _cache['trade_engine'] is None:
        from modules.megasena.trade_engine import MegaMindTradeEngine
        te = MegaMindTradeEngine()
        dados = get_dados()
        if dados:
            te.carregar_historico(dados['df'])
        _cache['trade_engine'] = te
    return _cache['trade_engine']


# ============================================================
#  ROTAS — MEGAMIND TRADE ENGINE (Pilares 1, 2 e 3)
# ============================================================

@megasena_bp.route('/trade')
@login_required
def trade_page():
    """Dashboard MegaMind Trade Engine."""
    dados = get_dados()
    if dados is None:
        return render_template('megasena/trade.html', erro=True)
    return render_template('megasena/trade.html', erro=False,
                           ultimo=dados['ultimo'], total_jogos=dados['total_jogos'])


@megasena_bp.route('/api/trade-analise')
@login_required
def api_trade_analise_mega():
    """
    JSON completo dos 3 Pilares MegaMind:
    Pilar 1 -> Trend quinzenal + consolidacao mensal
    Pilar 2 -> SMA-50 + Bollinger da soma
    Pilar 3 -> Backtest 10 concursos com Sharpe Ratio
    """
    te = _get_trade_engine_mega()
    if not te._carregado:
        return jsonify({'erro': 'Historico nao carregado'}), 500
    try:
        resultado = te.analise_completa()
        return jsonify(_serializar_mega(resultado))
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@megasena_bp.route('/api/trade-gerar', methods=['POST'])
@login_required
def api_trade_gerar_mega():
    """
    Gera N palpites (padrao 5) filtrados pelo Bollinger da soma,
    com regra de quadrantes e pelo menos 1 dezena oversold.
    """
    te = _get_trade_engine_mega()
    if not te._carregado:
        return jsonify({'erro': 'Historico nao carregado'}), 500

    body = request.get_json(silent=True) or {}
    qtd = min(int(body.get('qtd', 5)), 10)

    try:
        palpites = te.gerar_palpites(qtd=qtd)
        bollinger = te.calcular_bollinger_soma()
        oversold = te.identificar_oversold(top_n=5)
        trend = te.calcular_trend_quinzenal()

        return jsonify(_serializar_mega({
            'palpites': palpites,
            'bollinger': bollinger,
            'oversold_top5': oversold,
            'trend_quinzenal': trend[:10],
            'total_gerados': len(palpites),
        }))
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ════════════════════════════════════════════════════════════
#  ROTAS DO AVALIADOR DE JOGOS (Boletim Explicável)
# ════════════════════════════════════════════════════════════


def _serializar_mega(obj):
    """Converte tipos numpy para JSON-serializáveis."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _serializar_mega(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serializar_mega(i) for i in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, set):
        return sorted(list(obj))
    elif isinstance(obj, tuple):
        return list(obj)
    return obj


@megasena_bp.route('/api/avaliar-jogo', methods=['POST'])
@login_required
def api_avaliar_jogo():
    """Avalia um jogo de 6 dezenas com 8 critérios e retorna boletim JSON."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    avaliador = _get_avaliador()
    body = request.get_json(silent=True) or {}
    numeros = body.get('numeros', [])

    try:
        nums = sorted(list(set([int(n) for n in numeros])))
    except (ValueError, TypeError):
        return jsonify({'erro': 'Números inválidos'}), 400

    if len(nums) != 6:
        return jsonify({'erro': 'Envie exatamente 6 números'}), 400

    resultado = avaliador.avaliar_e_pontuar_jogo(nums)
    return jsonify(_serializar_mega(resultado))


@megasena_bp.route('/api/gerar-com-boletim', methods=['POST'])
@login_required
def api_gerar_com_boletim():
    """Gera N jogos e retorna cada um com seu boletim de avaliação."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    avaliador = _get_avaliador()
    gerador = _get_gerador()

    body = request.get_json(silent=True) or {}
    qtd = min(int(body.get('qtd', 3)), 10)
    estrategia = body.get('estrategia', 'equilibrado')

    try:
        jogos_com_boletim = []

        for _ in range(qtd):
            jogo, valido, validacoes = gerador.gerar_jogo_validado(
                estrategia=estrategia,
                quentes=dados['quentes'],
                frias=dados['frias'],
            )
            boletim = avaliador.avaliar_e_pontuar_jogo(jogo)
            jogos_com_boletim.append({
                'jogo': jogo,
                'valido_gerador': valido,
                'boletim': boletim,
            })

        jogos_com_boletim.sort(key=lambda x: x['boletim']['nota_final'], reverse=True)

        return jsonify(_serializar_mega({'jogos': jogos_com_boletim}))
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@megasena_bp.route('/api/gerar-jogo-fisico', methods=['POST'])
@login_required
def api_gerar_jogo_fisico():
    """Gera jogos da Mega-Sena usando o simulador físico e termodinâmico."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    avaliador = _get_avaliador()
    body = request.get_json(silent=True) or {}
    qtd = min(int(body.get('qtd', 1)), 5)
    n_simulacoes = min(int(body.get('simulacoes', 5)), 20)

    from modules.analise_avancada.fisica_teorica import GloboFisicoSimulator

    simulador = GloboFisicoSimulator(
        universo=60,
        dezenas_sorteio=6,
        iteracoes=200
    )

    try:
        jogos = []
        for i in range(qtd):
            res_fisico = simulador.gerar_jogo_fisico(
                historico_sorteios=avaliador.historico_listas if avaliador else [],
                n_simulacoes=n_simulacoes
            )
            jogo_gerado = res_fisico['jogo']
            boletim = avaliador.avaliar_e_pontuar_jogo(jogo_gerado)

            jogos.append({
                'jogo': jogo_gerado,
                'fisica': {
                    'confianca_fisica': res_fisico['confianca_fisica'],
                    'n_simulacoes': res_fisico['n_simulacoes'],
                },
                'boletim': boletim
            })

        return jsonify(_serializar_mega({'jogos': jogos}))

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ════════════════════════════════════════════════════════════
#  QUANT-MASTER — Gerador Elite (Behavioral Bias Filter + SIH)
# ════════════════════════════════════════════════════════════

def _get_quant_master():
    """Retorna (ou inicializa) o QuantMasterEngine com histórico carregado."""
    if _cache['quant_master'] is None:
        from modules.megasena.quant_master import QuantMasterEngine
        qm = QuantMasterEngine()
        dados = get_dados()
        if dados:
            qm.carregar_historico(dados['df'])
        _cache['quant_master'] = qm
    return _cache['quant_master']


@megasena_bp.route('/quant-master')
@login_required
def quant_master_page():
    """Página do Gerador MESTRE — Quant-Master."""
    dados = get_dados()
    if dados is None:
        return render_template('megasena/quant_master.html', erro=True)
    qm = _get_quant_master()
    axioma = qm.info_axioma()
    # Converter row Pandas para dict puro antes de passar ao template
    ultimo_row = dados['ultimo']
    ultimo = {
        'Concurso': int(ultimo_row['Concurso']),
        'Data': str(ultimo_row.get('Data', '')),
        'Dezenas': list(ultimo_row['Dezenas']),
        'Soma': int(ultimo_row['Soma']),
    }
    return render_template(
        'megasena/quant_master.html',
        erro=False,
        axioma=axioma,
        total_jogos=dados['total_jogos'],
        ultimo=ultimo,
    )


@megasena_bp.route('/api/quant-master', methods=['POST'])
@login_required
def api_quant_master():
    """
    API JSON do Quant-Master.
    Body: {"qtd": 5, "n_candidatos": 50000}
    Retorna lista de jogos com SIH e justificativa quantitativa.
    """
    qm = _get_quant_master()
    if not qm._carregado:
        return jsonify({'erro': 'Histórico não carregado'}), 500

    body = request.get_json(silent=True) or {}
    qtd = min(int(body.get('qtd', 5)), 10)
    n_candidatos = min(int(body.get('n_candidatos', 50_000)), 200_000)

    try:
        resultado = qm.gerar_jogos(qtd=qtd, n_candidatos=n_candidatos)
        return jsonify(_serializar_mega(resultado))
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
