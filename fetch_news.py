# -*- coding: utf-8 -*-
"""
fetch_news_html.py — 全球宏观财经与新闻全景看板 (纯 HTML 版)
针对网上的 fetch_news.py 简化重构：
  1. 仅导出 HTML 文件，去除 Markdown 导出逻辑。
  2. 参考本地配置，修复了 Yahoo / 36氪 / 华尔街见闻 / 经济观察报 等失效/404 RSS 源。
  3. 保留时效性解析 (🔥/⭐/💤/⏰) 与历史数据去重机制。
"""

import os
import re
import glob
import time
import logging
from datetime import datetime, timedelta, timezone
import requests
import feedparser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ===================== 参数配置 =====================
DEDUP_LOOKBACK_DAYS = 7        # 历史去重窗口（天）
MAX_HEADLINES_PER_SOURCE = 10  # 单源提取上限
MIN_HEADLINE_LENGTH = 6        # 最小标题字符长度
MAX_NEWS_AGE_HOURS = 72        # 最大有效新闻时限（小时）

# ===================== 新闻源配置（参考本地优化版） =====================
CUSTOM_NEWS_SOURCES = [
    # ---------- 美股 / 全球金融 ----------
    ("CNBC (消费品与商业频道-头条)", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch (市场观察-热点头条)", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Google News 美股专题", "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en&topic=K"),
    ("Nasdaq (纳斯达克市场资讯)", "https://www.nasdaq.com/feed/rssoutbound"),
    ("Financial Times (金融时报-全球经济)", "https://www.ft.com/global-economy?format=rss"),
    ("Investing.com (全球投资网-快讯)", "https://www.investing.com/rss/news_25.rss"),
    ("Seeking Alpha (寻找阿尔法-个股)", "https://seekingalpha.com/feed.xml"),

    # ---------- 科技创投 ----------
    ("TechCrunch (科技创投)", "https://techcrunch.com/feed/"),
    ("36氪 (科技创投-中文)", "https://news.google.com/rss/search?q=site:36kr.com&hl=zh-CN&gl=CN&ceid=CN:zh"),
    ("虎嗅网 (商业科技-中文)", "https://news.google.com/rss/search?q=site:huxiu.com&hl=zh-CN&gl=CN&ceid=CN:zh"),

    # ---------- 中国官方 / 国内财经 ----------
    ("人民网-人民日报精选", "https://plink.anyfeeder.com/people"),
    ("新华网-要闻", "https://plink.anyfeeder.com/newscn/whxw"),
    ("界面新闻-财经频道", "https://plink.anyfeeder.com/jiemian/finance"),
    ("华尔街见闻-中文财经", "https://news.google.com/rss/search?q=site:wallstreetcn.com&hl=zh-CN&gl=CN&ceid=CN:zh"),
    ("A股/股票/基金 中文热点", "https://news.google.com/rss/search?q=A股%20OR%20股票%20OR%20基金&hl=zh-CN&gl=CN&ceid=CN:zh"),

    # ---------- 国际要闻 ----------
    ("Google News 中文财经总榜", "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-CN"),
    ("卫报 (英国)-全球头条", "https://www.theguardian.com/world/rss"),
    ("朝日新闻 (日本)-国际要闻", "http://www.asahi.com/rss/asahi/newsheadlines.rdf"),
    ("半岛电视台-国际新闻", "https://plink.anyfeeder.com/aljazeera/news"),
    ("悉尼先驱晨报 (澳洲)", "https://www.smh.com.au/rss/feed.xml"),
    ("印度时报 (印度)", "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"),
    ("俄罗斯卫星通讯社", "https://sputniknews.cn/export/rss2/archive/index.xml"),
]

