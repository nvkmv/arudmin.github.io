import base64
import json
import logging
import httpx
import time
import os

from .config import COOKIE_FILENAME, DATA_FILENAME
from .config import AUTH_LOGIN, AUTH_PASS
from .config import COOKIE_B64_FILENAME
# from dotenv import load_dotenv
from functools import reduce

DEBUG = False

logging.basicConfig(level=logging.INFO if not DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

endpoint = '/api/generation'
start_url = "https://300.ya.ru"
auth_url = "https://passport.yandex.ru/auth/welcome?retpath=https://300.ya.ru"


class Parser():
    def __init__(self):
        self.cookies = self._get_cookies()
        self.async_client = httpx.Client(
            base_url=start_url,
            timeout=httpx.Timeout(timeout=40.0, read=None),
            cookies=self.cookies)  # type: ignore
        logger.info('service 300.ya.ru successfully loaded')

    def _get_cookies(self):
        cookies = str(os.getenv("COOKIE", ""))
        if cookies:
            cookies = base64.b64decode(cookies)
            cookies = cookies.decode("ascii").replace("'", '"')
            logger.info("Loading cookies from ENVIRONMENT.")
            # cookies = base64.b64encode(cookie_env.encode('ascii'))
            return json.loads(cookies)
        try:
            cookies = json.load(open(COOKIE_FILENAME))
            logger.info("Loading cookies from JSON FILE.")
            return cookies
        except BaseException:
            logger.error("NO COOKIES. Loading cookies from WEBSITE.")

        from selenium import webdriver
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        # options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        try:
            chrome = ChromeDriverManager().install()
        except BaseException:
            return False
        wd = webdriver.Chrome(
            service=ChromeService(chrome),
            options=options)

        wd.get(auth_url)
        try:  # login
            wd.find_element(By.ID, "passp-field-login").send_keys(AUTH_LOGIN)
        except BaseException:
            logger.info("Не удалось ввести логин.")

        wd.find_element(By.XPATH, '//button[@id="passp:sign-in"]').click()
        time.sleep(2)
        try:  # password
            wd.find_element(By.ID, "passp-field-passwd").send_keys(AUTH_PASS)
        except TimeoutException:
            logger.info("Не удалось ввести пароль.")

        wd.find_element(By.XPATH, '//button[@id="passp:sign-in"]').click()

        time.sleep(25)

        cookies_data = wd.get_cookies()
        cookies = [{k['name']: k['value']} for k in cookies_data]
        cookies = reduce(lambda x, y: dict(x, **y), cookies)

        enc = str(cookies).encode('ascii')  # utf-8 by default
        cookies_b64 = base64.b64encode(enc).decode('ascii')
        print(cookies_b64)

        json.dump(cookies_b64, open(COOKIE_B64_FILENAME, 'w'))
        json.dump(cookies, open(COOKIE_FILENAME, 'w'))
        return cookies

    def _check_availability(self):
        data = {"action": "0"}
        request_url = '/cgi-bin/office/kpp5/archive.cgi'
        self.async_client.post(request_url, data=data)
        # root = lh.fromstring(resp.text)
        # if root.text_content().startswith('location.href'):
        #     logger.error('COOKIES EXPIRED')
        #     self.__init__()

    def _clear_cookies(self):
        self.async_client = httpx.Client(
            base_url=start_url,
            cookies=None
        )

    def get_content_with_parser(self, url):
        payload = {"video_url": url}
        # headers = {"Content-Type": "application/json"}
        resp = self.async_client.post(endpoint, json=payload)
        # logger.debug(f"{resp.status_code, resp.json}")
        return resp

    def get_response(self, url):
        """ Делает первичный запрос и возвращает информацию для апдейтов """
        resp = self.get_content_with_parser(url)
        data = resp.json()
        # logger.warning(data)
        if not data or "message" in data:
            logger.error("Can't login to the service.")
            json.dump("", open(COOKIE_FILENAME, 'w'))
            return {"status_code": "error", **data}
        return {"status_code": data["status_code"],
                "interval": data["poll_interval_ms"],
                "session_id": data["session_id"]}

    def update_response(self, session_id, url):
        # status_not_finished = True
        # while status_not_finished:
        # interval = interval / 1000
        # time.sleep(interval)
        payload = {"video_url": url, "session_id": session_id}
        resp = self.async_client.post(endpoint, json=payload)
        # status_not_finished = bool(data["status_code"])
        return resp.json()
        # for theses in data["keypoints"]:
        #     print()
        #     print("***", theses["content"], "***")
        #     for content in theses["theses"]:
        #         print("--", content["content"])


def main():
    parser = Parser()
    url = "https://www.youtube.com/watch?v=t9Ilev-uk4w"  # live stream
    # url = "https://www.youtube.com/watch?v=kjbpP5tJ5QM"

    resp = parser.get_response(url)
    print(resp)
    interval = int(resp["interval"]) / 1000 + 0.1
    session_id = resp["session_id"]
    status_not_finished = True

    while status_not_finished:
        time.sleep(interval)
        data = parser.update_response(session_id, url)
        logger.warning(data)
        status_not_finished = bool(data["status_code"])
    json.dump(data, open(DATA_FILENAME, 'w'))
    print("=============== OK ===============")
    # for theses in data["keypoints"]:
    #     print()
    #     print("***", theses["content"], "***")
    #     for content in theses["theses"]:
    #         print("--", content["content"])


def load_cookie_b64():
    cookies_b64 = open(COOKIE_B64_FILENAME, encoding="ascii")
    cookies_b64 = cookies_b64.read()
    cookies = base64.b64decode(cookies_b64)
    cookies = cookies.decode("ascii").replace("'", '"')
    print(cookies)
    json.loads(cookies)


if __name__ == "__main__":
    main()
    # load_cookie_b64()
