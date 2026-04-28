"""
LotoMind Portal — Blueprint Lotofácil (Rotas)
================================================
Dashboard, estatísticas e gerador para Lotofácil.
"""

import numpy as np
from flask import Blueprint, render_template, request, jsonify
from auth import login_required

lotofacil_bp = Blueprint('lotofacil', __name__, template_folder='../../templates/lotofacil')

# ── Inicialização Lazy ────────────────────────────────────

_cache = {'dados': None, 'engine': None, 'intel_engine': None, 'predictor': None, 'avaliador': None, 'trade_engine': None, 'hybrid_engine': None}


def _get_engine():
    if _cache['engine'] is None:
        from modules.lotofacil.engine import LotofacilEngine
        _cache['engine'] = LotofacilEngine()
    return _cache['engine']


def _get_intel_engine():
    if _cache['intel_engine'] is None:
        from modules.lotofacil.intelligence_engine import LotofacilIntelligenceEngine
        _cache['intel_engine'] = LotofacilIntelligenceEngine()
    return _cache['intel_engine']


def _get_predictor():
    if _cache['predictor'] is None:
        from modules.lotofacil.advanced_stats import LotteryPredictor
        _cache['predictor'] = LotteryPredictor()
    return _cache['predictor']


def _get_avaliador():
    if _cache['avaliador'] is None:
        from modules.analise_avancada.avaliador import AvaliadorDeJogos
        _cache['avaliador'] = AvaliadorDeJogos(loteria='lotofacil')
    avaliador = _cache['avaliador']
    if not avaliador.historico_carregado:
        dados = get_dados()
        if dados:
            avaliador.carregar_historico(dados['df'])
    return avaliador


def _carregar_dados(qtd=200):
    engine = _get_engine()
    df = engine.buscar_dados_oficiais(qtd)
    if df is None or df.empty:
        return None

    contagem, quentes, frias = engine.analisar_frequencias(df)
    fixos = engine.calcular_fixos_semana(df, top_n=10)
    probabilidades = engine.calcular_probabilidades(df)
    tendencias = engine.tendencia_numeros(df)
    ciclos = engine.calcular_ciclos(df)

    # Carregar motor de inteligência
    intel = _get_intel_engine()
    intel.carregar_historico(df)

    ultimo = df.iloc[0]

    return {
        'df': df, 'contagem': contagem, 'quentes': quentes, 'frias': frias,
        'fixos': fixos, 'probabilidades': probabilidades, 'tendencias': tendencias,
        'ciclos': ciclos, 'ultimo': ultimo, 'total_jogos': len(df),
    }


def get_dados(qtd=200):
    if _cache['dados'] is None:
        _cache['dados'] = _carregar_dados(qtd)
    return _cache['dados']


# ── ROTAS ─────────────────────────────────────────────────

@lotofacil_bp.route('/')
@login_required
def dashboard():
    dados = get_dados()
    if dados is None:
        return render_template('lotofacil/dashboard.html', erro=True)

    freq_labels = list(range(1, 26))
    freq_values = [dados['contagem'].get(i, 0) for i in freq_labels]
    total_pares = dados['df']['Pares'].sum()
    total_impares = dados['df']['Impares'].sum()
    top10 = dados['contagem'].most_common(10)

    df_sorted = dados['df'].sort_values('Concurso')
    soma_concursos = df_sorted['Concurso'].tolist()
    soma_values = df_sorted['Soma'].tolist()
    media_soma = round(dados['df']['Soma'].mean(), 1)

    return render_template('lotofacil/dashboard.html',
        erro=False, ultimo=dados['ultimo'],
        freq_labels=freq_labels, freq_values=freq_values,
        total_pares=int(total_pares), total_impares=int(total_impares),
        top10=top10, quentes=sorted(dados['quentes']),
        frias=sorted(dados['frias']), total_jogos=dados['total_jogos'],
        fixos=dados['fixos'],
        soma_concursos=soma_concursos, soma_values=soma_values, media_soma=media_soma,
    )


@lotofacil_bp.route('/estatisticas')
@login_required
def estatisticas():
    dados = get_dados()
    if dados is None:
        return render_template('lotofacil/estatisticas.html', erro=True)

    engine = _get_engine()
    ciclos_sorted = sorted(dados['ciclos'].items(), key=lambda x: x[1], reverse=True)[:10]
    paridade_det = engine.analisar_paridade_detalhada(dados['df'])

    return render_template('lotofacil/estatisticas.html',
        erro=False, fixos=dados['fixos'], tendencias=dados['tendencias'],
        probabilidades=dados['probabilidades'],
        ciclos=ciclos_sorted, paridade_det=paridade_det,
        total_jogos=dados['total_jogos'],
    )


