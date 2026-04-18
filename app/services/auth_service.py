from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession
from app.models.user import User

SESSION_COOKIE_NAME = "moneylook_session"
SESSION_IDLE_TIMEOUT = timedelta(minutes=15)
PASSWORD_ITERATIONS = 390000


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_digest = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, expected_digest)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.db.query(User).filter(User.email == email).one_or_none()
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    def create_session(self, user: User) -> str:
        token = secrets.token_urlsafe(32)
        now = utc_now()
        session = AuthSession(
            token_hash=hash_token(token),
            user_id=user.id,
            created_at=now,
            last_seen_at=now,
        )
        self.db.add(session)
        self.db.commit()
        return token

    def get_active_user(self, token: str) -> User | None:
        session = self.db.query(AuthSession).filter(AuthSession.token_hash == hash_token(token)).one_or_none()
        if not session:
            return None

        now = utc_now()
        if session.last_seen_at + SESSION_IDLE_TIMEOUT < now:
            self.db.delete(session)
            self.db.commit()
            return None

        session.last_seen_at = now
        self.db.commit()
        self.db.refresh(session)
        return session.user

    def delete_session(self, token: str) -> None:
        session = self.db.query(AuthSession).filter(AuthSession.token_hash == hash_token(token)).one_or_none()
        if session:
            self.db.delete(session)
            self.db.commit()
