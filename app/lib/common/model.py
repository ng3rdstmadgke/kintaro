import base64
from typing import Any, Callable

import boto3
from pydantic import BaseModel, field_validator, ValidationInfo

from lib.common.secrets import get_secret_value
from lib.env import get_env

def get_encrypt_kms(kms_key_id: str, aws_region: str) -> Callable[[str], str]:
    kms_client = boto3.client('kms', region_name=aws_region)
    def encrypt_kms(data: str) -> str:
        if  data.startswith("@encrypted@") or data == "":
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
        if not data.startswith("@encrypted@") or data == "":
            return data
        decrypt_response = kms_client.decrypt(
            CiphertextBlob=base64.b64decode(data.replace("@encrypted@", ""))
        )
        decrypted_text = decrypt_response['Plaintext'].decode()
        return decrypted_text
    return decrypt_kms

decrypt_kms = get_decrypt_kms(get_env().aws_region)

class TimeCardSetting(BaseModel):
    class TimeCardSetting(BaseModel):
        class TimeCardSettingValue(BaseModel):
            clock_in: str
            clock_out: str
        Mon: TimeCardSettingValue
        Tue: TimeCardSettingValue
        Wed: TimeCardSettingValue
        Thu: TimeCardSettingValue
        Fri: TimeCardSettingValue
    enabled: bool
    jobcan_id: str
    jobcan_password: str
    setting: TimeCardSetting

    @field_validator('jobcan_password', mode='before')
    @classmethod
    def encrypt_jobcan_password(cls, v: str, info: ValidationInfo) -> Any:
        return encrypt_kms(v)

    def decrypt_jobcan_password(self) -> str:
        return decrypt_kms(self.jobcan_password)
