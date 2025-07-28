"""
NekoBot 猫咪图片插件
功能：通过命令获取不同分类的猫咪图片，支持缓存管理和管理员控制
"""

NAME: str = '猫咪图片插件'  # 插件名
DESCRIBE: str = '提供多种猫咪图片功能 | 指令: 来只猫, 猫图分类, 清理猫图缓存'  # 插件描述
PRIORITY: int = 75  # 较高优先级

import httpx
import hashlib
import os
from typing import Union
from utils.utils import send_pic, set_shared_data, get_shared_data, del_shared_data, get_user_id
from botpy.message import C2CMessage, GroupMessage, DirectMessage, Message
from botpy import logger

# 全局变量
admin: list[str] = []
cache_dir = "cat_cache"
api_url = "https://nekos.best/api/v2/neko"  # 使用NekosBest API[4](@ref)

async def onLoad(_admin: list[str], _logger):
    """
    插件加载初始化
    """
    global admin, logger
    logger = _logger
    admin = _admin
    
    # 初始化缓存目录
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        logger.info(f"创建缓存目录: {cache_dir}")
    
    # 初始化共享数据
    if (await get_shared_data('CAT_ENABLED')) is None:
        await set_shared_data('CAT_ENABLED', True)
        await set_shared_data('CAT_CACHE_SIZE', 0)
    
    logger.info(f"{NAME} 加载完成 | 优先级: {PRIORITY}")

async def onUnload():
    """
    插件卸载清理
    """
    await del_shared_data('CAT_ENABLED')
    await del_shared_data('CAT_CACHE_SIZE')
    logger.info(f"{NAME} 已卸载")

async def handle_cat_command(message: Union[C2CMessage, GroupMessage], seq: int) -> int:
    """
    处理猫咪图片相关命令
    """
    user_id = get_user_id(message)
    content = message.content.strip()
    
    # 管理员命令
    if content == "清理猫图缓存":
        if user_id not in admin:
            await message.reply(content="❌ 需要管理员权限", msg_seq=seq)
            return 0
        return await clear_cache(message, seq)
    
    if content.startswith("猫图分类"):
        return await send_category_options(message, seq)
    
    # 普通用户命令
    if content == "来只猫":
        return await send_random_cat(message, seq)
    
    return seq

async def send_random_cat(message: Union[C2CMessage, GroupMessage], seq: int) -> int:
    """
    发送随机猫咪图片
    """
    if not await get_shared_data('CAT_ENABLED'):
        await message.reply(content="🐾 猫咪插件当前已禁用", msg_seq=seq)
        return 0
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url)
            if response.status_code != 200:
                raise Exception(f"API 错误: {response.status_code}")
            
            data = response.json()
            if not data.get("results"):
                raise Exception("无返回结果")
            
            cat_data = data["results"][0]
            image_url = cat_data["url"]
            artist = cat_data.get("artist_name", "未知艺术家")
            
            # 缓存管理
            cached_path = await cache_image(image_url)
            if cached_path:
                await send_pic(message, path=cached_path, msg_seq=seq)
                await message.reply(
                    content=f"🎨 艺术家: {artist}\n💾 已缓存到本地",
                    msg_seq=seq+1
                )
                return seq + 2
            
            # 无缓存直接发送
            await send_pic(message, url=image_url, msg_seq=seq)
            return seq + 1
            
    except Exception as e:
        logger.error(f"获取猫咪图片失败: {str(e)}")
        await message.reply(content="😿 获取猫咪图片失败，请稍后再试", msg_seq=seq)
        return 0

async def cache_image(url: str) -> str:
    """
    缓存图片到本地
    """
    cache_size = await get_shared_data('CAT_CACHE_SIZE') or 0
    
    # 生成唯一文件名
    file_hash = hashlib.md5(url.encode()).hexdigest()
    file_path = os.path.join(cache_dir, f"{file_hash}.png")
    
    # 已存在则直接返回
    if os.path.exists(file_path):
        return file_path
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                # 更新缓存大小
                await set_shared_data('CAT_CACHE_SIZE', cache_size + 1)
                return file_path
    except Exception as e:
        logger.warning(f"图片缓存失败: {str(e)}")
    
    return ""

async def clear_cache(message: Union[C2CMessage, GroupMessage], seq: int) -> int:
    """
    清理图片缓存
    """
    try:
        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        
        await set_shared_data('CAT_CACHE_SIZE', 0)
        await message.reply(content="✅ 猫图缓存已清理", msg_seq=seq)
        return seq + 1
    except Exception as e:
        logger.error(f"清理缓存失败: {str(e)}")
        await message.reply(content="❌ 缓存清理失败", msg_seq=seq)
        return 0

async def send_category_options(message: Union[C2CMessage, GroupMessage], seq: int) -> int:
    """
    发送猫咪图片分类选项
    """
    categories = ["neko", "kitsune", "waifu"]  # 支持的分类[4](@ref)
    options = "\n".join([f"▪ {cat}" for cat in categories])
    
    await message.reply(
        content=f"🐱 可用猫图分类:\n{options}\n发送「来只猫 [分类]」获取",
        msg_seq=seq
    )
    return seq + 1

# 事件处理函数
async def onGroupAtMessage(message: GroupMessage, seq: int) -> int:
    return await handle_cat_command(message, seq)

async def onC2CMessage(message: C2CMessage, seq: int) -> int:
    return await handle_cat_command(message, seq)

async def onDirectMessage(message: DirectMessage) -> bool:
    # 简单回复频道私信
    if message.content == "来只猫":
        await message.reply(content="请使用群聊或私聊命令")
    return False

async def onAtMessage(message: Message) -> bool:
    # 频道@消息处理
    if "来只猫" in message.content:
        await message.reply(content="🐾 使用 /猫图分类 查看可用选项")
    return False