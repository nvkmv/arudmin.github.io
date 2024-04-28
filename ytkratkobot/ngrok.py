from os import getenv
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.


def get_ngrok_url(WEBAPP_PORT):
    from pyngrok import ngrok
    NGROK_AUTH_TOKEN = getenv("NGROK_AUTH_TOKEN", "")
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    http_tunnel = ngrok.connect(WEBAPP_PORT, bind_tls=True)
    return http_tunnel.public_url.replace("https://", "")
