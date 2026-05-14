from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.llm import LlmChatRequest, LlmChatResponse, LlmConnectionTestResponse, LlmSettingsRead, LlmSettingsUpdate
from app.services.llm_service import LlmConfigurationError, LlmProviderError, LlmService


def register_llm_routes(app: FastAPI) -> None:
    @app.get("/llm/settings", response_model=LlmSettingsRead, tags=["LLM"])
    def get_settings(db: Session = Depends(get_db)):
        return LlmService(db).read_settings()

    @app.put("/llm/settings", response_model=LlmSettingsRead, tags=["LLM"])
    def update_settings(payload: LlmSettingsUpdate, db: Session = Depends(get_db)):
        return LlmService(db).update_settings(payload)

    @app.post("/llm/chat", response_model=LlmChatResponse, tags=["LLM"])
    def chat(payload: LlmChatRequest, db: Session = Depends(get_db)):
        try:
            message = LlmService(db).chat(payload.messages)
        except LlmConfigurationError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        except LlmProviderError as error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

        return LlmChatResponse(message=message)

    @app.post("/llm/test", response_model=LlmConnectionTestResponse, tags=["LLM"])
    def test_connection(db: Session = Depends(get_db)):
        try:
            LlmService(db).test_connection()
        except LlmConfigurationError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        except LlmProviderError as error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

        return LlmConnectionTestResponse(ok=True, message="LLM connection successful")
