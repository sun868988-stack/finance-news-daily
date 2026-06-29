import os
import time
from datetime import datetime, timedelta, timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_site_headlines(name, url):
    print(f"正在抓取 [{name}] -> {url} ...")
    headlines = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return [f"因网站限制，暂无实时更新（状态码 {response.status_code}）"]
        
        soup = BeautifulSoup(response.text, 'html.parser')
        found_tags = soup.find_all(['h1', 'h2', 'h3'])
        
        for tag in found_tags:
            text = tag.get_text(strip=True)
            if 18 < len(text) < 130:
                link_tag = tag.find('a') if tag.name != 'a' else tag
                if not link_tag and tag.parent.name == 'a':
                    link_tag = tag.parent
                href = link_tag.get('href') if link_tag else None
                item = f"[{text}]({urljoin(url, href)})" if href else text
                if item not in headlines:
                    headlines.append(item)
            if len(headlines) >= 5:
                break
                
        if not headlines:
            links = soup.find_all('a')
            for link in links:
                text = link.get_text(strip=True)
                if 25 < len(text) < 100 and not text.startswith(('Terms', 'Privacy', 'Sign In', 'Cookie')):
                    href = link.get('href')
                    item = f"[{text}]({urljoin(url, href)})" if href else text
                    if item not in headlines:
                        headlines.append(item)
                if len(headlines) >= 4:
                    break
    except Exception as e:
        return [f"该时段网络连接暂不可达 (错误: {e})"]
    
    return headlines if headlines else ["今日该时段暂无置顶简报更新"]

def main():
    urls = [
        ("Reuters (路透社)", "https://www.reuters.com"),
        ("Bloomberg (彭博社)", "https://www.bloomberg.com"),
        ("CNBC (消费品与商业频道)", "https://www.cnbc.com"),
        ("WSJ (华尔街日报)", "https://www.wsj.com"),
        ("MarketWatch (市场观察)", "https://www.marketwatch.com"),
        ("Financial Times (金融时报)", "https://www.ft.com"),
        ("Barrons (巴伦周刊)", "https://www.barrons.com"),
        ("Seeking Alpha (寻找阿尔法)", "https://seekingalpha.com"),
        ("TechCrunch (科技媒体)", "https://techcrunch.com"),
        ("Yahoo Finance (雅虎财经)", "https://finance.yahoo.com"),
        ("Investing.com (英为财情)", "https://www.investing.com"),
        ("TradingView (交易视图)", "https://www.tradingview.com"),
        ("SEC Edgar (美国证监会披露系统)", "https://www.sec.gov/cgi-bin/browse-edgar")
    ]
    
    md_content = []
    md_content.append("# 🌐 全球核心财经与科技全景看板")
    
    # 强制锁定北京时间 (UTC+8)
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    
    time_string = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
    md_content.append(f"> 🤖 智能机器人自动巡检更新时间：`{time_string}` (北京时间)\n")
    md_content.append("--- \n")
    
    for name, url in urls:
        headlines = fetch_site_headlines(name, url)
        md_content.append(f"### 📌 {name}")
        for index, headline in enumerate(headlines, 1):
            md_content.append(f"{index}. {headline}")
        md_content.append("")
        time.sleep(1)
        
    final_text = "\n".join(md_content)
    
    # 动态命名生成文件：形如 2026-06-29_2230.md
    file_name = now_beijing.strftime('%Y-%m-%d_%H%M.md')
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(final_text)
        
    print(f"🏁 简报已完美写入新文件：{file_name}")

if __name__ == "__main__":
    main()
           
