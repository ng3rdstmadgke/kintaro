import base64
import hmac
import hashlib

from typing import Optional
from pydantic_settings import BaseSettings

class Environment (BaseSettings):
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_client_secret: str
    token_secret_key: str ="123456789"
    app_name: str = "kintaro"
    stage_name: str = "local"
    aws_region: str = "ap-northeast-1"
    endpoint_url: Optional[str] = None

    def get_secret_hash(self, username: str) -> str:
        # SECRET_HASH計算
        message = bytes(username + self.cognito_client_id, "utf-8")
        key = bytes(self.cognito_client_secret, "utf-8")
        secret_hash = base64.b64encode(
            hmac.new(key, message, digestmod=hashlib.sha256).digest()
        ).decode()
        return secret_hash


def get_env() -> Environment:
    return Environment()