@lotofacil_bp.route('/conferir', methods=['POST'])
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
    qtd = len(acertos)

    premios = {11: 'R$ 6,00', 12: 'R$ 12,00', 13: 'R$ 30,00', 14: 'R$ 1.500,00', 15: 'LOTOFÁCIL — PRÊMIO MÁXIMO!'}
    premio = premios.get(qtd, 'Sem prêmio')

    return jsonify({
        'concurso': int(dados['ultimo']['Concurso']),
        'data': dados['ultimo']['Data'], 'sorteio': dados['ultimo']['Dezenas'],
        'seu_jogo': nums, 'acertos': acertos, 'qtd_acertos': qtd, 'premio': premio,
    })


@lotofacil_bp.route('/calor')
@login_required
def calor():
    dados = get_dados()
    if dados is None:
        return render_template('lotofacil/dashboard.html', erro=True)
    return render_template('lotofacil/calor.html', contagem=dict(dados['contagem']), universo=list(range(1, 26)))


@lotofacil_bp.route('/gerador', methods=['GET', 'POST'])
@login_required
def gerador():
    dados = get_dados()
    if dados is None:
        return render_template('lotofacil/dashboard.html', erro=True)
        
    engine = _get_engine()
    from modules.lotofacil.generator import LotofacilGenerator
    gen = LotofacilGenerator(engine, dados['df'])
    
    jogo_gerado = None
    estrategia_usada = ""
    
    if request.method == 'POST':
        estrategia = request.form.get('estrategia', 'padrao')
        jogo_gerado = gen.gerar_jogo(estrategia)
        nomes = {'padrao': 'Gerador Padrão', 'quentes': 'Estratégia Ouro (Quentes+Frias)', 'mestre': 'Gerador MESTRE', 'aleatorio_pro': 'Gerador PRO (Validado)'}
        estrategia_usada = nomes.get(estrategia, estrategia)
    
    return render_template('lotofacil/gerador.html', 
        erro=False, quentes=dados['quentes'], frias=dados['frias'],
        jogo_gerado=jogo_gerado, estrategia_usada=estrategia_usada
    )


@lotofacil_bp.route('/montecarlo', methods=['GET', 'POST'])
@login_required
def montecarlo():
    dados = get_dados()
    if dados is None:
        return render_template('lotofacil/dashboard.html', erro=True)
        
    melhores = None
    if request.method == 'POST':
        try:
            qtd = int(request.form.get('qtd', 5000))
            top_k = int(request.form.get('top_k', 5))
            from modules.lotofacil.monte_carlo import LotofacilMonteCarlo
            mc = LotofacilMonteCarlo(_get_engine(), dados['df'])
            melhores = mc.simular(num_simulacoes=qtd, top_n=top_k)
        except ValueError:
            pass

    return render_template('lotofacil/montecarlo.html', erro=False, melhores=melhores)


@lotofacil_bp.route('/atualizar')
@login_required
def atualizar():
    _cache['dados'] = None
    _cache['intel_engine'] = None
    _cache['predictor'] = None
    _cache['avaliador'] = None
    _cache['trade_engine'] = None
    _cache['hybrid_engine'] = None
    return jsonify({'status': 'ok', 'mensagem': 'Cache limpo.'})


def _get_trade_engine():
    """Retorna (ou inicializa) o LotoMindTradeEngine com histórico carregado."""
    if _cache['trade_engine'] is None:
        from modules.lotofacil.trade_engine import LotoMindTradeEngine
        te = LotoMindTradeEngine()
        dados = get_dados()
        if dados:
            te.carregar_historico(dados['df'])
        _cache['trade_engine'] = te
    return _cache['trade_engine']


# ════════════════════════════════════════════════════════════
#  ROTAS — TRADE ENGINE (Pilares 1, 2 e 3)
# ════════════════════════════════════════════════════════════

@lotofacil_bp.route('/trade')
@login_required
def trade_page():
    """Renderiza o dashboard 'Trading Room' do LotoMind Trade Engine."""
    dados = get_dados()
    if dados is None:
        return render_template('lotofacil/trade.html', erro=True)
    return render_template('lotofacil/trade.html', erro=False,
                           ultimo=dados['ultimo'], total_jogos=dados['total_jogos'])


