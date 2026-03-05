from pathlib import Path
from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    GITHUB_PAT_TOKEN: str = ""
    OPENAI_API_KEY: str = ""
    APIFY_API_TOKEN: str = ""

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATA_DIR: str = "data"
    TEMPLATES_DIR: str = "templates"
    OUTPUT_DIR: str = "output"
    LOGS_DIR: str = "logs"

    OPENAI_CV_MODEL: str = "gpt-4o"
    OPENAI_SCORING_MODEL: str = "gpt-4.1-nano"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_CV_TEMPERATURE: float = 0.3
    OPENAI_SCORING_TEMPERATURE: float = 0.1
    OPENAI_COVER_TEMPERATURE: float = 0.4

    GITHUB_USERNAME: str = ""

    APIFY_POLL_INTERVAL_SECONDS: int = 10
    APIFY_TIMEOUT_SECONDS: int = 600

    DEFAULT_DEADLINE_DAYS: int = 30
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "env_file_encoding": "utf-8"}

    @property
    def data_path(self) -> Path:
        return PROJECT_ROOT / self.DATA_DIR

    @property
    def templates_path(self) -> Path:
        return PROJECT_ROOT / self.TEMPLATES_DIR

    @property
    def output_path(self) -> Path:
        return PROJECT_ROOT / self.OUTPUT_DIR

    @property
    def logs_path(self) -> Path:
        return PROJECT_ROOT / self.LOGS_DIR


settings = Settings()
