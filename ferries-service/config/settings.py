import os
from dotenv import load_dotenv

#force to find .env from project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # config/
ROOT_DIR = os.path.dirname(BASE_DIR)  # project root
load_dotenv(os.path.join(ROOT_DIR, ".env"))


class Settings:
    SINDO_AGENT_URL: str = os.getenv("SINDO_AGENT_URL") or "https://api.test.sindoferry.com.sg/Agent"
    SINDO_CORE_URL: str = os.getenv("SINDO_CORE_URL") or "https://core.test.sindoferry.com.sg/api"
    SINDO_AGENT_CODE: str = os.getenv("SINDO_AGENT_CODE", "")
    SINDO_USERNAME: str = os.getenv("SINDO_USERNAME", "")
    SINDO_PASSWORD: str = os.getenv("SINDO_PASSWORD", "")

    def validate(self):
        missing = [k for k, v in self.__dict__.items() if v in (None, "")]
        if missing:
            raise RuntimeError(f"Missing required env vars: {missing}")

settings = Settings()
settings.validate()
