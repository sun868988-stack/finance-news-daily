# -*- coding: utf-8 -*-
"""
fetch_news.py — 针对网上脚本修改：
  1. 输出方式恢复为网上原版的纯 Markdown (.md) 文件。
  2. 新闻源参考本地配置进行了失效修复（替换了 Yahoo/36氪/华尔街见闻等失效源）。
  3. 保持网上原版的逻辑与路径保存机制。
"""

import os
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

# ===================== 新闻源配置（参考本地修复版） =====================
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

MAX_HEADLINES_PER_SOURCE = 10
MIN_HEADLINE_LENGTH = 6

def fetch_rss_headlines(name, url):
    logger.info(f"巡检源 [{name}] -> {url[:60]}")
    headlines = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            logger.warning(f"[{name}] HTTP {response.status_code}")
            return []
        feed = feedparser.parse(response.content)
        if not feed.entries:
            logger.warning(f"[{name}] RSS 返回空")
            return []
        
        seen = set()
        for entry in feed.entries:
            text = entry.get("title", "").strip()
            if " - " in text and len(text) > 60:
                text = text.rsplit(" - ", 1)[0]
            if text and len(text) >= MIN_HEADLINE_LENGTH and text not in seen:
                seen.add(text)
                headlines.append(text)
                if len(headlines) >= MAX_HEADLINES_PER_SOURCE:
                    break
    except Exception as e:
        logger.error(f"[{name}] 异常: {e}")
        return []
        
    return headlines

def main():
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    
    # 网上原版保存方式（输出目录）
    output_dir = "news_output"
    os.makedirs(output_dir, exist_ok=True)

    time_string = now_beijing.strftime("%Y-%m-%d %H:%M:%S")
    date_string = now_beijing.strftime("%Y-%m-%d")

    md_lines = []
    md_lines.append("# 🌐 全球宏观财经与顶级报纸全景看板")
    md_lines.append(f"> 🕒 自动巡检时间：`{time_string}` (北京时间)\n")
    md_lines.append("---")

    total_news = 0
    for name, url in CUSTOM_NEWS_SOURCES:
        headlines = fetch_rss_headlines(name, url)
        md_lines.append(f"### 📌 {name}")
        if headlines:
            for idx, text in enumerate(headlines, 1):
                md_lines.append(f"{idx}. {text}")
            total_news += len(headlines)
        else:
            md_lines.append("> ⏳ 今日该时段暂未获取到数据 / 无更新")
        md_lines.append("")
        time.sleep(0.3)

    # 导出 Markdown 文件
    out_md = os.path.join(output_dir, f"{date_string}_{now_beijing.strftime('%H%M')}.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    logger.info(f"✅ Markdown 文件已成功生成并保存至：{out_md}，共计 {total_news} 条新闻。")

if __name__ == "__main__":
    main()
