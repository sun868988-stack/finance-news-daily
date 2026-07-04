import os
import time
from datetime import datetime, timedelta, timezone
import requests
import xml.etree.ElementTree as ET

# =====================================================================
# 🌐 全球核心财经与宏观数据源
# =====================================================================
CUSTOM_NEWS_SOURCES = [
    ("WSJ (华尔街日报-世界新闻)", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("Financial Times (金融时报-全球经济)", "https://www.ft.com/global-economy?format=rss"),
    ("CNBC (消费品与商业频道-头条)", "https://search.cnbc.com/rs/search/all/view.rss?partnerId=2000"),
    ("MarketWatch (市场观察-热点头条)", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Yahoo Finance (雅虎财经-美股头条)", "https://finance.yahoo.com/news/rssindex"),
    ("Barrons (巴伦周刊-周末深度分析)", "https://feeds.content.dowjones.io/public/rss/barrons_online"),
    ("Seeking Alpha (寻找阿尔法-个股核心墙)", "https://seekingalpha.com/feed.xml"),
    ("TradingView (交易视图-官方技术分析)", "https://www.tradingview.com/feed/"),
    ("TechCrunch (科技巨头与一级市场风口简报)", "https://techcrunch.com/feed/"),
    ("BLS (美国劳工统计局-最新核心指标公告)", "https://www.bls.gov/feed/bls_latest_news.rss"),
    ("FRED (圣路易斯联储-最新经济数据库动态)", "https://fred.stlouisfed.org/newrss.php"),
    ("SEC Edgar (美国证监会-今日高管变动与披露公告)", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count=40&output=atom"),
    ("WallStreetcn (华尔街见闻-全球核心实时快讯)", "https://rss.dragonegg.ai/wallstreetcn/global"),
    ("Bloomberg (彭博社-市场速报-可能受限)", "https://www.bloomberg.com/feeds/bmd/europe.xml"),
    ("Reuters (路透社-财经快讯-改用官方备用直连)", "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best-topic"),
]

def fetch_rss_headlines(name, url):
    print(f"正在获取 [{name}] -> {url} ...")
    headlines = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            return [f"暂无实时更新 (Status: {response.status_code})"]
            
        # 🛡️ 容错保护 1：如果返回的数据不包含 XML 特征，直接跳过，防止解析崩溃
        content_str = response.content.decode('utf-8', errors='ignore').strip()
        if not content_str.startswith('<'):
            print(f"⚠️ [{name}] 返回了非 XML 内容，可能遭遇频率限制，已安全跳过。")
            return ["该时段接口连接暂不可达"]

        root = ET.fromstring(response.content)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry') or root.findall('.//entry')
            
        for item in items:
            title_node = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
            text = title_node.text.strip() if title_node is not None and title_node.text else ""
            
            if text and len(text) > 8:
                if text not in headlines:
                    headlines.append(text)
                    
            if len(headlines) >= 3:
                break
                
    except Exception as e:
        # 🛡️ 容错保护 2：捕获所有可能引发异常的解析错误，确保程序绝不中断
        print(f"⚠️ [{name}] 处理数据时发生异常: {e}，已自动跳过。")
        return [f"该时段接口连接暂不可达"]
        
    return headlines if headlines else ["今日该时段暂无置顶简报更新"]

def main():
    raw_content_list = []
    
    # 1. 顺序抓取新闻源
import os
import time
from datetime import datetime, timedelta, timezone
import requests
import feedparser  # 🚀 激活你 requirements.txt 里的强力解析库

# =====================================================================
# 🌐 全球核心财经与宏观数据源（全面校对修复版）
# =====================================================================
CUSTOM_NEWS_SOURCES = [
    ("WSJ (华尔街日报-世界新闻)", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("Financial Times (金融时报-全球经济)", "https://www.ft.com/global-economy?format=rss"),
    ("CNBC (消费品与商业频道-头条)", "https://search.cnbc.com/rs/search/all/view.rss?partnerId=2000"),
    ("MarketWatch (市场观察-热点头条)", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Yahoo Finance (雅虎财经-美股头条)", "https://finance.yahoo.com/news/rssindex"),
    ("Barrons (巴伦周刊-深度分析)", "https://feeds.content.dowjones.io/public/rss/barrons_online"),
    ("Seeking Alpha (寻找阿尔法-个股核心墙)", "https://seekingalpha.com/feed.xml"),
    ("TradingView (交易视图-官方技术分析)", "https://www.tradingview.com/feed/"),
    ("TechCrunch (科技巨头与一级市场风口简报)", "https://techcrunch.com/feed/"),
    ("BLS (美国劳工统计局-最新核心指标公告)", "https://www.bls.gov/feed/bls_latest_news.rss"),
    ("FRED (圣路易斯联储-最新经济数据库动态)", "https://fred.stlouisfed.org/newrss.php"),
    ("WallStreetcn (华尔街见闻-全球核心实时快讯)", "https://rss.dragonegg.ai/wallstreetcn/global"),
    ("Bloomberg (彭博社-市场速报)", "https://www.bloomberg.com/feeds/bmd/europe.xml"),
]

def fetch_rss_headlines(name, url):
    print(f"正在获取 [{name}] -> {url} ...")
    headlines = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # 使用 requests 获取网页，防止被部分防爬虫机制拦截
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            return [f"暂无实时更新 (Status: {response.status_code})"]
            
        # 🚀 使用 feedparser 强力解析，完美兼容所有华尔街日报/CNBC等特殊格式
        feed = feedparser.parse(response.content)
        
        for entry in feed.entries:
            text = entry.get('title', '').strip()
            if text and len(text) > 8:
                if text not in headlines:
                    headlines.append(text)
            if len(headlines) >= 3:
                break
                
    except Exception as e:
        print(f"⚠️ [{name}] 处理数据时发生异常: {e}")
        return ["该时段接口连接暂不可达"]
        
    return headlines if headlines else ["今日该时段暂无置顶简报更新"]

def main():
    raw_content_list = []
    
    # 1. 顺序抓取新闻源
    for name, url in CUSTOM_NEWS_SOURCES:
        headlines = fetch_rss_headlines(name, url)
        raw_content_list.append(f"\n### 📌 {name}")
        for index, headline in enumerate(headlines, 1):
            raw_content_list.append(f"{index}. {headline}")
        time.sleep(0.3)
        
    all_raw_text = "\n".join(raw_content_list)
    
    # 2. 生成报头信息
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    time_string = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
    
    final_text = (
        f"# 🌐 全球核心财经与科技全景看板 (GitHub 本地安全版)\n"
        f"> 🕒 自动巡检时间：`{time_string}` (北京时间)\n\n"
        f"---"
        f"{all_raw_text}"
    )
    
    # 📂 3. 检查并自动建立文件夹
    folder_name = "每日股市财经新闻"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name, exist_ok=True)
        
    file_name = os.path.join(folder_name, now_beijing.strftime('%Y-%m-%d_%H%M.md'))
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(final_text)
        
    print(f"🏁 原始财经简报已安全写入文件：{file_name}")

if __name__ == "__main__":
    main()
