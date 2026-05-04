from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from urllib.parse import urlparse

import app.models  # noqa: F401
from app.api.account_types import register_account_type_routes
from app.api.auth import register_auth_routes
from app.api.bank_accounts import register_bank_account_routes
from app.api.categories import register_category_routes
from app.api.expenses import register_expense_routes
from app.api.incomes import register_income_routes
from app.api.recurring_expenses import register_recurring_expense_routes
from app.api.recurring_incomes import register_recurring_income_routes
from app.api.stats import register_stats_routes
from app.core.config import settings
from app.core.database import Base, engine
from app.core.database import SessionLocal
from app.services.auth_service import SESSION_COOKIE_NAME, SESSION_IDLE_TIMEOUT, AuthService

app = FastAPI(title="Moneylook API")

PUBLIC_PATHS = {
    "/",
    "/auth/login",
    "/auth/logout",
    "/docs",
    "/openapi.json",
    "/redoc",
}

UNSAFE_METHODS = {"DELETE", "PATCH", "POST", "PUT"}
CSRF_EXEMPT_PATHS = {
    "/auth/login",
}


def origin_from_url(value: str | None) -> str | None:
    if not value:
        return None

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return None

    return f"{parsed.scheme}://{parsed.netloc}"


def get_trusted_origins(request) -> set[str]:
    request_origin = origin_from_url(str(request.url))
    configured_origins = {
        origin.strip().rstrip("/")
        for origin in settings.CSRF_TRUSTED_ORIGINS.split(",")
        if origin.strip()
    }

    return {request_origin, *configured_origins}


def is_trusted_origin(request) -> bool:
    source_origin = origin_from_url(request.headers.get("origin")) or origin_from_url(request.headers.get("referer"))
    return source_origin in get_trusted_origins(request)


@app.on_event("startup")
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_system_account_types()
    ensure_column("incomes", "category_id")
    ensure_column("incomes", "recurring_income_id")
    ensure_column("expenses", "recurring_expense_id")
    ensure_bank_account_default_column()
    ensure_foreign_key_column(
        "recurring_incomes",
        "category_id",
        "categories",
        "id",
        "fk_recurring_incomes_category_id",
    )
    ensure_foreign_key_column(
        "categories",
        "parent",
        "categories",
        "id",
        "fk_categories_parent",
    )
    migrate_recurring_schedule_columns("recurring_expenses")
    migrate_recurring_schedule_columns("recurring_incomes")
    normalize_frequency_values("recurring_expenses")
    normalize_frequency_values("recurring_incomes")


def ensure_column(table_name: str, column_name: str) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in columns:
        return

    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} INTEGER"))


def ensure_system_account_types() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("account_types"):
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE account_types ADD COLUMN IF NOT EXISTS code VARCHAR(50)"))
        connection.execute(text("ALTER TABLE account_types ADD COLUMN IF NOT EXISTS is_system BOOLEAN"))
        connection.execute(text("UPDATE account_types SET is_system = FALSE WHERE is_system IS NULL"))
        connection.execute(text("ALTER TABLE account_types ALTER COLUMN is_system SET DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE account_types ALTER COLUMN is_system SET NOT NULL"))
        connection.execute(
            text(
                """
                WITH current_candidate AS (
                    SELECT id
                    FROM account_types
                    WHERE lower(name) IN ('current', 'compte courant')
                    ORDER BY id
                    LIMIT 1
                )
                UPDATE account_types
                SET code = 'current', is_system = TRUE
                WHERE id IN (SELECT id FROM current_candidate)
                AND NOT EXISTS (
                    SELECT 1
                    FROM account_types
                    WHERE code = 'current'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO account_types (name, code, is_system)
                SELECT 'current', 'current', TRUE
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM account_types
                    WHERE code = 'current'
                )
                """
            )
        )
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_account_types_code ON account_types (code)"))


