from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage, SystemMessage

from models.pan_schemas import PanQueryRequest
from models.json_response import JsonData
from agents.pan_agent import process_pan_query
from core.auth import get_current_user
from core.llm import get_default_llm
from services.pan_qa import answer_question
import logging


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/pan",
    tags=["网盘查询"],
)


async def choose_skill(question: str) -> str:
    message = await get_default_llm().ainvoke(
        [
            SystemMessage(
                content="你只负责分类，只回答一个英文单词。用户明确在问文件名、文件数量、文件大小、文件类型、文件夹、存储空间时，回答 file。其他问题都回答 content，包括人名、年龄、验证码，以及任何可能写在文件正文里的事实。"
            ),
            HumanMessage(content=question),
        ]
    )
    text = message.content
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return "content" if "content" in text.lower() or "内容" in text else "file"


@router.post("/query")
async def pan_query(
    request: PanQueryRequest, current_user: dict = Depends(get_current_user)
):
    request.account_id = current_user["account_id"]
    skill = await choose_skill(request.query)
    logger.info("用户%s 问题=%s 工作流=%s", request.account_id, request.query, skill)
    if skill == "content":
        result = await answer_question(request.account_id, request.query)
        return JsonData.success({"type": "file_content", "data": result})
    return await process_pan_query(request)
