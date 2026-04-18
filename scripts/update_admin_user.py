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
    password = getpass("Nouveau mot de passe admin: ")
    confirmation = getpass("Confirmation: ")
    if password != confirmation:
        raise SystemExit("Les mots de passe ne correspondent pas.")
    if not password:
        raise SystemExit("Le mot de passe ne peut pas être vide.")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description="Écraser l'email et le mot de passe de l'admin Moneylook.")
    parser.add_argument("--email", required=True, help="Nouvel email de connexion de l'admin.")
    parser.add_argument("--password", help="Nouveau mot de passe admin. Si absent, il sera demandé sans affichage.")
    args = parser.parse_args()

    password = args.password or read_password()

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        user = db.query(User).order_by(User.id).first()
        if not user:
            raise SystemExit("Aucun utilisateur trouvé. Utilise d'abord scripts/create_admin_user.py.")

        user.email = args.email
        user.password_hash = hash_password(password)
        db.commit()
        print(f"Admin mis à jour: {args.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
