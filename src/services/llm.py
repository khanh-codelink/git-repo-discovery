from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from src.config import AzureOpenAIConfig, get_settings


class LLMService:
    """Service for interacting with the LLM."""

    _instance: "LLMService | None" = None

    def __init__(self) -> None:
        self._llm: BaseChatModel = self._build_online_llm(get_settings().llm_settings)
        self._current: BaseChatModel = self._llm

    # ── Singleton ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_llm_service() -> "LLMService":
        if LLMService._instance is None:
            LLMService._instance = LLMService()
        return LLMService._instance

    # ── Public API ────────────────────────────────────────────────────────────

    @staticmethod
    def active_llm() -> BaseChatModel:
        return LLMService.get_llm_service()._current

    def get_active_llm(self) -> BaseChatModel:
        return self._current

    @staticmethod
    def _build_online_llm(llm_config: AzureOpenAIConfig) -> BaseChatModel:
        """Get the LLM instance."""
        if llm_config.endpoint and llm_config.api_key:
            return AzureChatOpenAI(
                model=llm_config.model_name,
                azure_deployment=llm_config.deployment_name,
                api_version=llm_config.endpoint_version,
                azure_endpoint=llm_config.endpoint,
                api_key=llm_config.api_key,
            )
        else:
            return ChatOpenAI(model_name=llm_config.model_name, openai_api_key=llm_config.api_key)
