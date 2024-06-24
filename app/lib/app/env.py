from typing import Optional
from pydantic_settings import BaseSettings

class Environment (BaseSettings):
    token_secret_key: str ="123456789"
    app_name: str = "kintaro"
    stage_name: str = "local"
    aws_region: str = "ap-northeast-1"
    endpoint_url: Optional[str] = None
    dynamo_table_name: str
    secret_name: str

def get_env() -> Environment:
    return Environment()