import traceback
from typing import Tuple
from datetime import datetime, timedelta

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from lib.app.env import get_env, Environment
from lib.app.schema import TimeCardSetting
from lib.app.util import get_dynamo_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


def create_token(username: str, env: Environment = get_env()) -> str:
    payload={
        # JWT "sub" Claim : https://openid-foundation-japan.github.io/draft-ietf-oauth-json-web-token-11.ja.html#subDef
        "sub": username,
        "scopes": [],
        "exp": datetime.now() + timedelta(minutes=60)
    }

    # トークンの生成
    return jwt.encode(payload, env.token_secret_key, algorithm="HS256")

def get_setting_or_default(dynamo_client, username: str, env: Environment) -> TimeCardSetting:
    item = dynamo_client.get_item(
        TableName=env.dynamo_table_name,
        Key={"username": {"S": username}}
    )
    try:
        timecard_setting = item["Item"]["setting"]["S"]
        return TimeCardSetting.model_validate_json(timecard_setting)
    except KeyError:
        return TimeCardSetting.model_validate({
          "enabled": False,
          "jobcan_id": "",
          "jobcan_password": "",
          "setting": {
              "Mon": {"clock_in": "09:00", "clock_out": "18:00"},
              "Tue": {"clock_in": "09:00", "clock_out": "18:00"},
              "Wed": {"clock_in": "09:00", "clock_out": "18:00"},
              "Thu": {"clock_in": "09:00", "clock_out": "18:00"},
              "Fri": {"clock_in": "09:00", "clock_out": "18:00"},
          }
        })

def get_current_user(
    token: str = Depends(oauth2_scheme),
    dynamo_client = Depends(get_dynamo_client),
    env: Environment = Depends(get_env)
) -> Tuple[str, TimeCardSetting]:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        # JWTのデコードと電子署名のチェックを行う
        payload = jwt.decode(token, env.token_secret_key, algorithms=["HS256"])
        # デコードされたJWTのペイロードからusernameを取得
        username = payload["sub"]
    except JWTError as e:
        print("{}\n{}".format(str(e), traceback.format_exc()))
        raise credentials_exception

    try:
        setting = get_setting_or_default(dynamo_client, username, env)
        return (username, setting)
    except Exception as e:
        print("{}\n{}".format(str(e), traceback.format_exc()))
        raise credentials_exception