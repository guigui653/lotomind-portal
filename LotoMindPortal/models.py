"""
LotoMind Portal — Modelos do Banco de Dados
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """Usuário do portal."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sessions = db.relationship('LoginSession', backref='user', lazy=True)
    tokens = db.relationship('EmailToken', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'


class LoginSession(db.Model):
    """Sessão de login com binding de IP/device."""
    __tablename__ = 'login_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)


class EmailToken(db.Model):
    """Token temporário de 6 dígitos enviado por e-mail."""
    __tablename__ = 'email_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    used = db.Column(db.Boolean, default=False)

    def is_expired(self, minutes=10):
        """Token expira em 10 minutos."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return (now - created) > timedelta(minutes=minutes)


# ── Histórico de Sorteios (Cache Local) ────────────────────────

class SorteioLotofacil(db.Model):
    """Sorteios da Lotofácil."""
    __tablename__ = 'sorteios_lotofacil'

    concurso = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(15), nullable=False)
    dezenas = db.Column(db.String(50), nullable=False)  # ex: "01,02,03..." (2 dígitos separados por vírgula)
    timestamp_sync = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class SorteioMegaSena(db.Model):
    """Sorteios da Mega-Sena."""
    __tablename__ = 'sorteios_megasena'

    concurso = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(15), nullable=False)
    dezenas = db.Column(db.String(50), nullable=False)
    timestamp_sync = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ── Arsenal de Jogos ───────────────────────────────────────────

class JogoSalvo(db.Model):
    """Arsenal de Jogos Salvos (Slots 1 a 8)."""
    __tablename__ = 'jogos_salvos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loteria = db.Column(db.String(20), nullable=False)  # "lotofacil" ou "megasena"
    slot = db.Column(db.Integer, nullable=False)        # 1 a 8
    nome_estrategia = db.Column(db.String(100), nullable=False)  # e.g., "Jogo 1 (Estatístico)"
    dezenas = db.Column(db.String(100), nullable=False) # e.g., "01,02,05..."
    score_metric = db.Column(db.Float, nullable=True)   # Score Monte Carlo se houver
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # O usuário pode alterar em qual slot o jogo está, para gerenciar o Arsenal.
    user_rel = db.relationship('User', backref=db.backref('arsenal', lazy='dynamic', cascade="all, delete-orphan"))

