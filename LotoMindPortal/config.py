"""
LotoMind Portal — Configurações
"""
import secrets
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('LOTOMIND_SECRET') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'lotomind.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessão — 7 dias
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ── Gmail SMTP ─────────────────────────────────────────
    # Use uma "Senha de App" do Google (não sua senha normal):
    # Google Account → Segurança → Verificação em 2 etapas → Senhas de app
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'gbezerra294@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'SUA_SENHA_DE_APP_AQUI'
    MAIL_DEFAULT_SENDER = ('LotoMind Portal', os.environ.get('MAIL_USERNAME') or 'gbezerra294@gmail.com')

    APP_NAME = 'LotoMind Portal'