@lotofacil_bp.route('/api/trade-analise')
@login_required
def api_trade_analise():
    """
    Endpoint JSON: retorna análise completa dos 3 Pilares.
    Pilar 1 → dezenas semanal, quinzenal, âncoras
    Pilar 2 → SMA-10 por âncora + Bollinger da soma
    Pilar 3 → backtest dos últimos 5 concursos
    """
    te = _get_trade_engine()
    if not te._carregado:
        return jsonify({'erro': 'Histórico não carregado'}), 500
    try:
        resultado = te.analise_completa()
        return jsonify(_serializar(resultado))
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@lotofacil_bp.route('/api/trade-gerar', methods=['POST'])
@login_required
def api_trade_gerar():
    """
    Endpoint JSON: gera N palpites (padrão 5) filtrados pelas Bandas de Bollinger,
    baseados nas dezenas âncora do Pilar 1.
    """
    te = _get_trade_engine()
    if not te._carregado:
        return jsonify({'erro': 'Histórico não carregado'}), 500

    body = request.get_json(silent=True) or {}
    qtd = min(int(body.get('qtd', 5)), 10)

    try:
        palpites = te.gerar_palpites(qtd=qtd)
        bollinger = te.calcular_bollinger()
        semana = te.calcular_dezenas_semana()
        quinzena = te.calcular_dezenas_quinzena()
        ancoras = te.calcular_ancoras(semana, quinzena)

        return jsonify(_serializar({
            'palpites': palpites,
            'bollinger': bollinger,
            'ancoras': ancoras,
            'total_gerados': len(palpites),
        }))
    except Exception as e:
        return jsonify({'erro': str(e)}), 500



# ════════════════════════════════════════════════════════════
#  ROTAS DE INTELIGÊNCIA LotoMind v2.0
# ════════════════════════════════════════════════════════════