def ensure_bank_account_default_column() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("bank_accounts"):
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS initial_balance_cents INTEGER"))
        connection.execute(text("UPDATE bank_accounts SET initial_balance_cents = 0 WHERE initial_balance_cents IS NULL"))
        connection.execute(text("ALTER TABLE bank_accounts ALTER COLUMN initial_balance_cents SET DEFAULT 0"))
        connection.execute(text("ALTER TABLE bank_accounts ALTER COLUMN initial_balance_cents SET NOT NULL"))

        connection.execute(text("ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS is_default BOOLEAN"))
        connection.execute(text("UPDATE bank_accounts SET is_default = FALSE WHERE is_default IS NULL"))
        connection.execute(text("ALTER TABLE bank_accounts ALTER COLUMN is_default SET DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE bank_accounts ALTER COLUMN is_default SET NOT NULL"))
        connection.execute(
            text(
                """
                UPDATE bank_accounts
                SET is_default = FALSE
                WHERE is_default = TRUE
                AND id NOT IN (
                    SELECT MIN(id)
                    FROM bank_accounts
                    WHERE is_default = TRUE
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_bank_accounts_single_default
                ON bank_accounts (is_default)
                WHERE is_default = TRUE
                """
            )
        )


def ensure_foreign_key_column(
    table_name: str,
    column_name: str,
    referenced_table: str,
    referenced_column: str,
    constraint_name: str,
) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(table_name) or not inspector.has_table(referenced_table):
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    with engine.begin() as connection:
        if column_name not in columns:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} INTEGER"))

    inspector = inspect(engine)
    foreign_keys = inspector.get_foreign_keys(table_name)
    has_foreign_key = any(
        foreign_key.get("constrained_columns") == [column_name]
        and foreign_key.get("referred_table") == referenced_table
        for foreign_key in foreign_keys
    )
    if has_foreign_key:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                f"ALTER TABLE {table_name} "
                f"ADD CONSTRAINT {constraint_name} "
                f"FOREIGN KEY ({column_name}) "
                f"REFERENCES {referenced_table} ({referenced_column})"
            )
        )


def migrate_recurring_schedule_columns(table_name: str) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return

    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS is_active BOOLEAN"))
        connection.execute(text(f"UPDATE {table_name} SET is_active = TRUE WHERE is_active IS NULL"))
        connection.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN is_active SET DEFAULT TRUE"))
        connection.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN is_active SET NOT NULL"))

        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS date_policy VARCHAR(30)"))
        connection.execute(text(f"UPDATE {table_name} SET date_policy = 'same_day' WHERE date_policy IS NULL"))
        connection.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN date_policy SET DEFAULT 'same_day'"))
        connection.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN date_policy SET NOT NULL"))

        connection.execute(text(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS start_date"))
        connection.execute(text(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS end_date"))


def normalize_frequency_values(table_name: str) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if "frequency" not in columns:
        return


@app.middleware("http")
async def require_authentication(request, call_next):
    path = request.url.path
    if request.method == "OPTIONS":
        return await call_next(request)

    if request.method in UNSAFE_METHODS and path not in CSRF_EXEMPT_PATHS and not is_trusted_origin(request):
        return JSONResponse({"detail": "Untrusted request origin"}, status_code=403)

    if path in PUBLIC_PATHS:
        return await call_next(request)

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    db = SessionLocal()
    try:
        user = AuthService(db).get_active_user(token)
        if not user:
            response = JSONResponse({"detail": "Session expired"}, status_code=401)
            response.delete_cookie(
                SESSION_COOKIE_NAME,
                httponly=True,
                samesite="lax",
                secure=settings.SESSION_COOKIE_SECURE,
            )
            return response
        request.state.user = user
    finally:
        db.close()

    response = await call_next(request)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_IDLE_TIMEOUT.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response


register_auth_routes(app)
register_account_type_routes(app)
register_bank_account_routes(app)
register_category_routes(app)
register_expense_routes(app)
register_income_routes(app)
register_recurring_expense_routes(app)
register_recurring_income_routes(app)
register_stats_routes(app)


@app.get("/")
def root():
    return {"status": "ok"}
