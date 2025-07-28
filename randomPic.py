
NAME = '随机图插件'
DESCRIBE = '发送 随机图帮助 查看菜单'
PRIORITY = 70

# import random
from botpy.message import GroupMessage, C2CMessage
from typing import Union
from utils.utils import get_shared_data, set_shared_data, del_shared_data ,send_pic, get_user_id

admin = []

async def onLoad(_admin: list, _):
    global admin
    admin = _admin
    if (await get_shared_data('randomPic_open')) is None:
        await set_shared_data('randomPic_open', True)

async def onUnload():
    if (await get_shared_data('randomPic_open')) is not None:
        await del_shared_data('randomPic_open')

async def onMessage(message: Union[GroupMessage, C2CMessage], seq: int = 1):
    if (_open:=message.content.startswith('开启随机图')) or message.content.startswith('关闭随机图'):
        if get_user_id(message) not in admin:
            await message.reply(content='权限不足', msg_seq=seq)
            return 0
        await set_shared_data('randomPic_open', _open)
        await message.reply(content='已开启随机图' if _open else '已关闭随机图', msg_seq=seq)
        return 0
    if (await get_shared_data('randomPic_open')) is False:
        return seq
    if message.content.startswith(('随机图帮助', '随机图菜单', '随机图')):
        await message.reply(content='\n随机图帮助:' \
                            '\n· 随机图帮助:' \
                            '\n    查看此菜单' \
                            '\n· 随机图指令:' \
                            '\n    甘城' \
                            '\n    东方' \
                            # '\n    动漫壁纸' \
                            # '\n    动漫头像' \
                            '\n· 主人指令:' \
                            '\n    开启随机图' \
                            '\n    关闭随机图', msg_seq=seq)
    elif message.content.startswith('甘城'):
        await send_pic(message, url='https://api.317ak.com/API/tp/gcmm.php', msg_seq=seq)
    elif message.content.startswith('东方'):
        await send_pic(message, url='https://img.paulzzh.com/touhou/random', msg_seq=seq)
    # elif message.content.startswith('动漫壁纸'):
    #     await send_pic(message, url=f'https://api.lucksss.com/api/dmbz?type={random.choice(["pc", "pe"])}')
    # elif message.content.startswith('动漫头像'):
    #     await send_pic(message, url='https://api.lucksss.com/api/dmbz?type=avatar')
    else:
        return seq
    return 0

onGroupAtMessage = onMessage
onC2CMessage = onMessage

