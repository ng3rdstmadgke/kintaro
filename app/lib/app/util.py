from typing import Callable
import base64

import boto3
from fastapi import Depends

from lib.app.env import get_env, Environment

def get_cognito_idp_client(env: Environment = Depends(get_env)):
    return boto3.client('cognito-idp', region_name=env.aws_region)

def get_dynamo_client(env: Environment = Depends(get_env)):
    return boto3.client('dynamodb', region_name=env.aws_region, endpoint_url=env.endpoint_url)

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

encrypt_kms = get_encrypt_kms(get_env().kms_key_id, get_env().aws_region)

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