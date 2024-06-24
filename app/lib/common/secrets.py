from typing import Callable

from pydantic import BaseModel
import boto3

from lib.env import get_env

class SecretValue(BaseModel):
    jobcan_client_code: str
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_client_secret: str
    kms_key_id: str
    token_secret_key: str

def get_secret_value_factory(secret_name: str, aws_region: str) -> Callable[[], SecretValue]:
    client = boto3.client('secretsmanager', region_name=aws_region)
    def get_secret_value():
        response = client.get_secret_value(
            SecretId=secret_name
        )
        return SecretValue.model_validate_json(response['SecretString'])
    return get_secret_value

get_secret_value = get_secret_value_factory(get_env().secret_name, get_env().aws_region)
