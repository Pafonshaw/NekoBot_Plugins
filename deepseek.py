NAME: str = "Deepseek AI"  # 插件名
DESCRIBE: str = "发送 ds帮助 查看帮助"  # 插件描述
PRIORITY: int = 0  # 插件优先级, AI插件, 设置最低优先级


import os
import aiofiles
import json
import httpx
import traceback
from utils.utils import set_shared_data, get_shared_data, del_shared_data, get_user_id
from botpy.message import GroupMessage, C2CMessage
from typing import Union

admin: list[str] = []
logger = None
root: str = "./deepseek/"
deepseek = None
ds_menu = """
ds帮助:
1. ds帮助:
    此菜单
2. Miku[问题]
    Miku预设(实际指令中不含方括号)
3. Neko[问题]
    Neko预设(不含方括号)
4. [问题]
    默认使用Neko预设
5. 清除上下文[Neko|Miku]
    清除预设上下文(不含方括号,预设二选一)"""


class Deepseek:
    url = "https://api.deepseek.com/chat/completions"
    token: str = ""
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    neko: str = (
        r"你是一只名为NachoNeko的猫娘,你喜欢'喵','Nya~'.由于平台限制,你的回复里不能出现url,并且最好不要使用markdown.你的回复里可以用[动作描写]来表示动作,用(心理描写)来表示心情,用<环境描写>来描述场景,用{事件描述}来发生事件.用户是你的主人."
    )
    miku: str = r"你是虚拟歌姬miku"

    def user(self, _content: str):
        return {"role": "user", "content": _content}

    def system(self, _content: str):
        return {"role": "system", "content": _content}

    def assistant(self, _content: str):
        return {"role": "assistant", "content": _content}

    async def ask(self, user_id: str, role: str, content: str):
        payload = {
            "model": "deepseek-reasoner",
            "messages": [],
            "temperature": 1.3,
            "stream": False,
        }
        user_file = f"{root}{role}/{user_id}.json"
        if os.path.exists(user_file):
            async with aiofiles.open(user_file, "r", encoding="utf-8") as f:
                payload["messages"] = json.loads(await f.read())
        elif role == "Neko":
            payload["messages"].append(self.system(self.neko))
        elif role == "Miku":
            payload["messages"].append(self.system(self.miku))
        payload["messages"].append(self.user(content))
        async with httpx.AsyncClient(headers=self.headers, timeout=90) as client:
            resp = await client.post(self.url, json=payload)
            resp.raise_for_status()
        data = resp.json()
        thinking = data["choices"][0]["message"]["reasoning_content"]
        answer = data["choices"][0]["message"]["content"]
        payload["messages"].append(self.assistant(answer))
        async with aiofiles.open(user_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(payload["messages"], indent=4, ensure_ascii=False))
        return f"\nThinking: \n{thinking}\n{'='*7}\nAnswer: \n{answer}"


async def onLoad(_admin: list[str], _logger):
    global admin
    global deepseek
    global logger
    admin = _admin
    deepseek = Deepseek()
    logger = _logger
    if (await get_shared_data("deepseek")) is None:
        await set_shared_data("deepseek", True)
    if not os.path.exists(root):
        os.makedirs(root)
        os.makedirs(f"{root}Neko")
        os.makedirs(f"{root}Miku")


async def onUnload():
    if (await get_shared_data("deepseek")) is not None:
        await del_shared_data("deepseek")
    if os.path.exists(root):
        os.rmdir(root)


async def onMessage(message: Union[C2CMessage, GroupMessage], seq: int = 1):
    if (_open := message.content == "开启ds") or (message.content == "关闭ds"):
        # 开关插件
        if get_user_id(message) not in admin:
            await message.reply(content="权限不足", msg_seq=seq)
            return 0
        await set_shared_data("deepseek", _open)
        await message.reply(
            content="已开启ds" if _open else "已关闭ds", msg_seq=seq
        )
        return 0
    if (await get_shared_data("deepseek")) is False:
        return seq
    if message.content.lower().startswith(("ds帮助", "ds菜单")):
        await message.reply(content=ds_menu)
    elif message.content.lower().startswith("清除上下文"):
        role = message.content[5:].title()
        if role not in ["Neko", "Miku"]:
            await message.reply(content="\n请选择正确的要清除上下文的预设(Neko或Miku)")
            return 0
        user_id = get_user_id(message)
        user_file = f"{root}{role}/{user_id}.json"
        if os.path.exists(user_file):
            os.remove(user_file)
            await message.reply(content=f"已清除{role}预设上下文")
        else:
            await message.reply(content=f"{role}预设上下文不存在")
    else:
        role = "Neko"
        content = message.content[4:].strip()
        if message.content.lower().startswith("miku"):
            role = "Miku"
        elif message.content.lower().startswith("neko"):
            pass
        else:
            content = message.content
        if not content:
            await message.reply(content="请输入问题")
            return 0
        user_id = get_user_id(message)
        try:
            answer = await deepseek.ask(user_id, role, content)
        except Exception as e:
            logger.error(f"ds-miku出错: {repr(e)}, 调用堆栈: {traceback.format_exc()}")
            await message.reply(content="请求失败")
            return 0
        answer = answer.replace('.', '·') # bot禁止发送url
        await message.reply(content=answer)
        return 0


# 群聊艾特事件
onGroupAtMessage = onMessage
# 私聊事件
onC2CMessage = onMessage



