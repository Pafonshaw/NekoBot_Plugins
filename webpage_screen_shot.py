

NAME: str = "网页截图"  # 插件名
DESCRIBE: str = "发送链接给bot, 返回网页截图"  # 插件描述
PRIORITY: int = 1  # 插件优先级

import asyncio
from selenium import webdriver
import traceback
from selenium.webdriver.edge.service import Service
from utils.utils import get_shared_data, set_shared_data, del_shared_data, send_pic, get_user_id
from botpy.message import GroupMessage, C2CMessage
from typing import Union

admin: list[str] = []
logger = None

async def onLoad(_admin: list[str], _logger):
    global admin
    global logger
    admin = _admin
    logger = _logger
    if (await get_shared_data("webpage_screen_shot")) is None:
        await set_shared_data("webpage_screen_shot", True)

async def onUnload():
    if (await get_shared_data("webpage_screen_shot")) is not None:
        await del_shared_data("webpage_screen_shot")


async def get_webpage_screenshot(url: str):
    # 配置Edge浏览器选项
    options = webdriver.EdgeOptions()
    options.add_argument('headless')    # 无头模式
    options.add_argument('incognito')   # 无痕模式
    # 设置UA
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')

    # 初始化WebDriver
    service = Service(executable_path=r'D:\python\Scripts\msedgedriver.exe')
    driver = webdriver.Edge(service=service, options=options)
    try:
        loop = asyncio.get_event_loop()
        # 打开网页
        await loop.run_in_executor(None, lambda: driver.get(url))
        width = await loop.run_in_executor(None, driver.execute_script, "return document.documentElement.scrollWidth")
        height = await loop.run_in_executor(None, driver.execute_script, "return document.documentElement.scrollHeight")
        await loop.run_in_executor(None, driver.set_window_size, width, height)  # 修改浏览器窗口大小
        # 等待页面加载完成
        await asyncio.sleep(5)
        # 获取截图
        screenshot = await loop.run_in_executor(None, driver.get_screenshot_as_png)
        return screenshot
    finally:
        # 关闭浏览器
        await loop.run_in_executor(None, driver.quit)

async def onMessage(message: Union[C2CMessage, GroupMessage], seq: int = 1):
    if (_open := message.content == "开启网页截图") or (message.content == "关闭网页截图"):
        # 开关插件
        if get_user_id(message) not in admin:
            await message.reply(content="权限不足", msg_seq=seq)
            return 0
        await set_shared_data("webpage_screen_shot", _open)
        await message.reply(
            content="已开启网页截图" if _open else "已关闭网页截图", msg_seq=seq
        )
        return 0
    if (await get_shared_data("webpage_screen_shot")) is False:
        return seq
    if message.content.startswith("http"):
        try:
            screenshot = await get_webpage_screenshot(message.content)
            if screenshot:
                await send_pic(message, data=screenshot, msg_seq=seq)
        except Exception as e:
            logger.error(f"截图失败: {repr(e)}, 调用堆栈: {traceback.format_exc()}")
            await message.reply(content="截图失败", msg_seq=seq)
        return 0
    return seq

# 群聊艾特事件
onGroupAtMessage = onMessage
# 私聊事件
onC2CMessage = onMessage


