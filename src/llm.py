from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from src.config import AzureOpenAIConfig, get_settings


class LLMService:
    """Service for interacting with the LLM."""

    def __init__(self) -> None:
        self._llm: BaseChatModel = self._build_online_llm(get_settings().llm_settings)

    def _build_online_llm(self, llm_config: AzureOpenAIConfig) -> BaseChatModel:
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