def _serializar(obj):
    """Converte tipos numpy para JSON-serializáveis."""
    if isinstance(obj, dict):
        return {k: _serializar(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serializar(i) for i in obj]
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
    return obj


@lotofacil_bp.route('/inteligencia')
@login_required
def inteligencia_page():
    dados = get_dados()
    if dados is None:
        return render_template('lotofacil/inteligencia.html', erro=True)

    intel = _get_intel_engine()
    resumo = intel.resumo_diretrizes()
    hiper = intel.probabilidade_hipergeometrica()
    maturados = intel.calcular_maturacao()
    pares_pos, pares_neg = intel.pares_de_ouro()
    benford = intel.analise_benford()
    trios_ouro = intel.trios_de_ouro()

    return render_template('lotofacil/inteligencia.html',
        erro=False,
        total_jogos=dados['total_jogos'],
        entropia_media=round(intel.entropia_media, 3),
        chi2_info=intel.chi2_resultado,
        resumo=resumo,
        hiper=_serializar(hiper),
        maturados=maturados,
        pares_pos=pares_pos,
        pares_neg=pares_neg,
        benford=benford,
        trios=trios_ouro,
        atrasados=intel.decaimento[:12],
        rolling=intel.rolling,
        ciclos=intel.ciclos,
        moldura_stats=intel.moldura_stats,
    )


@lotofacil_bp.route('/gerar-inteligente', methods=['POST'])
@login_required
def gerar_inteligente():
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    intel = _get_intel_engine()
    try:
        body = request.get_json(silent=True) or {}
        qtd = min(int(body.get('qtd', 5)), 10)
        jogos = intel.gerar_multiplos_jogos(qtd=qtd)
        return jsonify({'jogos': _serializar(jogos)})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@lotofacil_bp.route('/api/analise-inteligente', methods=['POST'])
@login_required
def api_analise_inteligente():
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    intel = _get_intel_engine()
    body = request.get_json(silent=True) or {}
    numeros = body.get('numeros', [])

    try:
        nums = sorted(list(set([int(n) for n in numeros])))
    except (ValueError, TypeError):
        return jsonify({'erro': 'Números inválidos'}), 400

    if len(nums) != 15:
        return jsonify({'erro': 'Envie exatamente 15 números'}), 400

    resultado = intel.analise_completa_jogo(nums)
    return jsonify(_serializar(resultado))


@lotofacil_bp.route('/api/predict-score', methods=['POST'])
@login_required
def api_predict_score():
    """Scoring avançado via Markov + Poisson (LotteryPredictor)."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    predictor = _get_predictor()
    if not predictor._historico_carregado:
        predictor.carregar_historico(dados['df'])

    body = request.get_json(silent=True) or {}
    numeros = body.get('numeros', [])

    try:
        nums = sorted(list(set([int(n) for n in numeros])))
    except (ValueError, TypeError):
        return jsonify({'erro': 'Números inválidos'}), 400

    if len(nums) != 15:
        return jsonify({'erro': 'Envie exatamente 15 números'}), 400

    resultado = predictor.confidence_score(nums)
    return jsonify(_serializar(resultado))


# ════════════════════════════════════════════════════════════
#  ROTAS DO AVALIADOR DE JOGOS (Boletim Explicável)
# ════════════════════════════════════════════════════════════

@lotofacil_bp.route('/api/avaliar-jogo', methods=['POST'])
@login_required
def api_avaliar_jogo():
    """Avalia um jogo com 8 critérios e retorna boletim JSON completo."""
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

    if len(nums) != 15:
        return jsonify({'erro': 'Envie exatamente 15 números'}), 400

    resultado = avaliador.avaliar_e_pontuar_jogo(nums)
    return jsonify(_serializar(resultado))


@lotofacil_bp.route('/api/gerar-com-boletim', methods=['POST'])
@login_required
def api_gerar_com_boletim():
    """Gera N jogos inteligentes e retorna cada um com seu boletim de avaliação."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    intel = _get_intel_engine()
    avaliador = _get_avaliador()

    body = request.get_json(silent=True) or {}
    qtd = min(int(body.get('qtd', 3)), 10)

    try:
        jogos_intel = intel.gerar_multiplos_jogos(qtd=qtd)
        jogos_com_boletim = []

        for jogo_info in jogos_intel:
            boletim = avaliador.avaliar_e_pontuar_jogo(jogo_info['jogo'])
            jogos_com_boletim.append({
                'jogo': jogo_info['jogo'],
                'score_inteligencia': jogo_info.get('score_final', 0),
                'boletim': boletim,
            })

        # Ordenar por nota do boletim (decrescente)
        jogos_com_boletim.sort(key=lambda x: x['boletim']['nota_final'], reverse=True)

        return jsonify(_serializar({'jogos': jogos_com_boletim}))
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@lotofacil_bp.route('/api/gerar-jogo-fisico', methods=['POST'])
@login_required
def api_gerar_jogo_fisico():
    """Gera jogos usando o simulador físico e termodinâmico."""
    dados = get_dados()
    if dados is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 500

    avaliador = _get_avaliador()
    body = request.get_json(silent=True) or {}
    qtd = min(int(body.get('qtd', 1)), 5)
    n_simulacoes = min(int(body.get('simulacoes', 5)), 20)
    
    from modules.analise_avancada.fisica_teorica import GloboFisicoSimulator
    
    simulador = GloboFisicoSimulator(
        universo=25,
        dezenas_sorteio=15,
        iteracoes=150
    )

    try:
        jogos = []
        for i in range(qtd):
            # Passar histórico (que o avaliador já tem ou que podemos pegar do avaliador.historico_listas) para termodinâmica
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
            
        return jsonify(_serializar({'jogos': jogos}))
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ════════════════════════════════════════════════════════════
#  ROTAS — MOTOR HÍBRIDO MONTE CARLO + IA
# ════════════════════════════════════════════════════════════

def _get_hybrid_engine():
    """Retorna (ou inicializa) o LotofacilHybridEngine com dependências."""
    if _cache['hybrid_engine'] is None:
        from modules.lotofacil.monte_carlo import LotofacilMonteCarlo
        from modules.lotofacil.hybrid_engine import LotofacilHybridEngine
        dados = get_dados()
        if dados is None:
            return None
        mc   = LotofacilMonteCarlo(_get_engine(), dados['df'])
        intel = _get_intel_engine()
        _cache['hybrid_engine'] = LotofacilHybridEngine(mc, intel)
    return _cache['hybrid_engine']


@lotofacil_bp.route('/hibrido')
@login_required
def hibrido_page():
    """Renderiza o dashboard do Motor Híbrido MC + IA."""
    dados = get_dados()
    if dados is None:
        return render_template('lotofacil/hibrido.html', erro=True)
    return render_template('lotofacil/hibrido.html',
                           erro=False,
                           ultimo=dados['ultimo'],
                           total_jogos=dados['total_jogos'])


@lotofacil_bp.route('/api/gerar-hibrido', methods=['POST'])
@login_required
def api_gerar_hibrido():
    """
    Endpoint JSON: executa o funil Monte Carlo → IA.

    Body JSON (opcional):
        qtd         : int  — quantidade de apostas desejadas  (padrão 5, max 20)
        simulacoes  : int  — simulações Monte Carlo           (padrão 10000, max 50000)

    Retorna:
        {
            apostas    : [{ dezenas, score_mc, score_ia, classificacao, detalhes }],
            stats_mc   : { simulacoes_solicitadas, cenarios_gerados, cenarios_avaliados },
            tempo_ms   : float
        }
    """
    hybrid = _get_hybrid_engine()
    if hybrid is None:
        return jsonify({'erro': 'Dados históricos não disponíveis'}), 500

    body       = request.get_json(silent=True) or {}
    qtd        = max(1, min(int(body.get('qtd', 5)),        20))
    simulacoes = max(1_000, min(int(body.get('simulacoes', 10_000)), 50_000))

    try:
        resultado = hybrid.gerar_aposta_hibrida(
            qtd_apostas    = qtd,
            num_simulacoes = simulacoes,
        )
        return jsonify(_serializar(resultado))
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
