from os import getenv
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

APP_NAME = "ytkratkobot"

# Bot token can be obtained via https://t.me/BotFather
TELEGRAM_TOKEN = getenv("TELEGRAM_TOKEN", "")
# Webserver settings
# bind localhost only to prevent any external access
WEB_SERVER_HOST = "0.0.0.0"
# Port for incoming request from reverse proxy. Should be any available port
WEB_SERVER_PORT = 8087
# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = "/webhook"
# Secret key to validate requests from Telegram (optional)
WEBHOOK_SECRET = "123456789123456789123456789"
# Base URL for webhook will be used to generate webhook URL for Telegram,
# in this example it is used public DNS with HTTPS support
FLY_APP_NAME = getenv("FLY_APP_NAME", APP_NAME)
BASE_WEBHOOK_URL = f"https://{FLY_APP_NAME}.fly.dev"

try:
    from ngrok import get_ngrok_url
    BASE_WEBHOOK_URL = get_ngrok_url(WEB_SERVER_PORT)
except ImportError:
    pass

ADMIN_ID = getenv('ADMIN_ID', "")

AUTH_LOGIN = getenv('AUTH_LOGIN', "")
AUTH_PASS = getenv('AUTH_PASS', "")

COOKIE_FILENAME = "ytkratkobot/json/cookie.json"
COOKIE_B64_FILENAME = "ytkratkobot/json/cookie_b64.json"
DATA_FILENAME = "ytkratkobot/json/data.json"
TELEGRAPH_FILENAME = "ytkratkobot/json/telegraph.json"

ERROR_CODE = {}
ERROR_CODE[21] = "Нейросеть пока не умеет пересказывать видео длиннее четырех часов. Попробуйте другое."
ERROR_CODE[23] = "Нейросеть пока не научилась пересказывать онлайн трасляции. Попробуйте другое."
