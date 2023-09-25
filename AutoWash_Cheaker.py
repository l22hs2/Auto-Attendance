import os
import time
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def nowTime():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return(f"=== {now} ===")

# 시작 시간 출력
print(nowTime())

# 크롬 옵션
options = webdriver.ChromeOptions()
options.add_argument("--incognito")
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument('--no-sandbox')

# 텔레그램 세팅
token = os.environ.get('telegram_token')
chat_id = os.environ.get('telegram_chat_id')
button = {"inline_keyboard" : [[{"text" : "홈페이지로 이동", "url" : "https://autowash.co.kr/mypage/mileage.php"}]]}

# 텔레그램 봇 API
class Telegram:
    def __init__(self, msg):
        data = {"chat_id" : chat_id, "text": msg, "parse_mode": 'markdown', "reply_markup" : button}
        url = f"https://api.telegram.org/bot{token}/sendMessage?"
        requests.post(url, json=data)


try:
    # 출석체크 크롤러
    class Cheaker(Telegram):
        # 생성자
        def __init__(self, id, pw):
            self.id = id
            self.pw = pw
            self.alertText = ""
            self.point = ""

        # 출석체크
        def run(self):
            # Chromium 실행 (패키지: chromium-chromedriver)
            driver = webdriver.Chrome(options=options)

            # 로그인
            driver.get("https://autowash.co.kr/member/login.php")
            driver.implicitly_wait(5)
            driver.find_element(By.ID, 'loginId').send_keys(self.id)              # ID입력
            driver.find_element(By.ID, 'loginPwd').send_keys(self.pw)             # PW입력
            driver.find_element(By.CLASS_NAME, 'member_login_order_btn').click()  # 로그인 버튼 클릭
        
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@class="cate_serach"]'))) # 메인 페이지로 복귀했는지 체크 (로그인 성공)
            driver.find_element(By.XPATH, '//span[@class="btn_scroll_top2"]/a').click() # 출석 체크 배너 클릭

            # 출석 체크
            fail_cnt = 0 # 출석 실패 횟수

            while True:
                try:
                    # 출석 체크 버튼 클릭
                    time.sleep(1)
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//button[@id="attendanceCheck"]'))).click()

                    # 출석 체크 성공 여부 확인
                    time.sleep(1)
                    WebDriverWait(driver, 5).until(EC.alert_is_present()) # 알림창 대기

                    alert = driver.switch_to.alert # 알림창
                    self.alertText = alert.text
                    print(self.alertText) # 알림창 문구 출력
                    alert.accept() # 알림창 닫기
                    
                    # 보유 마일리지 조회
                    driver.find_element(By.XPATH, '//div[@class="mypage_wrap"]/a').click() # 마이페이지 이동
                    driver.implicitly_wait(5)
                    self.point = driver.find_element(By.XPATH, '//div[@class="mypage_top_wallet"]/ul/li[2]/span[2]/a/strong').text # 보유 마일리지
                    print(f"보유 마일리지: {self.point}원")

                    break

                except: # 예외 처리
                    fail_cnt += 1

                # 5회 이상 실패시 출석체크 중단
                if fail_cnt >= 5:
                    break

            if fail_cnt > 0:
                fail = f"[ {self.id} ] 출석 체크 실패 이력 존재 (재시도 {fail_cnt}회)"
                print(fail)
                Telegram(fail) # 실패 메시지 전송

            # driver 종료
            driver.quit()

    # 메인 계정 인스턴스 생성 및 실행
    main = Cheaker(str(os.environ.get('login_id_main')), str(os.environ.get('login_pw_main')))
    main.run()
    print(nowTime()) # 메인 계정 출석체크 완료 시간 출력

    # 서브 계정 인스턴스 생성 및 실행
    sub = Cheaker(str(os.environ.get('login_id_sub')), str(os.environ.get('login_pw_sub')))
    sub.run()

    # 출석체크 현황 보고 메시지 전송
    msg = f"\U00002705 *오토워시 출석 체크*\n\n\U0001F194 {main.id}\n{main.alertText}\n보유 마일리지: {main.point}원\n\n\U0001F194 {sub.id}\n{sub.alertText}\n보유 마일리지: {sub.point}원"
    Telegram(msg)

except:
    Telegram("\U0001F6A8 *오토워시 출석체크* - 오류 발생")

finally:
    # 종료 시간 출력
    print(nowTime()), print()