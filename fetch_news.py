import os
import sys
import glob
import time
import logging
from datetime import datetime, timedelta, timezone
import requests
import feedparser

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

CUSTOM_NEWS_SOURCES = [
    ("WSJ (华尔街日报-世界新闻)", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("CNBC (消费品与商业频道-头条)", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch (市场观察-热点头条)", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Yahoo Finance (雅虎财经-美股头条)", "https://finance.yahoo.com/news/rssindex"),
    ("Financial Times (金融时报-全球经济)", "https://www.ft.com/global-economy?format=rss"),
    ("Investing.com (全球投资网-核心美股快讯)", "https://www.investing.com/rss/news_25.rss"),
    ("TechCrunch (科技巨头与一级市场简报)", "https://techcrunch.com/feed/"),
    ("Seeking Alpha (寻找阿尔法-个股核心墙)", "https://seekingalpha.com/feed.xml"),
    ("人民网-人民日报核心精选", "https://plink.anyfeeder.com/people"),
    ("新华网-新华社新闻", "https://plink.anyfeeder.com/newscn/whxw"),
    ("界面新闻-财经频道", "https://plink.anyfeeder.com/jiemian/finance"),
    ("36氪-科技创投", "https://plink.anyfeeder.com/36kr"),
    ("华尔街见闻-中文财经", "https://plink.anyfeeder.com/wallstreetcn"),
    ("经济观察报", "https://plink.anyfeeder.com/eeo"),
    ("纽约时报 (美国)-国际中文精选", "https://cn.nytimes.com/rss/"),
    ("卫报 (英国)-全球头条简报", "https://www.theguardian.com/world/rss"),
    ("镜报 (德国 Der Spiegel)-国际版", "https://www.spiegel.de/international/index.rss"),
    ("朝日新闻 (日本)-国际要闻", "http://www.asahi.com/rss/asahi/newsheadlines.rdf"),
    ("半岛电视台-中东新闻", "https://plink.anyfeeder.com/aljazeera/news"),
    ("悉尼先驱晨报 (澳洲)-核心大盘", "https://www.smh.com.au/rss/feed.xml"),
    ("印度时报 (印度)-亚洲经济要闻", "https://timesofindia.indiations.com/rssfeeds/296589292.cms"),
]

DEDUP_LOOKBACK_DAYS = 7
MAX_HEADLINES_PER_SOURCE = 10
MIN_HEADLINE_LENGTH = 6
MAX_NEWS_AGE_HOURS = 72  

def get_entry_age(entry):
    """""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        try:
            pub_time = datetime(*published[:6], tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            age_hours = (now - pub_time).total_seconds() / 3600
            time_str = pub_time.strftime("%m-%d %H:%M")
            return age_hours, time_str
        except Exception:
            return None, None
    return None, None


def format_freshness_flag(age_hours):
    """""
    if age_hours is None:
        return ""
    if age_hours <= 6:
        return " 🔥"
    elif age_hours <= 24:
        return " ⭐"
    elif age_hours <= 48:
        return " 💤"
    elif age_hours <= MAX_NEWS_AGE_HOURS:
        return " ⏰"
    else:
        return " 🗑️"


def compute_source_freshness(headlines_with_age):
    """""
    if not headlines_with_age:
        return "N/A"
    ages = [h['age'] for h in headlines_with_age if h['age'] is not None]
    if not ages:
        return "未知"
    avg_age = sum(ages) / len(ages)
    if avg_age <= 6:
        return "🔥 火热"
    elif avg_age <= 24:
        return "⭐ 新鲜"
    elif avg_age <= 48:
        return "💤 稍枧"
    else:
        return f"⏰ {avg_age:.0f}h前"


def load_history(output_dir, lookback_days=DEDUP_LOOKBACK_DAYS):
    history = {}
    cutoff = datetime.now() - timedelta(days=lookback_days)
    pattern = os.path.join(output_dir, "????-??-??_????.md")
    files = sorted(glob.glob(pattern))
    for fpath in files:
        fname = os.path.basename(fpath)
        date_str = fname[:10]
        try:
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        if file_date < cutoff:
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        current_source = None
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("### 📌 "):
                current_source = line.replace("### 📌 ", "").strip()
                if current_source not in history:
                    history[current_source] = set()
            elif current_source and line and line[0].isdigit():
                parts = line.split(". ", 1)
                if len(parts) > 1:
                    headline = parts[1].strip()
                    if len,headline) >= MIN_HEADLINE_LENGTH:
                        history[current_source].add(headline)
    total = sum(len(v) for v in history.values())
    logger.info(f"历史去重库加载完成：{len(history)} 个源，共 {total} 条历史标题")
    return history


def fetch_rss_headlines(name, url, history_set=None):
    logger.info(f"正在巡检源 [{name}] -> {url}")
    all_entries = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            logger.warning(f"[{name}] 请求失败，状态码: {response.status_code}")
            return [], 0, 0, "失败"
        feed = feedparser.parse(response.content)
        if not feed.entries:
            logger.warning(f"[{name}] RSS源返回空内宩")
            return [], 0, 0, "空"
        seen_in_this_run = set()
        for entry in feed.entries:
            text = entry.get("title", "").strip()
            if text and len(text) >= MIN_HEADLINE_LENGTH and text not in seen_in_this_run:
                seen_in_this_run.add(text)
                age_hours, time_str = get_entry_age(entry)
                all_entries.append({
                    'title': text,
                    'age': age_hours,
                    'time': time_str
                })
    except requests.exceptions.RequestException as e:
        logger.error(f"[{name}] 网络请求失败: {type(e).__name__}: {e}")
        return [], 0, 0, "罩廜错误"
    except Exception as e:
        logger.error(f"[{name}] 未预期错误: {type(e).__name__}: {e}")
        return [], 0, 0, "异常"

    # 去重
    if history_set is not None:
        new_entries = []
        dup_count = 0
        for h in all_entries:
            if h['title'] in history_set:
                dup_count += 1
            else:
                new_entries.append(h)
                history_set.add(h['title'])
    else:
        new_entries = all_entries
        dup_count = 0

    # 新鲜庖评分
    freshness = compute_source_freshness(new_entries)

    # 给衡不赇新闻数
    stale_count = sum(1 for h in new_entries if h['age'] is not None and h['age'] > MAX_NEWS_AGE_HOURS)

    new_entries = new_entries[:MAX_HEADLINES_PER_SOURCE]

    if dup_count > 0:
        logger.info(f"  -> 去重过滤: {dup_count} 条重复，{len(new_entries)} 条新内容，新鲜度: {freshness}")
    else:
        logger.info(f"  -> 获取 {len(new_entries)} 条内容，新鲜度: {freshness}")

    return new_entries, dup_count, stale_count, freshness


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "每日股市财经新闻")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("=" * 60)
    logger.info("加载卆史数据构建去重库...")
    history = load_history(output_dir)

    logger.info("=" * 60)
    logger.info("开始巡检RSS源...")

    raw_content_list = []
    total_new = 0
    total_dup = 0
    total_stale = 0
    source_with_updates = 0
    source_no_updates = 0
    source_fresh_list = []
    source_stale_list = []

    for name, url in CUSTOM_NEWS_SOURCES:
        history_set = history.get(name, set())
        entries, dup_count, stale_count, freshness = fetch_rss_headlines(name, url, history_set)
        total_dup += dup_count
        total_stale += stale_count

        raw_content_list.append(f"\n### 📌 {name}  [{freshness}]")

        if entries:
            for idx, h in enumerate(entries, 1):
                time_tag = f" ({h['time']})" if h['time'] else ""
                flag = format_freshness_flag(h['age'])
                raw_content_list.append(f"{idx}. {h['title']}{flag}{time_tag}")
            total_new += len(entries)
            source_with_updates += 1
            if stale_count > 0 and stale_count == len(entries):
                source_stale_list.append(name)
            else:
                source_fresh_list.append(name)
        else:
            if dup_count > 0:
                raw_content_list.append("> 🔄 今日无新更新（选有头条与前日重复）")
            else:
                raw_content_list.append("> ⏳今日该时段暂未获取到数据")
            source_no_updates += 1

        time.sleep(0.5)

    all_raw_text = "\n".join(raw_content_list)
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(timezone.utc).astimezone(tz_beijing)
    time_string = now_beijing.strftime("%Y-%m-%d %H:%M:%S")
    date_string = now_beijing.strftime("%Y-%m-%d")

    # 构建时效性总结
    freshness_summary = ""
    if source_stale_list:
        freshness_summary = f"\n⚠️ **以下源内容已偏旧**（已跇{MAX_NEWS_AGE_HOURS}h）：{'、'.join(source_stale_list)}  这些错误是无所有J\n"
    if total_stale > 0:
        freshness_summary += f"⚠️ 本次扫描发现 {total_stale} 条内容发布时间超跇{MAX_NEWS_AGE_HOURS}小时，请注意时效性\n"
    
    summary_line = (
        f"\n---\n"
        f"📈 **未次扫描摘要�：{source_with_updates} 个源有更新，"
        f"{source_no_updates} 个源无新内容，"
        f"去重过滤 {total_dup} 条重复标题，"
        f"新增 {total_new} 条内容\n"
        f"{freshness_summary}"
        f"\n> 🕐 新鲜度标记：🔥=6h内！⭐=24h内！💤=48h内！⏰=72h🗑️>72h＊超跇����")\n"
    )

    final_text = (
        f"# 🌐 全球宏观财经与顶级报纸全景看板\n"
        f"> 🕒 自动巡检时间：`{time_string}` (北京时间)\n"
        f"> 🔍 已自动去重（对比最近{DEDUP_LOOKBACK_DAYS}天数据）+ 时效性标记\n"
        f"{summary_line}"
        f"---"
        f"{all_raw_text}"
    )

    file_name = os.path.join(output_dir, f"{date_string}_{now_beijing.strftime('%H%M')}.md")
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(final_text)

    logger.info("=" * 60)
    logger.info(f"巡检完成！")
    logger.info(f"   ✅ {source_with_updates} 个源有更新")
    logger.info(f"   ⏭️  {source_no_updates} 个源无新内容")
    logger.info(f"   🗑️  去重过滤 {total_dup} 条")
    logger.info(f"   ✨ 新增 {total_new} 条")
    logger.info(f"   ⏰ 其中 {total_stale} 条超跇时效")
    logger.info(f"   📁 已写入：{file_name}")


if __name__ == "__main__":
    main()
