"""
앱 설정 관리 모듈
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App
    app_name: str = "곡소리매매법"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key"

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/goksori_db"

    # Crawler
    crawl_interval_hours: int = 4
    kospi200_list_update_days: int = 7
    request_delay_seconds: float = 1.0
    max_comments_per_stock: int = 100

    # External APIs
    dart_api_key: str = ""
    adsense_client_id: str = ""
    kakao_js_key: str = ""

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "../../config/.env")
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
