from typing import Any
from pydantic import BaseModel, field_validator, ValidationInfo, computed_field
from lib.app.util import encrypt_kms, decrypt_kms

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

class NewPasswordRequest(BaseModel):
    username: str
    new_password: str
    session: str
