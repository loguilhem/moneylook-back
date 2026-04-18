from datetime import date

from fastapi import Depends, FastAPI, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.stats import (
    BalanceRead,
    ExpenseByAccountRead,
    ExpenseByCategoryPercentRead,
    ExpenseByCategoryRead,
    ExpenseByMonthRead,
    TotalAmountRead,
)
from app.services.stats_service import StatsService


def register_stats_routes(app: FastAPI) -> None:
    @app.get("/stats/expenses/total", response_model=TotalAmountRead, tags=["Stats"])
    def get_total_expenses(
        start_date: date = Query(...),
        end_date: date = Query(...),
        db: Session = Depends(get_db),
    ):
        total = StatsService(db).get_total_expenses(start_date, end_date)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_cents": total,
        }

    @app.get(
        "/stats/incomes/total",
        response_model=TotalAmountRead,
        tags=["Stats"],
    )
    def get_total_incomes(
        start_date: date = Query(...),
        end_date: date = Query(...),
        db: Session = Depends(get_db),
    ):
        total = StatsService(db).get_total_incomes(start_date, end_date)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_cents": total,
        }

    @app.get(
        "/stats/expenses/by-category",
        response_model=list[ExpenseByCategoryRead],
        tags=["Stats"],
    )
    def get_expenses_by_category(
        start_date: date = Query(...),
        end_date: date = Query(...),
        db: Session = Depends(get_db),
    ):
        return StatsService(db).get_expenses_by_category(start_date, end_date)

    @app.get(
        "/stats/expenses/by-category-percent",
        response_model=list[ExpenseByCategoryPercentRead],
        tags=["Stats"],
    )
    def get_expenses_by_category_percent(
        start_date: date = Query(...),
        end_date: date = Query(...),
        db: Session = Depends(get_db),
    ):
        return StatsService(db).get_expenses_by_category_percent(start_date, end_date)

    @app.get(
        "/stats/expenses/by-account",
        response_model=list[ExpenseByAccountRead],
        tags=["Stats"],
    )
    def get_expenses_by_account(
        start_date: date = Query(...),
        end_date: date = Query(...),
        db: Session = Depends(get_db),
    ):
        return StatsService(db).get_expenses_by_account(start_date, end_date)

    @app.get(
        "/stats/expenses/by-month",
        response_model=list[ExpenseByMonthRead],
        tags=["Stats"],
    )
    def get_expenses_by_month(
        start_date: date = Query(...),
        end_date: date = Query(...),
        db: Session = Depends(get_db),
    ):
        return StatsService(db).get_expenses_by_month(start_date, end_date)

    @app.get("/stats/balance", response_model=BalanceRead, tags=["Stats"])
    def get_balance(
        start_date: date = Query(...),
        end_date: date = Query(...),
        db: Session = Depends(get_db),
    ):
        return StatsService(db).get_balance(start_date, end_date)