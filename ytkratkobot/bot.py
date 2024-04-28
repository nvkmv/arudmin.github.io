import logging
import sys
import time
import json
from re import Match

from .config import ADMIN_ID, DATA_FILENAME, ERROR_CODE
from .config import BASE_WEBHOOK_URL, WEBHOOK_PATH
from .config import TELEGRAM_TOKEN, WEBHOOK_SECRET
from .config import WEB_SERVER_HOST, WEB_SERVER_PORT

from .functions import Parser
from .func_telegraph import parse_data

from aiohttp import web
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram.webhook.aiohttp_server import setup_application
from aiogram.client.default import DefaultBotProperties

parser = Parser()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# All handlers should be attached to the Router (or Dispatcher)
router = Router()

regex = '(?:.+?)?(?:\/v\/|watch\/|live\/|\?v=|\&v=|youtu\.be\/'  # type: ignore
regex += '|\/v=|^youtu\.be\/|watch\%3Fv\%3D|live\/)([a-zA-Z0-9_-]{11})+'  # type: ignore


@router.message(F.text.regexp(regex).as_("url"))
async def catch_yt_link(message: Message, url: Match, bot: Bot) -> None:
    """
    This handler receives messages with `youtube` links
    """
    try:
        await bot.send_chat_action(
            message.chat.id, ChatAction.UPLOAD_DOCUMENT)
        parser = Parser()
    except BaseException:
        await on_error(message, bot)
        return

    url = url.string
    resp = parser.get_response(url)

    # проверяем наличие ошибки в ответе
    if "status_code" in resp.keys():
        if "error" == resp["status_code"]:
            if "Not Found" in resp["message"]:
                logger.error(f'{resp["message"]}, {url}')
                await message.reply("Некорректная ссылка")
                return
            await on_error(message, bot, text=resp["message"])
            return
    # проверка на наличие параметра interval
    if "interval" not in resp.keys():
        await on_error(message, bot)
        return

    interval = int(resp["interval"]) / 1000 + 0.1
    session_id = resp["session_id"]
    status_not_finished = True

    while status_not_finished:
        time.sleep(interval)
        data = parser.update_response(session_id, url)
        # Если это живая трансляция - исключаем
        if data["status_code"] == 2:
            await message.reply(ERROR_CODE[data["error_code"]] or "Ошибка")
            await bot.send_message(ADMIN_ID,
                                   f"{url}\r\n\r\n{json.dumps(data)}")
            return
        status_not_finished = bool(data["status_code"])

    json.dump(data, open(DATA_FILENAME, 'w'))

    # отправляем данные для формирования страницы в telegraph
    yturl = str(url) if data["content_id"] == "" else ""
    resp = parse_data(data, yturl)

    # проверяем наличие ошибки в ответе
    if "error" in resp.keys():
        await on_error(message, bot)
        return

    # отправляем ссылку админу
    if message.from_user and int(ADMIN_ID) != int(message.from_user.id):
        username = message.from_user.full_name
        user_url = message.from_user.url
        msg = f"<a href='{user_url}'>{username}</a>" + "\r\n\r\n" + resp["url"]
        await bot.send_message(
            ADMIN_ID, msg, disable_web_page_preview=True,
            disable_notification=True)

    # отправляем ссылку пользователю
    await message.reply(
        # + "<pre>Работает на базе YandexGPT</pre>"
        resp["url"] + "\r\n\r\n<a href='https://t.me/ytkratkobot'>@ytkratkobot</a>")


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    full_name = message.from_user.full_name if message.from_user else ""
    await message.answer("".join([
        f"Привет, {hbold(full_name)}!",
        "\r\n\r\n",
        "Пришли ссылку на Ютуб-видео, а нейросеть ",
        "быстро и кратко перескажет его содержание.",
        "<pre>Работает на базе YandexGPT</pre>"]))


@router.message()
async def echo_handler(message: types.Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types
    (like text, photo, sticker etc.)
    """
    try:
        await message.reply("Некорректная ссылка на ютуб-видео.")
        # Send a copy of the received message
        # await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def on_startup(bot: Bot) -> None:
    # If you have a self-signed SSL certificate, then you will need
    # to send a public certificate to Telegram
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}",
                          secret_token=WEBHOOK_SECRET)
    await bot.send_message(ADMIN_ID, "bot started")


async def on_error(message: Message, bot: Bot, text=""):
    username = message.from_user.full_name  # type: ignore
    user_url = message.from_user.url  # type: ignore
    url = f"<a href='{user_url}'>{username}</a>"
    await message.answer("".join([
        "Произошла ошибка во время работы, попробуйте позже.",
        "\r\n\r\n",
        "Поддержка уже в курсе, сейчас разберутся."]))
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"❗error {text}\r\n{url}\r\n\r\n{str(message.text)}",
        disable_web_page_preview=True)


def main() -> None:
    # Dispatcher is a root router
    dp = Dispatcher()
    # ... and all other routers should be attached to Dispatcher
    dp.include_router(router)

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)

    # Initialize Bot instance with a default
    # parse mode which will be passed to all API calls
    bot = Bot(TELEGRAM_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler
    # which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(asyncio.run(main))
    # asyncio.run(main())
    main()
