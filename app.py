"""
资产配置再平衡 - Flask Web 应用
"""
import os
import logging

from flask import Flask, render_template, request, redirect, url_for, flash

import config as cfg
import data_loader
import rebalancer
import db

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


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=40511)
