"""
LotoMind Portal — Aplicação Principal
=======================================
Factory app Flask com Blueprints para Mega-Sena e Lotofácil.
"""

import os
from datetime import timedelta
from flask import Flask, redirect, url_for, render_template, session
from flask_login import LoginManager, current_user

from config import Config
from models import db, User


from flask_mail import Mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.permanent_session_lifetime = timedelta(seconds=Config.PERMANENT_SESSION_LIFETIME)

    # Criar diretórios necessários
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)

    # ── Banco de Dados ────────────────────────────────────
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ── Flask-Mail ────────────────────────────────────────
    mail = Mail(app)

    # ── Login Manager ─────────────────────────────────────
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar o portal.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Blueprints ────────────────────────────────────────

    # Auth — passa instância do mail
    from auth import auth_bp, init_mail
    init_mail(mail)
    app.register_blueprint(auth_bp)

    # Mega-Sena
    from modules.megasena.routes import megasena_bp
    app.register_blueprint(megasena_bp, url_prefix='/megasena')

    # Lotofácil
    from modules.lotofacil.routes import lotofacil_bp
    app.register_blueprint(lotofacil_bp, url_prefix='/lotofacil')

    # Arsenal
    from modules.arsenal.routes import arsenal_bp
    app.register_blueprint(arsenal_bp)

    # ── Rotas Principais ──────────────────────────────────

    from auth import login_required

    @app.route('/')
    @login_required
    def index():
        return redirect(url_for('main.dashboard'))

    # Blueprint principal (dashboard home)
    from flask import Blueprint
    main_bp = Blueprint('main', __name__)

    @main_bp.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @main_bp.route('/presentation')
    def presentation():
        """Serve a apresentação MegaMind Quant 3.0 (sem autenticação)."""
        from flask import send_from_directory
        return send_from_directory(app.root_path, 'megamind_evolution.html')

    @main_bp.route('/megamind-dashboard')
    def megamind_dashboard():
        """Serve o Dashboard BI MegaMind Quant (sem autenticação)."""
        from flask import send_from_directory
        return send_from_directory(app.root_path, 'megamind_dashboard.html')

    app.register_blueprint(main_bp)

    # ── Forçar sessão permanente ──────────────────────────
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    return app


app = create_app()
# Vercel, o app esta aqui!

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
    