import os
import psutil
from yt_dlp import YoutubeDL


def yt_audio(url):
    url = ["https://www.youtube.com/watch?v=1Ut6RouSs0w"]
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.download(url)


def get_yt_info(url):
    youtube_dl_opts = {"skip_download": True}
    with YoutubeDL(youtube_dl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        if info_dict:
            url = info_dict.get("url", None)
            id = info_dict.get("id", None)
            title = info_dict.get('title', None)
        else:
            return
    return {"video_url": url, "video_id": id, "video_title": title}


if __name__ == "__main__":
    url = "https://m.youtube.com/watch?v=XIbl7ewBypY"
    resp = get_yt_info(url)
    print(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2)
    print(resp)