# ===================== 时效计算 =====================
def get_entry_age(entry):
    for key in ("published_parsed", "updated_parsed", "published", "updated"):
        val = entry.get(key)
        if not val:
            continue
        try:
            if isinstance(val, tuple):
                pub_time = datetime(*val[:6], tzinfo=timezone.utc)
            else:
                pub_time = datetime.strptime(val[:25], "%a, %d %b %Y %H:%M:%S %z").astimezone(timezone.utc)
            now = datetime.now(timezone.utc)
            age_hours = (now - pub_time).total_seconds() / 3600
            time_str = pub_time.astimezone(timezone(timedelta(hours=8))).strftime("%m-%d %H:%M")
            return age_hours, time_str
        except Exception:
            continue
    return None, None

def format_freshness_tag(age_hours):
    if age_hours is None:
        return ("#888888", "未知")
    if age_hours <= 6:
        return ("#e74c3c", "🔥 6h内")
    elif age_hours <= 24:
        return ("#f39c12", "⭐ 24h内")
    elif age_hours <= 48:
        return ("#27ae60", "💤 48h内")
    elif age_hours <= MAX_NEWS_AGE_HOURS:
        return ("#2980b9", "⏰ 72h内")
    else:
        return ("#888888", "🗑️ >72h")

def compute_source_freshness(headlines_with_age):
    if not headlines_with_age:
        return "N/A"
    ages = [h['age'] for h in headlines_with_age if h['age'] is not None]
    if not ages:
        return "未知"
    avg_age = sum(ages) / len(ages)
    if avg_age <= 6:
        return "🔥 火热"
    elif avg_age <= 24:
        return "⭐ 新鲜"
    elif avg_age <= 48:
        return "💤 稍旧"
    else:
        return f"⏰ {avg_age:.0f}h前"

# ===================== 历史去重库 =====================
def load_history(output_dir, lookback_days=DEDUP_LOOKBACK_DAYS):
    history = {}
    cutoff = datetime.now() - timedelta(days=lookback_days)
    pattern = os.path.join(output_dir, "????-??-??_????.html")
    files = sorted(glob.glob(pattern))
    for fpath in files:
        fname = os.path.basename(fpath)
        date_str = fname[:10]
        try:
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        if file_date < cutoff:
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        current_source = None
        for line in content.split("\n"):
            if '<h3>' in line:
                current_source = re.sub(r'<[^>]+>', '', line).strip()
                if current_source not in history:
                    history[current_source] = set()
            elif '<li>' in line and current_source:
                title_clean = re.sub(r'<[^>]+>', '', line).strip()
                title_clean = re.sub(r'^\d+\.\s*', '', title_clean)
                if title_clean:
                    history[current_source].add(title_clean)
    return history

# ===================== 抓取与解析 =====================
def fetch_rss_headlines(name, url, history_set=None):
    logger.info(f"扫描新闻源 [{name}] -> {url[:60]}")
    all_entries = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return [], 0, 0, "失败"
        feed = feedparser.parse(response.content)
        if not feed.entries:
            return [], 0, 0, "空"
        seen_in_this_run = set()
        for entry in feed.entries:
            text = entry.get("title", "").strip()
            if " - " in text and len(text) > 60:
                text = text.rsplit(" - ", 1)[0]
            if text and len(text) >= MIN_HEADLINE_LENGTH and text not in seen_in_this_run:
                seen_in_this_run.add(text)
                age_hours, time_str = get_entry_age(entry)
                all_entries.append({'title': text, 'age': age_hours, 'time': time_str})
    except Exception as e:
        logger.error(f"[{name}] 异常: {e}")
        return [], 0, 0, "异常"

    if history_set is not None:
        new_entries = []
        dup_count = 0
        for h in all_entries:
            if h['title'] in history_set:
                dup_count += 1
            else:
                new_entries.append(h)
                history_set.add(h['title'])
    else:
        new_entries = all_entries
        dup_count = 0

    freshness = compute_source_freshness(new_entries)
    stale_count = sum(1 for h in new_entries if h['age'] is not None and h['age'] > MAX_NEWS_AGE_HOURS)
    new_entries = new_entries[:MAX_HEADLINES_PER_SOURCE]
    return new_entries, dup_count, stale_count, freshness

