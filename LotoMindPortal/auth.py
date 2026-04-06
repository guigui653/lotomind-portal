"""
LotoMind Portal — Blueprint de Autenticação (Token por E-mail)
===============================================================
Fluxo: email + senha → gera token 6 dígitos → envia ao Gmail → valida → dashboard
"""

import random
import secrets
from functools import wraps
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
import bcrypt

from models import db, User, LoginSession, EmailToken

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Flask-Mail (inicializado no app.py via init_app)
mail = None


def init_mail(mail_instance):
    global mail
    mail = mail_instance


# ── Decorador @login_required com verificação de IP ──────────

def login_required(f):
    """Exige login E verifica binding de IP/device. (DESATIVADO PELO USUÁRIO)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Bypass completo de autenticação para entrada direta
        return f(*args, **kwargs)
    return decorated


# ── Helpers ───────────────────────────────────────────────────

def _gerar_token_6_digitos():
    return str(random.randint(100000, 999999))


def _enviar_email_token(user_email, token):
    """Envia o token de 6 dígitos para o e-mail do usuário."""
    try:
        msg = Message(
            subject='🔐 LotoMind Portal — Seu código de acesso',
            recipients=[user_email],
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;
                    background: #0f1729; color: #e8eaf0; padding: 32px; border-radius: 16px;
                    border: 1px solid rgba(0,208,132,0.2);">
            <h2 style="color: #00d084; text-align: center;">🌟 LotoMind Portal</h2>
            <p style="text-align: center; color: #7a8599;">Seu código de verificação é:</p>
            <div style="text-align: center; margin: 24px 0;">
                <span style="font-size: 48px; font-weight: 900; letter-spacing: 16px;
                             color: #00d084; font-family: monospace;">{token}</span>
            </div>
            <p style="color: #7a8599; font-size: 13px; text-align: center;">
                ⏱️ Este código expira em <strong>10 minutos</strong>.
            </p>
            <hr style="border-color: rgba(255,255,255,0.06); margin: 20px 0;">
            <p style="color: #4a5568; font-size: 11px; text-align: center;">
                Se não foi você, ignore este e-mail.
            </p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[AUTH] Erro ao enviar e-mail: {e}")
        return False


# ── ROTAS ─────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and session.get('email_verified'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode('utf-8')[:72], user.password_hash.encode('utf-8')):
            # Invalidar tokens anteriores do usuário
            EmailToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
            db.session.commit()

            # Gerar novo token de 6 dígitos
            token_code = _gerar_token_6_digitos()
            email_token = EmailToken(user_id=user.id, token=token_code)
            db.session.add(email_token)
            db.session.commit()

            # Tentar enviar e-mail
            enviado = _enviar_email_token(user.email, token_code)

            # Guardar estado na sessão
            session['pre_verify_user_id'] = user.id
            session['remember_me'] = remember

            if enviado:
                flash(f'Código enviado para {user.email}. Verifique sua caixa de entrada!', 'success')
            else:
                # Falha no envio — em dev, mostra o token no flash para testes
                flash(f'⚠️ Falha ao enviar e-mail. [DEV] Token: {token_code}', 'warning')

            return redirect(url_for('auth.verify'))
        else:
            flash('E-mail ou senha incorretos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Tela de verificação do token recebido por e-mail."""
    user_id = session.get('pre_verify_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        token_input = request.form.get('token', '').strip()

        # Buscar o token mais recente não usado
        email_token = EmailToken.query.filter_by(
            user_id=user.id, token=token_input, used=False
        ).order_by(EmailToken.id.desc()).first()

        if email_token and not email_token.is_expired():
            # Token válido — marcar como usado e criar sessão
            email_token.used = True
            db.session.commit()

            login_user(user, remember=session.get('remember_me', False))
            session['email_verified'] = True
            session.pop('pre_verify_user_id', None)

            # Criar sessão com binding de IP
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            session_token = secrets.token_hex(32)

            LoginSession.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
            new_session = LoginSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=client_ip,
                user_agent=request.headers.get('User-Agent', '')[:500],
            )
            db.session.add(new_session)
            db.session.commit()
            session['session_token'] = session_token

            flash('Bem-vindo ao LotoMind Portal!', 'success')
            return redirect(url_for('main.dashboard'))

        elif email_token and email_token.is_expired():
            flash('Código expirado (10 min). Faça login novamente.', 'danger')
            return redirect(url_for('auth.login'))
        else:
            flash('Código inválido. Verifique e tente novamente.', 'danger')

    return render_template('auth/mfa.html', email=user.email)


@auth_bp.route('/reenviar')
def reenviar():
    """Reenvia o token por e-mail."""
    user_id = session.get('pre_verify_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if user:
        EmailToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
        db.session.commit()

        token_code = _gerar_token_6_digitos()
        email_token = EmailToken(user_id=user.id, token=token_code)
        db.session.add(email_token)
        db.session.commit()

        enviado = _enviar_email_token(user.email, token_code)
        if enviado:
            flash('Novo código enviado ao seu e-mail!', 'success')
        else:
            flash(f'⚠️ Falha ao enviar. [DEV] Token: {token_code}', 'warning')

    return redirect(url_for('auth.verify'))


@auth_bp.route('/logout')
def logout():
    session_token = session.get('session_token')
    if session_token:
        ls = LoginSession.query.filter_by(session_token=session_token).first()
        if ls:
            ls.is_active = False
            db.session.commit()

    logout_user()
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))
