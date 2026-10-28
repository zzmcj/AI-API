"""把图片识别成普通文本。后续切块和摘要只处理这些文字。"""
from __future__ import annotations

import io
import logging
import zipfile
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

_ocr_engine = None

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_V = "{urn:schemas-microsoft-com:vml}"


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR

        _ocr_engine = RapidOCR()
    return _ocr_engine


def format_image_text(lines: list[str]) -> str:
    """识别结果写成带「图中文字」的普通文本块。"""
    body = "\n".join(line.strip() for line in lines if line and line.strip())
    if not body:
        return ""
    return f"【图中文字】\n{body}"


def ocr_image_bytes(data: bytes) -> str:
    """识别一张图片。没有文字或识别失败时返回空字符串。"""
    if not data:
        return ""
    try:
        import cv2
        import numpy as np

        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            return ""
        result, _ = _get_ocr()(image)
    except Exception:
        logger.exception("图片识别失败")
        return ""
    if not result:
        return ""
    lines = [item[1] for item in result if len(item) > 1 and item[1]]
    return format_image_text(lines)


def ocr_pdf_page_images(page) -> str:
    """识别 PDF 某一页里的内嵌图。"""
    try:
        images = list(page.images)
    except Exception:
        logger.exception("提取 PDF 内嵌图失败")
        return ""
    blocks = [ocr_image_bytes(image.data) for image in images]
    return "\n\n".join(block for block in blocks if block)


def parse_docx_bytes(data: bytes) -> str:
    """按文档顺序抽出 Word 正文，遇到图片就插入识别出的文本块。"""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        logger.exception("Word 文件无法打开")
        return ""
    with archive:
        names = set(archive.namelist())
        if "word/document.xml" not in names:
            return ""
        rels = _docx_image_rels(archive, names)
        root = ET.fromstring(archive.read("word/document.xml"))
        parts: list[str] = []
        for paragraph in root.iter(f"{_W}p"):
            line = "".join(node.text or "" for node in paragraph.iter(f"{_W}t")).strip()
            if line:
                parts.append(line)
            for image_id in _paragraph_image_ids(paragraph):
                image_name = rels.get(image_id)
                if not image_name or image_name not in names:
                    continue
                block = ocr_image_bytes(archive.read(image_name))
                if block:
                    parts.append(block)
    return "\n\n".join(parts)


def _docx_image_rels(archive: zipfile.ZipFile, names: set[str]) -> dict[str, str]:
    rels_name = "word/_rels/document.xml.rels"
    if rels_name not in names:
        return {}
    root = ET.fromstring(archive.read(rels_name))
    mapping = {}
    for rel in root.findall(f"{_REL}Relationship"):
        target = rel.attrib.get("Target", "")
        if "media/" not in target:
            continue
        target = target.lstrip("/")
        if not target.startswith("word/"):
            target = f"word/{target}"
        mapping[rel.attrib.get("Id", "")] = target
    return mapping


def _paragraph_image_ids(paragraph: ET.Element) -> list[str]:
    image_ids = []
    for node in paragraph.iter(f"{_A}blip"):
        image_id = node.attrib.get(f"{_R}embed")
        if image_id:
            image_ids.append(image_id)
    for node in paragraph.iter(f"{_V}imagedata"):
        image_id = node.attrib.get(f"{_R}id")
        if image_id:
            image_ids.append(image_id)
    return image_ids
