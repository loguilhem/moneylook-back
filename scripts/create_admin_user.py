import argparse
from getpass import getpass
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import app.models  # noqa: E402,F401
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.auth_service import hash_password  # noqa: E402


def read_password() -> str:
    password = getpass("Mot de passe admin: ")
    confirmation = getpass("Confirmation: ")
    if password != confirmation:
        raise SystemExit("Les mots de passe ne correspondent pas.")
    if not password:
        raise SystemExit("Le mot de passe ne peut pas être vide.")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description="Créer l'unique utilisateur admin Moneylook.")
    parser.add_argument("--email", required=True, help="Email de connexion de l'admin.")
    parser.add_argument("--password", help="Mot de passe admin. Si absent, il sera demandé sans affichage.")
    args = parser.parse_args()

    password = args.password or read_password()

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_user = db.query(User).order_by(User.id).first()
        if existing_user:
            raise SystemExit(
                "Un utilisateur existe déjà. Utilise scripts/update_admin_user.py pour écraser l'admin."
            )

        user = User(email=args.email, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        print(f"Admin créé: {args.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
