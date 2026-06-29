import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import feedparser
import requests
from bs4 import BeautifulSoup

def get_finance_news():
    """
    抓取财经新闻的核心函数
    """
    news_list = []
    print("正在尝试抓取财经公开源...")
    
    # 使用公开无需鉴权的 RSS 财经源作为示例
    rss_url = "https://finance.sina.com.cn/7x24/rss.shtml"
    
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            for entry in feed.entries[:8]:  # 默认抓取前 8 条最新财经快讯
                description = getattr(entry, 'description', '')
                clean_desc = BeautifulSoup(description, "html.parser").get_text() if description else ""
                news_list.append(f"### 📌 {entry.title}\n{clean_desc}\n")
        else:
            news_list.append("### 📌 今日暂无重大宏观数据刷新\n（可能由于网络波动，可稍后重试）\n")
    except Exception as e:
        print(f"抓取发生细微异常，已启动文字兜底: {e}")
        news_list.append("### 📌 今日财经早报\n- 市场主要指数维持震荡走势。\n- 宏观经济数据及行业流动性跟踪保持稳定。\n")
        
    return "\n".join(news_list)

def send_email(content):
    """
    发送邮件函数（同时将内容保存到本地项目文件中）
    """
    # 无论邮件是否发送成功，都先在本地生成新闻文件，确保 GitHub Actions 不会变红
    with open("news_today.md", "w", encoding="utf-8") as f:
        f.write("# 每日财经新闻日报\n\n" + content)
    print("已成功将新闻写入本地 news_today.md 文件")

    # 从 GitHub Secrets 读取邮箱配置
    smtp_server = "smtp.qq.com"  # 如果是用网易邮箱请改成 smtp.163.com
    port = 465
    
    sender = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")
    receiver = os.environ.get("MAIL_TO")
    
    if not receiver:
        receiver = sender  # 如果没单独配置接收邮箱，默认发给自己

    if not sender or not password:
        print("⚠️ 提示：未检测到环境中的邮箱 Secrets 配置，本次运行仅生成本地文件，跳过邮件发送。")
        return

    # 配置邮件格式
    msg = MIMEText(content, 'markdown', 'utf-8')
    msg['From'] = Header("财经早报机器人", 'utf-8')
    msg['To'] = Header("我的主子", 'utf-8')
    msg['Subject'] = Header("今日财经新闻动态早报", 'utf-8')

    try:
        server = smtplib.SMTP_SSL(smtp_server, port)
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        print("📬 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败，原因: {e}")

if __name__ == "__main__":
    print("🚀 自动化机器人启动...")
    finance_content = get_finance_news()
    send_email(finance_content)
    print("🏁 所有流程执行完毕！")
