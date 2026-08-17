import argparse
import getpass

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from yas_api.core.security import hash_password
from yas_api.db.session import SessionLocal
from yas_api.models import AdminUser


def create_admin() -> None:
    parser = argparse.ArgumentParser(description="Cria um usuario administrador")
    parser.add_argument("--name", help="Nome do administrador")
    parser.add_argument("--email", help="E-mail de acesso")
    args = parser.parse_args()

    name = args.name or input("Nome: ").strip()
    email = (args.email or input("E-mail: ")).strip().lower()
    password = getpass.getpass("Senha: ")
    confirmation = getpass.getpass("Confirme a senha: ")

    if not name or "@" not in email:
        raise SystemExit("Nome e e-mail valido sao obrigatorios")
    if len(password) < 8:
        raise SystemExit("A senha deve ter ao menos 8 caracteres")
    if password != confirmation:
        raise SystemExit("As senhas nao conferem")

    try:
        with SessionLocal() as db:
            if db.scalar(select(AdminUser).where(AdminUser.email == email)):
                raise SystemExit("Ja existe um administrador com esse e-mail")
            db.add(AdminUser(name=name, email=email, password_hash=hash_password(password)))
            db.commit()
    except OperationalError as exc:
        raise SystemExit("Banco nao preparado. Execute: uv run alembic upgrade head") from exc

    print(f"Administrador {email} criado com sucesso.")


if __name__ == "__main__":
    create_admin()
