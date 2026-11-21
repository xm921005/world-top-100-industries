#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球最赚钱 100 个行业 —— 自动更新脚本

数据源：Yahoo Finance chart API（公开、免 key）
口径：用覆盖各细分行业的美股行业/主题 ETF 作为“行业代理”，
      以近 1 个月区间收益率(%) 作为“行业赚钱效应”的代理指标并排名。
      同时给出近 3 个月、近 1 年收益率(%) 供参考。
输出：README.md（首页榜单区块） + data/latest.json（机器可读）
"""

import json
import os
import random
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
README_PATH = os.path.join(BASE_DIR, "README.md")
LATEST_JSON = os.path.join(DATA_DIR, "latest.json")

START_MARK = "<!-- RANKING_START -->"
END_MARK = "<!-- RANKING_END -->"

# (代码, 中文行业名, 细分领域)  —— 覆盖约 110 个细分行业，抓取失败会自动剔除，最终取前 100
SECTORS = [
    ("XLK", "信息技术", "科技大盘"), ("VGT", "信息技术", "科技硬件软件"),
    ("FTEC", "信息技术", "科技综合"), ("IYW", "信息技术", "美国科技"),
    ("SOXX", "半导体", "芯片"), ("SMH", "半导体", "芯片设计"),
    ("XSW", "软件服务", "软件"), ("SKYY", "云计算", "云服务"),
    ("IGV", "软件服务", "扩展软件"), ("WCLD", "云计算", "云软件"),
    ("HACK", "网络安全", "信息安全"), ("CQQQ", "中国科技", "中国互联网"),
    ("AIQ", "人工智能", "AI 综合"), ("BOTZ", "机器人与 AI", "机器人"),
    ("IRBO", "机器人与 AI", "智能机器人"), ("FINX", "金融科技", "FinTech"),
    ("ARKK", "创新科技", "颠覆性创新"),
    ("XLF", "金融", "金融大盘"), ("VFH", "金融", "金融综合"),
    ("FFIN", "金融", "金融综合"), ("IYF", "金融", "美国金融"),
    ("KBE", "银行", "银行业"), ("KRE", "区域银行", "区域银行"),
    ("IAI", "券商投行", "证券"), ("KIE", "保险", "保险业"),
    ("XLV", "医疗保健", "医疗大盘"), ("VHT", "医疗保健", "医疗综合"),
    ("FPH", "医疗保健", "医疗综合"), ("IYH", "医疗保健", "美国医疗"),
    ("IBB", "生物科技", "生物制药"), ("XBI", "生物科技", "生物科技"),
    ("PPA", "航空航天与国防", "军工"), ("ITA", "航空航天与国防", "军工"),
    ("XAR", "航空航天与国防", "航空制造"),
    ("XLE", "能源", "能源大盘"), ("VDE", "能源", "能源综合"),
    ("FENY", "能源", "能源综合"), ("IYE", "能源", "美国能源"),
    ("XOP", "油气勘探", "上游油气"), ("OIH", "油服", "油田服务"),
    ("USO", "原油", "原油商品"), ("UNG", "天然气", "天然气商品"),
    ("XLY", "可选消费", "消费大盘"), ("VCR", "可选消费", "消费综合"),
    ("FDIS", "可选消费", "消费综合"), ("IYC", "可选消费", "美国消费"),
    ("XRT", "零售", "零售商"), ("XLP", "必需消费", "消费 staple"),
    ("VDC", "必需消费", "日用消费"), ("FSTA", "必需消费", "食品饮料"),
    ("PBJ", "食品饮料", "食品"),
    ("XLI", "工业", "工业大盘"), ("VIS", "工业", "工业综合"),
    ("FIND", "工业", "工业综合"), ("IYJ", "工业", "美国工业"),
    ("WOOD", "林木", "林业"),
    ("XLB", "原材料", "材料大盘"), ("VAW", "原材料", "材料综合"),
    ("FMAT", "原材料", "材料综合"), ("IYB", "原材料", "美国材料"),
    ("COPX", "铜矿", "铜采选"), ("CPER", "铜", "铜商品"),
    ("XLU", "公用事业", "公用大盘"), ("VPU", "公用事业", "公用综合"),
    ("FUTY", "公用事业", "公用综合"),
    ("XLRE", "房地产", "REIT 大盘"), ("VNQ", "房地产", "REIT 综合"),
    ("FREL", "房地产", "REIT 综合"), ("IYR", "房地产", "美国 REIT"),
    ("XLC", "通信服务", "通信大盘"), ("VCOM", "通信服务", "通信综合"),
    ("FCOM", "通信服务", "通信综合"), ("IYZ", "电信", "电信运营"),
    ("SOCL", "社交媒体", "社交网络"),
    ("LIT", "锂电", "锂电产业链"), ("TAN", "太阳能", "光伏"),
    ("ICLN", "清洁能源", "清洁能源"), ("FAN", "风能", "风电"),
    ("HYDR", "氢能", "氢燃料"), ("URNM", "铀矿", "铀采选"),
    ("URA", "铀", "铀综合"),
    ("GDX", "黄金矿业", "金矿"), ("GDXJ", "小型金矿", "初级金矿"),
    ("SIL", "白银矿业", "银矿"), ("GLD", "黄金", "黄金商品"),
    ("SLV", "白银", "白银商品"),
    ("ESPO", "游戏娱乐", "游戏"), ("CARZ", "汽车", "汽车制造"),
    ("MJ", "大麻", "医用大麻"),
    ("TLT", "长期美债", "20年+ 国债"), ("IEF", "中期美债", "7-10年国债"),
    ("HYG", "高收益债", "垃圾债"), ("LQD", "投资级公司债", "公司债"),
    ("SPY", "标普500", "美股宽基"), ("QQQ", "纳斯达克100", "科技宽基"),
    ("IWM", "罗素2000", "小盘股"), ("DIA", "道琼斯", "蓝筹宽基"),
]

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def fetch_chart(symbol, retries=3):
    """抓 Yahoo chart 一年日线，返回 (timestamps, closes)。"""
    last_err = None
    for attempt in range(retries):
        host = "query1.finance.yahoo.com" if (attempt % 2 == 0) else "query2.finance.yahoo.com"
        url = f"https://{host}/v8/finance/chart/{symbol}?range=1y&interval=1d"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(UA_POOL), "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                payload = json.loads(r.read().decode("utf-8"))
            result = payload["chart"]["result"][0]
            ts = result.get("timestamp", [])
            closes = result["indicators"]["quote"][0].get("close", [])
            if not ts or not closes:
                return None, None
            return ts, closes
        except Exception as e:  # noqa: BLE001 - 网络抓取需容错
            last_err = e
            time.sleep(0.6 * (attempt + 1))
    return None, None


def ret_since(ts, closes, days):
    """自 days 天前到最新的区间收益率(%)。数据不足时退回最早点。"""
    pts = [(t, c) for t, c in zip(ts, closes) if c is not None and c > 0]
    if len(pts) < 2:
        return None
    cutoff = time.time() - days * 86400
    base = pts[0][1]
    for t, c in reversed(pts):
        if t <= cutoff:
            base = c
            break
    last = pts[-1][1]
    if base <= 0:
        return None
    return round((last / base - 1.0) * 100.0, 2)


def compute_one(item):
    code, name, sub = item
    ts, closes = fetch_chart(code)
    if not ts:
        return None
    r1m = ret_since(ts, closes, 30)
    r3m = ret_since(ts, closes, 90)
    r1y = ret_since(ts, closes, 365)
    if r1m is None:
        return None
    return {"code": code, "name": name, "sub": sub, "r1m": r1m, "r3m": r3m, "r1y": r1y}


def build_ranking():
    rows = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(compute_one, s): s for s in SECTORS}
        for fut in as_completed(futures):
            try:
                row = fut.result()
            except Exception:  # noqa: BLE001
                row = None
            if row:
                rows.append(row)
    rows.sort(key=lambda x: x["r1m"], reverse=True)
    return rows[:100], len(rows)


def fmt_pct(v):
    if v is None:
        return "—"
    return f"{v:+.2f}%"


def render_table(rows):
    lines = [
        "| 排名 | 行业(代理ETF) | ETF代码 | 细分领域 | 近1月收益率(%) | 近3月收益率(%) | 近1年收益率(%) |",
        "|---:|---|---|---|---:|---:|---:|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r['name']} | `{r['code']}` | {r['sub']} | "
            f"{fmt_pct(r['r1m'])} | {fmt_pct(r['r3m'])} | {fmt_pct(r['r1y'])} |"
        )
    return "\n".join(lines)


def update_readme(table, updated, total):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    block = (
        f"<!-- 本区块由 update.py 自动生成，请勿手动编辑 -->\n"
        f"> 最近更新（UTC）：{updated} · 有效样本 {total} 个行业 · 排名口径：近 1 月收益率(%) 由高到低\n\n"
        f"{table}"
    )
    if START_MARK in content and END_MARK in content:
        pre = content.split(START_MARK)[0]
        post = content.split(END_MARK)[1]
        content = pre + START_MARK + "\n" + block + "\n" + END_MARK + post
    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    rows, total = build_ranking()
    if not rows:
        raise SystemExit("抓取失败：没有任何有效行业数据，请检查网络/数据源。")
    updated = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    table = render_table(rows)
    update_readme(table, updated, total)

    payload = {
        "updated_utc": updated,
        "criteria": "近1月收益率(%)降序；行业由美股行业/主题ETF代理",
        "unit": "percent",
        "valid_samples": total,
        "top100": rows,
    }
    with open(LATEST_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"OK updated={updated} valid_samples={total} top={rows[0]['name']} {fmt_pct(rows[0]['r1m'])}")


if __name__ == "__main__":
    main()
