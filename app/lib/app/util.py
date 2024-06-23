from typing import Callable
import base64
import hmac
import hashlib


import boto3
from fastapi import Depends
from pydantic import BaseModel

from lib.app.env import get_env, Environment

def get_cognito_idp_client(env: Environment = Depends(get_env)):
    return boto3.client('cognito-idp', region_name=env.aws_region)

def get_dynamo_client(env: Environment = Depends(get_env)):
    return boto3.client('dynamodb', region_name=env.aws_region, endpoint_url=env.endpoint_url)

#
# SecretsManager
#
class SecretValue(BaseModel):
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_client_secret: str
    kms_key_id: str

def get_secret_value_factory(secret_name: str, aws_region: str) -> Callable[[], SecretValue]:
    client = boto3.client('secretsmanager', region_name=aws_region)
    def get_secret_value():
        response = client.get_secret_value(
            SecretId=secret_name
        )
        return SecretValue.model_validate_json(response['SecretString'])
    return get_secret_value

get_secret_value = get_secret_value_factory(get_env().secret_name, get_env().aws_region)


#
# Cognito
#
def get_secret_hash(username: str, cognito_client_id: str, cognito_client_secret: str) -> str:
    # SECRET_HASH計算
    message = bytes(username + cognito_client_id, "utf-8")
    key = bytes(cognito_client_secret, "utf-8")
    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode()
    return secret_hash


#
# KMS
#
def get_encrypt_kms(kms_key_id: str, aws_region: str) -> Callable[[str], str]:
    kms_client = boto3.client('kms', region_name=aws_region)
    def encrypt_kms(data: str) -> str:
        if  data.startswith("@encrypted@"):
            return data
        response = kms_client.encrypt(KeyId=kms_key_id, Plaintext=data.encode())
        ciphertext_blob = response["CiphertextBlob"]
        ciphertext_str = "@encrypted@" + base64.b64encode(ciphertext_blob).decode('utf-8')
        return ciphertext_str
    return encrypt_kms

encrypt_kms = get_encrypt_kms(get_secret_value().kms_key_id, get_env().aws_region)

def get_decrypt_kms(aws_region: str) -> Callable[[str], str]:
    kms_client = boto3.client('kms', region_name=aws_region)
    def decrypt_kms(data: str) -> str:
        if not data.startswith("@encrypted@"):
            return data
        decrypt_response = kms_client.decrypt(
            CiphertextBlob=base64.b64decode(data.replace("@encrypted@", ""))
        )
        decrypted_text = decrypt_response['Plaintext'].decode()
        return decrypted_text
    return decrypt_kms

decrypt_kms = get_decrypt_kms(get_env().aws_region)
