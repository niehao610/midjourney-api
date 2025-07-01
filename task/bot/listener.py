import os
from discord import Intents, Message
from discord.ext import commands
from loguru import logger
from lib.api import PROXY_URL
from task.bot import TriggerStatus
from task.bot.handler import (
    match_trigger_id,
    set_temp,
    pop_temp,
    get_temp,
    callback_trigger,
    callback_describe
)

# 调试模式：设置环境变量 DEBUG_ALL_MESSAGES=true 来记录所有消息
DEBUG_ALL_MESSAGES = os.getenv("DEBUG_ALL_MESSAGES", "false").lower() == "true"

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents, proxy=PROXY_URL)


@bot.event
async def on_ready():
    logger.success(f"🚀 Discord Bot已连接 - 用户: {bot.user} (ID: {bot.user.id})")
    logger.info(f"📊 Bot连接状态:")
    logger.info(f"  - 延迟: {bot.latency * 1000:.2f}ms")
    logger.info(f"  - 服务器数量: {len(bot.guilds)}")
    logger.info(f"  - 频道数量: {len(list(bot.get_all_channels()))}")
    logger.info(f"  - 用户数量: {len(bot.users)}")
    
    # 列出所有连接的服务器
    for guild in bot.guilds:
        logger.info(f"  - 服务器: {guild.name} (ID: {guild.id})")
        
    logger.info("🎯 开始监听Midjourney Bot消息...")


@bot.event
async def on_connect():
    logger.info("🔗 Bot已连接到Discord")


@bot.event
async def on_disconnect():
    logger.warning("🔌 Bot与Discord断开连接")


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"❌ Bot事件错误 - 事件: {event}, 参数: {args}")


@bot.event
async def on_guild_join(guild):
    logger.info(f"🎉 Bot加入新服务器: {guild.name} (ID: {guild.id})")


@bot.event
async def on_message(message: Message):
    # 如果开启了完整调试模式，记录所有消息
    if DEBUG_ALL_MESSAGES:
        logger.info(f"📨 [全部消息] 用户: {message.author.name}({message.author.id}), 内容: {message.content[:200]}...")
        if message.embeds:
            logger.debug(f"📨 [全部消息] Embeds: {[embed.to_dict() for embed in message.embeds]}")
    else:
        # 正常调试模式：只记录部分信息
        logger.debug(f"收到消息 - 用户: {message.author.name}({message.author.id}), 内容: {message.content[:100]}...")
    
    # 检查是否是Midjourney Bot的消息
    if message.author.id != 936929561302675456:
        # 如果消息包含Midjourney相关内容，记录实际的用户ID
        if any(keyword in message.content.lower() for keyword in ['midjourney', 'mj', 'imagine', 'upscale', 'variation', 'job', 'waiting', 'stopped']):
            logger.warning(f"🤖 可能的Midjourney Bot消息 - 用户: {message.author.name}({message.author.id}), 内容: {message.content[:100]}...")
            
            # 如果是调试模式，显示完整信息
            if DEBUG_ALL_MESSAGES:
                logger.info(f"🔍 完整消息信息:")
                logger.info(f"  - 用户名: {message.author.name}")
                logger.info(f"  - 用户ID: {message.author.id}")
                logger.info(f"  - 显示名: {message.author.display_name}")
                logger.info(f"  - 是否为Bot: {message.author.bot}")
                logger.info(f"  - 消息内容: {message.content}")
                logger.info(f"  - 频道: {message.channel.name if hasattr(message.channel, 'name') else 'DM'}")
                logger.info(f"  - 服务器: {message.guild.name if message.guild else 'DM'}")
        
        if not DEBUG_ALL_MESSAGES:
            logger.debug(f"on_message: {message.content} ，author: {message.author.id}  != 936929561302675456")
        return

    logger.info(f"✅ 收到Midjourney Bot消息: {message.content}")
    logger.debug(f"on_message embeds: {message.embeds[0].to_dict() if message.embeds else message.embeds}")
    content = message.content
    trigger_id = match_trigger_id(content)
    if not trigger_id:
        logger.debug(f"未找到trigger_id: {content}")
        return

    if content.find("Waiting to start") != -1:
        trigger_status = TriggerStatus.start.value
        set_temp(trigger_id)
    elif content.find("(Stopped)") != -1:
        trigger_status = TriggerStatus.error.value
        pop_temp(trigger_id)
    else:
        trigger_status = TriggerStatus.end.value
        pop_temp(trigger_id)

    await callback_trigger(trigger_id, trigger_status, message)


@bot.event
async def on_message_edit(_: Message, after: Message):
    if after.author.id != 936929561302675456:
        return

    logger.debug(f"on_message_edit: {after.content}")
    if after.embeds:
        embed = after.embeds[0]
        if not (embed.image.width and embed.image.height):
            return

        embed = embed.to_dict()
        logger.debug(f"on_message_edit embeds: {embed}")
        trigger_status = TriggerStatus.text.value
        trigger_id = await callback_describe(trigger_status, after, embed)
        pop_temp(trigger_id)
        return

    trigger_id = match_trigger_id(after.content)
    if not trigger_id:
        return

    if after.webhook_id != "":
        await callback_trigger(trigger_id, TriggerStatus.generating.value, after)


@bot.event
async def on_message_delete(message: Message):
    if message.author.id != 936929561302675456:
        return

    trigger_id = match_trigger_id(message.content)
    if not trigger_id:
        return

    if get_temp(trigger_id) is None:
        return

    logger.debug(f"on_message_delete: {message.content}")
    logger.warning(f"sensitive content: {message.content}")
    trigger_status = TriggerStatus.banned.value
    pop_temp(trigger_id)
    await callback_trigger(trigger_id, trigger_status, message)
