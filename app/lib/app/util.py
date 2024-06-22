import boto3

from fastapi import Depends

from lib.app.env import get_env, Environment
from lib.app.schema import TimeCardSetting

def get_cognito_idp_client(env: Environment = Depends(get_env)):
    return boto3.client('cognito-idp', region_name=env.aws_region)

def get_dynamo_client(env: Environment = Depends(get_env)):
    return boto3.client('dynamodb', region_name=env.aws_region, endpoint_url=env.endpoint_url)

def get_setting_or_default(dynamo_client, username: str, env: Environment) -> TimeCardSetting:
    table_name = f"{env.app_name}-{env.stage_name}-Users"
    item = dynamo_client.get_item(TableName=table_name, Key={"username": {"S": username}})
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
