import os
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, BigInteger, Index
from sqlalchemy.sql import func
from loguru import logger

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "luban_v2v")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")

# 数据库连接字符串
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 创建数据库连接
database = Database(DATABASE_URL)

# 创建SQLAlchemy引擎和元数据
engine = create_engine(DATABASE_URL.replace("aiomysql", "pymysql"), echo=False)
metadata = MetaData()

# 定义 midjourney_task 表结构
midjourney_task = Table(
    "midjourney_task",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("task_name", String(64), nullable=False, default=""),
    Column("task_id", String(64), nullable=False, default=""),
    Column("trigger_id", String(32), nullable=False, default=""),
    Column("ref_pic_url", Text, nullable=True),
    Column("image_index", Integer, default=0),
    Column("msg_id", BigInteger, default=0),
    Column("msg_hash", String(64), default=""),
    Column("zoom_out", Integer, default=0),
    Column("direction", String(32), nullable=False, default=""),
    Column("task_type", String(32), nullable=False, default=""),
    Column("task_status", String(32), nullable=False, default=""),
    Column("result_url", Text, nullable=True),
    Column("attachments", Text, nullable=True),
    Column("created_at", DateTime, default=func.now()),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    # 索引
    Index("unq_task_id", "task_id", unique=True),
    Index("idx_trigger_id", "trigger_id"),
)


async def connect_db():
    """连接数据库"""
    try:
        await database.connect()
        logger.info("数据库连接成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise


async def disconnect_db():
    """断开数据库连接"""
    try:
        await database.disconnect()
        logger.info("数据库连接已断开")
    except Exception as e:
        logger.error(f"数据库断开连接失败: {e}")


def create_tables():
    """创建数据库表"""
    try:
        metadata.create_all(engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        raise 