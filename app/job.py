import sys
from typing import Optional
import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pydantic import BaseModel

from lib.common.secrets import get_secret_value_factory, SecretValue
from lib.common.util import get_setting_or_default
from lib.env import Environment, get_env

# メッセージをパースして表示
class SqsMessageBody(BaseModel):
    username: str

def sqs_receive_message(sqs_url: str, aws_region: str) -> Optional[SqsMessageBody]:
    # SQSクライアントの生成
    sqs_client = boto3.client('sqs', region_name=aws_region)

    # キューからメッセージを取り出す
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/receive_message.html
    response = sqs_client.receive_message(
        QueueUrl=sqs_url,
        MaxNumberOfMessages=1,  # 取得するメッセージの最大数
        WaitTimeSeconds=10, # ポーリングの待ち時間
    )
    messages = response.get("Messages", [])

    # メッセージが存在しない場合はそのまま終了
    if len(messages) <= 0:
        return None

    # 取得したメッセージを削除
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/delete_message.html
    sqs_client.delete_message(
        QueueUrl=env.sqs_url,
        ReceiptHandle=messages[0]["ReceiptHandle"],
    )
    return SqsMessageBody.model_validate_json(messages[0]["Body"])



def main(env: Environment, secret_value: SecretValue, jobcan_username: str, jobcan_password: str):
    # 打刻処理
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # ヘッドレスモードを有効にする
    chrome_options.add_argument("--disable-gpu")  # 可能であればGPUの使用を無効にする
    chrome_options.add_argument("--no-sandbox")    # サンドボックスモードを無効にする（特定の環境で必要）
    driver = webdriver.Chrome(options=chrome_options)

    # ログイン画面にアクセス
    driver.get("https://ssl.jobcan.jp/jbcoauth/login")
    driver.implicitly_wait(1)

    # クライアントコードの入力フォームを開く
    client_code_btn = driver.find_element(By.ID, "client_code_link")
    client_code_btn.click()
    driver.implicitly_wait(1)

    # ログイン情報の入力
    username = driver.find_element(By.ID, "user_email")  # ユーザー名入力欄のname属性を指定
    client_code = driver.find_element(By.ID, "user_client_code")  # ユーザー名入力欄のname属性を指定
    password = driver.find_element(By.ID, "user_password")  # パスワード入力欄のname属性を指定
    username.send_keys(jobcan_username)
    client_code.send_keys(secret_value.jobcan_client_code)
    password.send_keys(jobcan_password)

    # ログインボタンのクリック
    login_button = driver.find_element(By.ID, "login_button")  # ログインボタンのname属性を指定
    login_button.click()
    driver.implicitly_wait(3)
    driver.save_screenshot("tmp/login.png")

    # 勤怠ページに異動
    driver.get("https://ssl.jobcan.jp/jbcoauth/login")

    driver.save_screenshot("tmp/kintai.png")

    # 退勤ボタンをクリック
    #adit_btn = driver.find_element(By.ID, "adit-button-push")
    #adit_btn.click()
    # driver.implicitly_wait(3)
    driver.save_screenshot("tmp/adit.png")

    # S3にスクリーンショットをアップロード
    s3_client = boto3.client('s3', region_name=env.aws_region)
    screenshots = ["tmp/login.png", "tmp/kintai.png", "tmp/adit.png"]
    for screenshot in screenshots:
        s3_key = f"kintaro/{screenshot}"
        with open(screenshot, "rb") as f:
            s3_client.put_object(Bucket=env.app_bucket, Key=s3_key, Body=f)

    # ページタイトルを表示
    title = driver.title
    print(title)

if __name__ == "__main__":
    env = get_env()
    secret_value = get_secret_value_factory(env.secret_name, env.aws_region)()

    if env.debug:
        args = sys.argv
        jobcan_username = args[1]
        sqs_message_body = SqsMessageBody(
            username=jobcan_username,
        )
    else:
        sqs_message_body = sqs_receive_message(env.sqs_url, env.aws_region)
        if sqs_message_body is None:
            exit()
    
    dynamodb_client = boto3.client('dynamodb', region_name=env.aws_region)
    setting = get_setting_or_default(
        dynamodb_client,
        env.dynamo_table_name,
        sqs_message_body.username,
    )

    main(env, secret_value, setting.jobcan_id, setting.decrypt_jobcan_password())