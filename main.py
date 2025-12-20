import feedparser
import requests
import os
import shutil
from datetime import datetime
import pytz
import time

# --- 配置区 ---
RSS_URL = "https://36kr.com/feed" 
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- AI 调用封装 ---
def call_gemini(prompt):
    if not API_KEY:
        print("❌ 错误：未找到 GEMINI_API_KEY")
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": safety_settings
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                return None
        else:
            print(f"API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Network Error: {e}")
        return None

# --- 生成每日综述 ---
def generate_overview(titles):
    prompt = f"""
    你是一个科技情报分析师。请根据以下今日新闻标题，写一段150字左右的【市场舆情综述】。
    要求：
    1. 语气专业、客观，类似金融研报。
    2. 提炼出核心趋势（如AI应用、硬件发布、股市波动等）。
    3. 不要使用列表，写成一段通顺的文字。
    
    新闻标题：
    {titles}
    """
    return call_gemini(prompt)

# --- 生成单条摘要 ---
def generate_summary(content):
    prompt = f"""
    请对这条新闻进行极简总结（50字以内），并提取1个核心标签。
    格式要求：摘要内容|标签
    
    新闻内容：
    {content[:800]}
    """
    return call_gemini(prompt)

def main():
    # 1. 准备目录
    posts_dir = "docs/posts"
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)

    # 2. 获取时间
    tz = pytz.timezone('Asia/Shanghai')
    today = datetime.now(tz).strftime("%Y-%m-%d")
    now_time = datetime.now(tz).strftime("%H:%M")

    print(f"🚀 开始抓取: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ RSS 抓取失败或为空")
        return

    # 取前 10 条
    entries = feed.entries[:10]
    titles_list = [e.title for e in entries]
    
    # 3. 生成宏观综述
    print("🤖 正在生成宏观综述...")
    overview_text = generate_overview("\n".join(titles_list))
    if not overview_text:
        overview_text = "今日暂无 AI 生成的综述，请直接查看下方简讯。"

    # 4. 拼接 Markdown 头部
    # 使用 \n 换行，确保没有多余空格
    md = f"# 📅 舆情日报 {today}\n\n"
    md += f'<div class="update-time">更新于北京时间 {now_time}</div>\n\n'

    md += '<div class="daily-overview">\n'
    md += '<h3>🛡️ AI 核心情报</h3>\n'
    md += f'<p>{overview_text}</p>\n'
    md += '</div>\n\n'

    md += '<div class="news-list">\n'

    # 5. 循环处理每条新闻
    for i, entry in enumerate(entries):
        print(f"[{i+1}/{len(entries)}] 处理: {entry.title}")
        
        content = entry.summary if 'summary' in entry else entry.title
        ai_res = generate_summary(content)
        
        summary = "AI 暂未生成摘要"
        tag = "资讯"
        
        if ai_res and "|" in ai_res:
            parts = ai_res.split("|")
            summary = parts[0].strip()
            if len(parts) > 1: tag = parts[1].strip()
        elif ai_res:
            summary = ai_res

        # --- 🔴 关键修改：使用拼接方式，确保 0 缩进 ---
        card = ""
        card += '<div class="news-card">\n'
        card += f'<h4><a href="{entry.link}" target="_blank">{entry.title}</a></h4>\n'
        card += f'<div class="summary">{summary}</div>\n'
        card += '<div class="news-meta">\n'
        card += f'<span class="tag-pill">{tag}</span>\n'
        card += '<span class="source-name">36Kr</span>\n'
        card += '</div>\n'
        card += '</div>\n\n'
        
        md += card
        
        # 简单限速
        time.sleep(1)

    md += '</div>\n' # 闭合 news-list

    # 6. 保存文件
    file_path = os.path.join(posts_dir, f"{today}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md)
    
    # 复制为 latest.md
    shutil.copy(file_path, os.path.join(posts_dir, "latest.md"))
    print(f"✅ 完成！文件已生成：{file_path}")

if __name__ == "__main__":
    main()
