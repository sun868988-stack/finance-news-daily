# ... 前面的代码保持不变 ...

if __name__ == "__main__":
    content = get_finance_news()
    
    # 1. 依然执行邮件发送
    send_email(content)
    
    # 2. 新增：将新闻内容保存到仓库本地（给其他机器人扫描用）
    # 转换为适合 Markdown 查看的格式（去掉一些 HTML 标签）
    md_content = content.replace("<h2>", "# ").replace("</h2>", "\n\n")
    md_content = md_content.replace("<h3>🔍 ", "## 🔍 ").replace("</h3>", "\n")
    md_content = md_content.replace("<ul>", "").replace("</ul>", "")
    md_content = md_content.replace("<li>", "* ").replace("</li>", "\n")
    md_content = md_content.replace("<p style='color:red;'>", "❌ ").replace("</p>", "\n")
    
    with open("news_today.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print("新闻已成功保存到本地 news_today.md！")
