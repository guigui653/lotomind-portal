"""
LotoMind Portal — Setup/Migração do Banco de Dados
====================================================
Cria o banco SQLite e o usuário admin com credenciais fixas.
Token MFA agora é enviado por e-mail (não mais via Google Authenticator).

Uso: python init_db.py
"""

import os
import sys
import bcrypt

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, User

ADMIN_EMAIL = "gbezerra294@gmail.com"
ADMIN_PASSWORD = "NietzscheCreed69"


def init_database():
    app = create_app()

    with app.app_context():
        # Recriar tabelas (drop + create para refletir novo schema sem mfa_secret)
        db.drop_all()
        db.create_all()
        print("✅ Banco de dados criado: instance/lotomind.db")

        # Hash bcrypt (senha truncada a 72 bytes — limite do bcrypt)
        password_hash = bcrypt.hashpw(
            ADMIN_PASSWORD.encode('utf-8')[:72],
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')

        admin = User(email=ADMIN_EMAIL, password_hash=password_hash)
        db.session.add(admin)
        db.session.commit()

        print("\n" + "=" * 55)
        print("   🔐 LotoMind Portal — Admin Configurado")
        print("=" * 55)
        print(f"   📧 Email:   {ADMIN_EMAIL}")
        print(f"   🔑 Senha:   ****** (hash bcrypt salvo)")
        print(f"   📨 MFA:     Token de 6 dígitos por e-mail")
        print("=" * 55)
        print("\n   ▸ Configure MAIL_PASSWORD em config.py")
        print("   ▸ Execute: python app.py")
        print("   ▸ Acesse:  http://localhost:5050")
        print("=" * 55)


if __name__ == '__main__':
    init_database()
