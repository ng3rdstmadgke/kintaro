import traceback

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm

from lib.app.env import get_env, Environment
from lib.app.auth import get_current_user, create_token
from lib.app.schema import TimeCardSetting, NewPasswordRequest
from lib.app.util import (
    get_dynamo_client,
    get_cognito_idp_client,
    get_secret_value,
    get_secret_hash,
)

env = get_env()

app = FastAPI(
    redoc_url="/api/redoc",
    docs_url="/api/docs",
    openapi_url="/api/docs/openapi.json"
)

####################################
# 画面表示
####################################

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

@app.get("/new_password", response_class=HTMLResponse)
async def new_password(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new_password.html",
        context={}
    )

@app.get("/timecard", response_class=HTMLResponse)
async def timecard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="timecard/index.html",
        context={}
    )


####################################
# API
####################################
@app.get("/api/healthcheck")
def healthcheck():
    return {"status": "Healthy"}


@app.get("/api/timecard", response_model=TimeCardSetting)
def get_timecard(
    current_user = Depends(get_current_user)
):
    _, current_setting = current_user
    decrypted = current_setting.decrypt_jobcan_password()
    current_setting.jobcan_password = decrypted
    return current_setting


@app.post("/api/timecard", response_model=TimeCardSetting)
def update_timecard(
    data: TimeCardSetting,
    current_user = Depends(get_current_user),
    dynamo_client = Depends(get_dynamo_client),
    env: Environment = Depends(get_env),
):
    username, _ = current_user
    timecard_setting = TimeCardSetting.model_dump_json(data)
    dynamo_client.put_item(
        TableName=env.dynamo_table_name,
        Item={ "username": {"S": username}, "setting": {"S": timecard_setting} }
    )
    data.jobcan_password = data.decrypt_jobcan_password()
    return data


@app.post("/api/new_password")
def update_password(
    data: NewPasswordRequest,
    cognito_idp_client = Depends(get_cognito_idp_client),
    secret_value = Depends(get_secret_value),
):
    try:
        secret_hash = get_secret_hash(
            data.username,
            secret_value.cognito_client_id,
            secret_value.cognito_client_secret
        )
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp/client/admin_set_user_password.html
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp/client/respond_to_auth_challenge.html
        response = cognito_idp_client.respond_to_auth_challenge(
            ChallengeName="NEW_PASSWORD_REQUIRED",
            ClientId=secret_value.cognito_client_id,
            ChallengeResponses={
                "USERNAME": data.username,
                "NEW_PASSWORD": data.new_password,
                "SECRET_HASH": secret_hash,
            },
            Session=data.session,
        )
    except cognito_idp_client.exceptions.NotAuthorizedException as e:
        print("{}\n{}".format(str(e), traceback.format_exc()))
        raise HTTPException(status_code=400, detail=f"Failed to update password")

    if "AuthenticationResult" not in response or "IdToken" not in response["AuthenticationResult"]:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_token(data.username, secret_value.token_secret_key)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/token")
def get_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    cognito_idp_client = Depends(get_cognito_idp_client),
    secret_value = Depends(get_secret_value),
):
    username = form_data.username
    password = form_data.password

    try:
        secret_hash = get_secret_hash(
            username,
            secret_value.cognito_client_id,
            secret_value.cognito_client_secret
        )
        # Cognitoから認証情報取得
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp/client/initiate_auth.html
        response = cognito_idp_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
                "SECRET_HASH": secret_hash,
            },
            ClientId=secret_value.cognito_client_id,
        )
    except cognito_idp_client.exceptions.NotAuthorizedException as e:
        print("{}\n{}".format(str(e), traceback.format_exc()))
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # NOTE: admin_create_userで作成したユーザーは初回ログイン時にパスワード変更が必要
    if "ChallengeName" in response and response["ChallengeName"] == "NEW_PASSWORD_REQUIRED":
        return {"status": "NEW_PASSWORD_REQUIRED", "session": response["Session"]}

    if "AuthenticationResult" not in response or "IdToken" not in response["AuthenticationResult"]:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_token(username, secret_value.token_secret_key)
    return {"access_token": access_token, "token_type": "bearer"}


####################################
# 静的ファイル
####################################
# html=True : パスの末尾が "/" の時に自動的に index.html をロードする
# name="static" : FastAPIが内部的に利用する名前を付けます
app.mount("/static", StaticFiles(directory=f"/opt/app/static", html=True), name="static")