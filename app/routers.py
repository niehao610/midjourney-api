from fastapi import APIRouter, UploadFile, Depends
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
import uuid
from lib.api import discord
from lib.api.discord import TriggerType
from lib.db_operations import db_ops
from lib.auth import get_current_user, check_user_token_limit, consume_user_token_by_app_key
from util._queue import taskqueue
from .handler import prompt_handler, unique_id
from .schema import (
    TriggerExpandIn,
    TriggerImagineIn,
    TriggerUVIn,
    TriggerResetIn,
    QueueReleaseIn,
    TriggerResponse,
    TriggerZoomOutIn,
    UploadResponse,
    TriggerDescribeIn,
    SendMessageResponse,
    SendMessageIn,
    MidjourneyResultIn,
    SimpleResponse,
)

router = APIRouter()


@router.post("/imagine", response_model=TriggerResponse)
async def imagine(
    body: TriggerImagineIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    # 记录API请求日志
    logger.info(f"🎨 /imagine请求 - 用户: {current_user.get('user_name')}, Prompt长度: {len(body.prompt)}, PicURL: {'有' if body.picurl else '无'}")
    
    trigger_id, prompt = prompt_handler(body.prompt, body.picurl)
    trigger_type = TriggerType.generate.value

    
    # 创建数据库任务记录
    try:
        task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name="imagine by prompt",
            task_id=task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url=body.picurl,
            image_index=0,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.generate, prompt)
    logger.info(f"任务创建成功: {trigger_id}")
    
    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))
    
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": task_id}


@router.post("/upscale", response_model=TriggerResponse)
async def upscale(
    body: TriggerUVIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    
    trigger_type = TriggerType.upscale.value

    try:
        old_task_id =  body.trigger_id

        old_task = await db_ops.get_task_by_task_id(old_task_id)

        if not old_task:
            return {"message": "任务不存在"}

        trigger_id = old_task.get("trigger_id")
        sub_task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name="upscale image by index" + str(body.index),
            task_id=sub_task_id,
            trigger_id= trigger_id,
            task_type=trigger_type,
            ref_pic_url='',
            image_index=body.index,
            msg_id=body.msg_id,
            msg_hash=body.msg_hash,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")


    taskqueue.put(trigger_id, discord.upscale, **body.dict())
    
    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))
    
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": sub_task_id}


@router.post("/variation", response_model=TriggerResponse)
async def variation(
    body: TriggerUVIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    trigger_type = TriggerType.variation.value

    # 创建数据库任务记录
    try:
        old_task_id =  body.trigger_id

        old_task = await db_ops.get_task_by_task_id(old_task_id)

        if not old_task:
            return {"message": "任务不存在"}

        trigger_id = old_task.get("trigger_id")
        sub_task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name="variation image by index" + str(body.index),
            task_id=sub_task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url='',
            image_index=body.index,
            msg_id=body.msg_id,
            msg_hash=body.msg_hash,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.variation, **body.dict())
    
    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))
    
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": sub_task_id}


@router.post("/reset", response_model=TriggerResponse)
async def reset(
    body: TriggerResetIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.reset.value

    # 创建数据库任务记录
    try:
        task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name="reset image",
            task_id=task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url='',
            image_index=0,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.reset, **body.dict())
    
    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))
    
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": task_id}


@router.post("/describe", response_model=TriggerResponse)
async def describe(
    body: TriggerDescribeIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.describe.value

    # 创建数据库任务记录
    try:
        task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name="describe image",
            task_id=task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url=body.upload_filename,
            image_index=0,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.describe, **body.dict())
    
    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))
    
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": task_id}


