from datetime import datetime, timedelta
from typing import List, Tuple
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError

from lib.app.env import get_env

app = FastAPI(
    redoc_url="/api/redoc",
    docs_url="/api/docs",
    openapi_url="/api/docs/openapi.json"
)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )

@app.get("/timecard", response_class=HTMLResponse)
async def timecard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="timecard/index.html",
        context={}
    )


@app.get("/api/healthcheck")
def healthcheck():
    return {"status": "Healthy"}



class TimeCard(BaseModel):
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

@app.get("/api/timecard", response_model=TimeCard)
def read_timecard():
    return {
        "enabled": True,
        "jobcan_id": "123456789",
        "jobcan_password": "password",
        "setting": {
            "Mon": {"clock_in": "09:00", "clock_out": "18:00"},
            "Tue": {"clock_in": "09:00", "clock_out": "18:00"},
            "Wed": {"clock_in": "09:00", "clock_out": "18:00"},
            "Thu": {"clock_in": "09:00", "clock_out": "18:00"},
            "Fri": {"clock_in": "09:00", "clock_out": "18:00"},
        }
    }

@app.post("/api/timecard", response_model=TimeCard)
def post_timecard(
    data: TimeCard
):
    return {
        "enabled": False,
        "jobcan_id": "123456789",
        "jobcan_password": "password",
        "setting": {
            "Mon": {"clock_in": "09:30", "clock_out": "18:30"},
            "Tue": {"clock_in": "09:30", "clock_out": "18:30"},
            "Wed": {"clock_in": "09:30", "clock_out": "18:30"},
            "Thu": {"clock_in": "09:30", "clock_out": "18:30"},
            "Fri": {"clock_in": "09:30", "clock_out": "18:30"},
        }
    }

@app.post("/api/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    _password = form_data.password
    payload={
        # JWT "sub" Claim : https://openid-foundation-japan.github.io/draft-ietf-oauth-json-web-token-11.ja.html#subDef
        "sub": form_data.username,
        "scopes": [],
        "exp": datetime.now() + timedelta(minutes=60)
    }

    # トークンの生成
    token_secret_key = "123456789"
    access_token = jwt.encode(payload, token_secret_key, algorithm="HS256")
    return {"access_token": access_token, "token_type": "bearer"}


# html=True : パスの末尾が "/" の時に自動的に index.html をロードする
# name="static" : FastAPIが内部的に利用する名前を付けます
app.mount("/static", StaticFiles(directory=f"/opt/app/static", html=True), name="static")