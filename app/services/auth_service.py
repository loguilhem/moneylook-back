from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_session import AuthSession
from app.models.login_attempt import LoginAttempt
from app.models.user import User

SESSION_COOKIE_NAME = "moneylook_session"
SESSION_IDLE_TIMEOUT = timedelta(minutes=15)
PASSWORD_ITERATIONS = 390000
LOGIN_MAX_FAILED_ATTEMPTS = 3
LOGIN_LOCK_DURATION = timedelta(minutes=15)


class LoginLockedError(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_login_identifier(email: str) -> str:
    return email.strip().lower()


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

    def get_login_attempt(self, identifier: str) -> LoginAttempt | None:
        return self.db.query(LoginAttempt).filter(LoginAttempt.identifier == identifier).one_or_none()

    def ensure_login_is_allowed(self, identifier: str) -> None:
        if not settings.LOGIN_BRUTE_FORCE_ENABLED:
            return

        attempt = self.get_login_attempt(identifier)
        if not attempt or not attempt.locked_until:
            return

        if attempt.locked_until > utc_now():
            raise LoginLockedError("Too many login attempts. Try again later.")

        self.db.delete(attempt)
        self.db.commit()

    def record_failed_login(self, identifier: str) -> bool:
        if not settings.LOGIN_BRUTE_FORCE_ENABLED:
            return False

        now = utc_now()
        attempt = self.get_login_attempt(identifier)
        if not attempt:
            attempt = LoginAttempt(identifier=identifier, failed_count=0)
            self.db.add(attempt)

        attempt.failed_count += 1
        if attempt.failed_count >= LOGIN_MAX_FAILED_ATTEMPTS:
            attempt.locked_until = now + LOGIN_LOCK_DURATION

        self.db.commit()
        return attempt.locked_until is not None and attempt.locked_until > now

    def clear_failed_login(self, identifier: str) -> None:
        attempt = self.get_login_attempt(identifier)
        if attempt:
            self.db.delete(attempt)
            self.db.commit()

    def authenticate(self, email: str, password: str) -> User | None:
        identifier = normalize_login_identifier(email)
        self.ensure_login_is_allowed(identifier)

        user = self.db.query(User).filter(func.lower(User.email) == identifier).one_or_none()
        if not user or not verify_password(password, user.password_hash):
            if self.record_failed_login(identifier):
                raise LoginLockedError("Too many login attempts. Try again later.")
            return None

        self.clear_failed_login(identifier)
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
