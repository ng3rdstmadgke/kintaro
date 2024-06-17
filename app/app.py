import boto3
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

env = get_env()

app = FastAPI(
    redoc_url="/api/redoc",
    docs_url="/api/docs",
    openapi_url="/api/docs/openapi.json"
)

def get_dynamo_client():
    return boto3.client('dynamodb', region_name=env.aws_region, endpoint_url=env.aws_endpoint_url)

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

@app.get("/api/timecard", response_model=TimeCardSetting)
def read_timecard(
    dynamo_client = Depends(get_dynamo_client)
):
    user_name = "user1"
    table_name = f"{env.app_name}-{env.stage_name}-Users"
    item = dynamo_client.get_item(TableName=table_name, Key={"username": {"S": user_name}})
    timecard_setting = item["Item"]["settings"]["S"]
    return TimeCardSetting.model_validate_json(timecard_setting)

@app.post("/api/timecard", response_model=TimeCardSetting)
def post_timecard(
    data: TimeCardSetting,
    dynamo_client = Depends(get_dynamo_client)
):
    user_name = "user1"
    table_name = f"{env.app_name}-{env.stage_name}-Users"
    timecard_setting = TimeCardSetting.model_dump_json(data)
    dynamo_client.put_item(
        TableName=table_name,
        Item={ "username": {"S": user_name}, "settings": {"S": timecard_setting} }
    )
    return data

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