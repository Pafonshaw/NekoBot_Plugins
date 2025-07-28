

NAME = '哔站查询'
DESCRIBE = 'BV号查询视频信息'

import time
import httpx
from utils.utils import send_pic
from botpy.message import GroupMessage, C2CMessage
from typing import Union

async def video_info(message: Union[GroupMessage, C2CMessage], bv: str, seq):
    info_api = f'https://api.bilibili.com/x/web-interface/wbi/view?bvid={bv}'
    online_api = f'https://api.bilibili.com/x/player/online/total'
    headers = {
        "Host": "api.bilibili.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "identity",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
    }
    try:
        async with httpx.AsyncClient() as client:
            _datas = await client.get(info_api, headers=headers)
        datas = _datas.json()
    except Exception as e:
        return await message.reply(content=f'获取视频信息失败: {repr(e)}', msg_seq=seq)
    if datas['code'] != 0:
        return await message.reply(content=f'获取视频信息失败: {datas["message"]}', msg_seq=seq)
    data = datas['data']    # 拿到视频信息

    try:
        async with httpx.AsyncClient() as client:
            _datas = await client.get(online_api+f'?bvid={bv}&cid={data["pages"][0]["cid"]}', headers=headers)
        datas = _datas.json()
        if datas['code'] == 0:
            datas = datas['data']["total"]  # 拿到观看人数
        else:
            datas = '获取失败'
    except Exception:
        datas = '获取失败'

    try:
        await send_pic(message, url=data['pic'], msg_seq=seq)
    except Exception:
        pass
    
    return await message.reply(content=f'''
> 标题: {data["title"]}
> 发布: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data["pubdate"]))}
> 时长: {data["duration"]}秒
> 简介: {data["desc"]}
> 上传者: {data["owner"]["name"]}
> 投稿: {'原创' if data["copyright"] == 1 else '转载'}
> UID: {data["owner"]["mid"]}
> AV: {data["aid"]}
> BV: {data["bvid"]}
> 分区: {data["tname"]}
> 子分区: {data["tname_v2"]}
> 分P数: {data["videos"]}
> 播放: {data["stat"]["view"]}
> 点赞: {data["stat"]["like"]}
> 投币: {data["stat"]["coin"]}
> 收藏: {data["stat"]["favorite"]}
> 评论: {data["stat"]["reply"]}
> 弹幕: {data["stat"]["danmaku"]}
> 分享: {data["stat"]["share"]}
> 在线观看: {datas}'''.replace('.', '·'), msg_seq=seq+1)

async def onMessage(message: Union[GroupMessage, C2CMessage], seq: int = 1):
    if message.content.startswith('BV') and len(message.content) == 12:
        await video_info(message, message.content, seq)
        return 0
    return seq

onC2CMessage = onMessage
onGroupAtMessage = onMessage


