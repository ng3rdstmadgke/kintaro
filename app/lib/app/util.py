import boto3
from fastapi import Depends

from lib.env import get_env, Environment

def get_cognito_idp_client(env: Environment = Depends(get_env)):
    return boto3.client('cognito-idp', region_name=env.aws_region)

def get_dynamodb_client(env: Environment = Depends(get_env)):
    return boto3.client('dynamodb', region_name=env.aws_region, endpoint_url=env.endpoint_url)