# ===================== 主程序 =====================
def main():
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    month_folder_name = now_beijing.strftime("%Y%m") + "每日财经看板"
    
    # 输出目录路径
    base_download_dir = "/storage/emulated/0/Download"
    if not os.path.exists(base_download_dir):
        base_download_dir = os.path.join(os.getcwd(), "Download")
    output_dir = os.path.join(base_download_dir, "财经新闻", month_folder_name)
    os.makedirs(output_dir, exist_ok=True)

    history = load_history(output_dir)

    html_sections = []
    total_new = 0
    total_dup = 0
    source_with_updates = 0
    source_no_updates = 0

    for name, url in CUSTOM_NEWS_SOURCES:
        history_set = history.get(name, set())
        entries, dup_count, stale_count, freshness = fetch_rss_headlines(name, url, history_set)
        total_dup += dup_count

        section_html = f'<div class="source-card"><h3>{name} <span class="freshness-badge">{freshness}</span></h3><ul>'
        if entries:
            for idx, h in enumerate(entries, 1):
                color, tagtext = format_freshness_tag(h['age'])
                time_tag = f" ({h['time']})" if h['time'] else ""
                section_html += (
                    f'<li>{idx}. {h["title"]}{time_tag}'
                    f'<span style="color:{color};margin-left:8px;font-size:0.9em">{tagtext}</span></li>'
                )
            total_new += len(entries)
            source_with_updates += 1
        else:
            if dup_count > 0:
                section_html += '<li class="no-news">🔄 今日无新更新（已过滤重复内容）</li>'
            else:
                section_html += '<li class="no-news">⏳ 该时段未抓取到有效数据</li>'
            source_no_updates += 1
            
        section_html += "</ul></div>"
        html_sections.append(section_html)
        time.sleep(0.3)

    time_string = now_beijing.strftime("%Y-%m-%d %H:%M:%S")
    date_string = now_beijing.strftime("%Y-%m-%d")

    # 构建纯 HTML 看板
    full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>全球宏观财经全景看板</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft YaHei",sans-serif;}}
        body{{background:#f4f7fa;color:#222;padding:20px;max-width:1200px;margin:0 auto;}}
        h1{{text-align:center;color:#1a365d;margin-bottom:12px;font-size:24px;}}
        .meta{{text-align:center;color:#555;margin-bottom:24px;font-size:15px;}}
        .summary-panel{{background:#e8f0fc;padding:16px;border-radius:10px;margin-bottom:28px;}}
        .summary-panel h4{{margin-bottom:8px;color:#1a365d;}}
        .legend{{margin-top:8px;color:#444;font-size:14px;}}
        .source-card{{background:#ffffff;padding:18px;border-radius:12px;margin-bottom:16px;box-shadow:0 2px 8px #00000014;}}
        .source-card h3{{font-size:17px;color:#2c3e50;margin-bottom:10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}}
        .freshness-badge{{background:#3498db;color:#fff;padding:2px 8px;border-radius:12px;font-size:13px;}}
        .source-card ul{{padding-left:22px;}}
        .source-card li{{padding:6px 0;line-height:1.6;font-size:15px;}}
        .no-news{{color:#888;}}
    </style>
</head>
<body>
    <h1>🌐 全球宏观财经全景看板</h1>
    <div class="meta">自动巡检时间：{time_string} (北京时间)</div>
    <div class="summary-panel">
        <h4>📈 抓取摘要</h4>
        <p>{source_with_updates} 个源更新，{source_no_updates} 个源无新内容/失败，拦截 {total_dup} 条历史重复标题，新增 {total_new} 条。</p>
        <p class="legend">🕐 新鲜度标记：🔥=6h内 ⭐=24h内 💤=48h内 ⏰=72h 🗑️>72h</p>
    </div>
    {"\n".join(html_sections)}
</body>
</html>
'''

    # 保存 HTML
    out_html = os.path.join(output_dir, f"{date_string}_{now_beijing.strftime('%H%M')}.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(full_html)

    logger.info(f"✅ HTML 看板已成功导出：{out_html}")

if __name__ == "__main__":
    main()
