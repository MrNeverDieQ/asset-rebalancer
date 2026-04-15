"""
资产配置再平衡 - Flask Web 应用
"""
import os
import logging
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

import config as cfg
import data_loader
import rebalancer
import db
import ocr
import tagger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
app.secret_key = "asset-rebalancer-secret"
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")


@app.route("/", methods=["GET", "POST"])
def index():
    """首页：上传 Excel 并展示分析结果"""
    if request.method == "GET":
        return render_template("index.html", result=None)

    # 处理上传
    file = request.files.get("file")
    if not file or not file.filename.endswith((".xlsx", ".xls")):
        flash("请上传 .xlsx 或 .xls 文件", "error")
        return redirect(url_for("index"))

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    try:
        amounts = data_loader.load_portfolio(filepath)
        result = rebalancer.analyze(amounts)
        # 同时存入 DB
        items = data_loader.load_raw_items(filepath)
        db.save_holdings(items)
    except Exception as e:
        flash(f"分析失败: {e}", "error")
        return redirect(url_for("index"))

    return render_template("index.html", result=result)


# ============ OCR 截图流程 ============

@app.route("/ocr", methods=["GET"])
def ocr_page():
    return render_template("ocr.html", items=None, all_tags=cfg.ALL_TAGS, allowed_banks=cfg.ALLOWED_BANKS, now=datetime.now().strftime("%Y-%m-%d"))


@app.route("/ocr/upload", methods=["POST"])
def ocr_upload():
    file = request.files.get("image")
    if not file or not file.filename.lower().endswith(cfg.ALLOWED_IMAGE_EXT):
        flash(f"请上传图片文件（{', '.join(cfg.ALLOWED_IMAGE_EXT)}）", "error")
        return redirect(url_for("ocr_page"))

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    try:
        items = ocr.extract_from_image(filepath)
    except Exception as e:
        flash(f"OCR 识别失败: {e}", "error")
        return redirect(url_for("ocr_page"))

    if not items:
        flash("未从截图中识别到基金信息，请检查图片质量", "error")
        return redirect(url_for("ocr_page"))

    for item in items:
        item["tag"] = tagger.auto_tag(item["name"])

    return render_template("ocr.html", items=items, all_tags=cfg.ALL_TAGS, allowed_banks=cfg.ALLOWED_BANKS, now=datetime.now().strftime("%Y-%m-%d"))


@app.route("/ocr/save", methods=["POST"])
def ocr_save():
    data = request.get_json()
    if not data or not data.get("items"):
        return jsonify({"error": "无数据"}), 400

    items = data["items"]
    record_date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    for item in items:
        if not item.get("name") or not item.get("tag"):
            return jsonify({"error": f"基金名称和类型不能为空: {item}"}), 400
        try:
            float(item["amount"])
        except (ValueError, TypeError):
            return jsonify({"error": f"金额格式错误: {item['name']}"}), 400

    db.save_holdings(items, record_date)

    amounts = db.get_latest_holdings()
    for tag in cfg.ALL_TAGS:
        amounts.setdefault(tag, 0.0)
    result = rebalancer.analyze(amounts)

    return jsonify({"success": True, "saved": len(items), "need_rebalance": result.need_rebalance, "redirect": url_for("ocr_result")})


@app.route("/ocr/result")
def ocr_result():
    amounts = db.get_latest_holdings()
    if not amounts:
        flash("数据库中暂无持仓记录", "error")
        return redirect(url_for("ocr_page"))

    for tag in cfg.ALL_TAGS:
        amounts.setdefault(tag, 0.0)
    result = rebalancer.analyze(amounts)
    return render_template("index.html", result=result)


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=40511)
