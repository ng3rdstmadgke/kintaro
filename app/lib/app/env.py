from typing import Optional
from pydantic_settings import BaseSettings

class Environment (BaseSettings):
    app_name: str = "kintaro"
    stage_name: str = "local"
    aws_region: str = "ap-northeast-1"
    aws_endpoint_url: Optional[str] = None

def get_env() -> Environment:
    return Environment()