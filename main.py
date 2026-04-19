from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

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


@app.on_event("startup")
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_column("incomes", "category_id")
    ensure_column("incomes", "recurring_income_id")
    ensure_column("expenses", "recurring_expense_id")
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
    if request.method == "OPTIONS" or path in PUBLIC_PATHS:
        return await call_next(request)

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    db = SessionLocal()
    try:
        user = AuthService(db).get_active_user(token)
        if not user:
            response = JSONResponse({"detail": "Session expired"}, status_code=401)
            response.delete_cookie(SESSION_COOKIE_NAME, httponly=True, samesite="lax")
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
