import os
import time
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
button = {"inline_keyboard" : [[{"text" : "마일리지 내역 보기", "url" : "https://autowash.co.kr/myshop/mileage/historyList.html"}]]}

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

        def run(self):
            # Chromium 실행 (패키지: chromium-chromedriver)
            driver = webdriver.Chrome(options=options)

            # 로그인
            driver.get(r"https://autowash.co.kr/member/login.html?noMemberOrder&returnUrl=%2Fmyshop%2Findex.html")
            driver.implicitly_wait(5)
            driver.find_element(By.ID, 'member_id').send_keys(self.id)                  # ID입력
            driver.find_element(By.ID, 'member_passwd').send_keys(self.pw)              # PW입력
            driver.find_element(By.XPATH, '//div[@class="login__button"]/a').click()    # 로그인 버튼 클릭
        
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@class="bottom-nav__go"]'))) # 메인 페이지로 복귀했는지 (배너)체크 (=로그인 성공)
            driver.find_element(By.XPATH, '//div[@class="bottom-nav__go"]/a[2]').click() # 출석 체크 배너 클릭

            # 출석 체크
            fail_cnt = 0 # 출석 실패 횟수
            running = False # 출석 체크 수행 여부

            while True:
                try:
                    # 출석 체크 버튼 클릭 시도
                    try:
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//p[@class="ec-base-button gFull"]/a'))).click()
                        running = True
                    # 이미 출석 체크한 경우
                    except TimeoutException:
                        self.alertText = driver.find_element(By.XPATH, '//div[@id="contents"]/div/div[3]/div[3]/p').text
                        print(self.alertText)
                    
                    # 출석 체크 수행
                    if running:
                        # 보안문자
                        img = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@class="capcha "]/img'))) # Captcha 이미지
                        img.screenshot("/home/ubuntu/service/Web-Auto-Attendance/cap.png")  # 이미지 저장
                        time.sleep(1)

                        # Captcha 해독
                        driver.execute_script('window.open("https://google.com");') # 새 탭 생성
                        time.sleep(1)
                        driver.switch_to.window(driver.window_handles[-1]) # 탭 전환

                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@class="nDcEnd"]'))).click() # 구글 렌즈

                        input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@name='encoded_image']"))) # file input 태그
                        input.send_keys("/home/ubuntu/service/Web-Auto-Attendance/cap.png") # Captcha 이미지 첨부

                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//button[@id="ucj-2"]'))).click() # 텍스트 인식
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//button[@class="VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 kCfKMb"]'))).click() # 모든 텍스트 선택
                        time.sleep(1)
                        captcha = driver.find_element(By.XPATH, '//h1[@class="wCgoWb"]').text # 해독한 텍스트
                        captcha = captcha.replace(" " , "") # 공백 제거
                        print(captcha)

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        
                        driver.find_element(By.ID, 'secure_text').send_keys(captcha) # 보안문자 기입
                        driver.find_element(By.XPATH, '//a[@class="btnSubmit sizeS"]').click()


                        # 출석 체크 성공 여부 확인
                        WebDriverWait(driver, 5).until(EC.alert_is_present()) # 알림창 대기

                        alert = driver.switch_to.alert # 알림창
                        self.alertText = alert.text
                        print(self.alertText) # 알림창 문구 출력
                        alert.accept() # 알림창 닫기
                        time.sleep(1)

                        # 보안문자가 틀린 경우
                        if not self.alertText == "출석체크 처리되었습니다. 감사합니다.":
                            print("- 보안문자 불일치")
                            raise
                        
                    # 보유 마일리지 조회
                    driver.execute_script('window.open("https://autowash.co.kr/myshop/mileage/historyList.html");') # 새 탭 생성
                    time.sleep(1)
                    driver.switch_to.window(driver.window_handles[-1]) # 탭 전환

                    driver.implicitly_wait(5)
                    self.point = driver.find_element(By.XPATH, '//span[@id="xans_myshop_summary_avail_mileage"]').text # 보유 마일리지
                    print(f"보유 마일리지: {self.point}")

                    break
                
                # 예외 처리
                except Exception as e:
                    fail_cnt += 1       # 실패 횟수 증가
                    print(f"예외 발생: {fail_cnt}회")
                    print(e)
                    driver.refresh()    # Captcha 문자 새로고침을 위한 브라우저 새로고침

                # 3회 이상 실패시 출석체크 중단
                if fail_cnt >= 3:
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
    msg = f"\U00002705 *오토워시 출석 체크*\n\n\U0001F194 {main.id}\n{main.alertText}\n보유 마일리지: {main.point}\n\n\U0001F194 {sub.id}\n{sub.alertText}\n보유 마일리지: {sub.point}"
    Telegram(msg)

except Exception as e:
    Telegram("\U0001F6A8 *오토워시 출석체크* - 오류 발생")
    print("예외발생")
    print(e)

finally:
    # 종료 시간 출력
    print(nowTime()), print()