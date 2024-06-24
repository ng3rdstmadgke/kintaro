from pydantic import BaseModel

class NewPasswordRequest(BaseModel):
    username: str
    new_password: str
    session: str
