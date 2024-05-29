from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")  # ヘッドレスモードを有効にする
chrome_options.add_argument("--disable-gpu")  # 可能であればGPUの使用を無効にする
chrome_options.add_argument("--no-sandbox")    # サンドボックスモードを無効にする（特定の環境で必要）

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://www.selenium.dev/selenium/web/web-form.html")
title = driver.title
print(title)