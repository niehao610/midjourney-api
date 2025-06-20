from os import getenv

from exceptions import MissRequiredVariableError

GUILD_ID = getenv("GUILD_ID")
CHANNEL_ID = getenv("CHANNEL_ID")
USER_TOKEN = getenv("USER_TOKEN")
CALLBACK_URL = getenv("CALLBACK_URL")
PROXY_URL = getenv("PROXY_URL")

DRAW_VERSION = getenv("DRAW_VERSION")

# 数据库配置
DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = getenv("DB_PORT", "3306")
DB_NAME = getenv("DB_NAME", "luban_v2v")
DB_USER = getenv("DB_USER", "root")
DB_PASSWORD = getenv("DB_PASSWORD", "12345678")

if not all([GUILD_ID, CHANNEL_ID, USER_TOKEN, DRAW_VERSION]):
    raise MissRequiredVariableError(
        "Missing required environment variable: [GUILD_ID, CHANNEL_ID, USER_TOKEN, DRAW_VERSION]")
