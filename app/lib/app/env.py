from typing import Optional
from pydantic_settings import BaseSettings

class Environment (BaseSettings):
    aws_region: str = "ap-northeast-1"
    endpoint_url: Optional[str] = None
    dynamo_table_name: str
    secret_name: str

def get_env() -> Environment:
    return Environment()