import sys
import json
import boto3
from pydantic_settings import BaseSettings

username = sys.argv[1]

class Environment(BaseSettings):
    jobcan_username: str
    jobcan_password: str
    sqs_url: str

env = Environment()

sqs_client = boto3.client('sqs', region_name="ap-northeast-1")

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/send_message.html
response = sqs_client.send_message(
    QueueUrl=env.sqs_url,
    MessageBody=json.dumps({
        "username": username
    }, ensure_ascii=False)
)
print(response)