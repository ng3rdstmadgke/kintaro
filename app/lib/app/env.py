from pydantic_settings import BaseSettings

class Environment (BaseSettings):
    aws_region: str = "ap-northeast-1"

def get_env() -> Environment:
    return Environment()