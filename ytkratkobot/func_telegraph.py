import json
import logging
import time

from .config import TELEGRAPH_FILENAME, APP_NAME
from telegraph import Telegraph, TelegraphException
# from pprint import pprint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_data(data: dict, url: str = "") -> dict:
    """ Возвращает ссылку на готовую страницу - статью """
    html = ""
    telegraph = Telegraph()
    register = telegraph.create_account(
        short_name=f"@{APP_NAME}",
        author_name="YouTube Kratko Telegram Bot",
        author_url=f"https://t.me/{APP_NAME}")
    json.dump(register, open(TELEGRAPH_FILENAME, 'w'))

    # if not data["content_id"]:
    #     from func_yt import get_yt_info
    #     yt_info = get_yt_info(url)
    #     data["content_id"] = yt_info["video_id"] if yt_info else ""

    if data["content_id"]:
        yt_url = f'https://www.youtube.com/watch?v={data["content_id"]}'
        html += f'<figure><iframe src="/embed/youtube?url={yt_url}"></iframe>'
        html += f'<figcaption>{yt_url}</figcaption></figure>'
    elif url:
        html += f'<figure><iframe src="/embed/youtube?url={url}"></iframe>'
        html += f'<figcaption>{url}</figcaption></figure>'

    for theses in data["keypoints"]:
        yt = f'https://youtu.be/{data["content_id"]}?&t={theses["start_time"]}'
        if not data["content_id"] and url:
            yt = f'{url}?&t={theses["start_time"]}'
        hms = time.strftime('%H:%M:%S', time.gmtime(theses["start_time"]))
        hms = f"<a href='{yt}'>{hms}</a>"
        # hms = None if not data["content_id"] else hms
        html += f'<h4>{hms + " " if hms else ""}{theses["content"]}</h4>'
        html += "<pre>"
        for content in theses["theses"]:
            html += f'<p>• {content["content"]}</p><br>'
        html += "</pre>"

    try:
        response = telegraph.create_page(
            title=data["video_title"] or data["type"],
            html_content=html,)
    except TelegraphException:
        logger.error(data)
        return {"error": 1}

    return dict({"data": html, "url": response['url']})


if __name__ == "__main__":
    # main(dict())
    parse_data(dict())
    # import asyncio
    # asyncio.run(parse_data(dict()))
