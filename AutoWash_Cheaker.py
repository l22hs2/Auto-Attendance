import time
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import telegram
import asyncio

import account

# 시작 시간 출력
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"=== {now} ===")

# 텔레그램 세팅
token = account.telegram_token
chat_id = account.telegram_chat_id
bot = telegram.Bot(token=token)

async def send_message(message):
    await bot.send_message(chat_id=chat_id, text=f'{message}')

# 크롬 옵션
options = webdriver.ChromeOptions()
options.add_argument("--incognito")
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument('--no-sandbox')

# Chromium 실행 (패키지: chromium-chromedriver)
driver = webdriver.Chrome(service=Service('/usr/lib/chromium-browser/chromedriver'), options=options)

# 로그인
driver.get("https://autowash.co.kr/member/login.php")
driver.implicitly_wait(5)
driver.find_element(By.ID, 'loginId').send_keys(account.login_id)
driver.find_element(By.ID, 'loginPwd').send_keys(account.login_pw)
driver.find_element(By.CLASS_NAME, 'member_login_order_btn').click()

WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@class="cate_serach"]'))) # 메인 페이지로 복귀했는지 체크 (로그인 성공)
driver.find_element(By.XPATH, '//span[@class="btn_scroll_top2"]/a').click() # 출석 체크 배너 클릭

# 출석 체크
def attendance():
    fail_cnt = 0

    while True:
        try:
            # 출석 체크 버튼 클릭
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//button[@id="attendanceCheck"]'))).click()
            
            # 출석 체크 성공 여부 확인
            WebDriverWait(driver, 5).until(EC.alert_is_present()) # 알림창 대기
            alert = driver.switch_to.alert # 알림창
            alert_text = alert.text
            print(alert_text) # 알림창 문구 출력
            alert.accept() # 알림창 닫기
            
            myPage(alert_text) # 마이페이지로 이동
            break
        
        
        except: # 예외 처리
            fail_cnt += 1
            fail = f"출석 체크 실패, 재시도... ({fail_cnt}회)"
            print(fail)
            # asyncio.run(send_message(fail)) # 실패 메시지 전송

            # 5회 이상 실패시 중단
            if fail_cnt >= 5:
                break

# 보유 마일리지 조회
def myPage(alert_text):
    driver.find_element(By.XPATH, '//div[@class="mypage_wrap"]/a').click() # 마이페이지 이동
    driver.implicitly_wait(5)
    point = driver.find_element(By.XPATH, '//div[@class="mypage_top_wallet"]/ul/li[2]/span[2]/a/strong').text # 보유 마일리지
    print(f"보유 마일리지: {point}원")

    # 메시지 전송
    msg = f'''
    [ 오토워시 출석 체크 ]
    {alert_text}
    - 보유 마일리지: {point}
    '''
    msg = msg.lstrip()
    asyncio.run(send_message(msg))

# 출석 체크 함수 호출
attendance()

# 브라우저 종료
driver.quit()

# 종료 시간 출력
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"--- {now} ---")
print()