from typing import Optional
from pydantic_settings import BaseSettings

class Environment (BaseSettings):
    dynamo_table_name: str
    secret_name: str
    app_bucket: str
    sqs_url: str

    # デバッグ
    endpoint_url: Optional[str] = None
    debug: bool = False
    aws_region: str = "ap-northeast-1"

def get_env() -> Environment:
    return Environment()