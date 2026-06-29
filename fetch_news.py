import os
import time
from datetime import datetime, timedelta, timezone
import requests
import xml.etree.ElementTree as ET

# =====================================================================
# 🌐 在这里管理你的新闻源（未来想要添加新网站，直接在下面加一行即可）
# =====================================================================
CUSTOM_NEWS_SOURCES = [
    ("Reuters (路透社-财经快讯)", "https://rss.dragonegg.ai/reuters/business"),
    # 👇 已经为你替换为官方原生高频更新的市场速报源，带 Headers 伪装可稳定抓取
    ("Bloomberg (彭博社-市场速报)", "https://www.bloomberg.com/feeds/bmd/europe.xml"),
    ("Washington Post (华饰顿邮报-财经)", "https://feeds.washingtonpost.com/rss/business"),
    ("CNBC (消费品与商业频道-头条)", "https://search.cnbc.com/rs/search/all/view.rss?partnerId=2000"),
    ("WSJ (华尔街日报-世界新闻)", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("MarketWatch (市场观察-头条)", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Financial Times (金融时报-全球经济)", "https://www.ft.com/global-economy?format=rss"),
    ("Barrons (巴伦周刊-头条)", "https://feeds.content.dowjones.io/public/rss/barrons_online"),
    ("Seeking Alpha (寻找阿尔法-核心墙)", "https://seekingalpha.com/feed.xml"),
    ("TechCrunch (科技巨头简报)", "https://techcrunch.com/feed/"),
    ("Yahoo Finance (雅虎财经-美股头条)", "https://finance.yahoo.com/news/rssindex"),
    ("Investing.com (英为财情-最新行业)", "https://www.investing.com/rss/news_285.rss"),
    ("TradingView (交易视图-官方分析)", "https://www.tradingview.com/feed/"),
    ("SEC Edgar (美国证监会今日披露公告)", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count=40&output=atom"),
    
    # -----------------------------------------------------------------
    # 👇【下次要加新网站，请直接复制下面这一行，把名字和链接换掉即可】
    # ("媒体名称 (板块说明)", "https://这里填写新的RSS链接地址"),
    # -----------------------------------------------------------------
]

def fetch_rss_headlines(name, url):
    print(f"正在获取 [{name}] -> {url} ...")
    headlines = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return [f"因当前时段限制，暂无实时更新（状态码 {response.status_code}）"]
            
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        if not items:
            items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
        if not items:
            items = root.findall('.//entry')
            
        for item in items:
            title_node = item.find('title')
            if title_node is None:
                title_node = item.find('{http://www.w3.org/2005/Atom}title')
            text = title_node.text.strip() if title_node is not None and title_node.text else ""
            
            link_node = item.find('link')
            if link_node is None:
                link_node = item.find('{http://www.w3.org/2005/Atom}link')
            
            href = ""
            if link_node is not None:
                href = link_node.text if link_node.text else link_node.get('href', '')
                
            if text and len(text) > 8:
                item_str = f"[{text}]({href})" if href else text
                if item_str not in headlines:
                    headlines.append(item_str)
                    
            if len(headlines) >= 5:
                break
                
    except Exception as e:
        return [f"该时段接口连接暂不可达 (错误: {e})"]
        
    return headlines if headlines else ["今日该时段暂无置顶简报更新"]

def main():
    md_content = []
    md_content.append("# 🌐 全球核心财经与科技全景看板")
    
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    
    time_string = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
    md_content.append(f"> 🤖 智能机器人自动巡检更新时间：`{time_string}` (北京时间)\n")
    md_content.append("--- \n")
    
    # 这里直接读取最上面配置好的自定义新闻源
    for name, url in CUSTOM_NEWS_SOURCES:
        headlines = fetch_rss_headlines(name, url)
        md_content.append(f"### 📌 {name}")
        for index, headline in enumerate(headlines, 1):
            md_content.append(f"{index}. {headline}")
        md_content.append("")
        time.sleep(1)
        
    final_text = "\n".join(md_content)
    file_name = now_beijing.strftime('%Y-%m-%d_%H%M.md')
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(final_text)
        
    print(f"🏁 简报已完美写入新文件：{file_name}")

if __name__ == "__main__":
    main()
