"""
OCR 模块 - 使用 PaddleOCR 从截图中提取基金名称和金额
"""
import re
import logging
from typing import List, Dict

from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

# 全局实例，避免重复加载模型
_ocr = None


def _get_ocr() -> PaddleOCR:
    """懒加载 PaddleOCR 实例"""
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    return _ocr


def _extract_amount(text: str) -> float:
    """
    从文本中提取金额数字。
    支持格式：1,234.56 / 1234.56 / ¥1,234.56 等
    """
    text = text.replace(",", "").replace("，", "").replace("¥", "").replace("￥", "").strip()
    m = re.search(r"(\d+\.?\d*)", text)
    return float(m.group(1)) if m else -1


def _is_amount(text: str) -> bool:
    """判断文本是否像金额"""
    cleaned = text.replace(",", "").replace("，", "").replace("¥", "").replace("￥", "").strip()
    return bool(re.match(r"^\d+\.?\d*$", cleaned))


def _is_fund_name(text: str) -> bool:
    """判断文本是否像基金名称（含中文且不是纯数字）"""
    if _is_amount(text):
        return False
    # 包含中文字符，且长度 >= 2
    return bool(re.search(r"[\u4e00-\u9fff]", text)) and len(text.strip()) >= 2


def extract_from_image(image_path: str) -> List[Dict[str, str]]:
    """
    从截图中提取基金名称和金额。

    Args:
        image_path: 图片文件路径

    Returns:
        [{"name": "沪深300ETF", "amount": "35000.00"}, ...]
    """
    ocr = _get_ocr()
    result = ocr.ocr(image_path, cls=True)

    if not result or not result[0]:
        logger.warning("OCR 未识别到任何文字")
        return []

    # 提取所有文本行及其位置（用 y 坐标中心点排序分组）
    lines = []
    for line in result[0]:
        box, (text, conf) = line[0], line[1]
        # box 的 y 中心点
        y_center = (box[0][1] + box[2][1]) / 2
        x_center = (box[0][0] + box[2][0]) / 2
        lines.append({"text": text.strip(), "y": y_center, "x": x_center, "conf": conf})

    logger.info(f"OCR 识别到 {len(lines)} 个文本块")
    for l in lines:
        logger.debug(f"  [{l['x']:.0f},{l['y']:.0f}] {l['text']}")

    # 按 y 坐标分行（y 差距 < 20px 视为同一行）
    lines.sort(key=lambda l: l["y"])
    rows = []
    current_row = [lines[0]]
    for l in lines[1:]:
        if abs(l["y"] - current_row[0]["y"]) < 20:
            current_row.append(l)
        else:
            rows.append(sorted(current_row, key=lambda x: x["x"]))
            current_row = [l]
    rows.append(sorted(current_row, key=lambda x: x["x"]))

    # 从每行中提取 name + amount 配对
    items = []
    for row in rows:
        texts = [t["text"] for t in row]
        names = [t for t in texts if _is_fund_name(t)]
        amounts = [t for t in texts if _is_amount(t)]

        if names and amounts:
            items.append({
                "name": names[0],
                "amount": str(_extract_amount(amounts[0])),
            })

    # 如果同行配对效果不好，尝试相邻行配对：名称行 + 下一行金额
    if not items:
        logger.info("同行配对失败，尝试相邻行配对")
        for i, row in enumerate(rows):
            texts = [t["text"] for t in row]
            name_candidates = [t for t in texts if _is_fund_name(t)]
            if name_candidates and i + 1 < len(rows):
                next_texts = [t["text"] for t in rows[i + 1]]
                amt_candidates = [t for t in next_texts if _is_amount(t)]
                if amt_candidates:
                    items.append({
                        "name": name_candidates[0],
                        "amount": str(_extract_amount(amt_candidates[0])),
                    })

    logger.info(f"提取到 {len(items)} 条基金记录")
    return items
