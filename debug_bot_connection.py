#!/usr/bin/env python3
"""
Discord Bot 连接诊断工具
用于检查Bot连接状态、权限和配置问题
"""

import os
import asyncio
from dotenv import load_dotenv
from discord import Intents, Client
from loguru import logger

# 加载环境变量
load_dotenv()

class DiagnosticBot(Client):
    def __init__(self):
        # 启用所有必要的intents
        intents = Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.dm_messages = True
        super().__init__(intents=intents)
        
        self.diagnostic_complete = False

    async def on_ready(self):
        logger.success(f"🚀 诊断Bot连接成功!")
        logger.info(f"Bot信息: {self.user} (ID: {self.user.id})")
        logger.info(f"延迟: {self.latency * 1000:.2f}ms")
        
        await self.run_diagnostics()
        
    async def run_diagnostics(self):
        """运行完整的诊断"""
        logger.info("🔍 开始运行Bot诊断...")
        
        # 1. 检查服务器连接
        logger.info(f"📊 服务器连接状态:")
        logger.info(f"  - 连接的服务器数量: {len(self.guilds)}")
        
        if not self.guilds:
            logger.warning("⚠️ Bot没有连接到任何服务器!")
            logger.info("请确保Bot已被邀请到包含Midjourney Bot的服务器")
        
        # 2. 检查每个服务器的详细信息
        for guild in self.guilds:
            logger.info(f"  📍 服务器: {guild.name} (ID: {guild.id})")
            logger.info(f"    - 成员数量: {guild.member_count}")
            
            # 检查Bot权限
            me = guild.me
            if me:
                permissions = me.guild_permissions
                logger.info(f"    - Bot权限:")
                logger.info(f"      读取消息: {permissions.read_messages}")
                logger.info(f"      读取消息历史: {permissions.read_message_history}")
                logger.info(f"      发送消息: {permissions.send_messages}")
                logger.info(f"      管理员: {permissions.administrator}")
            
            # 查找Midjourney Bot
            midjourney_bot = None
            for member in guild.members:
                if 'midjourney' in member.name.lower() or member.id == 936929561302675456:
                    midjourney_bot = member
                    logger.info(f"    🎯 找到可能的Midjourney Bot: {member.name} (ID: {member.id})")
                    break
            
            if not midjourney_bot:
                logger.warning(f"    ⚠️ 在服务器 {guild.name} 中未找到Midjourney Bot")
            
            # 检查频道权限
            text_channels = [ch for ch in guild.channels if hasattr(ch, 'send')]
            logger.info(f"    - 文本频道数量: {len(text_channels)}")
            
            accessible_channels = 0
            for channel in text_channels[:5]:  # 只检查前5个频道
                try:
                    perms = channel.permissions_for(me)
                    if perms.read_messages and perms.read_message_history:
                        accessible_channels += 1
                        logger.debug(f"      ✅ 可访问频道: #{channel.name}")
                    else:
                        logger.debug(f"      ❌ 无权访问频道: #{channel.name}")
                except Exception as e:
                    logger.debug(f"      ❓ 检查频道权限失败: #{channel.name} - {e}")
            
            logger.info(f"    - 可访问的频道: {accessible_channels}/{len(text_channels)}")
        
        # 3. 测试消息接收
        logger.info("🔄 测试消息接收功能...")
        logger.info("请在Bot所在的任何频道发送一条测试消息，Bot将记录收到的消息")
        
        # 等待10秒来接收测试消息
        await asyncio.sleep(10)
        
        logger.info("✅ 诊断完成!")
        self.diagnostic_complete = True
        
    async def on_message(self, message):
        # 记录所有收到的消息
        if not message.author.bot and not self.diagnostic_complete:
            logger.info(f"📨 收到测试消息 - 用户: {message.author.name}, 内容: {message.content[:50]}...")
        
        # 记录所有机器人消息以查找Midjourney Bot
        if message.author.bot:
            logger.debug(f"🤖 Bot消息 - {message.author.name}({message.author.id}): {message.content[:100]}...")
            
            # 特别关注可能的Midjourney消息
            if any(keyword in message.content.lower() for keyword in ['imagine', 'upscale', 'variation', 'job', 'waiting']):
                logger.warning(f"🎯 可能的Midjourney消息 - {message.author.name}({message.author.id}): {message.content[:100]}...")

    async def on_connect(self):
        logger.info("🔗 Bot已连接到Discord")

    async def on_disconnect(self):
        logger.warning("🔌 Bot断开连接")

async def main():
    """主函数"""
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        logger.error("❌ 未找到BOT_TOKEN环境变量!")
        logger.info("请在.env文件中设置: BOT_TOKEN=your_bot_token_here")
        return
    
    logger.info("🔧 Discord Bot 连接诊断工具")
    logger.info("=" * 50)
    
    try:
        diagnostic_bot = DiagnosticBot()
        logger.info("🚀 启动诊断Bot...")
        
        # 运行30秒后自动停止
        async def auto_stop():
            await asyncio.sleep(30)
            logger.info("⏰ 诊断时间结束，正在停止Bot...")
            await diagnostic_bot.close()
        
        # 同时运行Bot和自动停止任务
        await asyncio.gather(
            diagnostic_bot.start(bot_token),
            auto_stop()
        )
        
    except Exception as e:
        logger.error(f"❌ Bot启动失败: {e}")
        logger.info("可能的原因:")
        logger.info("1. Bot Token无效或过期")
        logger.info("2. 网络连接问题") 
        logger.info("3. Discord API服务问题")
        logger.info("4. Bot权限配置错误")

if __name__ == "__main__":
    asyncio.run(main()) 