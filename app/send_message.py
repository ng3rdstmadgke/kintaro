import json
import boto3
from pydantic_settings import BaseSettings

class Environment(BaseSettings):
    jobcan_client_code: str
    jobcan_username: str
    jobcan_password: str
    sqs_url: str
    aws_region: str = "ap-northeast-1"

env = Environment()

sqs_client = boto3.client('sqs', region_name=env.aws_region)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/send_message.html
response = sqs_client.send_message(
    QueueUrl=env.sqs_url,
    MessageBody=json.dumps({
        "client_code": env.jobcan_client_code,
        "username": env.jobcan_username,
        "password": env.jobcan_password
    }, ensure_ascii=False)
)
print(response)