@router.post("/upload", response_model=UploadResponse)
async def upload_attachment(
    file: UploadFile,
    current_user: dict = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        return {"message": "must image"}

    trigger_id = str(unique_id())
    filename = f"{trigger_id}.jpg"
    file_size = file.size
    attachment = await discord.upload_attachment(filename, file_size, await file.read())
    if not (attachment and attachment.get("upload_url")):
        return {"message": "Failed to upload image"}

    return {
        "upload_filename": attachment.get("upload_filename"),
        "upload_url": attachment.get("upload_url"),
        "trigger_id": trigger_id,
    }


@router.post("/message", response_model=SendMessageResponse)
async def send_message(
    body: SendMessageIn,
    current_user: dict = Depends(get_current_user)
):
    picurl = await discord.send_attachment_message(body.upload_filename)
    if not picurl:
        return {"message": "Failed to send message"}

    return {"picurl": picurl}


@router.post("/midjourney/result", response_model=SimpleResponse)
async def midjourney_result(body: MidjourneyResultIn):
    """接收Midjourney结果数据并打印JSON内容	{
	    "type": "end",
	    "id": 1384952701758083308,
	    "content": "**<#3935532608#>Editorial fashion photography, a chic woman in a stylish cobalt blue trench coat is walking confidently towards the camera on a sunlit city street. In the background is the gleaming facade of a luxury jewelry boutique. Floating majestically in the sky above her is a colossal, translucent whale made of shimmering crystal and liquid light, sparkling brilliantly. The atmosphere is bright, ethereal, and dreamlike. Shot on a Canon EOS R5 with a 50mm f/1.2 lens, shallow depth of field, hyper-realistic, 8K, UHD. --ar 9:16 --v 7.0** - <@839907989619212348> (fast)\n-# Create, explore, and organize on [midjourney.com](<https://midjourney.com/imagine?from_discord=1>)",
	    "attachments": [
	        {
	            "filename": "forrynie.1981_3935532608Editorial_fashion_photography_a_chic_wo_d0966d3a-a86f-414d-8a67-be65951ef751.png",
	            "id": 1384952701284122765,
	            "proxy_url": "https://media.discordapp.net/attachments/1384158875657175166/1384952701284122765/forrynie.1981_3935532608Editorial_fashion_photography_a_chic_wo_d0966d3a-a86f-414d-8a67-be65951ef751.png?ex=68544d37&is=6852fbb7&hm=82195efc9fa6afc747673bc813d5b36f12f8c926fe94dd594e29a028c2077802&",
	            "size": 7556893,
	            "url": "https://cdn.discordapp.com/attachments/1384158875657175166/1384952701284122765/forrynie.1981_3935532608Editorial_fashion_photography_a_chic_wo_d0966d3a-a86f-414d-8a67-be65951ef751.png?ex=68544d37&is=6852fbb7&hm=82195efc9fa6afc747673bc813d5b36f12f8c926fe94dd594e29a028c2077802&",
	            "spoiler": false,
	            "height": 2912,
	            "width": 1632,
	            "content_type": "image/png"
	        }
	    ],
	    "embeds": [],
	    "trigger_id": "3935532608"
	}
   """
    
    logger.info(f"收到Midjourney结果数据: {body.json()}")
    print(f"Midjourney Result JSON: {body.json()}")
    
    # 更新数据库任务状态和结果
    try:
        if body.trigger_id:

            # 确定任务状态
            if body.type == "end":
                            # 提取结果URL
                result_url = None
                msg_hash = ''
                if body.attachments and len(body.attachments) > 0:
                    result_url = body.attachments[0].get("url")
                    msg_hash = body.attachments[0].get("filename").split("_")[-1].split(".")[0]

                task = await db_ops.get_task_by_trigger_id_status(body.trigger_id, "SUBMITTED")
                if not task:
                    logger.error(f"任务不存在: {body.trigger_id}")
                    return {"message": "任务不存在"}
                
                task_id = task.get("task_id")
                
                # 更新任务结果
                await db_ops.update_task_result(
                    task_id=task_id,
                    task_status="SUCCESS",
                    result_url=result_url,
                    attachments=body.attachments,
                    msg_id=body.id, 
                    msg_hash=msg_hash  # 如果有消息hash，可以从其他地方获取
                )
                logger.info(f"任务结果更新成功: {task_id} , trigger_id: {body.trigger_id}")
    except Exception as e:
        logger.error(f"更新任务结果失败: {e}")
    
    return {"message": "success"}


@router.post("/queue/release", response_model=TriggerResponse)
async def queue_release(
    body: QueueReleaseIn,
    current_user: dict = Depends(get_current_user)
):
    """bot 清除队列任务"""
    taskqueue.pop(body.trigger_id)

    return body


@router.post("/solo_variation", response_model=TriggerResponse)
async def solo_variation(
    body: TriggerUVIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.solo_variation.value

    # 创建数据库任务记录
    try:
        task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name="solo variation image",
            task_id=task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url='',
            image_index=0,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.solo_variation, **body.dict())

    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": task_id}

@router.post("/solo_low_variation", response_model=TriggerResponse)
async def solo_low_variation(
    body: TriggerUVIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.solo_low_variation.value

    # 创建数据库任务记录
    try:
        task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name="solo low variation image",
            task_id=task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url='',
            image_index=0,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.solo_low_variation, **body.dict())

    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": task_id}

@router.post("/solo_high_variation", response_model=TriggerResponse)
async def solo_high_variation(
    body: TriggerUVIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.solo_high_variation.value

    # 创建数据库任务记录
    try:
        task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name="solo high variation image",
            task_id=task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url='',
            image_index=0,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.solo_high_variation, **body.dict())

    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": task_id}

@router.post("/expand", response_model=TriggerResponse)
async def expand(
    body: TriggerExpandIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.expand.value

    # 创建数据库任务记录
    try:
        task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name=f"expand image {body.direction}",
            task_id=task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url='',
            image_index=0,
            direction=body.direction,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.expand, **body.dict())

    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": task_id}


@router.post("/zoomout", response_model=TriggerResponse)
async def zoomout(
    body: TriggerZoomOutIn,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(check_user_token_limit)
):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.zoomout.value

    # 创建数据库任务记录
    try:
        task_id = str(uuid.uuid4())
        await db_ops.create_task(
            task_name=f"zoom out image {body.zoomout}x",
            task_id=task_id,
            trigger_id=trigger_id,
            task_type=trigger_type,
            ref_pic_url='',
            image_index=0,
            zoom_out=body.zoomout,
            task_status="SUBMITTED"
        )
    except Exception as e:
        logger.error(f"创建任务记录失败: {e}")

    taskqueue.put(trigger_id, discord.zoomout, **body.dict())

    # 消费用户token
    await consume_user_token_by_app_key(current_user.get('app_key'))

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "result": task_id}


@router.get("/task/{task_id}")
async def get_task_by_id(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """根据task_id查询任务详情"""
    try:
        task = await db_ops.get_task_by_task_id(task_id)
        if task:
            if task["task_status"] == "SUCCESS":
                return {"status": "SUCCESS", "imageUrl": task["result_url"], "buttons": {"msg_id": task["msg_id"], "msg_hash": task["msg_hash"]}}
            else:
                return {"status":task["task_status"], "message": "任务未完成"}
        else:
            return {"status": "FAILURE", "message": "任务不存在"}
    except Exception as e:
        logger.error(f"查询任务失败: {e}")
        return {"status": "FAILURE"}


@router.get("/tasks")
async def get_tasks(
    status: str = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """查询任务列表"""
    try:
        if status:
            tasks = await db_ops.get_tasks_by_status(status, limit)
        else:
            tasks = await db_ops.get_all_tasks(limit, offset)
        
        return {"success": True, "data": tasks, "total": len(tasks)}
    except Exception as e:
        logger.error(f"查询任务列表失败: {e}")
        return {"success": False, "message": "查询失败"}

