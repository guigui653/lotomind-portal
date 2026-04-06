"""
LotoMind Portal — Blueprint Arsenal
===================================
Gerenciamento de jogos salvos e conferência global contra o último sorteio.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from auth import login_required
from models import db, JogoSalvo

arsenal_bp = Blueprint('arsenal', __name__, template_folder='../../templates/arsenal', url_prefix='/arsenal')


@arsenal_bp.route('/')
@login_required
def dashboard():
    """Mostra os 8 slots do Arsenal da Lotofácil (ou Mega)."""
    # Buscando os jogos atuais do usuário (Lotofácil)
    jogos = JogoSalvo.query.filter_by(user_id=current_user.id, loteria='lotofacil').order_by(JogoSalvo.slot).all()
    
    # Criar um array fixo de 8 slots
    slots = {i: None for i in range(1, 9)}
    for j in jogos:
        slots[j.slot] = j
        
    # Precisamos do último resultado da Lotofácil para conferência rápida
    ultimo_resultado = None
    from modules.lotofacil.routes import _get_engine
    engine = _get_engine()
    df = engine.buscar_dados_oficiais(1)
    if df is not None and not df.empty:
        ultimo_resultado = df.iloc[0]['Dezenas']
        
    # Fazer a conferência prévia
    resultados = {}
    if ultimo_resultado:
        result_set = set(ultimo_resultado)
        for i, j in slots.items():
            if j:
                jogo_set = set([int(x) for x in j.dezenas.split(',')])
                acertos = len(jogo_set.intersection(result_set))
                resultados[i] = acertos

    return render_template('arsenal/dashboard.html', 
        slots=slots, 
        ultimo_resultado=ultimo_resultado, 
        resultados=resultados
    )


@arsenal_bp.route('/salvar', methods=['POST'])
@login_required
def salvar():
    """Recebe AJAX dos geradores/simuladores para salvar em um slot."""
    dados = request.json
    try:
        slot = int(dados.get('slot', 1))
        dezenas = dados.get('dezenas', '')
        estrategia = dados.get('estrategia', 'Jogo Salvo')
        loteria = dados.get('loteria', 'lotofacil')
        score = dados.get('score_metric', None)
        if score is not None:
            score = float(score)
        
        # Validar max slots (8)
        if slot < 1 or slot > 8:
            return jsonify({'status': 'error', 'message': 'Slot inválido (max 8).'})
            
        # Verifica se já tem algo no slot para o user/loteria
        existente = JogoSalvo.query.filter_by(user_id=current_user.id, loteria=loteria, slot=slot).first()
        
        if existente:
            existente.dezenas = dezenas
            existente.nome_estrategia = estrategia
            existente.score_metric = score
        else:
            novo = JogoSalvo(
                user_id=current_user.id,
                loteria=loteria,
                slot=slot,
                nome_estrategia=estrategia,
                dezenas=dezenas,
                score_metric=score
            )
            db.session.add(novo)
            
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Salvo no slot {slot}'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@arsenal_bp.route('/deletar/<int:slot>', methods=['POST'])
@login_required
def deletar(slot):
    loteria = request.form.get('loteria', 'lotofacil')
    item = JogoSalvo.query.filter_by(user_id=current_user.id, loteria=loteria, slot=slot).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'})
