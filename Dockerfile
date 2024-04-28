FROM python:3.11-slim

RUN apt-get update

RUN apt-get install -y libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcairo2 libcups2 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0 libnspr4 libnss3 libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2 libxtst6 libx11-xcb1 xdg-utils libasound2

RUN apt-get install -y locales locales-all

ENV LANGUAGE ru_RU.UTF-8
ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8
RUN locale-gen ru_RU.UTF-8 && dpkg-reconfigure locales

RUN apt-get install --assume-yes --no-install-recommends --quiet unzip wget

RUN wget http://archive.ubuntu.com/ubuntu/pool/universe/c/chromium-browser/chromium-codecs-ffmpeg-extra_112.0.5615.49-0ubuntu0.18.04.1_amd64.deb -O ffmpeg.deb
RUN dpkg -i ffmpeg.deb
RUN rm ffmpeg.deb

RUN wget http://archive.ubuntu.com/ubuntu/pool/universe/c/chromium-browser/chromium-browser_112.0.5615.49-0ubuntu0.18.04.1_amd64.deb -O chromium.deb
RUN dpkg -i chromium.deb
RUN rm chromium.deb

COPY ./poetry.lock ./pyproject.toml ./

RUN pip install poetry
RUN poetry install

COPY . .

CMD poetry run python run.py
