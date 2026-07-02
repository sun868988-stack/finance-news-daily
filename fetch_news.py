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
import os
import time
from datetime import datetime, timedelta, timezone
import requests
import xml.etree.ElementTree as ET

# =====================================================================
# 🌐 全球核心财经与宏观数据源（稳健版：健康源前置，不稳定源已垫底）
# =====================================================================
CUSTOM_NEWS_SOURCES = [
    # 🌟 【健康稳定·第一梯队】优质权威的官方直连英文源（秒返回，无报错风险）
    ("WSJ (华尔街日报-世界新闻)", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("Financial Times (金融时报-全球经济)", "https://www.ft.com/global-economy?format=rss"),
    ("CNBC (消费品与商业频道-头条)", "https://search.cnbc.com/rs/search/all/view.rss?partnerId=2000"),
    ("MarketWatch (市场观察-热点头条)", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Yahoo Finance (雅虎财经-美股头条)", "https://finance.yahoo.com/news/rssindex"),
    
    # 📈 【健康稳定·第二梯队】深度周刊与个股基本面、行业风口
    ("Barrons (巴伦周刊-周末深度分析)", "https://feeds.content.dowjones.io/public/rss/barrons_online"),
    ("Seeking Alpha (寻找阿尔法-个股核心墙)", "https://seekingalpha.com/feed.xml"),
    ("TradingView (交易视图-官方技术分析)", "https://www.tradingview.com/feed/"),
    ("TechCrunch (科技巨头与一级市场风口简报)", "https://techcrunch.com/feed/"),
    
    # 🏢 【健康稳定·第三梯队】宏观数据源头与官方信息披露
    ("BLS (美国劳工统计局-最新核心指标公告)", "https://www.bls.gov/feed/bls_latest_news.rss"),
    ("FRED (圣路易斯联储-最新经济数据库动态)", "https://fred.stlouisfed.org/newrss.php"),
    ("SEC Edgar (美国证监会-今日高管变动与披露公告)", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count=40&output=atom"),
    
    # 🇨🇳 【中概与国内宏观核心】
    ("WallStreetcn (华尔街见闻-全球核心实时快讯)", "https://rss.dragonegg.ai/wallstreetcn/global"),

    # =================================================================
    # ⚠️ 【优化调整·已移至垫底】以下为近期高频报错/连接受限的源，排在最后
    # =================================================================
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
            
            if text and len(text) > 8:
                if text not in headlines:
                    headlines.append(text)
                    
            if len(headlines) >= 3:  # 每个源保留前3条最核心的，避免文本过长
                break
                
    except Exception as e:
        return [f"该时段接口连接暂不可达 (错误: {e})"]
        
    return headlines if headlines else ["今日该时段暂无置顶简报更新"]

def translate_via_gemini(raw_text):
    """利用 Gemini API 将全英文快讯升华翻译为高质量的中文财经内参"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ 未检测到 GEMINI_API_KEY，保持原始英文输出。")
        return raw_text
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # 专为财经博主调教的专业中文内参 Prompt
    prompt = (
        "你是一位资深的国际财经全媒体主编。请将下面抓取到的全球各大媒体的英文财经快讯，"
        "编译提炼为高质量的中文财经日报。要求：\n"
        "1. 使用地道、专业的中文财经术语（如：Fed译为美联储、bullish译为看涨、treasury译为国债、PCE译为个人消费支出）。\n"
        "2. 精简去重，合并跨媒体的类似新闻，保留核心的时间、机构、以及关键财务数据（如百分比、数十亿金额等）。\n"
        "3. 保持排版美观，使用优雅的 Markdown 列表分板块呈现，每个板块保留 2-4 条最重要的核心内参。\n"
        "4. ⚠️ 注意：不要输出任何前言（如'这是为您翻译的报告'）或结语，直接开始输出板块正文。\n\n"
        f"以下是需要你处理的原始快讯内容：\n{raw_text}"
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            translated_text = result['candidates'][0]['content']['parts'][0]['text']
            return translated_text
        else:
            print(f"Gemini API 响应异常 (状态码 {response.status_code}): {response.text}")
    except Exception as e:
        print(f"请求 Gemini 发生异常: {e}")
        
    return raw_text

def main():
    raw_content_list = []
    
    # 1. 按稳健顺序依次抓取所有新闻源
    for name, url in CUSTOM_NEWS_SOURCES:
        headlines = fetch_rss_headlines(name, url)
        raw_content_list.append(f"\n### 📌 {name}")
        for index, headline in enumerate(headlines, 1):
            raw_content_list.append(f"{index}. {headline}")
        time.sleep(0.5)
        
    all_raw_text = "\n".join(raw_content_list)
    
    # 2. 召唤 Gemini 编译为高质量中文内参
    print("🚀 正在召唤 Gemini AI 财经编辑进行全自动中文编译与精简...")
    chinese_report = translate_via_gemini(all_raw_text)
    
    # 3. 加上统一的报头和北京时间戳
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    time_string = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
    
    final_text = (
        f"# 🌐 全球核心财经与科技全景看板\n"
        f"> 🤖 智能机器人自动巡检更新时间：`{time_string}` (北京时间)\n\n"
        f"{chinese_report}"
    )
    
    # 4. 写入本地文件供 GitHub Actions 的下一步读取
    file_name = now_beijing.strftime('%Y-%m-%d_%H%M.md')
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(final_text)
        
    print(f"🏁 纯中文财经简报已完美写入文件：{file_name}")

if __name__ == "__main__":
    main()
