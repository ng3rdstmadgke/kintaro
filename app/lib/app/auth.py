import base64
import hmac
import hashlib
import traceback
from typing import Tuple
from datetime import datetime, timedelta

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from lib.env import get_env, Environment
from lib.common.util import get_setting_or_default
from lib.common.secrets import get_secret_value
from lib.common.model import TimeCardSetting
from lib.app.util import get_dynamodb_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def get_secret_hash(username: str, cognito_client_id: str, cognito_client_secret: str) -> str:
    # SECRET_HASH計算
    message = bytes(username + cognito_client_id, "utf-8")
    key = bytes(cognito_client_secret, "utf-8")
    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode()
    return secret_hash

def create_token(username: str, token_secret_key: str) -> str:
    payload={
        # JWT "sub" Claim : https://openid-foundation-japan.github.io/draft-ietf-oauth-json-web-token-11.ja.html#subDef
        "sub": username,
        "scopes": [],
        "exp": datetime.now() + timedelta(minutes=60)
    }

    # トークンの生成
    return jwt.encode(payload, token_secret_key, algorithm="HS256")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    dynamodb_client = Depends(get_dynamodb_client),
    env: Environment = Depends(get_env)
) -> Tuple[str, TimeCardSetting]:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        secret_value = get_secret_value()
        # JWTのデコードと電子署名のチェックを行う
        payload = jwt.decode(token, secret_value.token_secret_key, algorithms=["HS256"])
        # デコードされたJWTのペイロードからusernameを取得
        username = payload["sub"]
    except JWTError as e:
        print("{}\n{}".format(str(e), traceback.format_exc()))
        raise credentials_exception

    try:
        setting = get_setting_or_default(dynamodb_client, env.dynamo_table_name, username)
        return (username, setting)
    except Exception as e:
        print("{}\n{}".format(str(e), traceback.format_exc()))
        raise credentials_exception