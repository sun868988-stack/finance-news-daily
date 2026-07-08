import os
import sys
import time
import logging
from datetime import datetime, timedelta, timezone
import requests
import feedparser

# 修复Windows终端GBK编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# =====================================================================
# 🌐 全球核心财经与顶级主流报纸看板（修正版）
# =====================================================================
CUSTOM_NEWS_SOURCES = [
    # 🌟【板块一：华尔街核心大盘与全球科技前沿】
    ("WSJ (华尔街日报-世界新闻)", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("CNBC (消费品与商业频道-头条)", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch (市场观察-热点头条)", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Yahoo Finance (雅虎财经-美股头条)", "https://finance.yahoo.com/news/rssindex"),
    ("Financial Times (金融时报-全球经济)", "https://www.ft.com/global-economy?format=rss"),
    ("Investing.com (全球投资网-核心美股快讯)", "https://www.investing.com/rss/news_25.rss"),
    ("TechCrunch (科技巨头与一级市场简报)", "https://techcrunch.com/feed/"),
    ("Seeking Alpha (寻找阿尔法-个股核心墙)", "https://seekingalpha.com/feed.xml"),

    # 🇨🇳【板块二：国内中央权威与顶级财经证券报纸】
    ("人民网-人民日报核心精选", "http://www.people.com.cn/rss/politics.xml"),
    ("新华网-高层时政要闻", "http://www.xinhuanet.com/politics/news_politics.xml"),
    # 经济日报官方RSS暂不可用，原链接为人民网财经，已移除避免混淆
    ("新华网-财经要闻", "http://www.xinhuanet.com/finance/news_finance.xml"),
    # 深圳新闻网原链接为重复的新华网地方联播，已移除

    # 🏙️【板块三：港澳台与内地综合大报风向】
    # 明报、星岛日报、香港经济日报无官方RSS，原rsshub.app公共实例已不可用，已移除

    # 🌏【板块四：海外华文与全球主流大报】
    # 联合早报已关闭RSS服务，已移除
    ("纽约时报 (美国)-国际中文精选", "https://cn.nytimes.com/rss/"),
    ("卫报 (英国)-全球头条简报", "https://www.theguardian.com/world/rss"),
    ("镜报 (德国 Der Spiegel)-国际版", "https://www.spiegel.de/international/index.rss"),
    ("朝日新闻 (日本)-国际要闻", "http://www.asahi.com/rss/asahi/newsheadlines.rdf"),
    ("耶路撒冷邮报 (以色列)-中东风向标", "https://www.jpost.com/rss/rssfeedsheadlines.aspx"),
    ("悉尼先驱晨报 (澳洲)-核心大盘", "https://www.smh.com.au/rss/feed.xml"),
    ("印度时报 (印度)-亚洲经济要闻", "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"),
]


def fetch_rss_headlines(name, url):
    """抓取单个RSS源的标题，失败时返回提示信息"""
    logger.info(f"正在巡检源 [{name}] -> {url}")
    headlines = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            logger.warning(f"[{name}] 请求失败，状态码: {response.status_code}")
            return [f"因接口时段限制暂未获取到更新 (Status: {response.status_code})"]

        feed = feedparser.parse(response.content)

        if not feed.entries:
            logger.warning(f"[{name}] RSS源返回空内容")
            return ["因接口时段限制暂未获取到更新 (RSS源返回空内容)"]

        # 提取新闻标题并进行初步去重
        seen = set()
        for entry in feed.entries:
            text = entry.get("title", "").strip()
            if text and len(text) > 5 and text not in seen:
                seen.add(text)
                headlines.append(text)
            if len(headlines) >= 10:
                break

    except requests.exceptions.RequestException as e:
        logger.error(f"[{name}] 网络请求失败: {type(e).__name__}: {e}")
        return ["今日该时段网络波动，暂未获取到数据"]
    except Exception as e:
        logger.error(f"[{name}] 未预期错误: {type(e).__name__}: {e}")
        return ["今日该时段暂未获取到数据"]

    return headlines if headlines else ["今日该时段暂无置顶数据更新"]


def main():
    raw_content_list = []

    for name, url in CUSTOM_NEWS_SOURCES:
        headlines = fetch_rss_headlines(name, url)
        raw_content_list.append(f"\n### 📌 {name}")
        for index, headline in enumerate(headlines, 1):
            raw_content_list.append(f"{index}. {headline}")
        time.sleep(0.5)  # 每次请求完休眠0.5秒，安全防封锁

    all_raw_text = "\n".join(raw_content_list)
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    time_string = now_beijing.strftime("%Y-%m-%d %H:%M:%S")

    final_text = (
        f"# 🌐 全球宏观财经与顶级报纸全景看板\n"
        f"> 🕒 自动巡检时间：`{time_string}` (北京时间)\n\n"
        f"---"
        f"{all_raw_text}"
    )

    # 使用绝对路径或可配置的输出目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder_name = os.path.join(script_dir, "每日股市财经新闻")

    os.makedirs(folder_name, exist_ok=True)
    file_name = os.path.join(folder_name, now_beijing.strftime("%Y-%m-%d_%H%M.md"))

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(final_text)

    logger.info(f"🏁 终极全景简报已安全写入文件：{file_name}")


if __name__ == "__main__":
    main()
