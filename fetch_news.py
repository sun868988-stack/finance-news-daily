import os
import time
from datetime import datetime, timedelta, timezone
import requests
import feedparser

# =====================================================================
# 🌐 全球核心财经与宏观数据源（高饱满度、GitHub 直连无障碍版）
# =====================================================================
CUSTOM_NEWS_SOURCES = [
    # 🌟 华尔街核心大盘与科技前沿
    ("WSJ (华尔街日报-世界新闻)", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("CNBC (消费品与商业频道-头条)", "https://search.cnbc.com/rs/search/all/view.rss?partnerId=2000"),
    ("MarketWatch (市场观察-热点头条)", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Yahoo Finance (雅虎财经-美股头条)", "https://finance.yahoo.com/news/rssindex"),
    ("Financial Times (金融时报-全球经济)", "https://www.ft.com/global-economy?format=rss"),
    
    # 📈 个股基本面、技术分析与行业风口
    ("Investing.com (全球投资网-核心美股快讯)", "https://www.investing.com/rss/news_25.rss"),
    ("Reuters (路透社-全球商业与金融快讯)", "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best-topic"),
    ("TradingView (交易视图-官方技术分析)", "https://www.tradingview.com/feed/"),
    ("TechCrunch (科技巨头与一级市场简报)", "https://techcrunch.com/feed/"),
    ("Seeking Alpha (寻找阿尔法-个股核心墙)", "https://seekingalpha.com/feed.xml"),
    
    # 🇨🇳 国内宏观与 A 股/港股核心风向
    ("Xinhua News (新华网-核心财经大政方针)", "http://www.news.cn/fortune/pro/rss.xml"),
]

def fetch_rss_headlines(name, url):
    print(f"正在获取 [{name}] -> {url} ...")
    headlines = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return [f"因接口时段限制暂未获取到更新 (Status: {response.status_code})"]
            
        feed = feedparser.parse(response.content)
        
        # 提取新闻标题
        for entry in feed.entries:
            text = entry.get('title', '').strip()
            if text and len(text) > 6:
                if text not in headlines:
                    headlines.append(text)
            if len(headlines) >= 10:  # 每个源最多抓取 10 条最新的
                break
                
    except Exception as e:
        print(f"⚠️ [{name}] 抓取异常: {e}")
        return ["今日该时段暂无置顶简报更新"]
        
    return headlines if headlines else ["今日该时段暂无置顶简报更新"]

def main():
    raw_content_list = []
    
    for name, url in CUSTOM_NEWS_SOURCES:
        headlines = fetch_rss_headlines(name, url)
        raw_content_list.append(f"\n### 📌 {name}")
        for index, headline in enumerate(headlines, 1):
            raw_content_list.append(f"{index}. {headline}")
        time.sleep(0.5)  # 稍微加大延迟，防止被连续请求拦截
        
    all_raw_text = "\n".join(raw_content_list)
    
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    time_string = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
    
    final_text = (
        f"# 🌐 全球核心财经与科技全景看板 (GitHub 本地安全版)\n"
        f"> 🕒 自动巡检时间：`{time_string}` (北京时间)\n\n"
        f"---"
        f"{all_raw_text}"
    )
    
    folder_name = "每日股市财经新闻"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name, exist_ok=True)
        
    file_name = os.path.join(folder_name, now_beijing.strftime('%Y-%m-%d_%H%M.md'))
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(final_text)
        
    print(f"🏁 原始财经简报已安全写入文件：{file_name}")

if __name__ == "__main__":
    main()
