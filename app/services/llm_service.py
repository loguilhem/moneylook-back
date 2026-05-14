import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.models.llm_settings import LlmSettings
from app.schemas.llm import LlmChatMessage, LlmSettingsRead, LlmSettingsUpdate
from app.services.llm_context_service import LlmContextService

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "custom": "",
    "ollama": "http://localhost:11434",
}

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "custom": "",
    "ollama": "llama3.1",
}

SKIRO_SYSTEM_PROMPT = """
Tu es Skiro, l'assistant de l'application MoneyLook, un agent spécialisé dans la gestion de budget personnel.

Tu aides l'utilisateur à analyser ses dépenses et revenus, détecter les tendances, prévoir les fins de mois,
expliquer les écarts de budget et proposer des optimisations simples.

Règles:
- réponds dans la langue de session
- sois concret et chiffré
- ne donne pas de conseil financier réglementé
- indique toujours tes hypothèses
- si une donnée manque, demande-la ou explique la limite
- ne devine pas les montants
- pour les calculs, utilise les données fournies par l'application
""".strip()

MONEYLOOK_CONTEXT_PROMPT = """
Données Moneylook disponibles pour répondre à l'utilisateur:
{context_json}

Consignes d'utilisation des données:
- utilise ces données comme source principale pour les montants et tendances
- si la question demande une période absente du contexte, explique la limite et demande la période
- ne prétends pas avoir accès à des données qui ne sont pas dans ce contexte
- cite les dates/périodes utilisées quand tu donnes un calcul
""".strip()

MAX_CONTEXT_PROMPT_CHARS = 7500


class LlmConfigurationError(Exception):
    pass


class LlmProviderError(Exception):
    pass


def normalize_base_url(value: str) -> str:
    return value.strip().rstrip("/")


class LlmService:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> LlmSettings:
        settings = self.db.query(LlmSettings).order_by(LlmSettings.id).first()
        if settings:
            return settings

        settings = LlmSettings(
            enabled=False,
            provider="openai",
            base_url=DEFAULT_BASE_URLS["openai"],
            model=DEFAULT_MODELS["openai"],
            api_key="",
            organization="",
        )
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def read_settings(self) -> LlmSettingsRead:
        settings = self.get_settings()
        return self.to_read_schema(settings)

    def update_settings(self, payload: LlmSettingsUpdate) -> LlmSettingsRead:
        settings = self.get_settings()
        settings.enabled = payload.enabled
        settings.provider = payload.provider
        settings.base_url = normalize_base_url(payload.base_url or DEFAULT_BASE_URLS.get(payload.provider, ""))
        settings.model = payload.model or DEFAULT_MODELS.get(payload.provider, "")
        settings.organization = payload.organization

        if payload.api_key is not None:
            settings.api_key = payload.api_key

        self.db.commit()
        self.db.refresh(settings)
        return self.to_read_schema(settings)

    def to_read_schema(self, settings: LlmSettings) -> LlmSettingsRead:
        return LlmSettingsRead(
            enabled=settings.enabled,
            provider=settings.provider,
            base_url=settings.base_url,
            model=settings.model,
            organization=settings.organization,
            has_api_key=bool(settings.api_key),
        )

    def chat(self, messages: list[LlmChatMessage], include_data_context: bool = True) -> LlmChatMessage:
        settings = self.get_settings()
        self.ensure_chat_is_configured(settings)
        prepared_messages = self.prepare_messages(messages, include_data_context=include_data_context)

        if settings.provider == "ollama":
            content = self.chat_with_ollama(settings, prepared_messages)
        else:
            content = self.chat_with_openai_compatible(settings, prepared_messages)

        return LlmChatMessage(role="assistant", content=content)

    def test_connection(self) -> str:
        message = self.chat(
            [
                LlmChatMessage(
                    role="user",
                    content="Réponds uniquement par OK pour confirmer que la connexion LLM fonctionne.",
                )
            ],
            include_data_context=False,
        )
        return message.content

    def prepare_messages(self, messages: list[LlmChatMessage], include_data_context: bool) -> list[LlmChatMessage]:
        prepared_messages = list(messages)

        if not any(message.role == "system" for message in prepared_messages):
            prepared_messages.insert(0, LlmChatMessage(role="system", content=SKIRO_SYSTEM_PROMPT))

        if include_data_context:
            try:
                context = LlmContextService(self.db).build_context()
            except Exception as error:
                context = {
                    "available": False,
                    "error": f"Unable to build Moneylook data context: {error}",
                }

            context_json = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
            context_prompt = MONEYLOOK_CONTEXT_PROMPT.format(context_json=context_json)
            if len(context_prompt) > MAX_CONTEXT_PROMPT_CHARS:
                overflow = len(context_prompt) - MAX_CONTEXT_PROMPT_CHARS
                context_json = context_json[: max(0, len(context_json) - overflow - 24)] + "...[context truncated]"
                context_prompt = MONEYLOOK_CONTEXT_PROMPT.format(context_json=context_json)

            prepared_messages.insert(
                1,
                LlmChatMessage(
                    role="system",
                    content=context_prompt,
                ),
            )

        return prepared_messages

    def ensure_chat_is_configured(self, settings: LlmSettings) -> None:
        if not settings.enabled:
            raise LlmConfigurationError("LLM is disabled")

        if not settings.base_url:
            raise LlmConfigurationError("LLM base URL is missing")

        if not settings.model:
            raise LlmConfigurationError("LLM model is missing")

        if settings.provider != "ollama" and not settings.api_key:
            raise LlmConfigurationError("LLM API key is missing")

    def chat_with_openai_compatible(self, settings: LlmSettings, messages: list[LlmChatMessage]) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_key}",
        }
        if settings.organization:
            headers["OpenAI-Organization"] = settings.organization

        response = self.post_json(
            f"{normalize_base_url(settings.base_url)}/chat/completions",
            {
                "model": settings.model,
                "messages": [message.model_dump() for message in messages],
            },
            headers=headers,
        )

        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise LlmProviderError("Unexpected LLM response format") from error

        return str(content).strip()

    def chat_with_ollama(self, settings: LlmSettings, messages: list[LlmChatMessage]) -> str:
        response = self.post_json(
            f"{normalize_base_url(settings.base_url)}/api/chat",
            {
                "model": settings.model,
                "messages": [message.model_dump() for message in messages],
                "stream": False,
            },
            headers={"Content-Type": "application/json"},
        )

        try:
            content = response["message"]["content"]
        except (KeyError, TypeError) as error:
            raise LlmProviderError("Unexpected Ollama response format") from error

        return str(content).strip()

    def post_json(self, url: str, payload: dict, headers: dict[str, str]) -> dict:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise LlmProviderError(detail or f"LLM provider returned HTTP {error.code}") from error
        except (TimeoutError, URLError) as error:
            raise LlmProviderError(f"Unable to reach LLM provider: {error}") from error
        except json.JSONDecodeError as error:
            raise LlmProviderError("LLM provider returned invalid JSON") from error
