"""
    공주대학교 포털 및 LMS에 자동으로 로그인하는 스크립트입니다.
    
    최종 작성일 : 2024-05-29
    작성자 : 컴퓨터공학과 20 이진성(Thanks to chatGPT)
"""
import os
import json
import sys
import time
import getpass
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

LMS_LOGIN = 'https://kncu.kongju.ac.kr/xn-sso/login.php?auto_login=&sso_only=&cvs_lgn=&return_url=https%3A%2F%2Fkncu.kongju.ac.kr%2Fxn-sso%2Fgw-cb.php%3Ffrom%3D%26login_type%3Dstandalone%26return_url%3Dhttps%253A%252F%252Fkncu.kongju.ac.kr%252Flogin%252Fcallback'
LMS = 'https://knulms.kongju.ac.kr/'
PORTAL = 'https://portal.kongju.ac.kr/'


def get_base_dir():
    """
    개발 환경과 실행 환경의 디렉토리를 가져온다.
    """
    try:
        base_path = os.path.dirname(sys.executable)
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path

def hide_console():
    """
    콘솔을 최소화한다. (Windows에서만 적용됨)
    """
    if os.name == 'nt':
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

BASE_DIR = get_base_dir()
CONFIG_DIR = os.path.join(BASE_DIR, "config")

INFO_FILE = os.path.join(CONFIG_DIR, 'info.json')
KEY_FILE = os.path.join(CONFIG_DIR, 'key.key')


def check_config_dir():
    """
    config 디렉토리를 생성하여 info.json과 key.key 파일을 보관한다.
    """
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)


def generate_key():
    """
    대칭 암호화 키를 생성하여 key.key 파일에 저장한다.
    """
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)


def load_key():
    """
    대칭 암호화 키가 저장되어 있는 key.key 파일을 불러온다.

    Returns :
        bytes : 대칭 암호화 키
    """
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()


def encrpyt_message(message: str):
    """
    대칭 암호화 키를 이용하여 message를 암호화한다.

    Args :
        message (str) : 암호화할 메세지

    Returns :
        bytes : 암호화된 메세지
    """
    key = load_key()
    return Fernet(key).encrypt(message.encode())


def decrpyt_message(encrpyted_message: bytes):
    """
    대칭 암호화 키를 이용하여 message를 복호화한다.

    Args :
        encrpyted_message (bytes) : 암호화된 메세지

    Returns :
        str : 복호화된 메세지
    """
    key = load_key()
    return Fernet(key).decrypt(encrpyted_message).decode()


def load_information():
    """
    JSON으로 포맷된 username과 password를 복호화하여 불러온다.

    Returns :
        dict : username과 password가 포함된 딕셔너리 반환
        None : 파일이 존재하지 않으면 None 반환
    """
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, 'r') as f:
            information = json.load(f)
            username = decrpyt_message(information["username"].encode())
            password = decrpyt_message(information["password"].encode())
            return {'username': username, 'password': password}
    else:
        return None


def save_information(username: str, password: str):
    """
    유저의 정보를 암호화하여 JSON 파일로 저장한다.

    Args :
        username (str) : 사용자
        password (str) : 비밀번호
    """
    information = {
        'username': encrpyt_message(username).decode(),
        'password': encrpyt_message(password).decode()
    }

    with open(INFO_FILE, 'w') as f:
        json.dump(information, f)


def login(username: str, password: str):
    """
    LMS와 포탈에 자동으로 로그인한다.

    Args :
        username (str) : 아이디
        password (str) : 비밀번호
    """
    # Chrome 옵션 설정
    chrome_option = ChromeOptions()
    chrome_option.add_experimental_option("detach", True)

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=chrome_option)

    # LMS 로그인
    driver.get(LMS_LOGIN)
    username_input = driver.find_element(By.NAME, 'login_user_id')
    password_input = driver.find_element(By.NAME, 'login_user_password')
    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button = driver.find_element(By.CLASS_NAME, 'login_btn')
    login_button.click()

    driver.get(LMS)

    # 포탈 로그인
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(PORTAL)
    time.sleep(5)
    username_input = driver.find_element(
        By.ID, "frmIlban.sg_uid")
    password_input = driver.find_element(
        By.ID, "frmIlban.sg_pwd")
    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button = driver.find_element(
        By.ID, "frmIlban.pb_i_login")
    login_button.click()


def main():
    check_config_dir()

    if not os.path.exists(KEY_FILE):
        generate_key()

    information = load_information()

    if information:
        username = information["username"]
        password = information["password"]
    else:
        print("저장된 정보가 없습니다.", end='\n')
        username = input("아이디를 입력하세요: ")
        password = getpass.getpass("비밀번호를 입력하세요: ")
        save_information(username, password)

    hide_console()
    login(username, password)

    print("*******************************************************************")
    print("공주대학교 포탈과 LMS 자동 로그인 스크립트입니다")
    print("최종 작성일 : 2024-05-29")
    print("버그 제보 : https://github.com/BinarySstar/knu_auto_login/issues")
    print("\n콘솔 창을 닫으면 크롬 브라우저도 함께 종료됩니다")
    print("*******************************************************************")

if __name__ == "__main__":
    main()
