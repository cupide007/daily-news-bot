import feedparser
import requests
import os
import shutil
from datetime import datetime
import pytz
import time

# --- 配置 ---
RSS_URL = "https://36kr.com/feed" 
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- AI 调用函数 ---
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

# --- 生成每日综述 (图2 那个紫色的大卡片) ---
def generate_daily_overview(titles):
    titles_text = "\n".join([f"- {t}" for t in titles])
    prompt = f"""
    你是科技新闻主编。请根据以下今日新闻标题列表，写一段 150 字左右的【每日全网舆情综述】。
    
    要求：
    1. 语气专业、连贯，像一份情报报告。
    2. 不要列点，写成一段通顺的文字。
    3. 重点突出科技、AI 或商业领域的趋势。
    
    新闻标题列表：
    {titles_text}
    """
    return call_gemini(prompt)

# --- 生成单条摘要 ---
def summarize_single_news(content):
    prompt = f"请用一句话概括这篇新闻（50字以内），并提取1个核心行业标签。格式：摘要|标签\n内容：{content[:1000]}"
    return call_gemini(prompt)

# --- 主程序 ---
def main():
    # 1. 初始化
    posts_dir = "docs/posts"
    if not os.path.exists(posts_dir): os.makedirs(posts_dir)
    
    tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    time_str = datetime.now(tz).strftime("%H:%M")
    
    print(f"Fetching RSS: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    if not feed.entries: return

    # 取前 12 条
    entries = feed.entries[:12]
    titles = [e.title for e in entries]

    # 2. 生成【核心综述】(紫色卡片内容)
    print("正在生成每日综述...")
    overview = generate_daily_overview(titles)
    if not overview: overview = "今日暂无 AI 综述生成。"

    # 3. 开始构建 Markdown (使用 HTML 语法以应用 CSS)
    md_content = f"""# 📅 舆情日报 {today_str}
<div class="update-time">更新时间：{time_str}</div>

<div class="daily-overview">
    <h3>🛡️ AI 核心综述</h3>
    <p>{overview}</p>
</div>

<div class="news-list">
"""

    # 4. 循环处理每条新闻 (生成白色卡片)
    for entry in entries:
        print(f"处理: {entry.title}")
        content = entry.summary if 'summary' in entry else entry.title
        
        # 为了速度，每处理3条歇1秒，防止触发 API 限制
        # time.sleep(1) 
        
        res = summarize_single_news(content)
        if res and "|" in res:
            summary, tag = res.split("|", 1)
        else:
            summary, tag = res if res else entry.title, "资讯"

        # 拼接 HTML 卡片结构
        md_content += f"""
    <div class="news-card">
        <h4><a href="{entry.link}" target="_blank">{entry.title}</a></h4>
        <p class="summary">{summary}</p>
        <div class="news-meta">
            <span class="tag-pill">{tag.strip()}</span>
            <span>{entry.source.title if hasattr(entry, 'source') else '36Kr'}</span>
        </div>
    </div>
"""

    md_content += "</div>\n" # 闭合 news-list

    # 5. 保存文件
    filename = os.path.join(posts_dir, f"{today_str}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    shutil.copy(filename, os.path.join(posts_dir, "latest.md"))
    print("✅ 完成！")

if __name__ == "__main__":
    main()
