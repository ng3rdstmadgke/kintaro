from pydantic import BaseModel

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


class NewPasswordRequest(BaseModel):
    username: str
    new_password: str
    session: str