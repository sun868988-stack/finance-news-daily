import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_site_headlines(name, url):
    print(f"正在抓取 [{name}] -> {url} ...")
    headlines = []
    
    # 统一使用强大的 Headers
    # 特别声明：包含符合美国证监会 SEC EDGAR 要求的声明格式，防止因未声明身份被 SEC 直接 403 封禁
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 FinanceBloggerBot/1.0 (contact@myfinanceblog.com)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # 很多顶级财经网（如 Bloomberg、WSJ）有极强的 Cloudflare 盾，如果遇到 403/429，进行优雅降级兜底
        if response.status_code != 200:
            print(f"⚠️ [{name}] 返回状态码 {response.status_code}，可能触发了反爬或付费墙拦截。")
            return [f"因该网站防火墙限制，暂无实时更新（状态码 {response.status_code}，可稍后手动刷新）"]
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 💡 智能通用核心算法：优先提取页面中最核心的标题标签 (h1, h2, h3)
        # 这种做法比硬编码 class 类名更耐用，因为各大财经网前端几乎每周都在改标签样式名
        found_tags = soup.find_all(['h1', 'h2', 'h3'])
        
        for tag in found_tags:
            text = tag.get_text(strip=True)
            # 过滤掉太短（导航栏、时间标签）或太长（整段导语）的干扰信息
            if 18 < len(text) < 130:
                # 寻找标题内或者紧邻的超链接
                link_tag = tag.find('a') if tag.name != 'a' else tag
                if not link_tag and tag.parent.name == 'a':
                    link_tag = tag.parent
                    
                href = link_tag.get('href') if link_tag else None
                if href:
                    full_url = urljoin(url, href)  # 自动把相对路径（如 /news/123）补全为绝对路径
                    item = f"[{text}]({full_url})"
                else:
                    item = text
                    
                if item not in headlines:
                    headlines.append(item)
            
            if len(headlines) >= 5:  # 每个网站最多抓取前 5 条最新最核心的动态，避免版面过长
                break
                
        # 🔍 备用算法兜底：如果有些网站不用 h 标签，改用普通 a 链接，则启动文本长度过滤机制
        if not headlines:
            links = soup.find_all('a')
            for link in links:
                text = link.get_text(strip=True)
                if 25 < len(text) < 100 and not text.startswith(('Terms', 'Privacy', 'Sign In', 'Cookie', 'Subscribe')):
                    href = link.get('href')
                    full_url = urljoin(url, href) if href else url
                    item = f"[{text}]({full_url})"
                    if item not in headlines:
                        headlines.append(item)
                if len(headlines) >= 4:
                    break

    except Exception as e:
        print(f"❌ 抓取 [{name}] 发生连接异常: {e}")
        return [f"该时段网络连接暂不可达 (错误反馈: {e})"]
        
    return headlines if headlines else ["今日该时段暂无置顶简报更新"]

def main():
    # 完美装载你提供的 13 个顶级全球财经与科技目标源
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
    
    print("🚀 全球财经 13 大基地轮询轰炸系统启动...")
    
    md_content = []
    md_content.append("# 🌐 全球核心财经与科技全景看板")
    
    # 获取北京时间（GitHub 默认是 UTC，这里简单标注一下方便查看）
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    md_content.append(f"> 🤖 智能机器人自动巡检更新时间：`{current_time}` (基于云端海外高速节点扫描)\n")
    md_content.append("--- \n")
    
    # 开始多基地轰炸式循环抓取
    for name, url in urls:
        headlines = fetch_site_headlines(name, url)
        md_content.append(f"### 📌 {name}")
        for index, headline in enumerate(headlines, 1):
            md_content.append(f"{index}. {headline}")
        md_content.append("")  # 留空行隔离各网站内容
        
        # 💡 礼貌爬虫机制：每次抓取完一个网站，小憩 1 秒钟，防止频率过快被对方列入黑名单
        time.sleep(1)
        
    final_text = "\n".join(md_content)
    
    # 完美覆写本地的看板文件
    with open("news_today.md", "w", encoding="utf-8") as f:
        f.write(final_text)
        
    print("🏁 恭喜！13 大全球站点全部轮询扫描完成，已完美写入 news_today.md！")

if __name__ == "__main__":
    main()
