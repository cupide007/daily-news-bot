import feedparser
import requests
import os
import shutil
from datetime import datetime
import pytz

RSS_URL = "https://36kr.com/feed" 
API_KEY = os.environ.get("GEMINI_API_KEY")

def summarize_with_ai(content):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = f"请阅读以下新闻，用中文写一段摘要（50-80字），并提取1个标签。格式：摘要|标签\n\n内容：{content[:1500]}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200: return "AI生成失败|Error"
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "AI未响应|Error"

def main():
    # 1. 准备目录
    posts_dir = "docs/posts"
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)

    # 2. 获取时间
    tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    
    feed = feedparser.parse(RSS_URL)
    
    # 3. 生成 Markdown 内容
    md_content = f"# 📅 每日简报 {today_str}\n\n"
    md_content += f"> 更新时间：{datetime.now(tz).strftime('%H:%M')}\n\n"
    
    for entry in feed.entries[:10]: # 每天取前10条
        print(f"处理: {entry.title}")
        content = entry.summary if 'summary' in entry else entry.title
        res = summarize_with_ai(content)
        
        if "|" in res:
            summary, tag = res.split("|", 1)
        else:
            summary, tag = res, "News"
            
        # ⚠️ 这里是还原目标网站样式的关键 Markdown 格式
        md_content += f"### [{entry.title}]({entry.link})\n"
        md_content += f"- **标签**: `{tag.strip()}`\n"
        md_content += f"- **摘要**: {summary}\n\n"
        md_content += "---\n\n"

    # 4. 保存文件：例如 docs/posts/2025-12-21.md
    filename = os.path.join(posts_dir, f"{today_str}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    # 5. 同时更新 latest.md (方便首页按钮点击直接看最新的)
    shutil.copy(filename, os.path.join(posts_dir, "latest.md"))
    
    print(f"✅ 成功生成: {filename}")

if __name__ == "__main__":
    main()
    
    # 写入 index.html (这是 GitHub Pages 的默认入口)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("网页生成完毕！")

if __name__ == "__main__":
    main()
