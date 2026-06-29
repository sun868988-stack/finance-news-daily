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
           
