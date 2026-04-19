from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.auth import AuthUserRead, LoginRequest
from app.services.auth_service import (
    SESSION_COOKIE_NAME,
    SESSION_IDLE_TIMEOUT,
    AuthService,
    LoginLockedError,
)


def register_auth_routes(app: FastAPI) -> None:
    @app.post("/auth/login", response_model=AuthUserRead, tags=["Auth"])
    def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
        service = AuthService(db)
        try:
            user = service.authenticate(payload.email, payload.password)
        except LoginLockedError as error:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(error)) from error

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = service.create_session(user)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            max_age=int(SESSION_IDLE_TIMEOUT.total_seconds()),
            httponly=True,
            samesite="lax",
            secure=settings.SESSION_COOKIE_SECURE,
        )
        return user

    @app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["Auth"])
    def logout(request: Request, response: Response, db: Session = Depends(get_db)):
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if token:
            AuthService(db).delete_session(token)
        response.delete_cookie(
            SESSION_COOKIE_NAME,
            httponly=True,
            samesite="lax",
            secure=settings.SESSION_COOKIE_SECURE,
        )

    @app.get("/auth/me", response_model=AuthUserRead, tags=["Auth"])
    def me(request: Request):
        return request.state.user
