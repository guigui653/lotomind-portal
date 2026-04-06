"""
LotoMind Portal — Setup de Usuário
====================================
Execute este script para criar o primeiro usuário e configurar o MFA.
Uso: python setup_user.py
"""

import os
import sys
import bcrypt
import pyotp
import qrcode

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, User


def setup():
    app = create_app()

    with app.app_context():
        db.create_all()

        # Verificar se já existe usuário
        existing = User.query.first()
        if existing:
            print(f"\n⚠️  Já existe um usuário cadastrado: {existing.email}")
            resp = input("Deseja criar outro? (s/n): ").strip().lower()
            if resp != 's':
                print("Operação cancelada.")
                return

        print("\n" + "=" * 50)
        print("   🔐 LotoMind Portal — Configuração de Usuário")
        print("=" * 50)

        # Email
        email = input("\n📧 E-mail: ").strip().lower()
        if not email or '@' not in email:
            print("❌ E-mail inválido.")
            return

        # Senha
        password = input("🔑 Senha: ").strip()
        if len(password) < 6:
            print("❌ Senha deve ter pelo menos 6 caracteres.")
            return

        password_confirm = input("🔑 Confirme a senha: ").strip()
        if password != password_confirm:
            print("❌ Senhas não conferem.")
            return

        # Gerar hash da senha
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Gerar segredo MFA
        mfa_secret = pyotp.random_base32()
        totp = pyotp.TOTP(mfa_secret)
        provisioning_uri = totp.provisioning_uri(name=email, issuer_name="LotoMind Portal")

        # Criar usuário
        user = User(
            email=email,
            password_hash=password_hash,
            mfa_secret=mfa_secret,
        )
        db.session.add(user)
        db.session.commit()

        print("\n✅ Usuário criado com sucesso!")
        print(f"   Email: {email}")
        print(f"   MFA Secret: {mfa_secret}")

        # Gerar QR Code
        qr_path = os.path.join(os.path.dirname(__file__), 'mfa_qrcode.png')
        qr = qrcode.make(provisioning_uri)
        qr.save(qr_path)

        print(f"\n📱 QR Code salvo em: {qr_path}")
        print("   Escaneie com o Google Authenticator para configurar o MFA.")
        print(f"\n   URI: {provisioning_uri}")
        print("\n" + "=" * 50)
        print("   ✅ Configuração concluída! Execute: python app.py")
        print("=" * 50)


if __name__ == '__main__':
    setup()
